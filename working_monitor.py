#!/usr/bin/env python3
"""
工作监控面板 - 简单直接，确保数据能显示
"""

from flask import Flask, jsonify
import json
import time
from datetime import datetime
import threading
import os
import ccxt

app = Flask(__name__)

# 简单状态数据
data = {
    'status': 'running',
    'last_update': datetime.now().isoformat(),
    'account': {'balance': 0, 'available': 0},
    'market': {'price': 0, 'change': 0},
    'positions': [],
    'trades': [],
    'strategy': {'status': 'waiting'}
}

def get_simple_html():
    """生成简单的HTML页面"""
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>交易监控</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
            .card {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #4CAF50; }}
            .metric {{ display: flex; justify-content: space-between; margin: 5px 0; }}
            .label {{ color: #666; }}
            .value {{ font-weight: bold; }}
            .positive {{ color: #4CAF50; }}
            .negative {{ color: #f44336; }}
            .trade {{ background: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            .update-time {{ color: #888; font-size: 0.9em; text-align: right; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 自主交易监控面板</h1>
            <p>只显示信息，不干扰决策 | 最后更新: <span id="updateTime">{datetime.now().strftime("%H:%M:%S")}</span></p>
            
            <div class="card">
                <h3>💰 账户信息</h3>
                <div class="metric">
                    <span class="label">总余额</span>
                    <span id="balance" class="value">${data["account"]["balance"]:.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">可用余额</span>
                    <span id="available" class="value">${data["account"]["available"]:.2f}</span>
                </div>
            </div>
            
            <div class="card">
                <h3>📈 市场数据</h3>
                <div class="metric">
                    <span class="label">BTC价格</span>
                    <span id="price" class="value">${data["market"]["price"]:.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">24h涨跌</span>
                    <span id="change" class="value">0.00%</span>
                </div>
            </div>
            
            <div class="card">
                <h3>📊 当前持仓</h3>
                <div id="positions">
                    {get_positions_html()}
                </div>
            </div>
            
            <div class="card">
                <h3>📋 交易记录</h3>
                <div id="trades">
                    {get_trades_html()}
                </div>
            </div>
            
            <div class="update-time">
                数据每5秒自动刷新 | <button onclick="location.reload()">🔄 手动刷新</button>
            </div>
        </div>
        
        <script>
            // 自动刷新
            setTimeout(() => location.reload(), 5000);
            
            // 更新数据
            async function updateData() {{
                try {{
                    const response = await fetch('/api/data');
                    const result = await response.json();
                    
                    // 更新账户信息
                    document.getElementById('balance').textContent = '$' + result.account.balance.toFixed(2);
                    document.getElementById('available').textContent = '$' + result.account.available.toFixed(2);
                    
                    // 更新市场数据
                    document.getElementById('price').textContent = '$' + result.market.price.toFixed(2);
                    const changeElem = document.getElementById('change');
                    changeElem.textContent = result.market.change.toFixed(2) + '%';
                    changeElem.className = result.market.change >= 0 ? 'value positive' : 'value negative';
                    
                    // 更新持仓
                    document.getElementById('positions').innerHTML = result.positions_html;
                    
                    // 更新交易记录
                    document.getElementById('trades').innerHTML = result.trades_html;
                    
                    // 更新时间
                    document.getElementById('updateTime').textContent = new Date().toLocaleTimeString();
                }} catch (error) {{
                    console.error('更新失败:', error);
                }}
            }}
            
            // 初始加载
            updateData();
        </script>
    </body>
    </html>
    '''

def get_positions_html():
    """生成持仓HTML"""
    if not data['positions']:
        return '<div style="color: #666; text-align: center; padding: 10px;">无持仓</div>'
    
    html = ''
    for pos in data['positions']:
        pnl = pos.get('pnl', 0)
        pnl_class = 'positive' if pnl >= 0 else 'negative'
        pnl_sign = '+' if pnl >= 0 else ''
        
        html += f'''
        <div class="trade">
            <div class="metric">
                <span class="label">{pos.get('side', 'N/A')}</span>
                <span class="value">{pos.get('contracts', 0)}张</span>
            </div>
            <div class="metric">
                <span class="label">入场价</span>
                <span class="value">${pos.get('entry_price', 0):.2f}</span>
            </div>
            <div class="metric">
                <span class="label">当前价</span>
                <span class="value">${pos.get('current_price', 0):.2f}</span>
            </div>
            <div class="metric">
                <span class="label">盈亏</span>
                <span class="value {pnl_class}">{pnl_sign}${pnl:.4f}</span>
            </div>
        </div>
        '''
    return html

def get_trades_html():
    """生成交易记录HTML"""
    if not data['trades']:
        return '<div style="color: #666; text-align: center; padding: 10px;">无交易记录</div>'
    
    html = ''
    for trade in data['trades'][:10]:  # 只显示最近10笔
        direction = trade.get('direction', 'N/A')
        direction_emoji = '📈' if direction == 'LONG' else '📉' if direction == 'SHORT' else '🔄'
        
        html += f'''
        <div class="trade">
            <div class="metric">
                <span class="label">{direction_emoji} {trade.get('time', 'N/A')}</span>
                <span class="value">{trade.get('contracts', 0)}张</span>
            </div>
            <div class="metric">
                <span class="label">价格</span>
                <span class="value">${trade.get('entry_price', 0):.2f}</span>
            </div>
            <div class="metric">
                <span class="label">原因</span>
                <span class="value">{trade.get('reason', 'N/A')[:30]}...</span>
            </div>
        </div>
        '''
    return html

def update_data():
    """更新数据"""
    while True:
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
            
            # 更新账户余额
            balance = exchange.fetch_balance()
            data['account']['balance'] = balance['total'].get('USDT', 0)
            data['account']['available'] = balance['free'].get('USDT', 0)
            
            # 更新市场数据
            ticker = exchange.fetch_ticker('BTC/USDT:USDT')
            data['market']['price'] = ticker['last']
            data['market']['change'] = ticker['percentage']
            
            # 更新持仓
            positions = exchange.fetch_positions(['BTC/USDT:USDT'])
            data['positions'] = []
            
            for pos in positions:
                if pos['symbol'] == 'BTC/USDT:USDT':
                    contracts = float(pos.get('contracts', 0))
                    if contracts > 0:
                        position_info = {
                            'side': pos.get('side', 'N/A'),
                            'contracts': contracts,
                            'entry_price': float(pos.get('entryPrice', 0)),
                            'current_price': float(pos.get('markPrice', 0)),
                            'pnl': float(pos.get('unrealizedPnl', 0))
                        }
                        data['positions'].append(position_info)
            
            # 加载交易历史
            history_file = 'logs/autonomous_trades.json'
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    lines = f.readlines()
                    trades = [json.loads(line) for line in lines if line.strip()]
                    
                    data['trades'] = []
                    for trade in trades[-20:]:  # 最近20笔
                        try:
                            trade_time = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00')).strftime('%H:%M:%S')
                        except:
                            trade_time = trade.get('timestamp', 'N/A')
                        
                        trade_info = {
                            'time': trade_time,
                            'direction': trade.get('direction', 'N/A'),
                            'contracts': trade.get('contracts', 0),
                            'entry_price': trade.get('entry_price', 0),
                            'reason': trade.get('reason', 'N/A')
                        }
                        data['trades'].append(trade_info)
                    
                    # 最新的在前面
                    data['trades'].reverse()
            
            # 更新最后更新时间
            data['last_update'] = datetime.now().isoformat()
            
        except Exception as e:
            print(f"更新数据失败: {e}")
        
        time.sleep(5)

@app.route('/')
def index():
    """主页面"""
    return get_simple_html()

@app.route('/api/data')
def api_data():
    """API数据"""
    return jsonify({
        'account': data['account'],
        'market': data['market'],
        'positions_html': get_positions_html(),
        'trades_html': get_trades_html(),
        'last_update': data['last_update']
    })

if __name__ == '__main__':
    # 启动后台更新线程
    update_thread = threading.Thread(target=update_data, daemon=True)
    update_thread.start()
    
    print("🚀 启动工作监控面板...")
    print("🌐 访问地址: http://localhost:8084")
    print("📊 确保数据能正常显示")
    
    app.run(host='0.0.0.0', port=8084, debug=False)