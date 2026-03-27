#!/usr/bin/env python3
"""
移动止损机制 V1.0
功能：在盈利后自动将止损移动到成本价，保护利润
作者：Q李白
日期：2026-03-27
"""

import json
from datetime import datetime
from enum import Enum

class StopLossType(Enum):
    FIXED = "fixed"           # 固定止损
    PERCENTAGE = "percentage" # 百分比止损
    TRAILING = "trailing"     # 移动止损
    BREAKEVEN = "breakeven"   # 保本止损

class TrailingStopManager:
    """移动止损管理器"""
    
    def __init__(self, config_path=None):
        self.positions = {}
        self.config = {
            'profit_trigger': 0.01,      # 盈利1%后触发移动止损
            'trail_percent': 0.005,      # 追踪止损0.5%
            'breakeven_trigger': 0.015,  # 盈利1.5%后移至保本
            'min_profit_lock': 0.003,    # 最少锁定0.3%利润
        }
    
    def add_position(self, symbol, entry_price, position_size, direction='long'):
        """添加新仓位"""
        self.positions[symbol] = {
            'entry_price': entry_price,
            'current_price': entry_price,
            'position_size': position_size,
            'direction': direction,  # 'long' or 'short'
            'highest_price': entry_price if direction == 'long' else entry_price,
            'lowest_price': entry_price if direction == 'short' else entry_price,
            'stop_loss': None,
            'stop_loss_type': StopLossType.FIXED,
            'profit_percent': 0,
            'locked_profit': False,
            'created_at': datetime.now().isoformat()
        }
        return self.positions[symbol]
    
    def update_price(self, symbol, current_price):
        """更新价格并调整止损"""
        if symbol not in self.positions:
            return None
        
        pos = self.positions[symbol]
        pos['current_price'] = current_price
        
        # 计算盈利百分比
        if pos['direction'] == 'long':
            pos['profit_percent'] = (current_price - pos['entry_price']) / pos['entry_price']
            if current_price > pos['highest_price']:
                pos['highest_price'] = current_price
        else:  # short
            pos['profit_percent'] = (pos['entry_price'] - current_price) / pos['entry_price']
            if current_price < pos['lowest_price']:
                pos['lowest_price'] = current_price
        
        # 检查是否触发移动止损
        self._check_trailing_stop(symbol)
        
        return pos
    
    def _check_trailing_stop(self, symbol):
        """检查并更新移动止损"""
        pos = self.positions[symbol]
        profit_pct = pos['profit_percent']
        
        # 阶段1：盈利达到保本触发线 → 移至保本
        if profit_pct >= self.config['breakeven_trigger'] and not pos['locked_profit']:
            pos['stop_loss'] = pos['entry_price']
            pos['stop_loss_type'] = StopLossType.BREAKEVEN
            pos['locked_profit'] = True
            print(f"[{symbol}] 触发保本止损，止损价设为 {pos['entry_price']}")
        
        # 阶段2：盈利继续增加 → 移动止损跟随
        elif pos['locked_profit'] and profit_pct > self.config['profit_trigger']:
            if pos['direction'] == 'long':
                # 多头：止损价 = 最高价 × (1 - 追踪百分比)
                new_stop = pos['highest_price'] * (1 - self.config['trail_percent'])
                if new_stop > pos['entry_price'] and (pos['stop_loss'] is None or new_stop > pos['stop_loss']):
                    pos['stop_loss'] = new_stop
                    pos['stop_loss_type'] = StopLossType.TRAILING
                    print(f"[{symbol}] 移动止损更新至 {new_stop:.4f}")
            else:
                # 空头：止损价 = 最低价 × (1 + 追踪百分比)
                new_stop = pos['lowest_price'] * (1 + self.config['trail_percent'])
                if new_stop < pos['entry_price'] and (pos['stop_loss'] is None or new_stop < pos['stop_loss']):
                    pos['stop_loss'] = new_stop
                    pos['stop_loss_type'] = StopLossType.TRAILING
                    print(f"[{symbol}] 移动止损更新至 {new_stop:.4f}")
    
    def check_stop_loss(self, symbol, current_price):
        """检查是否触发止损"""
        if symbol not in self.positions:
            return False, None
        
        pos = self.positions[symbol]
        
        if pos['stop_loss'] is None:
            return False, None
        
        if pos['direction'] == 'long':
            triggered = current_price <= pos['stop_loss']
        else:
            triggered = current_price >= pos['stop_loss']
        
        if triggered:
            profit_at_stop = pos['profit_percent']
            return True, {
                'stop_price': pos['stop_loss'],
                'profit_at_stop': profit_at_stop,
                'stop_type': pos['stop_loss_type'].value
            }
        
        return False, None
    
    def get_position_status(self, symbol):
        """获取仓位状态"""
        if symbol not in self.positions:
            return None
        return self.positions[symbol]

def main():
    print("=== 移动止损机制测试 ===\n")
    
    manager = TrailingStopManager()
    
    # 模拟多头仓位
    symbol = "PIXEL"
    entry_price = 0.10
    manager.add_position(symbol, entry_price, 1000, 'long')
    print(f"建仓: {symbol} @ {entry_price}\n")
    
    # 模拟价格上涨过程
    prices = [0.1005, 0.1010, 0.1015, 0.1020, 0.1025, 0.1018, 0.1010]
    
    for price in prices:
        pos = manager.update_price(symbol, price)
        triggered, stop_info = manager.check_stop_loss(symbol, price)
        
        print(f"价格: {price:.4f} | 盈利: {pos['profit_percent']*100:.2f}% | 止损: {pos['stop_loss']} | 类型: {pos['stop_loss_type'].value}")
        
        if triggered:
            print(f"  ⚠️ 触发止损！平仓价格: {stop_info['stop_price']}, 盈利: {stop_info['profit_at_stop']*100:.2f}%")
            break
        print()

if __name__ == '__main__':
    main()