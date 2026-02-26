#!/usr/bin/env python3
import ccxt
import json
from datetime import datetime

print("🔐 测试OKX API连接...")

try:
    # 创建OKX交易所实例（永续合约）
    exchange = ccxt.okx({
        "apiKey": "9b5ee84f-13fd-43f5-ae6f-b96b2b0ed70d",
        "secret": "A7EABBD3C6D49A92C5B542E0189F4BEC",
        "password": "Lhc@930720",
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",  # 永续合约
        }
    })
    
    # 测试1: 获取账户余额
    print("📊 获取账户余额...")
    balance = exchange.fetch_balance()
    usdt_total = balance.get("total", {}).get("USDT", 0)
    usdt_free = balance.get("free", {}).get("USDT", 0)
    print("✅ 总资产: {:.2f} USDT".format(usdt_total))
    print("✅ 可用余额: {:.2f} USDT".format(usdt_free))
    
    # 测试2: 获取BTC永续合约市场信息
    print("📈 获取BTC永续合约信息...")
    ticker = exchange.fetch_ticker("BTC/USDT:USDT")
    print("✅ 当前价格: ${:,.2f}".format(ticker["last"]))
    print("✅ 24h涨跌幅: {:.2f}%".format(ticker["percentage"]))
    print("✅ 买一价: ${:,.2f}".format(ticker["bid"]))
    print("✅ 卖一价: ${:,.2f}".format(ticker["ask"]))
    
    # 测试3: 获取K线数据
    print("📅 获取最近K线数据...")
    ohlcv = exchange.fetch_ohlcv("BTC/USDT:USDT", "5m", limit=10)
    print("✅ 最新5分钟K线:")
    for i, candle in enumerate(ohlcv[-3:]):  # 显示最近3根
        ts = datetime.fromtimestamp(candle[0]/1000).strftime("%H:%M")
        print("   {} | 开:{:,.0f} 高:{:,.0f} 低:{:,.0f} 收:{:,.0f} 量:{:.2f}".format(
            ts, candle[1], candle[2], candle[3], candle[4], candle[5]))
    
    # 测试4: 检查合约规格
    print("⚙️ 检查合约规格...")
    market = exchange.market("BTC/USDT:USDT")
    print("✅ 合约乘数: {}".format(market["contractSize"]))
    print("✅ 最小交易量: {}".format(market["limits"]["amount"]["min"]))
    print("✅ 价格精度: {}".format(market["precision"]["price"]))
    
    # 测试5: 获取手续费率
    print("💰 检查手续费率...")
    try:
        fees = exchange.fetch_trading_fees()
        btc_fee = fees.get("BTC/USDT:USDT", {})
        if btc_fee:
            print("✅ Maker费率: {:.4%}".format(btc_fee.get("maker", 0)))
            print("✅ Taker费率: {:.4%}".format(btc_fee.get("taker", 0)))
    except:
        print("⚠️  无法获取手续费详情，使用默认值")
        print("✅ 默认Maker费率: 0.02%")
        print("✅ 默认Taker费率: 0.05%")
    
    print("\n🎯 API连接测试完成！系统就绪。")
    
except Exception as e:
    print("❌ 错误: {}".format(e))
    import traceback
    traceback.print_exc()