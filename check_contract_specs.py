#!/usr/bin/env python3
"""
检查OKX合约规格和交易参数
"""

import ccxt
import json

def check_contract_specs():
    print('📋 检查OKX合约规格...')
    print('='*50)
    
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
        
        # 获取市场信息
        symbol = 'BTC/USDT:USDT'
        markets = exchange.load_markets()
        
        if symbol not in markets:
            print(f'❌ 交易对 {symbol} 不存在')
            return
        
        market = markets[symbol]
        
        print('📊 合约详细信息:')
        print('-'*30)
        print(f'交易对: {symbol}')
        print(f'合约类型: {market.get("type", "N/A")}')
        print(f'是否活跃: {market.get("active", "N/A")}')
        
        # 限制信息
        limits = market.get('limits', {})
        print('\n📏 交易限制:')
        print(f'   最小交易量: {limits.get("amount", {}).get("min", "N/A")}')
        print(f'   最大交易量: {limits.get("amount", {}).get("max", "N/A")}')
        print(f'   最小价格变动: {limits.get("price", {}).get("min", "N/A")}')
        print(f'   最小交易金额: {limits.get("cost", {}).get("min", "N/A")}')
        
        # 精度信息
        precision = market.get('precision', {})
        print('\n🎯 精度设置:')
        print(f'   数量精度: {precision.get("amount", "N/A")}')
        print(f'   价格精度: {precision.get("price", "N/A")}')
        
        # 合约规格
        print('\n⚙️ 合约规格:')
        print(f'   合约乘数: {market.get("contractSize", "N/A")}')
        print(f'   结算货币: {market.get("settle", "N/A")}')
        print(f'   报价货币: {market.get("quote", "N/A")}')
        print(f'   基础货币: {market.get("base", "N/A")}')
        
        # 获取当前价格
        ticker = exchange.fetch_ticker(symbol)
        btc_price = ticker['last']
        
        print(f'\n💰 当前市场:')
        print(f'   BTC价格: ${btc_price:,.2f}')
        print(f'   24h涨跌: {ticker["percentage"]:.2f}%')
        
        # 计算最小交易金额
        min_amount = float(limits.get('amount', {}).get('min', 0.01))
        min_cost = min_amount * btc_price
        
        print(f'\n🎯 最小交易要求:')
        print(f'   最小BTC数量: {min_amount}')
        print(f'   对应金额: ${min_cost:.2f}')
        
        # 检查账户余额
        balance = exchange.fetch_balance()
        usdt_available = balance['free']['USDT']
        
        print(f'\n📊 账户资金:')
        print(f'   可用USDT: ${usdt_available:.2f}')
        
        # 测试不同杠杆下的要求
        print('\n⚡ 不同杠杆下的资金要求:')
        for leverage in [1, 5, 10, 20, 50]:
            required = min_cost / leverage
            status = '✅ 充足' if usdt_available >= required else '❌ 不足'
            print(f'   {leverage:2d}倍杠杆: 需要${required:7.2f} {status}')
        
        # 建议交易参数
        print('\n💡 建议交易参数:')
        
        # 使用5倍杠杆，最小交易量
        suggested_leverage = 5
        suggested_amount = min_amount
        suggested_cost = suggested_amount * btc_price
        margin_required = suggested_cost / suggested_leverage
        
        print(f'   建议杠杆: {suggested_leverage}x')
        print(f'   建议数量: {suggested_amount} BTC')
        print(f'   合约价值: ${suggested_cost:.2f}')
        print(f'   所需保证金: ${margin_required:.2f}')
        
        if usdt_available >= margin_required:
            print(f'   ✅ 资金充足，可以交易')
        else:
            print(f'   ❌ 资金不足，需要至少${margin_required:.2f}')
        
        # 检查现有持仓
        print('\n📈 现有持仓状态:')
        positions = exchange.fetch_positions([symbol])
        
        if positions:
            for pos in positions:
                if pos['symbol'] == symbol:
                    contracts = float(pos.get('contracts', 0))
                    if contracts > 0:
                        print(f'   ✅ 现有持仓: {contracts} BTC')
                        print(f'      方向: {pos.get("side", "N/A")}')
                        print(f'      入场价: ${pos.get("entryPrice", 0):,.2f}')
                        print(f'      未实现盈亏: ${pos.get("unrealizedPnl", 0):.2f}')
                    else:
                        print('   无持仓')
                    break
        else:
            print('   无持仓记录')
        
        print('\n📋 下一步建议:')
        if usdt_available >= margin_required:
            print('1. 使用最小交易量测试 (安全第一)')
            print('2. 验证订单执行流程')
            print('3. 测试平仓操作')
            print('4. 逐步增加交易规模')
        else:
            print('1. 增加账户资金')
            print('2. 或使用更低杠杆')
            print('3. 确认最小交易要求')
        
    except Exception as e:
        print(f'❌ 检查失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_contract_specs()