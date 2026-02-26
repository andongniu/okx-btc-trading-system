#!/usr/bin/env python3
"""
检查OKX账户余额
"""

import ccxt
import json

try:
    # 加载配置
    with open('config/final_config.json', 'r') as f:
        config = json.load(f)
    
    # 初始化交易所
    exchange = ccxt.okx({
        'apiKey': config['exchange']['api_key'],
        'secret': config['exchange']['secret'],
        'password': config['exchange']['passphrase'],
        'enableRateLimit': True,
        'proxies': config['exchange']['proxies'],
        'options': {'defaultType': 'swap'}
    })
    
    print('🔐 检查OKX账户余额...')
    
    # 获取账户余额
    balance = exchange.fetch_balance()
    
    print('📊 账户总览:')
    print('='*40)
    
    # 显示主要资产
    assets = ['USDT', 'BTC', 'ETH']
    for asset in assets:
        total = balance.get('total', {}).get(asset, 0)
        free = balance.get('free', {}).get(asset, 0)
        used = balance.get('used', {}).get(asset, 0)
        
        if total > 0 or free > 0 or used > 0:
            print(f'{asset}:')
            print(f'  总额: {total:.8f}')
            print(f'  可用: {free:.8f}')
            print(f'  占用: {used:.8f}')
            if asset == 'BTC':
                # 获取BTC价格计算美元价值
                ticker = exchange.fetch_ticker('BTC/USDT:USDT')
                btc_price = ticker['last']
                print(f'  价值: ${total * btc_price:.2f}')
            elif asset == 'ETH':
                # 获取ETH价格
                eth_ticker = exchange.fetch_ticker('ETH/USDT:USDT')
                eth_price = eth_ticker['last']
                print(f'  价值: ${total * eth_price:.2f}')
    
    # 检查永续合约账户
    print('\n📈 永续合约账户:')
    print('='*40)
    
    try:
        # 获取永续合约余额
        positions = exchange.fetch_positions(['BTC/USDT:USDT'])
        if positions:
            for pos in positions:
                if pos['symbol'] == 'BTC/USDT:USDT':
                    print(f'合约: {pos["symbol"]}')
                    print(f'  持仓量: {pos["contracts"]:.4f}')
                    print(f'  入场价: ${pos.get("entryPrice", 0):,.2f}')
                    print(f'  当前价: ${pos.get("markPrice", 0):,.2f}')
                    print(f'  未实现盈亏: ${pos.get("unrealizedPnl", 0):.2f}')
                    print(f'  保证金: ${pos.get("initialMargin", 0):.2f}')
        else:
            print('  无永续合约持仓')
    except Exception as e:
        print(f'  获取持仓失败: {e}')
    
    # 获取当前BTC价格
    print('\n💰 当前市场:')
    print('='*40)
    ticker = exchange.fetch_ticker('BTC/USDT:USDT')
    print(f'BTC价格: ${ticker["last"]:,.2f}')
    print(f'24h涨跌: {ticker["percentage"]:.2f}%')
    print(f'买一价: ${ticker["bid"]:,.2f}')
    print(f'卖一价: ${ticker["ask"]:,.2f}')
    print(f'24h最高: ${ticker["high"]:,.2f}')
    print(f'24h最低: ${ticker["low"]:,.2f}')
    
    # 资金需求分析
    print('\n🎯 资金需求分析:')
    print('='*40)
    usdt_total = balance.get('total', {}).get('USDT', 0)
    required = 200
    
    if usdt_total >= required:
        print(f'✅ 余额充足: ${usdt_total:.2f} USDT')
        print(f'   满足启动需求: ${required} USDT')
        print(f'   剩余: ${usdt_total - required:.2f}')
        
        # 检查可用余额
        usdt_free = balance.get('free', {}).get('USDT', 0)
        if usdt_free >= required * 0.8:  # 至少80%可用
            print(f'✅ 可用余额充足: ${usdt_free:.2f} USDT')
        else:
            print(f'⚠️  可用余额不足: ${usdt_free:.2f} USDT')
            print(f'   可能需要释放被占用的资金')
    else:
        print(f'❌ 余额不足: ${usdt_total:.2f} USDT')
        print(f'   需要: ${required} USDT')
        print(f'   缺口: ${required - usdt_total:.2f}')
        print('\n💡 建议:')
        print(f'   1. 转入至少${required - usdt_total:.2f} USDT')
        print('   2. 确认转入永续合约账户')
        print('   3. 等待到账后重新检查')
    
    print('\n📋 下一步:')
    if usdt_total >= required:
        print('   1. 启动监控系统验证')
        print('   2. 进行小额测试交易')
        print('   3. 正式启动30天挑战')
    else:
        print('   1. 转入所需资金')
        print('   2. 重新检查余额')
        print('   3. 然后继续后续步骤')
    
except Exception as e:
    print(f'❌ 检查失败: {e}')
    import traceback
    traceback.print_exc()