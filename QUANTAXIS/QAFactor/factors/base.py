# coding:utf-8
#
# The MIT License (MIT)
#
# Copyright (c) 2016-2021 yutiansut/QUANTAXIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
扩展因子基类

支持多字段因子的基类，继承自 QASingleFactor_DailyBase
"""

import datetime
from typing import List, Optional

import clickhouse_driver
import pandas as pd
from qaenv import (clickhouse_ip, clickhouse_password, clickhouse_port,
                   clickhouse_user)

from QUANTAXIS.QAFactor.feature import QASingleFactor_DailyBase


class QAMultiFactor_DailyBase(QASingleFactor_DailyBase):
    """
    支持多字段因子的基类
    
    继承自 QASingleFactor_DailyBase，但支持返回多个因子列
    每个因子类只需指定要提取的列名即可
    
    Usage:
        class MyFactor(QAMultiFactor_DailyBase):
            factor_name = 'my_factor'
            factor_column = 'DIF'  # 指定从指标结果中取哪一列
            
            def calc(self) -> pd.DataFrame:
                data = self.clientr.get_stock_day_qfq_adv(...)
                result = data.add_func(QA_indicator_MACD)
                return result
    """
    
    # 子类需要覆盖的类属性
    factor_column: str = ''  # 要提取的列名
    
    def __init__(self, factor_name: str = None, host=None, port=None, 
                 user=None, password=None, **kwargs):
        # 如果未指定 factor_name，使用 factor_column
        if factor_name is None:
            factor_name = self.factor_column or self.__class__.__name__
        
        super().__init__(factor_name=factor_name, host=host, port=port, 
                         user=user, password=password, **kwargs)
        
    def init_database(self):
        """初始化数据库表，支持单因子列存储"""
        self.client.execute('CREATE TABLE IF NOT EXISTS \
                            `factor`.`{}` (\
                            date Date,\
                            code String,\
                            factor Float32\
                            )\
                            ENGINE = ReplacingMergeTree() \
                            ORDER BY (date, code)\
                            SETTINGS index_granularity=8192'.format(self.factor_name))
    
    def calc(self) -> pd.DataFrame:
        """
        计算因子值
        
        Returns:
            pd.DataFrame with columns ['date', 'code', 'factor']
        """
        raise NotImplementedError
    
    def _extract_column(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        从多列数据中提取指定列
        
        Args:
            data: 包含多个因子列的 DataFrame
            
        Returns:
            提取后的 DataFrame，列名为 'factor'
        """
        if self.factor_column not in data.columns:
            raise ValueError(f"Column '{self.factor_column}' not found in data. "
                           f"Available columns: {list(data.columns)}")
        
        result = pd.DataFrame({
            'date': data['date'],
            'code': data['code'],
            'factor': data[self.factor_column]
        })
        return result.dropna()


class QAMultiColumnsFactor_DailyBase(QASingleFactor_DailyBase):
    """
    支持多列同时存储的因子基类
    
    适用于需要同时存储多个因子列的场景
    
    Usage:
        class MACDFactor(QAMultiColumnsFactor_DailyBase):
            factor_name = 'MACD'
            factor_columns = ['DIF', 'DEA', 'MACD']
            
            def calc(self) -> pd.DataFrame:
                # 返回包含多个因子列的数据
                pass
    """
    
    factor_columns: List[str] = []  # 要存储的列名列表
    
    def __init__(self, factor_name: str = None, host=None, port=None,
                 user=None, password=None, **kwargs):
        super().__init__(factor_name=factor_name or self.factor_name,
                        host=host, port=port, user=user, password=password, **kwargs)
    
    def init_database(self):
        """初始化多列表格"""
        columns_def = 'date Date, code String, ' + ', '.join(
            f'{col} Float32' for col in self.factor_columns
        )
        
        self.client.execute('CREATE TABLE IF NOT EXISTS \
                            `factor`.`{}` (\
                            {})\
                            ENGINE = ReplacingMergeTree() \
                            ORDER BY (date, code)\
                            SETTINGS index_granularity=8192'.format(
                                self.factor_name, columns_def))
    
    def insert_data(self, data: pd.DataFrame):
        """插入多列数据"""
        # 检查列
        data = data.copy()
        for col in self.factor_columns:
            if col not in data.columns:
                raise ValueError(f"Column '{col}' not found in data")
        
        data['date'] = pd.to_datetime(data['date'])
        
        # 确保factor列为float
        for col in self.factor_columns:
            data[col] = data[col].astype(float)
        
        data = data.to_dict('records')
        
        self.client.execute('INSERT INTO {} VALUES'.format(
            self.factor_name), data)
        
        self.client.execute('OPTIMIZE TABLE {} FINAL'.format(self.factor_name))
    
    def calc(self) -> pd.DataFrame:
        """
        Returns:
            pd.DataFrame with columns ['date', 'code', 'factor1', 'factor2', ...]
        """
        raise NotImplementedError


class QATechnicalFactorBase(QAMultiFactor_DailyBase):
    """
    技术因子基类
    
    提供获取行情数据和计算指标的通用方法
    """
    
    # 子类需要覆盖
    indicator_func = None  # QA_indicator_XXX 函数
    indicator_params: dict = {}  # 指标参数
    
    def finit(self):
        """初始化数据客户端"""
        try:
            from QUANTAXIS.QARealtimeDatahub import DataHub
            self.clientr = DataHub()
        except ImportError:
            # 如果没有实时数据Hub，使用备用方案
            self.clientr = None
    
    def get_market_data(self, code: str, start: str, end: str) -> pd.DataFrame:
        """
        获取行情数据
        
        Args:
            code: 股票代码
            start: 开始日期
            end: 结束日期
            
        Returns:
            pd.DataFrame with OHLCV columns
        """
        if self.clientr is None:
            raise RuntimeError("Data client not initialized")
        
        data = self.clientr.get_stock_day_qfq_adv(
            code, start, end
        )
        return data
    
    def calc_indicator(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算指标"""
        if self.indicator_func is None:
            raise NotImplementedError("indicator_func not set")
        
        if hasattr(data, 'add_func'):
            return data.add_func(self.indicator_func, **self.indicator_params)
        else:
            return self.indicator_func(data, **self.indicator_params)