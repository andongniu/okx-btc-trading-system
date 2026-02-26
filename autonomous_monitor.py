#!/usr/bin/env python3
"""
自主交易监控面板 - 只显示信息，不干扰决策
"""

from flask import Flask, render_template, jsonify, send_from_directory
import json
import time
from datetime import datetime
import threading
import logging
import os
import ccxt

app = Flask(__name__)

# 全局状态
monitor_data = {
    'system_status': 'autonomous_running',
    'last_update': datetime.now().isoformat(),
    
    # 账户信息
    'account': {
        'total_balance': 0.0,
        'available_balance': 0.0,
        'used_balance': 0.0,
        'equity': 0.0
    },
    
    # 市场数据
    'market': {
        'btc_price': 0.0,
        'btc_change': 0.0,
        'trend': 'neutral',
        'volatility': 'medium',
        'timestamp': datetime.now().isoformat()
    },
    
    # 当前持仓
    'positions': [],
    
    # 交易历史
    'trade_history': [],
    
    # 策略状态
    'strategy': {
        'status': 'waiting_for_signal',
        'last_signal_time': None,
        'last_signal': None,
        'consecutive_wins': 0,
        'consecutive_losses': 0,
        'daily_trades': 0,
        'daily_pnl': 0.0
    },
    
    # 系统信息
    'system_info': {
        'uptime': 0,
        'total_trades': 0,
        'total_pnl': 0.0,
        'win_rate': 0.0,
        'profit_factor': 0.0
    },
    
    # 警报
    'alerts': []
}

# 交易所连接
exchange = None

def init_exchange():
    """初始化交易所连接"""
    global exchange
    try:
        with open('config/final_config.json', 'r') as f:
            config = json.load(f)
        
        exchange = ccxt.okx({
            'apiKey': config['exchange']['api_key'],
            'secret': config['exchange']['secret'],
            'password': config['exchange']['passphrase'],
            'enableRateLimit': True,
            'proxies': config['exchange']['proxies'],
            'options': {'defaultType': 'swap'}
        })
        return True
    except Exception as e:
        logging.error(f"初始化交易所失败: {e}")
        return False

def load_trade_history():
    """加载交易历史"""
    try:
        history_file = 'logs/autonomous_trades.json'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                lines = f.readlines()
                trades = [json.loads(line) for line in lines if line.strip()]
                
                # 转换为显示格式
                monitor_data['trade_history'] = []
                for trade in trades[-20:]:  # 只显示最近20笔
                    trade_time = datetime.fromisoformat(trade['timestamp']).strftime('%H:%M:%S')
                    
                    # 计算盈亏（如果已平仓）
                    pnl = 0
                    status = trade.get('status', 'open')
                    
                    display_trade = {
                        'time': trade_time,
                        'direction': trade['direction'],
                        'contracts': trade['contracts'],
                        'btc_amount': trade['contracts'] * 0.01,
                        'entry_price': trade['entry_price'],
                        'stop_loss': trade.get('stop_loss_price', 0),
                        'take_profit': trade.get('take_profit_price', 0),
                        'leverage': trade['leverage'],
                        'reason': trade['reason'],
                        'confidence': trade.get('confidence', 0),
                        'status': status,
                        'pnl': pnl,
                        'order_id': trade.get('order_id', 'N/A')
                    }
                    
                    monitor_data['trade_history'].append(display_trade)
                
                # 反转顺序，最新的在前面
                monitor_data['trade_history'].reverse()
                
    except Exception as e:
        logging.error(f"加载交易历史失败: {e}")

def update_monitor_data():
    """更新监控数据"""
    while True:
        try:
            if exchange:
                # 更新账户余额
                balance = exchange.fetch_balance()
                total = balance['total'].get('USDT', 0)
                free = balance['free'].get('USDT', 0)
                used = balance['used'].get('USDT', 0)
                
                monitor_data['account']['total_balance'] = total
                monitor_data['account']['available_balance'] = free
                monitor_data['account']['used_balance'] = used
                monitor_data['account']['equity'] = total
                
                # 更新市场数据
                ticker = exchange.fetch_ticker('BTC/USDT:USDT')
                monitor_data['market']['btc_price'] = ticker['last']
                monitor_data['market']['btc_change'] = ticker['percentage']
                monitor_data['market']['timestamp'] = datetime.now().isoformat()
                
                # 分析趋势
                ohlcv = exchange.fetch_ohlcv('BTC/USDT:USDT', '15m', limit=20)
                closes = [c[4] for c in ohlcv]
                if len(closes) >= 20:
                    sma_20 = sum(closes[-20:]) / 20
                    current_price = closes[-1]
                    
                    if current_price > sma_20:
                        monitor_data['market']['trend'] = 'bullish'
                    else:
                        monitor_data['market']['trend'] = 'bearish'
                
                # 更新持仓
                positions = exchange.fetch_positions(['BTC/USDT:USDT'])
                monitor_data['positions'] = []
                
                for pos in positions:
                    if pos['symbol'] == 'BTC/USDT:USDT':
                        contracts = float(pos.get('contracts', 0))
                        if contracts > 0:
                            position_info = {
                                'symbol': pos['symbol'],
                                'contracts': contracts,
                                'btc_amount': contracts * 0.01,
                                'side': pos.get('side', 'N/A'),
                                'entry_price': float(pos.get('entryPrice', 0)),
                                'current_price': float(pos.get('markPrice', 0)),
                                'unrealized_pnl': float(pos.get('unrealizedPnl', 0)),
                                'leverage': float(pos.get('leverage', 0)),
                                'margin': float(pos.get('initialMargin', 0)),
                                'timestamp': datetime.now().isoformat()
                            }
                            monitor_data['positions'].append(position_info)
                            
                            # 如果有持仓，更新策略状态
                            monitor_data['strategy']['status'] = 'position_open'
                
                # 如果没有持仓，更新策略状态
                if not monitor_data['positions']:
                    monitor_data['strategy']['status'] = 'waiting_for_signal'
                
                # 加载交易历史
                load_trade_history()
                
                # 更新系统信息
                if monitor_data['trade_history']:
                    total_trades = len(monitor_data['trade_history'])
                    winning_trades = [t for t in monitor_data['trade_history'] if t.get('pnl', 0) > 0]
                    losing_trades = [t for t in monitor_data['trade_history'] if t.get('pnl', 0) < 0]
                    
                    win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
                    
                    monitor_data['system_info']['total_trades'] = total_trades
                    monitor_data['system_info']['win_rate'] = win_rate * 100
                
                # 更新最后更新时间
                monitor_data['last_update'] = datetime.now().isoformat()
                
                # 计算运行时间
                start_time = datetime.fromisoformat(monitor_data['last_update'].split('T')[0] + 'T00:00:00')
                uptime = datetime.now() - start_time
                monitor_data['system_info']['uptime'] = str(uptime).split('.')[0]
            
        except Exception as e:
            logging.error(f"更新监控数据失败: {e}")
        
        time.sleep(5)  # 5秒更新一次

@app.route('/')
def index():
    """主页面"""
    return render_template('autonomous_monitor_final.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """提供静态文件"""
    return send_from_directory(app.static_folder, filename)

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    return jsonify(monitor_data)

@app.route('/api/system_info')
def get_system_info():
    """获取系统信息"""
    return jsonify({
        'system_status': monitor_data['system_status'],
        'strategy_status': monitor_data['strategy']['status'],
        'last_update': monitor_data['last_update'],
        'uptime': monitor_data['system_info']['uptime']
    })

@app.route('/api/account_info')
def get_account_info():
    """获取账户信息"""
    return jsonify(monitor_data['account'])

@app.route('/api/market_info')
def get_market_info():
    """获取市场信息"""
    return jsonify(monitor_data['market'])

@app.route('/api/positions')
def get_positions():
    """获取持仓信息"""
    return jsonify(monitor_data['positions'])

@app.route('/api/trade_history')
def get_trade_history():
    """获取交易历史"""
    return jsonify(monitor_data['trade_history'])

@app.route('/api/strategy_status')
def get_strategy_status():
    """获取策略状态"""
    return jsonify(monitor_data['strategy'])

if __name__ == '__main__':
    # 创建日志目录
    os.makedirs('logs', exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/autonomous_monitor.log'),
            logging.StreamHandler()
        ]
    )
    
    # 初始化交易所
    if init_exchange():
        print('✅ 交易所连接成功')
    else:
        print('⚠️  交易所连接失败，使用模拟数据')
    
    # 启动后台更新线程
    update_thread = threading.Thread(target=update_monitor_data, daemon=True)
    update_thread.start()
    
    # 启动Flask服务器
    print("🚀 启动自主交易监控面板...")
    print("🌐 访问地址: http://localhost:8083")
    print("📊 只显示信息，不干扰决策")
    app.run(host='0.0.0.0', port=8083, debug=False)