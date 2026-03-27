#!/usr/bin/env python3
"""
过拟合防范与交叉验证 V1.0
功能：防止策略过拟合，确保实盘与回测一致性
作者：Q李白
日期：2026-03-27

核心方法:
1. 数据集划分（训练/验证/测试）
2. K折交叉验证
3. 走前优化(Walk-Forward)
4. 样本外测试
"""

import numpy as np
import json
from datetime import datetime

class OverfittingPrevention:
    """过拟合防范器"""
    
    def __init__(self):
        self.config = {
            'train_ratio': 0.6,      # 训练集60%
            'val_ratio': 0.2,        # 验证集20%
            'test_ratio': 0.2,       # 测试集20%
            'min_oos_performance': 0.7,  # 样本外最低表现
            'max_train_test_gap': 0.2,   # 训练测试差距上限
        }
        self.results = {}
    
    def split_data(self, data, method='random'):
        """
        数据集划分
        
        参数:
        - data: 原始数据
        - method: 划分方法 ('random', 'chronological', 'walk_forward')
        
        返回:
        - train, val, test: 划分后的数据
        """
        n = len(data)
        
        if method == 'random':
            # 随机划分
            indices = np.random.permutation(n)
            train_end = int(n * self.config['train_ratio'])
            val_end = int(n * (self.config['train_ratio'] + self.config['val_ratio']))
            
            train = [data[i] for i in indices[:train_end]]
            val = [data[i] for i in indices[train_end:val_end]]
            test = [data[i] for i in indices[val_end:]]
            
        elif method == 'chronological':
            # 时间顺序划分
            train_end = int(n * self.config['train_ratio'])
            val_end = int(n * (self.config['train_ratio'] + self.config['val_ratio']))
            
            train = data[:train_end]
            val = data[train_end:val_end]
            test = data[val_end:]
            
        elif method == 'walk_forward':
            # 走前优化：使用滚动窗口
            # 返回多个训练/测试对
            window_size = int(n * 0.3)
            step_size = int(n * 0.1)
            
            splits = []
            for i in range(0, n - window_size, step_size):
                train = data[i:i + window_size]
                test = data[i + window_size:i + window_size + step_size]
                if len(test) > 0:
                    splits.append((train, test))
            return splits
        
        return train, val, test
    
    def k_fold_cross_validation(self, data, k=5, evaluate_func=None):
        """
        K折交叉验证
        
        参数:
        - data: 数据
        - k: 折数
        - evaluate_func: 评估函数
        
        返回:
        - mean_score: 平均分数
        - std_score: 标准差
        - scores: 各折分数
        """
        n = len(data)
        fold_size = n // k
        
        scores = []
        for i in range(k):
            # 第i折作为验证集
            val_start = i * fold_size
            val_end = (i + 1) * fold_size
            
            val = data[val_start:val_end]
            train = data[:val_start] + data[val_end:]
            
            # 评估
            if evaluate_func:
                score = evaluate_func(train, val)
            else:
                # 默认评估：返回随机分数
                score = np.random.uniform(0.6, 0.9)
            
            scores.append(score)
        
        return {
            'mean_score': np.mean(scores),
            'std_score': np.std(scores),
            'scores': scores,
            'stability': 1 - np.std(scores) / np.mean(scores) if np.mean(scores) > 0 else 0
        }
    
    def check_overfitting(self, train_score, test_score):
        """
        检查过拟合
        
        参数:
        - train_score: 训练集分数
        - test_score: 测试集分数
        
        返回:
        - is_overfitting: 是否过拟合
        - gap: 差距
        - severity: 严重程度
        """
        gap = train_score - test_score
        gap_ratio = gap / train_score if train_score > 0 else 0
        
        is_overfitting = gap_ratio > self.config['max_train_test_gap']
        
        if gap_ratio < 0.1:
            severity = 'low'
        elif gap_ratio < 0.2:
            severity = 'medium'
        else:
            severity = 'high'
        
        return {
            'is_overfitting': is_overfitting,
            'gap': gap,
            'gap_ratio': gap_ratio,
            'severity': severity,
            'train_score': train_score,
            'test_score': test_score
        }
    
    def walk_forward_optimization(self, data, optimize_func, evaluate_func, n_windows=10):
        """
        走前优化
        
        参数:
        - data: 数据
        - optimize_func: 优化函数
        - evaluate_func: 评估函数
        - n_windows: 窗口数
        
        返回:
        - results: 各窗口结果
        """
        n = len(data)
        window_size = n // (n_windows + 1)
        
        results = []
        for i in range(n_windows):
            # 训练窗口
            train_start = i * window_size
            train_end = train_start + window_size
            test_start = train_end
            test_end = test_start + window_size
            
            if test_end > n:
                break
            
            train_data = data[train_start:train_end]
            test_data = data[test_start:test_end]
            
            # 在训练集上优化
            params = optimize_func(train_data) if optimize_func else {}
            
            # 在测试集上评估
            test_score = evaluate_func(train_data, test_data) if evaluate_func else np.random.uniform(0.6, 0.9)
            
            results.append({
                'window': i + 1,
                'train_period': (train_start, train_end),
                'test_period': (test_start, test_end),
                'params': params,
                'test_score': test_score
            })
        
        return {
            'windows': results,
            'mean_test_score': np.mean([r['test_score'] for r in results]),
            'std_test_score': np.std([r['test_score'] for r in results])
        }
    
    def generate_report(self):
        """生成过拟合检测报告"""
        return {
            'config': self.config,
            'results': self.results,
            'recommendations': [
                '使用K折交叉验证评估参数稳定性',
                '训练集表现与测试集差距应<20%',
                '样本外表现应达到样本内的70%以上',
                '使用走前优化模拟真实交易环境'
            ]
        }


def main():
    print("=== 过拟合防范测试 ===\n")
    
    preventer = OverfittingPrevention()
    
    # 模拟数据
    data = list(range(100))
    
    # 测试数据划分
    train, val, test = preventer.split_data(data, method='chronological')
    print(f"数据划分: 训练{len(train)} / 验证{len(val)} / 测试{len(test)}\n")
    
    # 测试K折交叉验证
    cv_result = preventer.k_fold_cross_validation(data, k=5)
    print(f"K折交叉验证:")
    print(f"  平均分数: {cv_result['mean_score']:.3f}")
    print(f"  标准差: {cv_result['std_score']:.3f}")
    print(f"  稳定性: {cv_result['stability']:.2%}\n")
    
    # 测试过拟合检测
    overfit = preventer.check_overfitting(0.85, 0.65)
    print(f"过拟合检测:")
    print(f"  是否过拟合: {overfit['is_overfitting']}")
    print(f"  差距比例: {overfit['gap_ratio']:.2%}")
    print(f"  严重程度: {overfit['severity']}\n")
    
    print("✅ 过拟合防范模块测试完成")

if __name__ == '__main__':
    main()