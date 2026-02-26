#!/usr/bin/env python3
"""
简单自主交易监控面板 - 所有代码在一个文件中
"""

from flask import Flask, render_template_string, jsonify
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
                    try:
                        trade_time = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00')).strftime('%H:%M:%S')
                    except:
                        trade_time = trade.get('timestamp', 'N/A')
                    
                    # 计算盈亏（如果已平仓）
                    pnl = trade.get('pnl', 0)
                    status = trade.get('status', 'open')
                    
                    display_trade = {
                        'time': trade_time,
                        'direction': trade.get('direction', 'N/A'),
                        'contracts': trade.get('contracts', 0),
                        'btc_amount': trade.get('contracts', 0) * 0.01,
                        'entry_price': trade.get('entry_price', 0),
                        'stop_loss': trade.get('stop_loss_price', 0),
                        'take_profit': trade.get('take_profit_price', 0),
                        'leverage': trade.get('leverage', 0),
                        'reason': trade.get('reason', 'N/A'),
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
                try:
                    start_time = datetime.fromisoformat(monitor_data['last_update'].split('T')[0] + 'T00:00:00')
                    uptime = datetime.now() - start_time
                    monitor_data['system_info']['uptime'] = str(uptime).split('.')[0]
                except:
                    monitor_data['system_info']['uptime'] = '00:00:00'
            
        except Exception as e:
            logging.error(f"更新监控数据失败: {e}")
        
        time.sleep(5)  # 5秒更新一次

# HTML模板（包含JavaScript）
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 自主交易监控面板</title>
    <style>
        :root {
            --primary: #4361ee;
            --success: #2ecc71;
            --warning: #f39c12;
            --danger: #e74c3c;
            --info: #3498db;
            --dark: #2c3e50;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #e9ecef;
        }
        
        .header h1 {
            color: #333;
            margin: 0;
            font-size: 2.5em;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .header .subtitle {
            color: #666;
            font-size: 1.2em;
            margin-top: 10px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 50px;
            font-weight: bold;
            font-size: 1.1em;
            margin-top: 15px;
            background: var(--primary);
            color: white;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            border: 1px solid #e9ecef;
        }
        
        .card h3 {
            color: #333;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 1.4em;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .metric .label {
            color: #666;
            font-weight: 500;
        }
        
        .metric .value {
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .positive { color: var(--success); }
        .negative { color: var(--danger); }
        .neutral { color: #666; }
        
        .position-item {
            padding: 15px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid var(--info);
        }
        
        .position-long { border-left-color: var(--success); }
        .position-short { border-left-color: var(--danger); }
        
        .trade-item {
            padding: 10px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #666;
        }
        
        .trade-open { border-left-color: var(--info); }
        .trade-closed { border-left-color: #666; }
        .trade-profit { border-left-color: var(--success); }
        .trade-loss { border-left-color: var(--danger); }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .info-item {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            text-align: center;
        }
        
        .info-item .label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        
        .info-item .value {
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .alert-box {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 0.9em;
        }
        
        .alert-info { background: #d1ecf1; color: #0c5460; }
        .alert-success { background: #d4edda; color: #155724; }
        .alert-warning { background: #fff3cd; color: #856404; }
        
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 自主交易监控面板</h1>
            <div class="subtitle">只显示信息，不干扰决策 | 观察模式</div>
            <div id="statusBadge" class="status-badge">状态: 自主运行中</div>
        </div>
        
        <div class="dashboard-grid">
            <!-- 系统状态 -->
            <div class="card">
                <h3>⚙️ 系统状态</h3>
                <div id="systemStatus" class="strategy-status" style="padding: 15px; background: #f8f9fa; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid var(--info);">
                    <div style="font-weight: bold; margin-bottom: 10px;">等待交易信号</div>
                    <div style="color: #666; font-size: 0.9em;">系统正在分析市场数据...</div>
                </div>
                
                <div class="info-grid">
                    <div class="info-item">
                        <div class="label">运行时间</div>
                        <div id="uptime" class="value">00:00:00</div>
                    </div>
                    <div class="info-item">
                        <div class="label">总交易次数</div>
                        <div id="totalTrades" class="value">0</div>
                    </div>
                    <div class="info-item">
                        <div class="label">胜率</div>
                        <div id="winRate" class="value">0%</div>
                    </div>
                    <div class="info-item">
                        <div class="label">最后更新</div>
                        <div id="lastUpdate" class="value">--:--:--</div>
                    </div>
                </div>
            </div>
            
            <!-- 账户信息 -->
            <div class="card">
                <h3>💰 账户信息</h3>
                <div class="metric">
                    <span class="label">总余额</span>
                    <span id="totalBalance" class="value">$0.00</span>
                </div>
                <div class="metric">
                    <span class="label">可用余额</span>
                    <span id="availableBalance" class="value">$0.00</span>
                </div>
                <div class="metric">
                    <span class="label">占用余额</span>
                    <span id="usedBalance" class="value">$0.00</span>
                </div>
                <div class="metric">
                    <span class="label">账户权益</span>
                    <span id="equity" class="value">$0.00</span>
                </div>
            </div>
            
            <!-- 市场数据 -->
            <div class="card">
                <h3>📈 市场数据</h3>
                <div class="metric">
                    <span class="label">BTC价格</span>
                    <span id="btcPrice" class="value">$0.00</span>
                </div>
                <div class="metric">
                    <span class="label">24h涨跌</span>
                    <span id="btcChange" class="value neutral">0.00%</span>
                </div>
                <div class="metric">
                    <span class="label">市场趋势</span>
                    <span id="marketTrend" class="value neutral">中性</span>
                </div>
                <div class="metric">
                    <span class="label">更新时间</span>
                    <span id="marketUpdate" class="value neutral">--:--:--</span>
                </div>
            </div>
        </div>
        
        <!-- 当前持仓 -->
        <div class="card">
            <h3>📊 当前持仓</h3>
            <div id="positionsContainer">
                <div style="color: #666; text-align: center; padding: 20px;">
                    无持仓
                </div>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <!-- 策略状态 -->
            <div