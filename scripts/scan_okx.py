#!/usr/bin/env python3
"""
OKX Funding Rate Scanner
使用 OKX Agent Trade Kit API 获取资金费率
"""

import os
import json
import time
import hmac
import hashlib
import base64
import urllib.request
from datetime import datetime

# OKX API 配置
OKX_API_KEY = os.environ.get('OKX_API_KEY', '')
OKX_API_SECRET = os.environ.get('OKX_API_SECRET', '')
OKX_PASSPHRASE = os.environ.get('OKX_PASSPHRASE', '')
OKX_BASE_URL = "https://www.okx.com"

def okx_request(endpoint, method='GET', params=None, body=None):
    """OKX API 请求"""
    timestamp = datetime.utcnow().isoformat() + 'Z'
    body_str = json.dumps(body) if body else ''
    query_string = '?' + '&'.join([f"{k}={v}" for k, v in params.items()]) if params else ''
    
    pre_hash = timestamp + method + endpoint + query_string + body_str
    
    signature = base64.b64encode(
        hmac.new(
            OKX_API_SECRET.encode(),
            pre_hash.encode(),
            hashlib.sha256
        ).digest()
    ).decode()
    
    headers = {
        'Content-Type': 'application/json',
        'OK-ACCESS-KEY': OKX_API_KEY,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': OKX_PASSPHRASE
    }
    
    url = f"{OKX_BASE_URL}{endpoint}{query_string}"
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
    # OKX 公开接口：获取所有合约信息
    endpoint = '/api/v5/public/instruments'
    params = {'instType': 'SWAP'}
    
    url = f"{OKX_BASE_URL}{endpoint}?instType=SWAP"
    req = urllib.request.Request(url)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"OKX API Error: {e}")
        return []
    
    if data.get('code') != '0':
        print(f"OKX API Error: {data.get('msg', 'Unknown error')}")
        return []
    
    results = []
    for contract in data.get('data', []):
        symbol = contract.get('instId', '')
        
        # 只处理 USDT 本位合约
        if not symbol.endswith('-USDT-SWAP'):
            continue
        
        # 获取资金费率
        fr_endpoint = '/api/v5/public/funding-rate'
        fr_url = f"{OKX_BASE_URL}{fr_endpoint}?instId={symbol}"
        fr_req = urllib.request.Request(fr_url)
        
        try:
            with urllib.request.urlopen(fr_req, timeout=10) as fr_resp:
                fr_data = json.loads(fr_resp.read().decode())
        except:
            continue
        
        if fr_data.get('code') == '0' and fr_data.get('data'):
            fr_info = fr_data['data'][0]
            funding_rate = float(fr_info.get('fundingRate', 0)) * 100  # 转为百分比
            next_funding_time = fr_info.get('nextFundingRate', 0)
            
            if funding_rate != 0:
                results.append({
                    'exchange': 'OKX',
                    'symbol': symbol.replace('-USDT-SWAP', '/USDT'),
                    'funding_rate': round(funding_rate, 4),
                    'next_funding_time': next_funding_time,
                    'timestamp': datetime.now().isoformat()
                })
        
        time.sleep(0.05)  # 避免请求过快
    
    results.sort(key=lambda x: abs(x['funding_rate']), reverse=True)
    return results

def main():
    print("=== OKX Funding Rate Scanner ===")
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