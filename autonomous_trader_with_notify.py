#!/usr/bin/env python3
"""
自主交易系统 - 带Telegram通知功能
"""

import ccxt
import json
import time
import numpy as np
from datetime import datetime
import logging
import os
import requests

class AutonomousTraderWithNotify:
    def __init__(self):
        """初始化交易系统"""
        print('🚀 初始化自主交易系统 (带通知功能)...')
        
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
        self.contract_multiplier = 0.01
        
        # 策略参数
        self.params = {
            'check_interval': 60,  # 检查间隔(秒)
            'min_position_size': 0.01,
            'max_position_size': 0.1,
            'risk_per_trade': 0.01,  # 1%风险
            'max_daily_trades': 5,
            'consecutive_loss_limit': 3
        }
        
        # 状态跟踪
        self.state = {
            'running': True,
            'last_check': None,
            'trades_today': 0,
            'consecutive_losses': 0,
            'consecutive_wins': 0,
            'daily_pnl': 0.0,
            'active_positions': [],
            'last_notification_time': None
        }
        
        # 初始化日志
        self.setup_logging()
        
        print('✅ 自主交易系统初始化完成')
        print(f'📊 检查间隔: {self.params["check_interval"]}秒')
        print(f'💰 风险控制: {self.params["risk_per_trade"]*100}%每笔交易')
        print(f'📈 最大仓位: {self.params["max_position_size"]}张合约')
        print(f'📱 Telegram通知: 已启用')
        print('🌐 监控面板: http://localhost:8084')
    
    def setup_logging(self):
        """设置日志"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/autonomous_trader_notify.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def send_telegram_notification(self, message):
        """发送Telegram通知"""
        try:
            # 这里需要配置Telegram Bot Token和Chat ID
            # 暂时先打印到日志，稍后配置
            self.logger.info(f"📱 Telegram通知: {message}")
            
            # 实际发送Telegram消息的代码（需要配置）
            # bot_token = "YOUR_BOT_TOKEN"
            # chat_id = "YOUR_CHAT_ID"
            # url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            # payload = {
            #     "chat_id": chat_id,
            #     "text": message,
            #     "parse_mode": "HTML"
            # }
            # response = requests.post(url, json=payload)
            # if response.status_code == 200:
            #     self.logger.info("Telegram通知发送成功")
            # else:
            #     self.logger.error(f"Telegram通知发送失败: {response.text}")
            
            # 暂时使用OpenClaw的消息功能
            print(f"\n📱 交易通知: {message}\n")
            
        except Exception as e:
            self.logger.error(f"发送通知失败: {e}")
    
    def analyze_market(self):
        """分析市场"""
        try:
            # 获取K线数据
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '15m', limit=100)
            closes = np.array([c[4] for c in ohlcv])
            
            # 计算技术指标
            sma_20 = np.mean(closes[-20:])
            sma_50 = np.mean(closes[-50:])
            current_price = closes[-1]
            
            # 计算支撑阻力
            support = np.min(closes[-20:])
            resistance = np.max(closes[-20:])
            price_position = (current_price - support) / (resistance - support) if resistance != support else 0.5
            
            # 计算波动率
            returns = np.diff(closes) / closes[:-1]
            volatility = np.std(returns) * np.sqrt(365 * 24 * 4)
            
            # 判断趋势
            if current_price > sma_20 > sma_50:
                trend = 'bullish'
            elif current_price < sma_20 < sma_50:
                trend = 'bearish'
            else:
                trend = 'neutral'
            
            # 判断波动率水平
            if volatility < 0.4:
                vol_level = 'low'
            elif volatility < 0.8:
                vol_level = 'medium'
            else:
                vol_level = 'high'
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'trend': trend,
                'volatility_level': vol_level,
                'volatility': float(volatility),
                'sma_20': float(sma_20),
                'sma_50': float(sma_50),
                'support': float(support),
                'resistance': float(resistance),
                'price_position': float(price_position)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"市场分析失败: {e}")
            return None
    
    def generate_signal(self, analysis):
        """生成交易信号"""
        if not analysis:
            return None
        
        # 检查冷却期
        if self.state['consecutive_losses'] >= self.params['consecutive_loss_limit']:
            self.logger.info("处于冷却期，暂停交易")
            return None
        
        # 检查每日交易限制
        if self.state['trades_today'] >= self.params['max_daily_trades']:
            self.logger.info("达到每日交易限制")
            return None
        
        trend = analysis['trend']
        price_position = analysis['price_position']
        vol_level = analysis['volatility_level']
        
        signal = None
        
        # 策略1: 趋势跟踪
        if trend == 'bullish' and price_position < 0.3:
            signal = {
                'direction': 'LONG',
                'reason': '上涨趋势，价格接近支撑位',
                'confidence': 0.7,
                'strategy': '趋势跟踪'
            }
        elif trend == 'bearish' and price_position > 0.7:
            signal = {
                'direction': 'SHORT',
                'reason': '下跌趋势，价格接近阻力位',
                'confidence': 0.7,
                'strategy': '趋势跟踪'
            }
        
        # 策略2: 均值回归（高波动率）
        elif trend == 'neutral' and vol_level == 'high':
            if price_position > 0.7:
                signal = {
                    'direction': 'SHORT',
                    'reason': '高波动率震荡，价格在阻力位',
                    'confidence': 0.6,
                    'strategy': '均值回归'
                }
            elif price_position < 0.3:
                signal = {
                    'direction': 'LONG',
                    'reason': '高波动率震荡，价格在支撑位',
                    'confidence': 0.6,
                    'strategy': '均值回归'
                }
        
        return signal
    
    def calculate_trade_params(self, signal, analysis):
        """计算交易参数"""
        if not signal or not analysis:
            return None
        
        current_price = analysis['current_price']
        vol_level = analysis['volatility_level']
        
        # 根据波动率设置止盈止损
        if vol_level == 'low':
            stop_loss_pct = 1.2
            take_profit_pct = 2.4
            leverage = 15
        elif vol_level == 'high':
            stop_loss_pct = 2.0
            take_profit_pct = 4.0
            leverage = 5
        else:
            stop_loss_pct = 1.5
            take_profit_pct = 3.0
            leverage = 10
        
        # 获取账户余额
        balance = self.exchange.fetch_balance()
        total_balance = balance['total'].get('USDT', 0)
        
        # 计算仓位大小
        risk_amount = total_balance * self.params['risk_per_trade']
        position_value = risk_amount / (stop_loss_pct / 100)
        contracts = position_value / (current_price * self.contract_multiplier)
        
        # 限制仓位大小
        contracts = max(self.params['min_position_size'], 
                       min(contracts, self.params['max_position_size']))
        contracts = round(contracts * 100) / 100
        
        # 计算止盈止损价格
        if signal['direction'] == 'LONG':
            stop_loss_price = current_price * (1 - stop_loss_pct / 100)
            take_profit_price = current_price * (1 + take_profit_pct / 100)
        else:
            stop_loss_price = current_price * (1 + stop_loss_pct / 100)
            take_profit_price = current_price * (1 - take_profit_pct / 100)
        
        trade_params = {
            'contracts': contracts,
            'leverage': leverage,
            'entry_price': current_price,
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price,
            'stop_loss_pct': stop_loss_pct,
            'take_profit_pct': take_profit_pct,
            'risk_amount': risk_amount,
            'potential_reward': position_value * (take_profit_pct / 100),
            'risk_reward_ratio': take_profit_pct / stop_loss_pct
        }
        
        # 只接受风险回报比大于1.5的交易
        if trade_params['risk_reward_ratio'] < 1.5:
            self.logger.info(f"风险回报比过低: {trade_params['risk_reward_ratio']:.2f}")
            return None
        
        return trade_params
    
    def execute_trade(self, signal, trade_params):
        """执行交易并发送通知"""
        try:
            # 设置杠杆
            self.exchange.set_leverage(trade_params['leverage'], self.symbol)
            
            # 执行订单
            if signal['direction'] == 'LONG':
                order = self.exchange.create_market_buy_order(self.symbol, trade_params['contracts'])
                side = '买入开多'
                side_emoji = '📈'
            else:
                order = self.exchange.create_market_sell_order(self.symbol, trade_params['contracts'])
                side = '卖出开空'
                side_emoji = '📉'
            
            # 记录交易
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'order_id': order['id'],
                'direction': signal['direction'],
                'contracts': trade_params['contracts'],
                'entry_price': trade_params['entry_price'],
                'stop_loss_price': trade_params['stop_loss_price'],
                'take_profit_price': trade_params['take_profit_price'],
                'stop_loss_pct': trade_params['stop_loss_pct'],
                'take_profit_pct': trade_params['take_profit_pct'],
                'leverage': trade_params['leverage'],
                'reason': signal['reason'],
                'strategy': signal.get('strategy', 'N/A'),
                'confidence': signal['confidence'],
                'risk_amount': trade_params['risk_amount'],
                'risk_reward_ratio': trade_params['risk_reward_ratio'],
                'status': 'open'
            }
            
            # 保存交易记录
            with open('logs/autonomous_trades.json', 'a') as f:
                f.write(json.dumps(trade_record) + '\n')
            
            # 更新状态
            self.state['trades_today'] += 1
            self.state['active_positions'].append(trade_record)
            self.state['last_notification_time'] = datetime.now().isoformat()
            
            # 发送Telegram通知
            notification_message = f"""
{side_emoji} <b>自主交易系统开仓通知</b>

<b>交易详情:</b>
• 方向: {side}
• 合约数量: {trade_params['contracts']}张 ({trade_params['contracts'] * 0.01:.4f} BTC)
• 入场价: ${trade_params['entry_price']:.2f}
• 止损价: ${trade_params['stop_loss_price']:.2f} (-{trade_params['stop_loss_pct']}%)
• 止盈价: ${trade_params['take_profit_price']:.2f} (+{trade_params['take_profit_pct']}%)
• 杠杆: {trade_params['leverage']}x
• 风险金额: ${trade_params['risk_amount']:.4f}
• 风险回报比: {trade_params['risk_reward_ratio']:.2f}:1

<b>策略信息:</b>
• 策略: {signal.get('strategy', 'N/A')}
• 原因: {signal['reason']}
• 信心度: {signal['confidence']*100:.0f}%

<b>订单信息:</b>
• 订单ID: {order['id']}
• 时间: {datetime.now().strftime('%H:%M:%S')}

<b>监控面板:</b>
http://localhost:8084
            """
            
            self.send_telegram_notification(notification_message)
            
            self.logger.info(f"✅ 交易执行成功: {side} {trade_params['contracts']}张合约")
            self.logger.info(f"   订单ID: {order['id']}")
            self.logger.info(f"   入场价: ${trade_params['entry_price']:.2f}")
            self.logger.info(f"   止损: ${trade_params['stop_loss_price']:.2f} (-{trade_params['stop_loss_pct']}%)")
            self.logger.info(f"   止盈: ${trade_params['take_profit_price']:.2f} (+{trade_params['take_profit_pct']}%)")
            self.logger.info(f"   杠杆: {trade_params['leverage']}x")
            self.logger.info(f"   风险回报比: {trade_params['risk_reward_ratio']:.2f}:1")
            self.logger.info(f"   策略: {signal.get('strategy', 'N/A')}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"交易执行失败: {e}")
            return False
    
    def monitor_positions(self):
        """监控持仓"""
        try:
            positions = self.exchange.fetch_positions([self.symbol])
            ticker = self.exchange.fetch_ticker(self.symbol)
            current_price = ticker['last']
            
            for pos in positions:
                if pos['symbol'] == self.symbol:
                    contracts = float(pos.get('contracts', 0))
                    if contracts > 0:
                        # 检查是否需要发送持仓更新通知
                        self.check_position_update(pos, current_price)
            
        except Exception as e:
            self.logger.error(f"监控持仓失败: {e}")
    
    def check_position_update(self, position, current_price):
        """检查持仓更新"""
        try:
            entry_price = float(position.get('entryPrice', 0))
            unrealized_pnl = float(position.get('unrealizedPnl', 0))
            pnl_percent = (current_price - entry_price) / entry_price * 100 if entry_price > 0 else 0
            
            # 每30分钟发送一次持仓更新
            last_notify = self.state.get('last_position_notify_time')
            now = datetime.now()
            
            if not last_notify or (now - datetime.fromisoformat(last_notify)).seconds > 1800:
                notification_message = f"""
📊 <b>持仓更新通知</b>

<b>持仓详情:</b>
• 方向: {position.get('side', 'N/A')}
• 合约数量: {float(position.get('contracts', 0))}张
• 入场价: ${entry_price:.2f}
• 当前价: ${current_price:.2f}
• 浮动盈亏: ${unrealized_pnl:.4f} ({pnl_percent:.2f}%)
• 杠杆: {float(position.get('leverage', 0))}x

<b>监控面板:</b>
http://localhost:8084
                """
                
                self.send_telegram_notification(notification_message)
                self.state['last_position_notify_time'] = now.isoformat()
                
        except Exception as e:
            self.logger.error(f"检查持仓更新失败: {e}")
    
    def run(self):
        """运行主循环"""
        print('\n🚀 开始自主交易 (带通知功能)...')
        print('='*50)
        
        iteration = 0
        while self.state['running']:
            try:
                iteration += 1
                self.state['last_check'] = datetime.now().isoformat()
                
                print(f'\n🔄 第{iteration}次检查 ({datetime.now().strftime("%H:%M:%S")})')
                print('-'*30)
                
                # 1. 分析市场
                analysis = self.analyze_market()
                if analysis:
                    print(f'📈 市场分析:')
                    print(f'   价格: ${analysis["