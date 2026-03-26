#!/usr/bin/env python3
"""
Gate.io Funding Rate Scanner
获取 Gate.io 永续合约的资金费率
"""

import os
import json
import time
import hmac
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime

# Gate API 配置
GATE_API_KEY = os.environ.get('GATE_API_KEY', '')
GATE_API_SECRET = os.environ.get('GATE_API_SECRET', '')
GATE_BASE_URL = "https://api.gateio.ws/api/v4"

def gate_request(endpoint, method='GET', params=None):
    """Gate API 请求"""
    url = f"{GATE_BASE_URL}{endpoint}"
    headers = {}
    
    if GATE_API_KEY and GATE_API_SECRET:
        timestamp = str(int(time.time()))
        query_string = urllib.parse.urlencode(params) if params else ''
        payload = f"{method}\n{endpoint}\n{query_string}\n{timestamp}"
        signature = hmac.new(
            GATE_API_SECRET.encode(),
            payload.encode(),
            hashlib.sha512
        ).hexdigest()
        headers = {
            'KEY': GATE_API_KEY,
            'Timestamp': timestamp,
            'SIGN': signature
        }
    
    if params and method == 'GET':
        url += '?' + urllib.parse.urlencode(params)
    
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def get_funding_rates():
    """获取所有永续合约的资金费率"""
    # Gate 公开接口：获取所有合约信息
    endpoint = '/futures/usdt/contracts'
    data = gate_request(endpoint)
    
    if 'error' in data:
        print(f"Gate API Error: {data['error']}")
        return []
    
    results = []
    for contract in data:
        symbol = contract.get('name', '')
        funding_rate = float(contract.get('funding_rate', 0)) * 100  # 转為百分比
        funding_rate_indicative = float(contract.get('funding_rate_indicative', 0)) * 100
        
        if funding_rate != 0:
            results.append({
                'exchange': 'Gate',
                'symbol': symbol,
                'funding_rate': round(funding_rate, 4),
                'funding_rate_indicative': round(funding_rate_indicative, 4),
                'mark_price': float(contract.get('mark_price', 0)),
                'index_price': float(contract.get('index_price', 0)),
                'timestamp': datetime.now().isoformat()
            })
    
    # 按费率绝对值排序
    results.sort(key=lambda x: abs(x['funding_rate']), reverse=True)
    return results

def main():
    print("=== Gate.io Funding Rate Scanner ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    rates = get_funding_rates()
    
    if not rates:
        print("No funding rate data found.")
        return
    
    # 显示前20个
    print(f"Top 20 Funding Rates (by absolute value):\n")
    print(f"{'Symbol':<15} {'Rate':>10} {'Indicative':>12} {'Direction':>10}")
    print("-" * 50)
    
    for r in rates[:20]:
        direction = "LONG" if r['funding_rate'] > 0 else "SHORT"
        print(f"{r['symbol']:<15} {r['funding_rate']:>9.4f}% {r['funding_rate_indicative']:>11.4f}% {direction:>10}")
    
    print(f"\nTotal: {len(rates)} contracts with non-zero funding rate")
    
    return rates

if __name__ == "__main__":
    main()