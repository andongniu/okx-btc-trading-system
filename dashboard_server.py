#!/usr/bin/env python3
"""
交易系统面板服务器
提供静态文件服务和API接口
"""

import json
import os
import time
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# 配置文件路径
CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'config')
DATA_DIR = os.path.join(os.path.dirname(__file__))
BACKTEST_RESULTS = os.path.join(DATA_DIR, 'backtest_results.json')
OKX_CONFIG = os.path.join(CONFIG_DIR, 'okx_backtest_config.json')
STRATEGY_FILE = os.path.join(DATA_DIR, 'user_data', 'strategies', 'SampleStrategy.py')

class TradingDashboardHandler(SimpleHTTPRequestHandler):
    """自定义HTTP处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        # API端点
        if parsed_path.path == '/api/system-status':
            self.send_system_status()
        elif parsed_path.path == '/api/backtest-results':
            self.send_backtest_results()
        elif parsed_path.path == '/api/config':
            self.send_config()
        elif parsed_path.path == '/api/strategy':
            self.send_strategy_info()
        elif parsed_path.path == '/api/recent-trades':
            self.send_recent_trades()
        elif parsed_path.path == '/api/equity-curve':
            self.send_equity_curve()
        else:
            # 静态文件服务
            super().do_GET()
    
    def send_json_response(self, data, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def send_system_status(self):
        """发送系统状态"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "status": "waiting",
                "exchange": "OKX",
                "trading_pair": "BTC/USDT:USDT",
                "trading_mode": "futures",
                "margin_mode": "isolated",
                "dry_run": True,
                "initial_balance": 10000,
                "current_balance": 10000,
                "max_open_trades": 3,
                "stake_amount": 100
            },
            "connection": {
                "proxy": "http://127.0.0.1:7897",
                "api_configured": False,
                "last_check": datetime.now().isoformat()
            },
            "performance": {
                "total_return": -98.92,
                "total_trades": 162,
                "win_rate": 0,
                "max_drawdown": -99.08,
                "sharpe_ratio": -2.34
            }
        }
        self.send_json_response(status)
    
    def send_backtest_results(self):
        """发送回测结果"""
        try:
            with open(BACKTEST_RESULTS, 'r') as f:
                results = json.load(f)
            self.send_json_response(results)
        except FileNotFoundError:
            self.send_json_response({
                "error": "Backtest results not found",
                "initial_balance": 10000,
                "final_balance": 107.98,
                "total_return": -98.92,
                "num_trades": 162,
                "trades": []
            })
    
    def send_config(self):
        """发送配置文件"""
        try:
            with open(OKX_CONFIG, 'r') as f:
                config = json.load(f)
            self.send_json_response(config)
        except FileNotFoundError:
            self.send_json_response({"error": "Config file not found"})
    
    def send_strategy_info(self):
        """发送策略信息"""
        try:
            with open(STRATEGY_FILE, 'r') as f:
                strategy_content = f.read()
            
            # 解析策略信息
            strategy_info = {
                "name": "SampleStrategy",
                "timeframe": "5m",
                "can_short": False,
                "minimal_roi": {"0": 0.10, "30": 0.05, "60": 0.02, "120": 0},
                "stoploss": -0.10,
                "trailing_stop": False,
                "startup_candle_count": 30,
                "indicators": ["RSI(14)", "SMA(20)", "SMA(50)", "Bollinger Bands(20,2)"],
                "entry_conditions": "RSI < 30 and price < SMA20",
                "exit_conditions": "RSI > 70 and price > SMA20"
            }
            self.send_json_response(strategy_info)
        except FileNotFoundError:
            self.send_json_response({"error": "Strategy file not found"})
    
    def send_recent_trades(self):
        """发送最近交易"""
        try:
            with open(BACKTEST_RESULTS, 'r') as f:
                results = json.load(f)
            
            # 获取最近10笔交易
            recent_trades = results.get("trades", [])[-20:]  # 最近20笔（10对）
            self.send_json_response({
                "recent_trades": recent_trades,
                "count": len(recent_trades),
                "timestamp": datetime.now().isoformat()
            })
        except FileNotFoundError:
            self.send_json_response({
                "recent_trades": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            })
    
    def send_equity_curve(self):
        """发送资金曲线数据"""
        try:
            with open(BACKTEST_RESULTS, 'r') as f:
                results = json.load(f)
            
            trades = results.get("trades", [])
            equity_data = []
            current_balance = results.get("initial_balance", 10000)
            
            # 添加初始点
            if trades:
                first_timestamp = int(trades[0].get("timestamp", 0))
                equity_data.append({
                    "timestamp": first_timestamp - 3600,  # 交易开始前1小时
                    "balance": current_balance
                })
            
            # 添加每个卖出交易后的资金
            for trade in trades:
                if trade.get("type") == "sell":
                    current_balance = trade.get("balance", current_balance)
                    equity_data.append({
                        "timestamp": int(trade.get("timestamp", 0)),
                        "balance": current_balance
                    })
            
            self.send_json_response({
                "equity_curve": equity_data,
                "initial_balance": results.get("initial_balance", 10000),
                "final_balance": results.get("final_balance", 10000),
                "count": len(equity_data)
            })
        except FileNotFoundError:
            self.send_json_response({
                "equity_curve": [],
                "initial_balance": 10000,
                "final_balance": 10000,
                "count": 0
            })
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {format % args}")

def start_server(port=8080):
    """启动HTTP服务器"""
    os.chdir(os.path.dirname(__file__))
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, TradingDashboardHandler)
    
    print(f"🚀 交易系统面板服务器已启动")
    print(f"📊 访问地址: http://localhost:{port}/trading_dashboard.html")
    print(f"📈 API端点:")
    print(f"   • 系统状态: http://localhost:{port}/api/system-status")
    print(f"   • 回测结果: http://localhost:{port}/api/backtest-results")
    print(f"   • 配置文件: http://localhost:{port}/api/config")
    print(f"   • 策略信息: http://localhost:{port}/api/strategy")
    print(f"   • 最近交易: http://localhost:{port}/api/recent-trades")
    print(f"   • 资金曲线: http://localhost:{port}/api/equity-curve")
    print(f"\n按 Ctrl+C 停止服务器")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")

if __name__ == '__main__':
    start_server()