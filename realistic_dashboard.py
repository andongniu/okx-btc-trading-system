#!/usr/bin/env python3
"""
务实交易系统监控仪表盘
"""

from flask import Flask, render_template, jsonify
import json
import time
from datetime import datetime
import threading
import logging
import os

app = Flask(__name__)

# 模拟数据（实际应该从交易引擎获取）
dashboard_data = {
    'system_status': 'running',
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
        'btc_price': 65431.30,
        'btc_change': 2.70,
        'timestamp': datetime.now().isoformat()
    },
    'performance': {
        'week1_target': 240.0,
        'week2_target': 290.0,
        'week3_target': 340.0,
        'week4_target': 400.0,
        'current_week': 1
    },
    'alerts': []
}

def update_dashboard():
    """定期更新仪表盘数据"""
    while True:
        try:
            # 更新市场数据
            dashboard_data['market_data']['timestamp'] = datetime.now().isoformat()
            
            # 模拟信号生成
            if len(dashboard_data['signals']) < 5:
                signal_time = datetime.now().strftime('%H:%M:%S')
                dashboard_data['signals'].insert(0, {
                    'time': signal_time,
                    'direction': 'LONG' if time.time() % 2 == 0 else 'SHORT',
                    'confidence': 0.75 + (time.time() % 10) * 0.02,
                    'price': 65431.30 + (time.time() % 1000) - 500,
                    'reason': 'EMA金叉 + 成交量放大',
                    'status': 'waiting'
                })
                if len(dashboard_data['signals']) > 10:
                    dashboard_data['signals'] = dashboard_data['signals'][:10]
            
            # 模拟交易记录
            if len(dashboard_data['recent_trades']) < 3:
                trade_time = datetime.now().strftime('%H:%M:%S')
                dashboard_data['recent_trades'].insert(0, {
                    'time': trade_time,
                    'direction': 'LONG',
                    'entry': 65400.00,
                    'exit': 65500.00,
                    'pnl': 15.42,
                    'pnl_percent': 0.77,
                    'leverage': 45,
                    'reason': '趋势突破入场'
                })
                if len(dashboard_data['recent_trades']) > 5:
                    dashboard_data['recent_trades'] = dashboard_data['recent_trades'][:5]
            
            # 更新资金曲线（模拟）
            dashboard_data['equity'] = 200.0 + (time.time() % 100) * 0.1
            
            # 更新风险指标
            dashboard_data['risk_indicators']['win_rate'] = 65.0 + (time.time() % 10) - 5
            dashboard_data['risk_indicators']['profit_factor'] = 1.8 + (time.time() % 5) * 0.1 - 0.25
            
        except Exception as e:
            logging.error(f"更新仪表盘失败: {e}")
        
        time.sleep(5)

@app.route('/')
def index():
    """主页面"""
    return render_template('realistic_dashboard_simple.html')

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    return jsonify(dashboard_data)

@app.route('/api/start_trading', methods=['POST'])
def start_trading():
    """启动交易"""
    dashboard_data['system_status'] = 'trading'
    dashboard_data['alerts'].append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'level': 'info',
        'message': '交易系统已启动'
    })
    return jsonify({'status': 'started'})

@app.route('/api/stop_trading', methods=['POST'])
def stop_trading():
    """停止交易"""
    dashboard_data['system_status'] = 'paused'
    dashboard_data['alerts'].append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'level': 'warning',
        'message': '交易系统已暂停'
    })
    return jsonify({'status': 'stopped'})

@app.route('/api/emergency_stop', methods=['POST'])
def emergency_stop():
    """紧急停止"""
    dashboard_data['system_status'] = 'emergency_stop'
    dashboard_data['alerts'].append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'level': 'critical',
        'message': '紧急停止已触发'
    })
    return jsonify({'status': 'emergency_stopped'})

@app.route('/api/test_trade', methods=['POST'])
def test_trade():
    """测试交易"""
    trade_time = datetime.now().strftime('%H:%M:%S')
    dashboard_data['recent_trades'].insert(0, {
        'time': trade_time,
        'direction': 'TEST',
        'entry': dashboard_data['market_data']['btc_price'],
        'exit': dashboard_data['market_data']['btc_price'] + 100,
        'pnl': 10.0,
        'pnl_percent': 0.5,
        'leverage': 45,
        'reason': '测试交易'
    })
    dashboard_data['alerts'].append({
        'time': trade_time,
        'level': 'info',
        'message': '测试交易执行成功'
    })
    return jsonify({'status': 'test_trade_executed'})

if __name__ == '__main__':
    # 创建模板目录
    os.makedirs('templates', exist_ok=True)
    
    # 启动后台更新线程
    update_thread = threading.Thread(target=update_dashboard, daemon=True)
    update_thread.start()
    
    # 启动Flask服务器
    print("🚀 启动务实交易监控仪表盘...")
    print("🌐 访问地址: http://localhost:8080")
    print("📊 监控系统状态中...")
    app.run(host='0.0.0.0', port=8080, debug=False)