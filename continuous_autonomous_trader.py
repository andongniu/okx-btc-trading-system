#!/usr/bin/env python3
"""
持续运行的自主交易系统 - 自动监控市场并执行交易
"""

import ccxt
import json
import time
import numpy as np
from datetime import datetime
import logging
import os

class ContinuousAutonomousTrader:
    def __init__(self):
        """初始化持续交易系统"""
        print('🚀 初始化持续自主交易系统...')
        
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
        
        # 🚀 激进策略参数
        self.params = {
            'check_interval': 30,  # 30秒检查一次
            'min_position_size': 0.01,
            'max_position_size': 0.15,  # 提高最大仓位
            'risk_per_trade': 0.015,  # 1.5%风险 (提高50%)
            'max_daily_trades': 12,   # 大幅提高交易次数
            'consecutive_loss_limit': 5,  # 放宽连续亏损限制
            
            # 🎯 激进信号条件
            'trend_following': {
                'long_support_threshold': 0.5,   # 支撑区<50% (原<30%)
                'short_resistance_threshold': 0.5,  # 阻力区>50% (原>70%)
                'confidence': 0.6
            },
            
            'mean_reversion': {
                'enabled': True,
                'volatility_threshold': 0.25,  # 更低阈值
                'long_support_threshold': 0.4,
                'short_resistance_threshold': 0.6,
                'confidence': 0.55
            },
            
            # 🎯 激进风险参数
            'risk_reward_ratio_min': 1.2,  # 更低要求 (原1.5)
            'volatility_adjustment': {
                'low': {'threshold': 0.4, 'stop_loss': 0.8, 'take_profit': 1.6, 'leverage': 25},
                'medium': {'threshold': 0.8, 'stop_loss': 1.2, 'take_profit': 2.4, 'leverage': 18},
                'high': {'threshold': 1.2, 'stop_loss': 1.6, 'take_profit': 3.2, 'leverage': 10}
            }
        }
        
        # 状态跟踪
        self.state = {
            'running': True,
            'last_check': None,
            'trades_today': 0,
            'consecutive_losses': 0,
            'consecutive_wins': 0,
            'daily_pnl': 0.0,
            'active_positions': []
        }
        
        # 初始化日志
        self.setup_logging()
        
        print('✅ 🚀 激进版自主交易系统初始化完成')
        print(f'📊 检查间隔: {self.params["check_interval"]}秒 (原60秒)')
        print(f'💰 风险控制: {self.params["risk_per_trade"]*100}%每笔交易 (提高50%)')
        print(f'📈 最大仓位: {self.params["max_position_size"]}张合约 (提高50%)')
        print(f'🎯 每日交易: {self.params["max_daily_trades"]}次 (大幅提高)')
        print(f'📍 支撑/阻力: 50%线 (原30%/70%)')
        print(f'⚖️  风险回报比: {self.params["risk_reward_ratio_min"]}:1 (降低要求)')
        print('🌐 监控面板: http://localhost:8084')
    
    def setup_logging(self):
        """设置日志"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/continuous_trader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
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
        
        # 🚀 策略1: 激进趋势跟踪
        if trend == 'bullish' and price_position < self.params['trend_following']['long_support_threshold']:
            signal = {
                'direction': 'LONG',
                'reason': f'上涨趋势，价格在支撑区({price_position:.1%}<{self.params["trend_following"]["long_support_threshold"]*100}%)',
                'confidence': self.params['trend_following']['confidence'],
                'strategy': '趋势跟踪'
            }
        elif trend == 'bearish' and price_position > self.params['trend_following']['short_resistance_threshold']:
            signal = {
                'direction': 'SHORT',
                'reason': f'下跌趋势，价格在阻力区({price_position:.1%}>{self.params["trend_following"]["short_resistance_threshold"]*100}%)',
                'confidence': self.params['trend_following']['confidence'],
                'strategy': '趋势跟踪'
            }
        
        # 🚀 策略2: 激进均值回归
        elif self.params['mean_reversion']['enabled'] and trend == 'neutral':
            if analysis['volatility'] > self.params['mean_reversion']['volatility_threshold']:
                if price_position < self.params['mean_reversion']['long_support_threshold']:
                    signal = {
                        'direction': 'LONG',
                        'reason': f'震荡行情，价格在支撑区({price_position:.1%}<{self.params["mean_reversion"]["long_support_threshold"]*100}%)',
                        'confidence': self.params['mean_reversion']['confidence'],
                        'strategy': '均值回归'
                    }
                elif price_position > self.params['mean_reversion']['short_resistance_threshold']:
                    signal = {
                        'direction': 'SHORT',
                        'reason': f'震荡行情，价格在阻力区({price_position:.1%}>{self.params["mean_reversion"]["short_resistance_threshold"]*100}%)',
                        'confidence': self.params['mean_reversion']['confidence'],
                        'strategy': '均值回归'
                    }
        
        return signal
    
    def calculate_trade_params(self, signal, analysis):
        """计算交易参数"""
        if not signal or not analysis:
            return None
        
        current_price = analysis['current_price']
        vol_level = analysis['volatility_level']
        
        # 🚀 根据波动率设置激进止盈止损
        if vol_level == 'low':
            stop_loss_pct = self.params['volatility_adjustment']['low']['stop_loss']
            take_profit_pct = self.params['volatility_adjustment']['low']['take_profit']
            leverage = self.params['volatility_adjustment']['low']['leverage']
        elif vol_level == 'high':
            stop_loss_pct = self.params['volatility_adjustment']['high']['stop_loss']
            take_profit_pct = self.params['volatility_adjustment']['high']['take_profit']
            leverage = self.params['volatility_adjustment']['high']['leverage']
        else:
            stop_loss_pct = self.params['volatility_adjustment']['medium']['stop_loss']
            take_profit_pct = self.params['volatility_adjustment']['medium']['take_profit']
            leverage = self.params['volatility_adjustment']['medium']['leverage']
        
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
        
        # 🚀 激进风险回报比要求
        if trade_params['risk_reward_ratio'] < self.params['risk_reward_ratio_min']:
            self.logger.info(f"风险回报比过低: {trade_params['risk_reward_ratio']:.2f} < {self.params['risk_reward_ratio_min']}")
            return None
        
        return trade_params
    
    def execute_trade(self, signal, trade_params):
        """执行交易"""
        try:
            # 设置杠杆
            self.exchange.set_leverage(trade_params['leverage'], self.symbol)
            
            # 执行订单
            if signal['direction'] == 'LONG':
                order = self.exchange.create_market_buy_order(self.symbol, trade_params['contracts'])
                side = '买入开多'
            else:
                order = self.exchange.create_market_sell_order(self.symbol, trade_params['contracts'])
                side = '卖出开空'
            
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
                        # 这里可以添加平仓逻辑
                        # 目前只记录状态
                        pass
            
        except Exception as e:
            self.logger.error(f"监控持仓失败: {e}")
    
    def run(self):
        """运行主循环"""
        print('\n🚀 开始持续自主交易...')
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
                    print(f'   价格: ${analysis["current_price"]:.2f}')
                    print(f'   趋势: {analysis["trend"]}')
                    print(f'   位置: {analysis["price_position"]:.2%}')
                    print(f'   波动率: {analysis["volatility_level"]}')
                
                # 2. 检查是否有持仓
                positions = self.exchange.fetch_positions([self.symbol])
                has_position = False
                for pos in positions:
                    if pos['symbol'] == self.symbol:
                        contracts = float(pos.get('contracts', 0))
                        if contracts > 0:
                            has_position = True
                            print(f'📊 当前持仓: {contracts}张合约')
                            break
                
                if not has_position:
                    print('📊 当前持仓: 无')
                    
                    # 3. 生成交易信号
                    signal = self.generate_signal(analysis)
                    if signal:
                        print(f'🎯 生成信号: {signal["direction"]}')
                        print(f'   原因: {signal["reason"]}')
                        print(f'   策略: {signal.get("strategy", "N/A")}')
                        
                        # 4. 计算交易参数
                        trade_params = self.calculate_trade_params(signal, analysis)
                        if trade_params:
                            print(f'📊 交易参数:')
                            print(f'   合约: {trade_params["contracts"]}张')
                            print(f'   杠杆: {trade_params["leverage"]}x')
                            print(f'   止损: {trade_params["stop_loss_pct"]}%')
                            print(f'   止盈: {trade_params["take_profit_pct"]}%')
                            print(f'   风险回报比: {trade_params["risk_reward_ratio"]:.2f}:1')
                            
                            # 5. 执行交易
                            self.execute_trade(signal, trade_params)
                        else:
                            print('⚠️  交易参数计算失败')
                    else:
                        print('🔄 等待交易信号...')
                else:
                    print('📊 已有持仓，等待平仓机会...')
                
                # 6. 监控持仓
                self.monitor_positions()
                
                print(f'\n⏳ 下次检查: {self.params["check_interval"]}秒后')
                print('🌐 监控面板: http://localhost:8083')
                
                # 等待下一次检查
                time.sleep(self.params['check_interval'])
                
            except KeyboardInterrupt:
                print('\n🛑 用户中断，停止交易系统')
                self.state['running'] = False
                break
            except Exception as e:
                self.logger.error(f"主循环错误: {e}")
                time.sleep(self.params['check_interval'])
        
        print('\n✅ 交易系统已停止')
        print('📊 最终状态:')
        print(f'   今日交易: {self.state["trades_today"]}次')
        print(f'   连续亏损: {self.state["consecutive_losses"]}次')
        print(f'   连续盈利: {self.state["consecutive_wins"]}次')
        print(f'   今日盈亏: ${self.state["daily_pnl"]:.4f}')

if __name__ == '__main__':
    trader = ContinuousAutonomousTrader()
    trader.run()