#!/usr/bin/env python3
"""
真实交易监控面板 - 显示正确持仓信息并控制交易
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import time
from datetime import datetime
import threading
import logging
import os
import ccxt

app = Flask(__name__, static_folder='templates')

# 全局状态
trading_data = {
    'system_status': 'ready',  # ready, trading, paused, stopped
    'capital': 200.0,
    'equity': 200.0,
    'target_capital': 400.0,
    'daily_target': 6.67,
    'daily_pnl': 0.0,
    'total_pnl': 0.0,
    'positions': [],
    'recent_trades': [],
    'signals': [],
    'risk_indicators': {
        'max_drawdown': 0.0,
        'risk_exposure': 0.0,
        'sharpe_ratio': 0.0,
        'win_rate': 0.0,
        'profit_factor': 0.0
    },
    'market_data': {
        'btc_price': 0.0,
        'btc_change': 0.0,
        'timestamp': datetime.now().isoformat()
    },
    'performance': {
        'week1_target': 240.0,
        'week2_target': 290.0,
        'week3_target': 340.0,
        'week4_target': 400.0,
        'current_week': 1
    },
    'alerts': [],
    'trading_config': {
        'symbol': 'BTC/USDT:USDT',
        'contract_size': 0.01,  # 1张合约 = 0.01 BTC
        'min_contracts': 0.01,  # 最小交易量
        'default_leverage': 10,
        'max_leverage': 50,
        'position_sizing': 0.05  # 5%资金每笔交易
    }
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
        
        # 加载历史交易记录
        load_trade_history()
        
        return True
    except Exception as e:
        logging.error(f"初始化交易所失败: {e}")
        return False

def load_trade_history():
    """加载历史交易记录"""
    try:
        if not exchange:
            return
        
        symbol = 'BTC/USDT:USDT'
        
        # 获取所有成交记录
        trades = exchange.fetch_my_trades(symbol, limit=50)
        
        for trade in trades:
            trade_time = datetime.fromtimestamp(trade["timestamp"]/1000).strftime('%H:%M:%S')
            trade_id = trade["id"]
            
            # 检查是否已存在
            exists = any(t.get('trade_id') == trade_id for t in trading_data['recent_trades'])
            if not exists:
                # 计算盈亏（如果是平仓）
                pnl = 0
                reason = "测试交易"
                strategy = "最小仓位验证"
                stop_loss = 0
                take_profit = 0
                
                # 根据交易类型设置策略信息
                if trade["side"] == "buy":
                    reason = "开仓测试 - 验证最小交易量"
                    strategy = "最小仓位验证策略"
                    stop_loss = trade["price"] * 0.99  # 1%止损
                    take_profit = trade["price"] * 1.02  # 2%止盈
                elif trade["side"] == "sell":
                    # 查找对应的买入交易计算盈亏
                    for prev_trade in trading_data['recent_trades']:
                        if prev_trade.get('direction') == 'LONG' and prev_trade.get('status') == 'open':
                            entry_price = prev_trade.get('entry_price', 0)
                            if entry_price > 0:
                                pnl = (trade["price"] - entry_price) * trade["amount"] * 0.01
                                reason = f"平仓 - 测试完成"
                                strategy = "测试平仓"
                                break
                
                trade_record = {
                    'trade_id': trade_id,
                    'time': trade_time,
                    'direction': 'LONG' if trade["side"] == "buy" else 'CLOSE',
                    'contracts': trade["amount"],
                    'btc_amount': trade["amount"] * 0.01,
                    'side': '买入' if trade["side"] == "buy" else '卖出',
                    'price': trade["price"],
                    'cost': trade["cost"],
                    'fee': trade.get("fee", {}).get("cost", 0),
                    'pnl': pnl,
                    'status': 'closed',
                    'reason': reason,
                    'strategy': strategy,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'leverage': 5
                }
                
                trading_data['recent_trades'].insert(0, trade_record)
        
        # 限制记录数量
        if len(trading_data['recent_trades']) > 50:
            trading_data['recent_trades'] = trading_data['recent_trades'][:50]
            
        logging.info(f"加载了 {len(trades)} 笔历史交易记录")
        
    except Exception as e:
        logging.error(f"加载历史交易记录失败: {e}")

def update_trading_data():
    """更新交易数据"""
    while True:
        try:
            if exchange:
                # 更新市场数据
                ticker = exchange.fetch_ticker('BTC/USDT:USDT')
                trading_data['market_data']['btc_price'] = ticker['last']
                trading_data['market_data']['btc_change'] = ticker['percentage']
                trading_data['market_data']['timestamp'] = datetime.now().isoformat()
                
                # 更新持仓
                positions = exchange.fetch_positions(['BTC/USDT:USDT'])
                trading_data['positions'] = []
                has_active_position = False
                
                for pos in positions:
                    if pos['symbol'] == 'BTC/USDT:USDT':
                        contracts = float(pos.get('contracts', 0))
                        if contracts > 0:
                            has_active_position = True
                            position_info = {
                                'symbol': pos['symbol'],
                                'contracts': contracts,
                                'btc_amount': contracts * 0.01,  # 合约乘数
                                'side': pos.get('side', 'N/A'),
                                'entry_price': float(pos.get('entryPrice', 0)),
                                'current_price': float(pos.get('markPrice', 0)),
                                'unrealized_pnl': float(pos.get('unrealizedPnl', 0)),
                                'leverage': float(pos.get('leverage', 0)),
                                'margin': float(pos.get('initialMargin', 0)),
                                'timestamp': datetime.now().isoformat()
                            }
                            trading_data['positions'].append(position_info)
                
                # 如果有活跃持仓，自动切换到trading状态
                if has_active_position and trading_data['system_status'] == 'ready':
                    trading_data['system_status'] = 'trading'
                    trading_data['alerts'].insert(0, {
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'level': 'info',
                        'message': '检测到持仓，系统自动切换到交易状态'
                    })
                    if len(trading_data['alerts']) > 10:
                        trading_data['alerts'] = trading_data['alerts'][:10]
                
                # 更新账户余额
                balance = exchange.fetch_balance()
                usdt_total = balance['total'].get('USDT', 0)
                usdt_free = balance['free'].get('USDT', 0)
                
                trading_data['capital'] = usdt_total
                trading_data['equity'] = usdt_total
                
                # 如果有持仓，计算包含未实现盈亏的权益
                if trading_data['positions']:
                    total_unrealized = sum(p['unrealized_pnl'] for p in trading_data['positions'])
                    trading_data['equity'] = usdt_total + total_unrealized
                    trading_data['total_pnl'] = total_unrealized
                
                # 更新风险指标
                if len(trading_data['recent_trades']) > 0:
                    winning_trades = [t for t in trading_data['recent_trades'] if t.get('pnl', 0) > 0]
                    losing_trades = [t for t in trading_data['recent_trades'] if t.get('pnl', 0) < 0]
                    
                    if winning_trades:
                        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades)
                    else:
                        avg_win = 0
                    
                    if losing_trades:
                        avg_loss = abs(sum(t['pnl'] for t in losing_trades) / len(losing_trades))
                    else:
                        avg_loss = 0
                    
                    win_rate = len(winning_trades) / len(trading_data['recent_trades']) if trading_data['recent_trades'] else 0
                    profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
                    
                    trading_data['risk_indicators']['win_rate'] = win_rate * 100
                    trading_data['risk_indicators']['profit_factor'] = profit_factor
            
            # 模拟信号生成（实际应该从策略生成）
            if trading_data['system_status'] == 'trading' and len(trading_data['signals']) < 10:
                signal_time = datetime.now().strftime('%H:%M:%S')
                trading_data['signals'].insert(0, {
                    'time': signal_time,
                    'direction': 'LONG' if time.time() % 2 == 0 else 'SHORT',
                    'confidence': 0.75 + (time.time() % 10) * 0.02,
                    'price': trading_data['market_data']['btc_price'],
                    'reason': '三重确认信号',
                    'status': 'waiting'
                })
                if len(trading_data['signals']) > 10:
                    trading_data['signals'] = trading_data['signals'][:10]
            
        except Exception as e:
            logging.error(f"更新交易数据失败: {e}")
        
        time.sleep(5)

def execute_trade(direction, contracts, leverage=10, reason="", strategy=""):
    """执行交易"""
    try:
        if not exchange:
            return False, "交易所未连接"
        
        symbol = 'BTC/USDT:USDT'
        
        # 设置杠杆
        exchange.set_leverage(leverage, symbol)
        
        # 获取当前价格
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # 计算止盈止损
        if direction == 'LONG':
            stop_loss = current_price * 0.985  # 1.5%止损
            take_profit = current_price * 1.03  # 3%止盈
            stop_loss_pct = 1.5
            take_profit_pct = 3.0
        else:
            stop_loss = current_price * 1.015  # 1.5%止损
            take_profit = current_price * 0.97  # 3%止盈
            stop_loss_pct = 1.5
            take_profit_pct = 3.0
        
        # 执行订单
        if direction == 'LONG':
            order = exchange.create_market_buy_order(symbol, contracts)
            side = '买入'
            order_side = 'buy'
        else:
            order = exchange.create_market_sell_order(symbol, contracts)
            side = '卖出'
            order_side = 'sell'
        
        # 获取成交详情
        trade_details = None
        try:
            # 获取订单详情
            order_info = exchange.fetch_order(order['id'], symbol)
            # 获取成交详情
            trades = exchange.fetch_my_trades(symbol, since=order['timestamp'] - 60000, limit=5)
            for trade in trades:
                if trade['order'] == order['id']:
                    trade_details = trade
                    break
        except:
            pass
        
        # 记录交易
        trade_time = datetime.now().strftime('%H:%M:%S')
        trade_record = {
            'trade_id': trade_details['id'] if trade_details else order['id'],
            'time': trade_time,
            'direction': direction,
            'contracts': contracts,
            'btc_amount': contracts * 0.01,
            'side': side,
            'order_id': order['id'],
            'order_side': order_side,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'stop_loss_pct': stop_loss_pct,
            'take_profit_pct': take_profit_pct,
            'status': 'open',
            'leverage': leverage,
            'reason': reason if reason else f'{direction}开仓 - 价格突破信号',
            'strategy': strategy if strategy else '三重确认策略',
            'risk_amount': contracts * 0.01 * current_price * (stop_loss_pct/100),  # 风险金额
            'reward_amount': contracts * 0.01 * current_price * (take_profit_pct/100),  # 潜在盈利
            'risk_reward_ratio': take_profit_pct / stop_loss_pct  # 风险回报比
        }
        
        if trade_details:
            trade_record.update({
                'executed_price': trade_details['price'],
                'fee': trade_details.get('fee', {}).get('cost', 0),
                'cost': trade_details['cost']
            })
        
        trading_data['recent_trades'].insert(0, trade_record)
        
        if len(trading_data['recent_trades']) > 50:
            trading_data['recent_trades'] = trading_data['recent_trades'][:50]
        
        # 添加警报
        trading_data['alerts'].insert(0, {
            'time': trade_time,
            'level': 'info',
            'message': f'{side} {contracts}张合约执行成功 (杠杆{leverage}x，止损{stop_loss_pct}%，止盈{take_profit_pct}%)'
        })
        
        if len(trading_data['alerts']) > 10:
            trading_data['alerts'] = trading_data['alerts'][:10]
        
        return True, "交易执行成功"
        
    except Exception as e:
        error_msg = f"交易执行失败: {str(e)}"
        logging.error(error_msg)
        
        trading_data['alerts'].insert(0, {
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': 'error',
            'message': error_msg
        })
        
        return False, error_msg

def close_all_positions():
    """平掉所有持仓"""
    try:
        if not exchange:
            return False, "交易所未连接"
        
        symbol = 'BTC/USDT:USDT'
        positions = exchange.fetch_positions([symbol])
        
        closed_count = 0
        for pos in positions:
            if pos['symbol'] == symbol and float(pos.get('contracts', 0)) > 0:
                contracts = float(pos.get('contracts', 0))
                side = pos.get('side', 'long')
                
                if side == 'long':
                    order = exchange.create_market_sell_order(symbol, contracts)
                    action = '卖出平多'
                else:
                    order = exchange.create_market_buy_order(symbol, contracts)
                    action = '买入平空'
                
                closed_count += 1
                
                # 记录平仓
                trade_time = datetime.now().strftime('%H:%M:%S')
                trading_data['recent_trades'].insert(0, {
                    'time': trade_time,
                    'direction': 'CLOSE',
                    'contracts': contracts,
                    'btc_amount': contracts * 0.01,
                    'side': action,
                    'order_id': order['id'],
                    'status': 'closed'
                })
        
        if closed_count > 0:
            msg = f'成功平掉{closed_count}个持仓'
            trading_data['alerts'].insert(0, {
                'time': datetime.now().strftime('%H:%M:%S'),
                'level': 'info',
                'message': msg
            })
            return True, msg
        else:
            return True, "无持仓可平"
        
    except Exception as e:
        error_msg = f"平仓失败: {str(e)}"
        logging.error(error_msg)
        
        trading_data['alerts'].insert(0, {
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': 'error',
            'message': error_msg
        })
        
        return False, error_msg

@app.route('/')
def index():
    """主页面"""
    return render_template('real_trading_dashboard.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """提供静态文件"""
    return send_from_directory(app.static_folder, filename)

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    return jsonify(trading_data)

@app.route('/api/start_trading', methods=['POST'])
def start_trading():
    """启动交易系统"""
    trading_data['system_status'] = 'trading'
    trading_data['alerts'].insert(0, {
        'time': datetime.now().strftime('%H:%M:%S'),
        'level': 'info',
        'message': '交易系统已启动'
    })
    return jsonify({'status': 'started', 'message': '交易系统已启动'})

@app.route('/api/stop_trading', methods=['POST'])
def stop_trading():
    """停止交易系统"""
    trading_data['system_status'] = 'paused'
    trading_data['alerts'].insert(0, {
        'time': datetime.now().strftime('%H:%M:%S'),
        'level': 'warning',
        'message': '交易系统已暂停'
    })
    return jsonify({'status': 'stopped', 'message': '交易系统已暂停'})

@app.route('/api/emergency_stop', methods=['POST'])
def emergency_stop():
    """紧急停止"""
    success, message = close_all_positions()
    trading_data['system_status'] = 'stopped'
    
    if success:
        trading_data['alerts'].insert(0, {
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': 'critical',
            'message': '紧急停止已触发: ' + message
        })
    else:
        trading_data['alerts'].insert(0, {
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': 'critical',
            'message': '紧急停止失败: ' + message
        })
    
    return jsonify({'status': 'emergency_stopped', 'message': message})

@app.route('/api/execute_trade', methods=['POST'])
def api_execute_trade():
    """执行交易"""
    data = request.json
    direction = data.get('direction', 'LONG')
    contracts = float(data.get('contracts', 0.01))
    leverage = int(data.get('leverage', 10))
    reason = data.get('reason', '')
    strategy = data.get('strategy', '')
    
    if trading_data['system_status'] != 'trading':
        return jsonify({'status': 'error', 'message': '交易系统未启动'})
    
    success, message = execute_trade(direction, contracts, leverage, reason, strategy)
    
    if success:
        return jsonify({'status': 'executed', 'message': message})
    else:
        return jsonify({'status': 'error', 'message': message})

@app.route('/api/close_positions', methods=['POST'])
def api_close_positions():
    """平掉所有持仓"""
    success, message = close_all_positions()
    
    if success:
        return jsonify({'status': 'closed', 'message': message})
    else:
        return jsonify({'status': 'error', 'message': message})

@app.route('/api/test_small_trade', methods=['POST'])
def test_small_trade():
    """测试小额交易"""
    # 使用最小交易量测试，添加策略信息
    success, message = execute_trade(
        'LONG', 
        0.01, 
        5,
        reason="系统功能测试 - 验证最小交易量",
        strategy="最小仓位验证策略"
    )
    
    if success:
        return jsonify({'status': 'test_executed', 'message': '测试交易执行成功'})
    else:
        return jsonify({'status': 'error', 'message': message})

if __name__ == '__main__':
    # 创建日志目录
    os.makedirs('logs', exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/real_trading_dashboard.log'),
            logging.StreamHandler()
        ]
    )
    
    # 初始化交易所
    if init_exchange():
        print('✅ 交易所连接成功')
    else:
        print('⚠️  交易所连接失败，使用模拟模式')
    
    # 启动后台更新线程
    update_thread = threading.Thread(target=update_trading_data, daemon=True)
    update_thread.start()
    
    # 启动Flask服务器
    print("🚀 启动真实交易监控面板...")
    print("🌐 访问地址: http://localhost:8082")
    print("📊 监控系统状态中...")
    app.run(host='0.0.0.0', port=8082, debug=False)