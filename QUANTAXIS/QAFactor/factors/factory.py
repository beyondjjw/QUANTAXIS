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
因子工厂

快速创建和批量管理因子
"""

import pandas as pd
from typing import Dict, List, Type, Optional

from QUANTAXIS.QAFactor.factors.base import QAMultiFactor_DailyBase
from QUANTAXIS.QAFactor.factors.register import (
    _FACTOR_REGISTRY, get_factor, list_factors
)


class FactorFactory:
    """
    因子工厂类
    
    提供因子创建、批量计算、管理等功能
    """
    
    def __init__(self):
        self._factors: Dict[str, QAMultiFactor_DailyBase] = {}
    
    def create_factor(self, factor_name: str, **kwargs) -> QAMultiFactor_DailyBase:
        """
        创建因子实例
        
        Args:
            factor_name: 注册的因子名称
            **kwargs: 传给因子构造器的参数
            
        Returns:
            因子实例
            
        Example:
            factory = FactorFactory()
            macd = factory.create_factor('MACD_DIF')
            macd.update_to_database()
        """
        if factor_name in self._factors:
            return self._factors[factor_name]
        
        cls = get_factor(factor_name)
        instance = cls(**kwargs)
        self._factors[factor_name] = instance
        return instance
    
    def batch_create(self, factor_names: List[str], **kwargs) -> Dict[str, QAMultiFactor_DailyBase]:
        """
        批量创建因子
        
        Args:
            factor_names: 因子名称列表
            **kwargs: 通用参数
            
        Returns:
            {factor_name: instance}
        """
        result = {}
        for name in factor_names:
            result[name] = self.create_factor(name, **kwargs)
        return result
    
    def calculate_all(self, codes: List[str], start: str, end: str,
                      factors: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        批量计算多个因子
        
        Args:
            codes: 股票代码列表
            start: 开始日期
            end: 结束日期
            factors: 要计算的因子列表，None 表示全部
            
        Returns:
            {factor_name: dataframe}
        """
        if factors is None:
            factors = list(_FACTOR_REGISTRY.keys())
        
        results = {}
        for name in factors:
            try:
                factor = self.create_factor(name)
                results[name] = factor.calc()
            except Exception as e:
                print(f"Error calculating {name}: {e}")
        
        return results
    
    def update_all(self, codes: List[str], start: str, end: str,
                   factors: List[str] = None):
        """
        批量更新因子到数据库
        
        Args:
            codes: 股票代码列表
            start: 开始日期
            end: 结束日期
            factors: 要更新的因子列表
        """
        if factors is None:
            factors = list(_FACTOR_REGISTRY.keys())
        
        for name in factors:
            try:
                factor = self.create_factor(name)
                factor.update_to_database()
                print(f"Updated {name}")
            except Exception as e:
                print(f"Error updating {name}: {e}")
    
    def list_available_factors(self, category: str = None) -> List[str]:
        """
        列出可用的因子
        
        Args:
            category: 可选分类过滤
            
        Returns:
            因子名称列表
        """
        return list(list_factors(category).keys())
    
    def get_factor_info(self, factor_name: str) -> Optional[Dict]:
        """
        获取因子信息
        
        Args:
            factor_name: 因子名称
            
        Returns:
            {name, description, category, class} 或 None
        """
        factors = list_factors()
        return factors.get(factor_name)
    
    @property
    def factors(self) -> Dict[str, QAMultiFactor_DailyBase]:
        """已创建的因子实例"""
        return self._factors.copy()


# 全局工厂实例
_default_factory: Optional[FactorFactory] = None


def get_factory() -> FactorFactory:
    """获取全局因子工厂实例"""
    global _default_factory
    if _default_factory is None:
        _default_factory = FactorFactory()
    return _default_factory


def create_factor(factor_name: str, **kwargs) -> QAMultiFactor_DailyBase:
    """便捷函数：创建单个因子"""
    return get_factory().create_factor(factor_name, **kwargs)


def update_factor(factor_name: str, **kwargs):
    """便捷函数：更新因子到数据库"""
    factor = create_factor(factor_name, **kwargs)
    factor.update_to_database()