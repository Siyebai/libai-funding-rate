#!/usr/bin/env python3
"""
AI 品种选择器
基于资金费率差异、流动性、历史稳定性自动筛选最优套利品种
"""

import json
import math
from datetime import datetime

class AssetSelector:
    def __init__(self):
        # 权重配置
        self.weights = {
            'spread': 0.40,        # 费率差异权重
            'liquidity': 0.25,    # 流动性权重
            'stability': 0.20,    # 历史稳定性权重
            'volume': 0.15        # 交易量权重
        }
        
        # 阈值配置
        self.thresholds = {
            'min_spread': 0.10,           # 最小费率差异 0.10%
            'min_liquidity': 100000,      # 最小流动性 10万U
            'max_volatility': 0.50,       # 最大历史波动率
            'min_volume': 1000000         # 最小日交易量 100万U
        }
        
        # 黑名单
        self.blacklist = ['RDNT']  # BG error 45110
    
    def calculate_score(self, opportunity):
        """计算综合得分"""
        score = 0.0
        
        # 1. 费率差异得分（越高越好）
        spread = abs(opportunity.get('spread', 0))
        spread_score = min(spread / 0.5, 1.0) * 100  # 归一化到0-100
        score += spread_score * self.weights['spread']
        
        # 2. 流动性得分（越高越好）
        liquidity = opportunity.get('liquidity', 0)
        liquidity_score = min(liquidity / 1000000, 1.0) * 100
        score += liquidity_score * self.weights['liquidity']
        
        # 3. 稳定性得分（波动率越低越好）
        volatility = opportunity.get('volatility', 1.0)
        stability_score = max(0, 100 - volatility * 200)
        score += stability_score * self.weights['stability']
        
        # 4. 交易量得分
        volume = opportunity.get('volume', 0)
        volume_score = min(volume / 10000000, 1.0) * 100
        score += volume_score * self.weights['volume']
        
        return round(score, 2)
    
    def assess_risk(self, opportunity):
        """风险评估"""
        risk_score = 0
        risk_factors = []
        
        # 1. 极端费率风险
        spread = abs(opportunity.get('spread', 0))
        if spread > 0.5:
            risk_score += 30
            risk_factors.append('极端费率差异')
        elif spread > 0.3:
            risk_score += 15
            risk_factors.append('高费率差异')
        
        # 2. 流动性风险
        liquidity = opportunity.get('liquidity', 0)
        if liquidity < 50000:
            risk_score += 25
            risk_factors.append('低流动性')
        elif liquidity < 100000:
            risk_score += 10
            risk_factors.append('中等流动性')
        
        # 3. 波动性风险
        volatility = opportunity.get('volatility', 0)
        if volatility > 0.5:
            risk_score += 20
            risk_factors.append('高历史波动')
        
        # 4. 交易所可靠性
        exchanges = [opportunity.get('long_exchange', ''), opportunity.get('short_exchange', '')]
        if 'Aster' in exchanges:
            risk_score += 5  # Aster 相对小众
            risk_factors.append('Aster交易所')
        
        # 风险等级
        if risk_score < 20:
            risk_level = 'LOW'
        elif risk_score < 40:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
        
        return {
            'score': risk_score,
            'level': risk_level,
            'factors': risk_factors
        }
    
    def filter_opportunities(self, opportunities):
        """过滤有效机会"""
        filtered = []
        
        for opp in opportunities:
            # 黑名单检查
            if opp.get('symbol') in self.blacklist:
                continue
            
            # 费率差异检查
            spread = abs(opp.get('spread', 0))
            if spread < self.thresholds['min_spread']:
                continue
            
            # 流动性检查
            liquidity = opp.get('liquidity', 0)
            if liquidity < self.thresholds['min_liquidity']:
                continue
            
            # 波动性检查
            volatility = opp.get('volatility', 0)
            if volatility > self.thresholds['max_volatility']:
                continue
            
            filtered.append(opp)
        
        return filtered
    
    def rank_opportunities(self, opportunities):
        """排序并评分"""
        # 过滤
        valid = self.filter_opportunities(opportunities)
        
        # 计算得分和风险
        for opp in valid:
            opp['score'] = self.calculate_score(opp)
            opp['risk'] = self.assess_risk(opp)
        
        # 按得分排序
        ranked = sorted(valid, key=lambda x: x['score'], reverse=True)
        
        return ranked
    
    def select_top(self, opportunities, n=5):
        """选择前N个最优机会"""
        ranked = self.rank_opportunities(opportunities)
        return ranked[:n]
    
    def generate_report(self, opportunities):
        """生成选择报告"""
        top = self.select_top(opportunities, 5)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_opportunities': len(opportunities),
            'filtered_count': len(self.filter_opportunities(opportunities)),
            'top_selections': top,
            'recommendations': []
        }
        
        for i, opp in enumerate(top, 1):
            rec = {
                'rank': i,
                'symbol': opp['symbol'],
                'score': opp['score'],
                'risk_level': opp['risk']['level'],
                'expected_daily_return': opp.get('daily_return', 0),
                'action': f"{opp['long_exchange']}多 + {opp['short_exchange']}空",
                'notes': []
            }
            
            if opp['risk']['level'] == 'HIGH':
                rec['notes'].append('⚠️ 高风险，建议观望或减半仓位')
            elif opp['risk']['level'] == 'MEDIUM':
                rec['notes'].append('⚡ 中等风险，建议谨慎建仓')
            else:
                rec['notes'].append('✅ 低风险，可正常建仓')
            
            report['recommendations'].append(rec)
        
        return report

def main():
    # 示例数据
    sample_opportunities = [
        {
            'symbol': 'JTO',
            'long_exchange': 'Gate',
            'short_exchange': 'Bitget',
            'spread': 0.0427,
            'daily_return': 1.82,
            'liquidity': 500000,
            'volume': 5000000,
            'volatility': 0.15
        },
        {
            'symbol': 'PIXEL',
            'long_exchange': 'Gate',
            'short_exchange': 'Bitget',
            'spread': 0.0182,
            'daily_return': 0.91,
            'liquidity': 800000,
            'volume': 8000000,
            'volatility': 0.10
        },
        {
            'symbol': 'SUPER',
            'long_exchange': 'Gate',
            'short_exchange': 'Bitget',
            'spread': 0.0512,
            'daily_return': 2.56,
            'liquidity': 300000,
            'volume': 3000000,
            'volatility': 0.25
        }
    ]
    
    selector = AssetSelector()
    report = selector.generate_report(sample_opportunities)
    
    print("=== AI 品种选择报告 ===")
    print(f"时间: {report['timestamp']}\n")
    print(f"总机会数: {report['total_opportunities']}")
    print(f"过滤后: {report['filtered_count']}\n")
    
    print("Top 5 推荐:\n")
    for rec in report['recommendations']:
        print(f"#{rec['rank']} {rec['symbol']}")
        print(f"   得分: {rec['score']} | 风险: {rec['risk_level']}")
        print(f"   日收: {rec['expected_daily_return']}% | 操作: {rec['action']}")
        for note in rec['notes']:
            print(f"   {note}")
        print()

if __name__ == "__main__":
    main()