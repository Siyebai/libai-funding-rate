#!/usr/bin/env python3
"""
Bitget Funding Rate Scanner
获取 Bitget 永续合约的资金费率
"""

import os
import json
import time
import hmac
import hashlib
import base64
import urllib.request
from datetime import datetime

# Bitget API 配置
BITGET_API_KEY = os.environ.get('BITGET_API_KEY', '')
BITGET_API_SECRET = os.environ.get('BITGET_API_SECRET', '')
BITGET_PASSPHRASE = os.environ.get('BITGET_API_PASSPHRASE', '')
BITGET_BASE_URL = "https://api.bitget.com"

def bitget_request(endpoint, method='GET', params=None, body=None):
    """Bitget API 请求"""
    url = f"{BITGET_BASE_URL}{endpoint}"
    timestamp = str(int(time.time() * 1000))
    
    body_str = json.dumps(body) if body else ''
    pre_hash = timestamp + method.upper() + endpoint + body_str
    
    signature = base64.b64encode(
        hmac.new(
            BITGET_API_SECRET.encode(),
            pre_hash.encode(),
            hashlib.sha256
        ).digest()
    ).decode()
    
    headers = {
        'Content-Type': 'application/json',
        'ACCESS-KEY': BITGET_API_KEY,
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': BITGET_PASSPHRASE
    }
    
    req = urllib.request.Request(url, headers=headers, method=method)
    if body:
        req.data = body_str.encode()
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def get_funding_rates():
    """获取所有 USDT 永续合约的资金费率"""
    # Bitget 公开接口
    endpoint = '/api/v2/mix/market/contracts'
    params = {'productType': 'USDT-FUTURES'}
    
    url = f"{BITGET_BASE_URL}{endpoint}?productType=USDT-FUTURES"
    req = urllib.request.Request(url)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Bitget API Error: {e}")
        return []
    
    if data.get('code') != '00000':
        print(f"Bitget API Error: {data.get('msg', 'Unknown error')}")
        return []
    
    results = []
    for contract in data.get('data', []):
        symbol = contract.get('symbol', '')
        funding_rate = float(contract.get('fundingRate', 0)) * 100  # 转為百分比
        next_funding_time = contract.get('nextFundingTime', 0)
        
        if funding_rate != 0:
            results.append({
                'exchange': 'Bitget',
                'symbol': symbol,
                'funding_rate': round(funding_rate, 4),
                'next_funding_time': next_funding_time,
                'timestamp': datetime.now().isoformat()
            })
    
    results.sort(key=lambda x: abs(x['funding_rate']), reverse=True)
    return results

def main():
    print("=== Bitget Funding Rate Scanner ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    rates = get_funding_rates()
    
    if not rates:
        print("No funding rate data found.")
        return
    
    print(f"Top 20 Funding Rates (by absolute value):\n")
    print(f"{'Symbol':<15} {'Rate':>10} {'Direction':>10}")
    print("-" * 40)
    
    for r in rates[:20]:
        direction = "SHORT" if r['funding_rate'] > 0 else "LONG"  # Bitget 正费率=空付多
        print(f"{r['symbol']:<15} {r['funding_rate']:>9.4f}% {direction:>10}")
    
    print(f"\nTotal: {len(rates)} contracts with non-zero funding rate")
    
    return rates

if __name__ == "__main__":
    main()