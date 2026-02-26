#!/usr/bin/env python3
import ccxt
import time

print("Testing OKX API connection...")

try:
    exchange = ccxt.okx({
        'apiKey': '9b5ee84f-13fd-43f5-ae6f-b96b2b0ed70d',
        'secret': 'A7EABBD3C6D49A92C5B542E0189F4BEC',
        'password': 'Lhc@930720',
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'},
    })
    
    print("1. Testing balance...")
    balance = exchange.fetch_balance()
    print(f"Total USDT: {balance['total'].get('USDT', 0)}")
    print(f"Free USDT: {balance['free'].get('USDT', 0)}")
    
    print("\n2. Testing ticker...")
    ticker = exchange.fetch_ticker('BTC/USDT:USDT')
    print(f"BTC Price: ${ticker['last']}")
    
    print("\n✅ API Connection Successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()