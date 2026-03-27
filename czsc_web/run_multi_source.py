# -*- coding: utf-8 -*-
"""
缠论分析 Web 服务 - 支持多数据源
包括: Tushare Pro / 聚宽 / 掘金 / 天勤 / 通达信 / 华宝

作者: beyondjjw (基于 zengbin93/czsc_web_ui 修改)
"""

import czsc
import json
import os
import time
import pandas as pd
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import define, options, parse_command_line
from tornado.web import RequestHandler, Application
from tornado.web import StaticFileHandler
from datetime import datetime, timedelta
from czsc import KlineAnalyze


# ============== 数据源适配器 ==============

class DataSourceAdapter:
    """数据源适配器基类"""
    
    def __init__(self):
        self.cache = {}
    
    @staticmethod
    def get_kline(ts_code, end_date, freq, asset='E'):
        raise NotImplementedError
    
    def get_klines(self, ts_code, end_date, freqs, asset='E'):
        """获取多周期K线"""
        result = {}
        for freq in freqs.split(','):
            try:
                kline = self.get_kline(ts_code, end_date, freq, asset)
                if kline is not None and len(kline) > 0:
                    result[freq] = kline
            except Exception as e:
                print(f"获取 {freq} 数据失败: {e}")
        return result


class TushareAdapter(DataSourceAdapter):
    """Tushare 数据源"""
    
    def __init__(self, token=None):
        super().__init__()
        import tushare as ts
        if token:
            ts.set_token(token)
        self.pro = ts.pro_api()
    
    def get_kline(self, ts_code, end_date, freq, asset='E'):
        try:
            from czsc.connectors.tushare import get_kline as tushare_kline
            return tushare_kline(ts_code, end_date, freq, asset)
        except:
            # 备用方案：直接使用 tushare
            return self._get_kline_direct(ts_code, end_date, freq)
    
    def _get_kline_direct(self, ts_code, end_date, freq):
        """直接使用 tushare 获取"""
        freq_map = {'1min': '1', '5min': '5', '15min': '15', '30min': '30', '60min': '60', 'D': 'D'}
        df = self.pro.daily(ts_code, start_date='20200101', end_date=end_date)
        if df is not None and len(df) > 0:
            df = df.sort_values('trade_date')
            df['dt'] = pd.to_datetime(df['trade_date'])
            return df
        return pd.DataFrame()


class JQDataAdapter(DataSourceAdapter):
    """聚宽数据源"""
    
    def __init__(self, token=None):
        super().__init__()
        self.token = token or os.getenv('JQDATA_TOKEN', '')
    
    def get_kline(self, ts_code, end_date, freq, asset='E'):
        try:
            from czsc.connectors.jqdata import get_kline as jq_kline
            return jq_kline(ts_code, end_date, freq, asset)
        except Exception as e:
            print(f"聚宽数据获取失败: {e}")
            return pd.DataFrame()


class GMAdapter(DataSourceAdapter):
    """掘金数据源"""
    
    def __init__(self, token=None):
        super().__init__()
        try:
            import gm
            self.gm = gm
            if token:
                self.gm.set_token(token)
        except ImportError:
            self.gm = None
    
    def get_kline(self, ts_code, end_date, freq, asset='E'):
        try:
            from czsc.connectors.gm import get_kline as gm_kline
            return gm_kline(ts_code, end_date, freq, asset)
        except Exception as e:
            print(f"掘金数据获取失败: {e}")
            return pd.DataFrame()


class TQAdapter(DataSourceAdapter):
    """天勤数据源"""
    
    def __init__(self, token=None):
        super().__init__()
        try:
            import tqsdk
            self.tq = tqsdk
        except ImportError:
            self.tq = None
    
    def get_kline(self, ts_code, end_date, freq, asset='E'):
        try:
            from czsc.connectors.tq import get_kline as tq_kline
            return tq_kline(ts_code, end_date, freq, asset)
        except Exception as e:
            print(f"天勤数据获取失败: {e}")
            return pd.DataFrame()


class TDXAdapter(DataSourceAdapter):
    """通达信数据源 (beyondjjw 定制)"""
    
    def __init__(self, ip_list=None, port=7709):
        super().__init__()
        self.ip_list = ip_list or [
            '121.14.110.84',  # 深圳
            '121.14.110.83',  # 上海
            '218.18.18.158',
            '218.18.18.159',
        ]
        self.port = port
        self.api = None
    
    def _get_api(self):
        """获取通达信API连接"""
        if self.api is None:
            try:
                from pytdx.hq import TdxHq_API
                self.api = TdxHq_API()
                for ip in self.ip_list:
                    try:
                        if self.api.connect(ip, self.port):
                            print(f"通达信连接成功: {ip}:{self.port}")
                            return self.api
                    except:
                        continue
                print("通达信: 所有IP连接失败")
                return None
            except ImportError:
                print("通达信: pytdx 未安装")
                return None
        return self.api
    
    def get_kline(self, ts_code, end_date, freq, asset='E'):
        """获取通达信K线"""
        api = self._get_api()
        if api is None:
            return pd.DataFrame()
        
        try:
            # 转换股票代码
            if '.' not in ts_code:
                ts_code = ts_code + '.SH' if ts_code.startswith('6') else ts_code + '.SZ'
            
            # 转换周期
            freq_map = {
                '1min': 1, '5min': 5, '15min': 15, 
                '30min': 30, '60min': 60, 'D': 0, 'W': 1, 'M': 2
            }
            tdx_freq = freq_map.get(freq, 30)
            
            # 计算起始日期
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            if freq == 'D':
                start_date = (end_dt - timedelta(days=2000)).strftime('%Y%m%d')
            elif freq == 'W':
                start_date = (end_dt - timedelta(days=7000)).strftime('%Y%m%d')
            else:
                start_date = (end_dt - timedelta(days=200)).strftime('%Y%m%d')
            
            # 获取数据
            df = api.get_kline_data(ts_code, tdx_freq, start_date, end_date)
            
            if df is not None and len(df) > 0:
                df['dt'] = pd.to_datetime(df['datetime'])
                df['close'] = df['close']
                df['open'] = df['open']
                df['high'] = df['high']
                df['low'] = df['low']
                df['volume'] = df['vol']
                return df.sort_values('dt')
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"通达信获取数据失败: {e}")
            return pd.DataFrame()
        finally:
            if api:
                try:
                    api.disconnect()
                except:
                    pass
    
    def __del__(self):
        if self.api:
            try:
                self.api.disconnect()
            except:
                pass


class LocalTDXAdapter(DataSourceAdapter):
    """本地通达信行情目录 (beyondjjw 定制)"""
    
    def __init__(self, tdx_path=None):
        """
        :param tdx_path: 通达信安装目录下的 T0002/dll 或自定义路径
        """
        super().__init__()
        self.tdx_path = tdx_path or os.getenv('TDX_PATH', '/home/ub/tdx')
    
    def get_kline(self, ts_code, end_date, freq, asset='E'):
        """从本地通达信目录读取K线"""
        try:
            # 转换股票代码格式
            if ts_code.startswith('6'):
                day_file = f"sh{ts_code}/day/{ts_code}.day"
            else:
                day_file = f"sz{ts_code}/day/{ts_code}.day"
            
            full_path = os.path.join(self.tdx_path, day_file)
            
            if not os.path.exists(full_path):
                print(f"通达信本地文件不存在: {full_path}")
                return pd.DataFrame()
            
            # 读取二进制文件
            with open(full_path, 'rb') as f:
                data = f.read()
            
            # 解析通达信 .day 文件格式
            records = []
            for i in range(0, len(data), 32):
                if i + 32 > len(data):
                    break
                chunk = data[i:i+32]
                # struct: date(4), open(4), high(4), low(4), close(4), vol(4), amount(8)
                import struct
                try:
                    date = struct.unpack('I', chunk[0:4])[0]
                    if date == 0:
                        continue
                    year = (date >> 16) & 0xFFFF
                    month = (date >> 8) & 0xFF
                    day = date & 0xFF
                    dt = datetime(year, month, day)
                    
                    record = {
                        'dt': dt,
                        'open': struct.unpack('f', chunk[4:8])[0],
                        'high': struct.unpack('f', chunk[8:12])[0],
                        'low': struct.unpack('f', chunk[12:16])[0],
                        'close': struct.unpack('f', chunk[16:20])[0],
                        'volume': struct.unpack('f', chunk[20:24])[0],
                    }
                    records.append(record)
                except:
                    continue
            
            df = pd.DataFrame(records)
            if len(df) > 0:
                df = df.sort_values('dt')
                # 过滤到指定日期
                end_dt = datetime.strptime(end_date, '%Y%m%d')
                df = df[df['dt'] <= end_dt]
            
            return df
            
        except Exception as e:
            print(f"读取通达信本地数据失败: {e}")
            return pd.DataFrame()


class GMMongoAdapter(DataSourceAdapter):
    """掘金增强版 + MongoDB 数据源 (beyondjjw 定制)"""
    
    def __init__(self):
        super().__init__()
    
    def get_kline(self, ts_code, end_date, freq, asset='E'):
        """使用QUANTAXIS获取K线"""
        try:
            from QUANTAXIS.QAFetch import QATdx
            # 使用通达信接口获取数据
            return QATdx.QA_fetch_get_stock_day(ts_code, start_date='20200101', end_date=end_date)
        except Exception as e:
            print(f"MongoDB数据获取失败: {e}")
            return pd.DataFrame()


class HuabaoAdapter(DataSourceAdapter):
    """华宝数据源 (beyondjjw 定制)"""
    
    def __init__(self):
        super().__init__()
    
    def get_kline(self, ts_code, end_date, freq, asset='E'):
        """使用华宝API获取K线"""
        try:
            from QUANTAXIS.czsc.czsc.gm_utils import get_huabao_kline
            return get_huabao_kline(ts_code, end_date, freq)
        except Exception as e:
            print(f"华宝数据获取失败: {e}")
            return pd.DataFrame()


# ============== 数据源工厂 ==============

def get_adapter(source: str) -> DataSourceAdapter:
    """获取数据源适配器"""
    adapters = {
        'ts': TushareAdapter,
        'jq': JQDataAdapter,
        'gm': GMAdapter,
        'tq': TQAdapter,
        'tdx': TDXAdapter,       # 通达信实时行情
        'tdx_local': LocalTDXAdapter,  # 通达信本地文件
        'gm_mongo': GMMongoAdapter,
        'huabao': HuabaoAdapter,
    }
    
    adapter_class = adapters.get(source, TushareAdapter)
    return adapter_class()


# ============== Web 服务 ==============

define("port", default=8005, help="run on the given port", type=int)
define("source", default="ts", help="data source: ts/jq/gm/tq/tdx/tdx_local/gm_mongo/huabao", type=str)


class CzscHandler(RequestHandler):
    """缠论分析接口"""
    
    def initialize(self, adapter):
        self.adapter = adapter
    
    def get(self):
        ts_code = self.get_argument("ts_code")
        trade_date = self.get_argument("trade_date")
        freqs = self.get_argument("freqs", "30min,D")
        
        try:
            # 获取K线数据
            klines = self.adapter.get_klines(ts_code, trade_date, freqs)
            
            if not klines:
                self.set_status(404)
                self.write(json.dumps({"error": "无数据"}, ensure_ascii=False))
                return
            
            # 缠论分析
            results = {}
            for freq, kline_df in klines.items():
                try:
                    if len(kline_df) < 30:
                        continue
                    
                    ka = KlineAnalyze(kline_df)
                    results[freq] = {
                        "symbol": ts_code,
                        "trade_date": trade_date,
                        "bars": len(ka.bars),
                        "bi_count": len(ka.bis),
                        "zd_count": len(ka.zhongduans),
                        "last_bi": ka.last_bi.to_dict() if ka.last_bi else None,
                        "last_zd": ka.last_zd.to_dict() if ka.last_zd else None,
                    }
                except Exception as e:
                    print(f"分析 {freq} 失败: {e}")
            
            self.write(json.dumps(results, ensure_ascii=False, indent=2))
            
        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}, ensure_ascii=False))


class MainHandler(RequestHandler):
    """主页"""
    
    def get(self):
        self.write("""
        <html>
        <head><title>缠论分析服务</title></head>
        <body>
        <h1>缠论分析服务</h1>
        <p>支持的参数:</p>
        <ul>
            <li>ts_code: 股票代码 (如 600122.SH)</li>
            <li>trade_date: 交易日期 (如 20230301)</li>
            <li>freqs: K线周期 (如 30min,D)</li>
        </ul>
        <p>示例: <a href="/api?ts_code=600122.SH&trade_date=20230301&freqs=30min,D">/api?ts_code=600122.SH&trade_date=20230301&freqs=30min,D</a></p>
        </body>
        </html>
        """)


def create_app(source='ts'):
    """创建应用"""
    adapter = get_adapter(source)
    
    application = Application([
        (r"/", MainHandler),
        (r"/api", CzscHandler, dict(adapter=adapter)),
        (r"/web/(.*)", StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "web")}),
    ])
    return application


def run_web(source='ts'):
    """启动Web服务"""
    parse_command_line()
    app = create_app(source)
    http_server = HTTPServer(app)
    http_server.listen(options.port)
    print(f"=" * 50)
    print(f"缠论分析服务已启动")
    print(f"数据源: {source}")
    print(f"端口: {options.port}")
    print(f"=" * 50)
    print(f"示例: http://localhost:{options.port}/api?ts_code=600122.SH&trade_date=20230301&freqs=30min,D")
    print(f"=" * 50)
    IOLoop.current().start()


if __name__ == "__main__":
    import sys
    source = sys.argv[1] if len(sys.argv) > 1 else 'ts'
    run_web(source)