#!/usr/bin/env python3
"""
仓位滚动建仓管理器 V1.0
功能：分批建仓，降低成本，成功率90%的资金管理策略
作者：Q李白
日期：2026-03-27

核心规则:
1. 总资金平均分成10份
2. 用1份资金分3次逢低分批建底仓
3. 最终形成3成仓位
4. 有盈利后逐步加仓到5成
5. 亏损不补仓
"""

import json
from datetime import datetime
from enum import Enum

class PositionPhase(Enum):
    WAITING = "waiting"        # 等待开仓
    BUILDING = "building"      # 建仓中
    HOLDING = "holding"        # 持有中
    PROFIT_ADDING = "profit_adding"  # 盈利加仓中
    STOPPED = "stopped"        # 已止损

class RollingPositionManager:
    """仓位滚动管理器"""
    
    def __init__(self, total_capital):
        self.total_capital = total_capital
        self.unit = total_capital / 10  # 每份资金
        self.positions = {}
        
        self.config = {
            'build_batches': 3,          # 底仓分3批建
            'build_interval_pct': 0.01,  # 每批间隔1%价格差异
            'profit_trigger': 0.02,       # 盈利2%后可加仓
            'max_position_pct': 0.5,      # 最大仓位50%
            'stop_loss_pct': 0.05,        # 止损5%
        }
    
    def start_building(self, symbol, initial_price, direction='long'):
        """开始建仓"""
        if symbol in self.positions:
            return {'error': 'Position already exists'}
        
        self.positions[symbol] = {
            'phase': PositionPhase.BUILDING,
            'direction': direction,
            'initial_price': initial_price,
            'current_price': initial_price,
            'batches_built': 0,
            'entries': [],  # 记录每笔入场
            'total_size': 0,
            'avg_entry_price': 0,
            'capital_used': 0,
            'profit_percent': 0,
            'can_add': False,
            'created_at': datetime.now().isoformat()
        }
        
        # 第一批建仓
        return self._build_batch(symbol, initial_price)
    
    def _build_batch(self, symbol, price):
        """执行一批建仓"""
        pos = self.positions[symbol]
        
        if pos['batches_built'] >= self.config['build_batches']:
            pos['phase'] = PositionPhase.HOLDING
            return {'status': 'building_complete', 'position': pos}
        
        batch_size = self.unit / 3  # 每批用1份资金的1/3
        batch_capital = batch_size * price if pos['direction'] == 'long' else batch_size
        
        pos['entries'].append({
            'batch': pos['batches_built'] + 1,
            'price': price,
            'size': batch_size,
            'capital': batch_capital,
            'time': datetime.now().isoformat()
        })
        
        pos['batches_built'] += 1
        pos['total_size'] += batch_size
        pos['capital_used'] += batch_capital
        
        # 计算平均入场价
        total_capital = sum(e['capital'] for e in pos['entries'])
        total_size = sum(e['size'] for e in pos['entries'])
        pos['avg_entry_price'] = total_capital / total_size if total_size > 0 else 0
        
        return {
            'status': 'batch_built',
            'batch': pos['batches_built'],
            'size': batch_size,
            'avg_price': pos['avg_entry_price'],
            'remaining_batches': self.config['build_batches'] - pos['batches_built']
        }
    
    def check_next_batch(self, symbol, current_price):
        """检查是否执行下一批建仓"""
        if symbol not in self.positions:
            return None
        
        pos = self.positions[symbol]
        
        if pos['phase'] != PositionPhase.BUILDING:
            return {'status': 'not_in_building_phase'}
        
        # 检查价格是否满足间隔要求
        if pos['direction'] == 'long':
            # 多头：价格下跌时加仓
            price_drop = (pos['avg_entry_price'] - current_price) / pos['avg_entry_price']
            should_build = price_drop >= self.config['build_interval_pct']
        else:
            # 空头：价格上涨时加仓
            price_rise = (current_price - pos['avg_entry_price']) / pos['avg_entry_price']
            should_build = price_rise >= self.config['build_interval_pct']
        
        if should_build and pos['batches_built'] < self.config['build_batches']:
            return self._build_batch(symbol, current_price)
        
        return {'status': 'waiting_for_price', 'current_drop_rise': price_drop if pos['direction'] == 'long' else price_rise}
    
    def update_price(self, symbol, current_price):
        """更新价格并检查状态"""
        if symbol not in self.positions:
            return None
        
        pos = self.positions[symbol]
        pos['current_price'] = current_price
        
        # 计算盈利百分比
        if pos['direction'] == 'long':
            pos['profit_percent'] = (current_price - pos['avg_entry_price']) / pos['avg_entry_price']
        else:
            pos['profit_percent'] = (pos['avg_entry_price'] - current_price) / pos['avg_entry_price']
        
        # 检查止损
        if pos['profit_percent'] <= -self.config['stop_loss_pct']:
            pos['phase'] = PositionPhase.STOPPED
            return {'status': 'stop_loss_triggered', 'position': pos}
        
        # 检查是否可以加仓
        if pos['profit_percent'] >= self.config['profit_trigger']:
            pos['can_add'] = True
            pos['phase'] = PositionPhase.PROFIT_ADDING
        
        return pos
    
    def add_position(self, symbol, price):
        """盈利后加仓"""
        if symbol not in self.positions:
            return {'error': 'Position not found'}
        
        pos = self.positions[symbol]
        
        if not pos['can_add']:
            return {'error': 'Not eligible for adding position'}
        
        # 检查是否已达到最大仓位
        current_position_pct = pos['capital_used'] / self.total_capital
        if current_position_pct >= self.config['max_position_pct']:
            return {'error': 'Max position reached'}
        
        # 加仓：用另一份资金
        add_size = self.unit
        add_capital = add_size * price if pos['direction'] == 'long' else add_size
        
        pos['entries'].append({
            'batch': 'add',
            'price': price,
            'size': add_size,
            'capital': add_capital,
            'time': datetime.now().isoformat()
        })
        
        pos['total_size'] += add_size
        pos['capital_used'] += add_capital
        
        # 重新计算平均入场价
        total_capital = sum(e['capital'] for e in pos['entries'])
        total_size = sum(e['size'] for e in pos['entries'])
        pos['avg_entry_price'] = total_capital / total_size
        
        return {
            'status': 'position_added',
            'add_size': add_size,
            'new_avg_price': pos['avg_entry_price'],
            'total_position_pct': pos['capital_used'] / self.total_capital
        }
    
    def get_position_summary(self, symbol):
        """获取仓位摘要"""
        if symbol not in self.positions:
            return None
        
        pos = self.positions[symbol]
        return {
            'symbol': symbol,
            'phase': pos['phase'].value,
            'direction': pos['direction'],
            'avg_entry_price': pos['avg_entry_price'],
            'current_price': pos['current_price'],
            'profit_percent': pos['profit_percent'] * 100,
            'total_size': pos['total_size'],
            'capital_used': pos['capital_used'],
            'position_pct': pos['capital_used'] / self.total_capital * 100,
            'batches_built': pos['batches_built'],
            'can_add': pos['can_add']
        }

def main():
    print("=== 仓位滚动建仓管理器测试 ===\n")
    
    # 假设总资金 1000U
    manager = RollingPositionManager(total_capital=1000)
    
    symbol = "PIXEL"
    initial_price = 0.10
    
    # 开始建仓
    result = manager.start_building(symbol, initial_price, 'long')
    print(f"第一批建仓: {result}\n")
    
    # 模拟价格下跌，触发第二批
    prices = [0.099, 0.098]  # 价格下跌
    
    for price in prices:
        result = manager.check_next_batch(symbol, price)
        if result.get('status') == 'batch_built':
            print(f"价格 {price}: 第{result['batch']}批建仓完成")
            print(f"  平均成本: {result['avg_price']:.4f}\n")
        else:
            print(f"价格 {price}: 等待中...\n")
    
    # 更新价格到盈利
    manager.update_price(symbol, 0.11)
    summary = manager.get_position_summary(symbol)
    print(f"仓位摘要:\n{json.dumps(summary, indent=2)}\n")

if __name__ == '__main__':
    main()