#!/usr/bin/env python3
"""
生存交易系统监控仪表盘
实时显示交易状态、决策思路、风险指标
"""

from flask import Flask, render_template, jsonify, request
import json
import threading
import time
from datetime import datetime
import logging
from survival_trader import SurvivalTrader

app = Flask(__name__)
trader = None
dashboard_data = {
    'system_status': 'initializing',
    'capital': 0,
    'equity': 0,
    'positions': [],
    'recent_trades': [],
    'metrics': {},
    'signals': [],
    'risk_indicators': {},
    'survival_status': 'critical'
}

def update_dashboard():
    """定期更新仪表盘数据"""
    global dashboard_data
    
    while True:
        try:
            if trader:
                # 更新系统状态
                dashboard_data['system_status'] = 'running' if trader.is_running else 'paused'
                dashboard_data['capital'] = trader.capital
                dashboard_data['equity'] = trader.capital + sum(
                    p.unrealized_pnl for p in trader.positions.values()
                )
                
                # 更新持仓
                dashboard_data['positions'] = [
                    {
                        'symbol': p.symbol,
                        'direction': p.direction.value,
                        'entry_price': p.entry_price,
                        'current_price': p.current_price,
                        'position_size': p.position_size,
                        'leverage': p.leverage,
                        'unrealized_pnl': p.unrealized_pnl,
                        'unrealized_pnl_percent': (p.unrealized_pnl / trader.capital) * 100,
                        'stop_loss': p.stop_loss,
                        'take_profit': p.take_profit,
                        'duration': (datetime.now() - p.entry_time).total_seconds() / 60
                    }
                    for p in trader.positions.values()
                ]
                
                # 更新最近交易
                dashboard_data['recent_trades'] = trader.trade_history[-10:]  # 最近10笔
                
                # 更新指标
                dashboard_data['metrics'] = trader.metrics
                
                # 计算风险指标
                dashboard_data['risk_indicators'] = calculate_risk_indicators(trader)
                
                # 更新生存状态
                dashboard_data['survival_status'] = calculate_survival_status(trader)
                
        except Exception as e:
            logging.error(f"仪表盘更新错误: {e}")
        
        time.sleep(5)  # 5秒更新一次

def calculate_risk_indicators(trader):
    """计算风险指标"""
    if not trader.positions:
        return {
            'total_exposure': 0,
            'max_drawdown': trader.metrics.get('max_drawdown', 0),
            'var_95': 0,
            'sharpe_ratio': 0,
            'calmar_ratio': 0
        }
    
    # 计算总风险暴露
    total_exposure = sum(
        p.position_size * p.entry_price * p.leverage 
        for p in trader.positions.values()
    ) / trader.capital
    
    return {
        'total_exposure': total_exposure,
        'max_drawdown': trader.metrics.get('max_drawdown', 0),
        'var_95': 0,  # 需要历史数据计算
        'sharpe_ratio': 0,
        'calmar_ratio': 0
    }

def calculate_survival_status(trader):
    """计算生存状态"""
    capital = trader.capital
    initial = trader.config['meta']['initial_capital']
    
    # 成本覆盖检查
    days_running = (datetime.now() - datetime.strptime(
        trader.config['meta']['start_date'], '%Y-%m-%d'
    )).days + 1
    
    required_daily_profit = trader.config['survival_rules']['min_daily_profit_for_survival']
    required_total = required_daily_profit * days_running
    
    if capital < initial - 50:  # 紧急关闭线
        return 'emergency'
    elif capital < initial + required_total:  # 未覆盖成本
        return 'critical'
    elif capital < initial * 1.5:  # 覆盖成本，开始增长
        return 'stable'
    elif capital < initial * 3:  # 良好增长
        return 'growing'
    else:  # 超额完成
        return 'thriving'

@app.route('/')
def index():
    """主仪表盘页面"""
    return render_template('survival_dashboard.html')

@app.route('/api/status')
def get_status():
    """获取系统状态API"""
    return jsonify(dashboard_data)

@app.route('/api/start', methods=['POST'])
def start_trading():
    """启动交易"""
    global trader
    if not trader:
        trader = SurvivalTrader('config/survival_config.json')
    
    trader.is_running = True
    # 在实际实现中，这里会启动交易线程
    return jsonify({'status': 'started'})

@app.route('/api/stop', methods=['POST'])
def stop_trading():
    """停止交易"""
    if trader:
        trader.is_running = False
    return jsonify({'status': 'stopped'})

@app.route('/api/trade', methods=['POST'])
def execute_manual_trade():
    """手动执行交易"""
    data = request.json
    # 这里可以添加手动交易逻辑
    return jsonify({'status': 'manual_trade_executed'})

@app.route('/api/history')
def get_trade_history():
    """获取交易历史"""
    if trader:
        return jsonify(trader.trade_history)
    return jsonify([])

@app.route('/api/metrics')
def get_metrics():
    """获取性能指标"""
    if trader:
        return jsonify(trader.metrics)
    return jsonify({})

if __name__ == '__main__':
    # 启动后台更新线程
    update_thread = threading.Thread(target=update_dashboard, daemon=True)
    update_thread.start()
    
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=8080, debug=True)