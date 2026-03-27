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
因子注册装饰器

提供因子注册功能，便于因子管理和查找
"""

from typing import Callable, Dict, Type

# 全局因子注册表
_FACTOR_REGISTRY: Dict[str, Type] = {}


def register_factor(name: str, description: str = "", category: str = "technical"):
    """
    因子注册装饰器
    
    Args:
        name: 因子名称
        description: 因子描述
        category: 因子分类 (technical/sentiment/fundamental/industry)
        
    Usage:
        @register_factor("MACD_DIF", "MACD差值因子", "technical")
        class MACD_DIF_Factor(QAMultiFactor_DailyBase):
            factor_column = 'DIF'
            ...
    
    Returns:
        装饰器函数
    """
    def wrapper(cls):
        cls.factor_name = name
        cls.description = description
        cls.category = category
        
        # 注册到全局表
        _FACTOR_REGISTRY[name] = cls
        
        return cls
    return wrapper


def get_factor(name: str) -> Type:
    """
    获取注册的因子类
    
    Args:
        name: 因子名称
        
    Returns:
        因子类
        
    Raises:
        KeyError: 因子不存在
    """
    if name not in _FACTOR_REGISTRY:
        raise KeyError(f"Factor '{name}' not found in registry. "
                      f"Available factors: {list_factors()}")
    return _FACTOR_REGISTRY[name]


def list_factors(category: str = None) -> Dict[str, Dict]:
    """
    列出所有已注册的因子
    
    Args:
        category: 可选过滤分类
        
    Returns:
        {因子名: {description, category, class}}
    """
    result = {}
    for name, cls in _FACTOR_REGISTRY.items():
        if category is None or getattr(cls, 'category', None) == category:
            result[name] = {
                'description': getattr(cls, 'description', ''),
                'category': getattr(cls, 'category', 'unknown'),
                'class': cls
            }
    return result


def clear_registry():
    """清空因子注册表（主要用于测试）"""
    _FACTOR_REGISTRY.clear()


# 自动注册表 - 存储需要自动发现的因子类
_AUTOREGISTERED_FACTORS = []


def autoreregister(cls: Type) -> Type:
    """
    自动注册装饰器
    
    用于标记需要被自动发现的因子类
    配合 FactorFactory 使用
    
    Args:
        cls: 因子类
        
    Returns:
        因子类（带标记）
    """
    cls._autoreregister = True
    _AUTOREGISTERED_FACTORS.append(cls)
    return cls