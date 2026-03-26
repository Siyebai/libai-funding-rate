#!/usr/bin/env python3
"""
Aster DEX Funding Rate Scanner
获取 Aster 永续合约的资金费率（Binance 风格 API）
"""

import os
import json
import time
import hmac
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime

# Aster API 配置
ASTER_API_KEY = os.environ.get('ASTER_API_KEY', '')
ASTER_API_SECRET = os.environ.get('ASTER_API_SECRET', '')
ASTER_BASE_URL = "https://fapi.asterdex.com"

def aster_request(endpoint, params=None):
    """Aster API 请求（Binance 风格）"""
    if params is None:
        params = {}
    
    params['timestamp'] = int(time.time() * 1000)
    query_string = urllib.parse.urlencode(params)
    
    if ASTER_API_SECRET:
        signature = hmac.new(
            ASTER_API_SECRET.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        query_string += f'&signature={signature}'
    
    url = f"{ASTER_BASE_URL}{endpoint}?{query_string}"
    headers = {}
    if ASTER_API_KEY:
        headers['X-MBX-APIKEY'] = ASTER_API_KEY
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def get_funding_rates():
    """获取所有合约的资金费率"""
    # 获取所有交易对信息
    endpoint = '/fapi/v1/exchangeInfo'
    data = aster_request(endpoint)
    
    if 'error' in data:
        print(f"Aster API Error: {data['error']}")
        return []
    
    symbols = [s['symbol'] for s in data.get('symbols', [])]
    results = []
    
    # 批量获取资金费率
    for symbol in symbols[:50]:  # 限制请求数量
        endpoint = '/fapi/v1/fundingRate'
        params = {'symbol': symbol, 'limit': 1}
        rate_data = aster_request(endpoint, params)
        
        if isinstance(rate_data, list) and rate_data:
            rate_info = rate_data[0]
            funding_rate = float(rate_info.get('fundingRate', 0)) * 100
            
            if funding_rate != 0:
                results.append({
                    'exchange': 'Aster',
                    'symbol': symbol,
                    'funding_rate': round(funding_rate, 4),
                    'funding_time': rate_info.get('fundingTime', 0),
                    'timestamp': datetime.now().isoformat()
                })
        
        time.sleep(0.1)  # 避免请求过快
    
    results.sort(key=lambda x: abs(x['funding_rate']), reverse=True)
    return results

def main():
    print("=== Aster Funding Rate Scanner ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    rates = get_funding_rates()
    
    if not rates:
        print("No funding rate data found.")
        return
    
    print(f"Top 20 Funding Rates (by absolute value):\n")
    print(f"{'Symbol':<15} {'Rate':>10} {'Direction':>10}")
    print("-" * 40)
    
    for r in rates[:20]:
        direction = "LONG" if r['funding_rate'] > 0 else "SHORT"
        print(f"{r['symbol']:<15} {r['funding_rate']:>9.4f}% {direction:>10}")
    
    print(f"\nTotal: {len(rates)} contracts with non-zero funding rate")
    
    return rates

if __name__ == "__main__":
    main()