#!/usr/bin/env python3
"""
手续费覆盖度计算器 V1.0
功能：计算费率套利的实际收益，扣除手续费后的净收益
作者：Q李白
日期：2026-03-27
"""

import json
from datetime import datetime

# 手续费配置（各交易所taker费率）
FEE_RATES = {
    'gate': 0.0005,    # 0.05%
    'bitget': 0.0006,  # 0.06%
    'aster': 0.0005,   # 0.05%
    'okx': 0.0005,     # 0.05%
}

# 每日结算次数
SETTLEMENTS_PER_DAY = 3

def calculate_coverage(rate_diff, exchanges=['gate', 'bitget'], trades_per_day=6):
    """
    计算手续费覆盖度
    
    参数:
    - rate_diff: 费率差异（小数，如0.001 = 0.1%）
    - exchanges: 使用的交易所列表
    - trades_per_day: 每日交易次数（开仓+平仓算2次）
    
    返回:
    - coverage: 覆盖度（0-1）
    - net_profit: 净收益率
    - is_profitable: 是否值得开仓
    """
    # 计算平均手续费率
    avg_fee = sum(FEE_RATES.get(ex, 0.0005) for ex in exchanges) / len(exchanges)
    
    # 每次交易手续费（开仓+平仓各一次）
    trade_fee = avg_fee * 2
    
    # 每日总手续费成本
    daily_fee_cost = trade_fee * trades_per_day / 2  # 每次往返交易
    
    # 每日费率收益（假设3次结算）
    daily_rate_income = rate_diff * SETTLEMENTS_PER_DAY
    
    # 净收益
    net_profit = daily_rate_income - daily_fee_cost
    
    # 覆盖度 = (收益 - 成本) / 收益
    if daily_rate_income > 0:
        coverage = max(0, net_profit / daily_rate_income)
    else:
        coverage = 0
    
    # 是否值得开仓（覆盖度>0.5且净收益为正）
    is_profitable = coverage > 0.5 and net_profit > 0
    
    return {
        'coverage': round(coverage, 4),
        'net_profit': round(net_profit, 6),
        'daily_fee_cost': round(daily_fee_cost, 6),
        'daily_rate_income': round(daily_rate_income, 6),
        'is_profitable': is_profitable
    }

def score_opportunity(rate_diff, exchanges, liquidity_score=0.8, stability_score=0.7):
    """
    综合评分模型（优化版）
    
    评分维度:
    - 费率差异：35%
    - 手续费覆盖度：15% (新增)
    - 流动性：20%
    - 历史稳定性：15%
    - 交易量：15%
    """
    coverage_data = calculate_coverage(rate_diff, exchanges)
    
    # 各项评分（0-100）
    rate_score = min(100, rate_diff * 1000)  # 0.1% = 100分
    coverage_score = coverage_data['coverage'] * 100
    liq_score = liquidity_score * 100
    stability_score_val = stability_score * 100
    volume_score = 70  # 默认值
    
    # 加权平均
    total_score = (
        rate_score * 0.35 +
        coverage_score * 0.15 +
        liq_score * 0.20 +
        stability_score_val * 0.15 +
        volume_score * 0.15
    )
    
    return {
        'total_score': round(total_score, 2),
        'rate_score': round(rate_score, 2),
        'coverage_score': round(coverage_score, 2),
        'coverage_data': coverage_data,
        'recommendation': 'PASS' if coverage_data['is_profitable'] else 'SKIP'
    }

def main():
    print("=== 手续费覆盖度计算器 ===\n")
    
    # 测试案例
    test_cases = [
        {'rate_diff': 0.001, 'exchanges': ['gate', 'bitget']},  # 0.1%差异
        {'rate_diff': 0.0005, 'exchanges': ['gate', 'bitget']},  # 0.05%差异
        {'rate_diff': 0.002, 'exchanges': ['gate', 'aster']},    # 0.2%差异
        {'rate_diff': 0.0003, 'exchanges': ['gate', 'bitget']},  # 0.03%差异
    ]
    
    for i, tc in enumerate(test_cases, 1):
        result = score_opportunity(tc['rate_diff'], tc['exchanges'])
        print(f"案例 {i}: 费率差异 {tc['rate_diff']*100:.2f}%")
        print(f"  覆盖度: {result['coverage_data']['coverage']*100:.1f}%")
        print(f"  净收益: {result['coverage_data']['net_profit']*100:.4f}%/天")
        print(f"  总分: {result['total_score']}")
        print(f"  建议: {result['recommendation']}")
        print()

if __name__ == '__main__':
    main()