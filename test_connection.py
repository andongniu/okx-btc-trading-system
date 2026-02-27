#!/usr/bin/env python3
import ccxt
import time

print("Testing OKX connection with proxy...")

# 方法1: 使用代理
exchange = ccxt.okx({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'password': 'YOUR_PASSPHRASE',
    'enableRateLimit': True,
    'timeout': 30000,
    'proxies': {
        'http': 'http://127.0.0.1:7897',
        'https': 'http://127.0.0.1:7897',
    },
    'options': {
        'defaultType': 'swap',
    }
})

try:
    print("1. Testing public endpoint (no auth needed)...")
    markets = exchange.load_markets()
    print(f"   ✅ Loaded {len(markets)} markets")
    
    print("\n2. Getting BTC ticker...")
    ticker = exchange.fetch_ticker('BTC/USDT:USDT')
    print(f"   ✅ Price: ${ticker['last']:,.2f}")
    print(f"   ✅ 24h change: {ticker['percentage']:.2f}%")
    
    print("\n3. Testing private endpoint (balance)...")
    # 先尝试一个简单的私有端点
    try:
        balance = exchange.fetch_balance()
        usdt = balance.get('total', {}).get('USDT', 0)
        print(f"   ✅ Balance: {usdt:.2f} USDT")
    except Exception as e:
        print(f"   ⚠️  Balance fetch failed (may be permission): {e}")
    
    print("\n🎯 Connection test completed successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()