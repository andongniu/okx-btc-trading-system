#!/usr/bin/env python3
"""
交易通知器 - 监控交易并发送Telegram通知
"""

import time
import json
import os
from datetime import datetime
import ccxt
from telegram_notify_config import send_telegram_message, get_telegram_config

class TradeNotifier:
    def __init__(self):
        """初始化通知器"""
        print('🔔 初始化交易通知器...')
        
        # 加载配置
        with open('config/final_config.json', 'r') as f:
            self.config = json.load(f)
        
        # 初始化交易所
        self.exchange = ccxt.okx({
            'apiKey': self.config['exchange']['api_key'],
            'secret': self.config['exchange']['secret'],
            'password': self.config['exchange']['passphrase'],
            'enableRateLimit': True,
            'proxies': self.config['exchange']['proxies'],
            'options': {'defaultType': 'swap'}
        })
        
        self.symbol = 'BTC/USDT:USDT'
        
        # 状态跟踪
        self.last_positions = []
        self.last_trade_count = 0
        self.notification_config = get_telegram_config()
        
        print('✅ 交易通知器初始化完成')
        print(f'📊 检查间隔: 30秒')
        print(f'📱 Telegram通知: {"已配置" if self.notification_config else "模拟模式"}')
    
    def check_new_trades(self):
        """检查新交易"""
        try:
            # 检查持仓变化
            positions = self.exchange.fetch_positions([self.symbol])
            current_positions = []
            
            for pos in positions:
                if pos['symbol'] == self.symbol:
                    contracts = float(pos.get('contracts', 0))
                    if contracts > 0:
                        position_info = {
                            'side': pos.get('side', 'N/A'),
                            'contracts': contracts,
                            'entry_price': float(pos.get('entryPrice', 0)),
                            'current_price': float(pos.get('markPrice', 0)),
                            'leverage': float(pos.get('leverage', 0)),
                            'unrealized_pnl': float(pos.get('unrealizedPnl', 0))
                        }
                        current_positions.append(position_info)
            
            # 检查是否有新开仓
            if len(current_positions) > len(self.last_positions):
                # 有新开仓
                new_position = current_positions[-1]  # 假设最新的是新开的
                self.send_open_position_notification(new_position)
            
            # 检查持仓是否平仓
            elif len(current_positions) < len(self.last_positions):
                # 有平仓
                self.send_close_position_notification()
            
            # 更新最后持仓状态
            self.last_positions = current_positions
            
            # 检查交易历史
            self.check_trade_history()
            
            return True
            
        except Exception as e:
            print(f"❌ 检查交易失败: {e}")
            return False
    
    def check_trade_history(self):
        """检查交易历史"""
        try:
            # 加载交易日志
            history_file = 'logs/autonomous_trades.json'
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    lines = f.readlines()
                    current_trade_count = len(lines)
                
                # 如果有新交易
                if current_trade_count > self.last_trade_count:
                    # 读取最新交易
                    with open(history_file, 'r') as f:
                        lines = f.readlines()
                        latest_trade = json.loads(lines[-1])
                    
                    # 如果是开仓交易且状态为open
                    if latest_trade.get('status') == 'open' and latest_trade.get('direction') in ['LONG', 'SHORT']:
                        self.send_trade_notification(latest_trade)
                    
                    self.last_trade_count = current_trade_count
                    
        except Exception as e:
            print(f"❌ 检查交易历史失败: {e}")
    
    def send_open_position_notification(self, position):
        """发送开仓通知"""
        side = position['side']
        side_emoji = '📈' if side.upper() == 'LONG' else '📉' if side.upper() == 'SHORT' else '🔄'
        
        message = f"""
{side_emoji} <b>🚀 自主交易系统开仓通知</b>

<b>交易详情:</b>
• 方向: {side}
• 合约数量: {position['contracts']}张 ({position['contracts'] * 0.01:.4f} BTC)
• 入场价: ${position['entry_price']:.2f}
• 当前价: ${position['current_price']:.2f}
• 杠杆: {position['leverage']}x
• 浮动盈亏: ${position['unrealized_pnl']:.4f}

<b>监控信息:</b>
• 时间: {datetime.now().strftime('%H:%M:%S')}
• 监控面板: http://localhost:8084

<i>系统正在监控持仓，如有变化会及时通知。</i>
        """
        
        print(f"\n📱 发送开仓通知...")
        send_telegram_message(message, self.notification_config)
    
    def send_close_position_notification(self):
        """发送平仓通知"""
        message = f"""
🔄 <b>📊 自主交易系统平仓通知</b>

<b>交易详情:</b>
• 状态: 已平仓
• 时间: {datetime.now().strftime('%H:%M:%S')}

<b>账户状态:</b>
• 系统正在等待下一个交易机会
• 监控面板持续更新

<b>监控面板:</b>
http://localhost:8084

<i>持仓已平仓，系统继续监控市场寻找机会。</i>
        """
        
        print(f"\n📱 发送平仓通知...")
        send_telegram_message(message, self.notification_config)
    
    def send_trade_notification(self, trade):
        """发送交易通知"""
        direction = trade.get('direction', 'N/A')
        direction_emoji = '📈' if direction == 'LONG' else '📉' if direction == 'SHORT' else '🔄'
        
        message = f"""
{direction_emoji} <b>🎯 自主交易系统执行交易</b>

<b>交易详情:</b>
• 方向: {direction}
• 合约数量: {trade.get('contracts', 0)}张
• 入场价: ${trade.get('entry_price', 0):.2f}
• 止损价: ${trade.get('stop_loss_price', 0):.2f} (-{trade.get('stop_loss_pct', 0)}%)
• 止盈价: ${trade.get('take_profit_price', 0):.2f} (+{trade.get('take_profit_pct', 0)}%)
• 杠杆: {trade.get('leverage', 0)}x
• 风险回报比: {trade.get('risk_reward_ratio', 0):.2f}:1

<b>策略信息:</b>
• 策略: {trade.get('strategy', 'N/A')}
• 原因: {trade.get('reason', 'N/A')}
• 信心度: {trade.get('confidence', 0)*100:.0f}%

<b>订单信息:</b>
• 订单ID: {trade.get('order_id', 'N/A')}
• 时间: {trade.get('timestamp', datetime.now().isoformat())}

<b>监控面板:</b>
http://localhost:8084
        """
        
        print(f"\n📱 发送交易通知...")
        send_telegram_message(message, self.notification_config)
    
    def run(self):
        """运行通知器"""
        print('\n🔔 启动交易通知器...')
        print('='*50)
        print('系统将每30秒检查一次交易状态')
        print('一旦检测到开仓，立即发送Telegram通知')
        print('='*50)
        
        iteration = 0
        while True:
            try:
                iteration += 1
                print(f'\n🔄 第{iteration}次检查 ({datetime.now().strftime("%H:%M:%S")})')
                
                # 检查新交易
                self.check_new_trades()
                
                # 等待下一次检查
                print(f'⏳ 下次检查: 30秒后')
                time.sleep(30)
                
            except KeyboardInterrupt:
                print('\n🛑 用户中断，停止通知器')
                break
            except Exception as e:
                print(f'❌ 通知器错误: {e}')
                time.sleep(30)

if __name__ == '__main__':
    notifier = TradeNotifier()
    notifier.run()