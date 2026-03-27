"""
AI 选股系统
基于机器学习的智能选股策略
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from datetime import datetime, timedelta


class AISelector:
    """AI 选股器"""
    
    def __init__(self, model_type: str = "lightgbm"):
        """
        初始化 AI 选股器
        
        :param model_type: 模型类型 ("lightgbm", "xgboost", "sklearn")
        """
        self.model_type = model_type
        self.model = None
        self.feature_cols = []
        self.is_trained = False
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        准备特征数据
        
        :param df: 原始数据
        :return: 特征数据
        """
        features = pd.DataFrame()
        
        # 基础特征
        if 'close' in df.columns:
            features['close'] = df['close']
            features['volume'] = df.get('volume', 0)
            features['high'] = df.get('high', df['close'])
            features['low'] = df.get('low', df['close'])
            
            # 价格变化率
            features['returns'] = df['close'].pct_change()
            
            # 移动平均
            for window in [5, 10, 20, 60]:
                features[f'ma_{window}'] = df['close'].rolling(window).mean()
                features[f'ma_ratio_{window}'] = df['close'] / features[f'ma_{window}']
            
            # 波动率
            features['volatility_5'] = df['close'].pct_change().rolling(5).std()
            features['volatility_20'] = df['close'].pct_change().rolling(20).std()
            
        return features.fillna(0)
    
    def create_label(self, df: pd.DataFrame, forward_days: int = 5, threshold: float = 0.05) -> pd.Series:
        """
        创建标签: 未来forward_days天涨幅超过threshold为正样本
        
        :param df: 原始数据
        :param forward_days: 未来天数
        :param threshold: 阈值
        :return: 标签
        """
        future_returns = df['close'].shift(-forward_days) / df['close'] - 1
        labels = (future_returns > threshold).astype(int)
        return labels
    
    def train(self, data: pd.DataFrame, target_col: str = "label"):
        """
        训练模型
        
        :param data: 训练数据
        :param target_col: 目标列名
        """
        if target_col not in data.columns:
            # 自动创建标签
            data[target_col] = self.create_label(data)
        
        # 准备特征
        X = self.prepare_features(data)
        y = data[target_col]
        
        self.feature_cols = X.columns.tolist()
        
        # 根据模型类型选择训练方法
        if self.model_type == "lightgbm":
            self._train_lightgbm(X, y)
        elif self.model_type == "xgboost":
            self._train_xgboost(X, y)
        else:
            self._train_sklearn(X, y)
            
        self.is_trained = True
        print(f"模型训练完成，使用特征数: {len(self.feature_cols)}")
    
    def _train_lightgbm(self, X, y):
        """训练 LightGBM 模型"""
        try:
            import lightgbm as lgb
            self.model = lgb.LGBMClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                num_leaves=31
            )
            self.model.fit(X, y)
        except ImportError:
            print("lightgbm 未安装，使用 sklearn 替代")
            self._train_sklearn(X, y)
    
    def _train_xgboost(self, X, y):
        """训练 XGBoost 模型"""
        try:
            import xgboost as xgb
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5
            )
            self.model.fit(X, y)
        except ImportError:
            print("xgboost 未安装，使用 sklearn 替代")
            self._train_sklearn(X, y)
    
    def _train_sklearn(self, X, y):
        """训练 sklearn 模型"""
        from sklearn.ensemble import RandomForestClassifier
        self.model = RandomForestClassifier(n_estimators=100, max_depth=5)
        self.model.fit(X, y)
    
    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        预测选股
        
        :param data: 待预测数据
        :return: 预测结果
        """
        if not self.is_trained:
            raise ValueError("模型未训练，请先调用 train 方法")
        
        X = self.prepare_features(data)
        
        # 确保特征列一致
        for col in self.feature_cols:
            if col not in X.columns:
                X[col] = 0
        X = X[self.feature_cols]
        
        # 预测概率
        proba = self.model.predict_proba(X)[:, 1]
        
        result = pd.DataFrame({
            'code': data.get('code', 'UNKNOWN'),
            'date': data.get('date', pd.Series(range(len(data)))),
            'score': proba
        })
        
        return result.sort_values('score', ascending=False)
    
    def select_top(self, data: pd.DataFrame, top_n: int = 10) -> List[str]:
        """
        选出 Top N 股票
        
        :param data: 待选数据
        :param top_n: 选股数量
        :return: 股票代码列表
        """
        result = self.predict(data)
        return result.head(top_n)['code'].tolist()


class FactorAISelector(AISelector):
    """基于因子的 AI 选股器"""
    
    def __init__(self, model_type: str = "lightgbm"):
        super().__init__(model_type)
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        使用 QUANTAXIS 因子库的特征
        """
        from QUANTAXIS.QAFactor.factors import calculate_all_technical_factors
        
        features = pd.DataFrame()
        
        # 使用因子库计算技术因子
        try:
            factor_data = calculate_all_technical_factors(df)
            if not factor_data.empty:
                # 合并因子特征
                factor_cols = [c for c in factor_data.columns if c not in ['date', 'code']]
                for col in factor_cols:
                    features[col] = factor_data[col]
        except Exception as e:
            print(f"因子计算失败: {e}")
        
        # 基础特征
        if 'close' in df.columns:
            features['close'] = df['close']
            features['volume'] = df.get('volume', 0)
            features['returns'] = df['close'].pct_change()
        
        return features.fillna(0)


class EnsembleSelector:
    """集成选股器 - 结合多个模型"""
    
    def __init__(self, selectors: List[AISelector] = None):
        self.selectors = selectors or []
    
    def add_selector(self, selector: AISelector):
        """添加选股器"""
        self.selectors.append(selector)
    
    def select(self, data: pd.DataFrame, weights: List[float] = None) -> pd.DataFrame:
        """
        集成选择
        
        :param data: 数据
        :param weights: 权重
        :return: 集成结果
        """
        if not self.selectors:
            raise ValueError("没有选股器")
        
        weights = weights or [1.0] * len(self.selectors)
        weights = [w / sum(weights) for w in weights]  # 归一化
        
        results = []
        for selector in self.selectors:
            try:
                r = selector.predict(data)
                results.append(r['score'] * weights[len(results)])
            except Exception as e:
                print(f"选股器预测失败: {e}")
        
        if not results:
            return pd.DataFrame()
        
        # 合并结果
        ensemble_score = sum(results)
        
        result = pd.DataFrame({
            'code': data.get('code', 'UNKNOWN'),
            'date': data.get('date', pd.Series(range(len(data)))),
            'score': ensemble_score
        })
        
        return result.sort_values('score', ascending=False)


# 使用示例
if __name__ == "__main__":
    # 创建模拟数据
    dates = pd.date_range("2024-01-01", periods=200)
    data = pd.DataFrame({
        'date': dates,
        'code': '000001',
        'close': np.random.randn(200).cumsum() + 100,
        'volume': np.random.randint(1000000, 10000000, 200)
    })
    
    # 创建并训练选股器
    selector = AISelector(model_type="sklearn")
    selector.train(data)
    
    # 选股
    top_stocks = selector.select_top(data, top_n=5)
    print(f"推荐股票: {top_stocks}")