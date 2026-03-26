#!/usr/bin/env python3
"""
三李白资金费率套利扫描器
综合扫描 Gate + Bitget + Aster 三大交易所，识别套利机会
"""

import os
import sys
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 添加脚本路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入各交易所扫描器
try:
    from scan_gate import get_funding_rates as get_gate_rates
except ImportError:
    get_gate_rates = lambda: []

try:
    from scan_bg import get_funding_rates as get_bg_rates
except ImportError:
    get_bg_rates = lambda: []

try:
    from scan_aster import get_funding_rates as get_aster_rates
except ImportError:
    get_aster_rates = lambda: []

def scan_all():
    """并行扫描所有交易所"""
    print("=== 三李白资金费率套利扫描器 ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        gate_future = executor.submit(get_gate_rates)
        bg_future = executor.submit(get_bg_rates)
        aster_future = executor.submit(get_aster_rates)
        
        gate_rates = gate_future.result()
        bg_rates = bg_future.result()
        aster_rates = aster_future.result()
    
    print(f"Gate:   {len(gate_rates)} contracts")
    print(f"Bitget: {len(bg_rates)} contracts")
    print(f"Aster:  {len(aster_rates)} contracts")
    print()
    
    # 构建符号映射
    gate_map = {r['symbol']: r for r in gate_rates}
    bg_map = {r['symbol']: r for r in bg_rates}
    aster_map = {r['symbol']: r for r in aster_rates}
    
    # 找出套利机会
    opportunities = []
    
    # 所有交易所共有的品种
    all_symbols = set(gate_map.keys()) | set(bg_map.keys()) | set(aster_map.keys())
    
    for symbol in all_symbols:
        gate_r = gate_map.get(symbol)
        bg_r = bg_map.get(symbol)
        aster_r = aster_map.get(symbol)
        
        # 计算套利机会
        rates = []
        if gate_r:
            rates.append(('Gate', gate_r['funding_rate']))
        if bg_r:
            rates.append(('Bitget', bg_r['funding_rate']))
        if aster_r:
            rates.append(('Aster', aster_r['funding_rate']))
        
        if len(rates) >= 2:
            # 找最大正费率和最大负费率
            rates.sort(key=lambda x: x[1], reverse=True)
            max_long = rates[0]  # 最大正费率 = 做多端
            max_short = rates[-1]  # 最大负费率 = 做空端
            
            spread = max_long[1] - max_short[1]
            
            if spread > 0.01:  # 差异 > 0.01%
                daily_return = spread * 3  # 每天3次结算
                
                # 风险评分
                risk = 'LOW'
                if spread > 0.05:
                    risk = 'MEDIUM'
                if spread > 0.1:
                    risk = 'HIGH'
                
                opportunities.append({
                    'symbol': symbol,
                    'long_exchange': max_long[0],
                    'long_rate': max_long[1],
                    'short_exchange': max_short[0],
                    'short_rate': max_short[1],
                    'spread': round(spread, 4),
                    'daily_return': round(daily_return, 4),
                    'risk': risk
                })
    
    # 按日收益排序
    opportunities.sort(key=lambda x: x['daily_return'], reverse=True)
    
    if not opportunities:
        print("No significant arbitrage opportunities found.")
        return []
    
    print(f"=== 发现 {len(opportunities)} 个套利机会 ===\n")
    print(f"{'Symbol':<12} {'Long':>8} {'L-Rate':>8} {'Short':>8} {'S-Rate':>8} {'Spread':>8} {'Daily':>8} {'Risk':>8}")
    print("-" * 80)
    
    for opp in opportunities[:15]:
        print(f"{opp['symbol']:<12} "
              f"{opp['long_exchange']:>8} {opp['long_rate']:>7.4f}% "
              f"{opp['short_exchange']:>8} {opp['short_rate']:>7.4f}% "
              f"{opp['spread']:>7.4f}% {opp['daily_return']:>7.4f}% "
              f"{opp['risk']:>8}")
    
    return opportunities

if __name__ == "__main__":
    scan_all()