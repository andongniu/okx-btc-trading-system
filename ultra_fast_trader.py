#!/usr/bin/env python3
"""
超快交易系统 - 10秒频率，实时响应
"""

import ccxt
import json
import time
import numpy as np
from datetime import datetime
import logging
import os

class UltraFastTrader:
    def __init__(self):
        """初始化超快交易系统"""
        print('🚀 初始化超快交易系统...')
        print('⚡ 10秒检查频率，实时响应市场变化')
        
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
        
        # ⚡ 超快参数
        self.params = {
            'check_interval': 10,  # 10秒检查一次！
            'min_position_size': 0.01,
            'max_position_size': 0.15,
            'risk_per_trade': 0.015,
            'max_daily_trades': 15,  # 提高交易次数
            'consecutive_loss_limit': 5,
            
            # 超快信号条件
            'trend_following': {
                'long_support_threshold': 0.5,
                'short_resistance_threshold': 0.5,
                'confidence': 0.6
            },
            
            'mean_reversion': {
                'enabled': True,
                'volatility_threshold': 0.2,  # 更低阈值
                'long_support_threshold': 0.4,
                'short_resistance_threshold': 0.6,
                'confidence': 0.55
            },
            
            'quick_breakout': {
                'enabled': True,
                'breakout_period': 10,  # 更短周期
                'breakout_multiplier': 1.005,  # 0.5%突破
                'confidence': 0.6
            },
            
            # 超快风险参数
            'risk_reward_ratio_min': 1.2,
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
            'active_positions': [],
            'last_prices': [],
            'price_change_rates': []
        }
        
        # 初始化日志
        self.setup_logging()
        
        print('✅ 超快交易系统初始化完成')
        print(f'⚡ 检查频率: {self.params["check_interval"]}秒 (原30秒)')
        print(f'📊 响应速度: 提高300%')
        print(f'🎯 每日交易: {self.params["max_daily_trades"]}次')
        print(f'📍 突破阈值: 0.5% (更敏感)')
        print('🌐 监控面板: http://localhost:8084')
        print('📱 Telegram通知: @anth6iu_noticer_bot')
    
    def setup_logging(self):
        """设置日志"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/ultra_fast_trader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze_market(self):
        """超快市场分析"""
        try:
            # 获取多种时间框架数据
            ohlcv_15m = self.exchange.fetch_ohlcv(self.symbol, '15m', limit=50)
            ohlcv_5m = self.exchange.fetch_ohlcv(self.symbol, '5m', limit=30)
            ohlcv_1m = self.exchange.fetch_ohlcv(self.symbol, '1m', limit=20)
            
            closes_15m = np.array([c[4] for c in ohlcv_15m])
            closes_5m = np.array([c[4] for c in ohlcv_5m])
            closes_1m = np.array([c[4] for c in ohlcv_1m])
            
            current_price = closes_15m[-1]
            
            # 记录价格变化 (用于动态调整)
            if len(self.state['last_prices']) >= 10:
                self.state['last_prices'].pop(0)
            self.state['last_prices'].append(current_price)
            
            # 计算短期变化率
            if len(self.state['last_prices']) >= 2:
                change_rate = (self.state['last_prices'][-1] - self.state['last_prices'][-2]) / self.state['last_prices'][-2]
                if len(self.state['price_change_rates']) >= 5:
                    self.state['price_change_rates'].pop(0)
                self.state['price_change_rates'].append(change_rate)
            
            # 快速计算技术指标
            sma_20 = np.mean(closes_15m[-20:]) if len(closes_15m) >= 20 else closes_15m[-1]
            sma_50 = np.mean(closes_15m[-50:]) if len(closes_15m) >= 50 else closes_15m[-1]
            
            # 快速支撑阻力
            support = np.min(closes_15m[-15:])  # 缩短周期
            resistance = np.max(closes_15m[-15:])
            price_position = (current_price - support) / (resistance - support) if resistance != support else 0.5
            
            # 快速波动率计算
            returns_15m = np.diff(closes_15m[-20:]) / closes_15m[-20:-1] if len(closes_15m) >= 20 else np.array([0])
            volatility = np.std(returns_15m) * np.sqrt(365 * 24 * 4) if len(returns_15m) > 1 else 0
            
            # 快速趋势判断
            if current_price > sma_20 > sma_50:
                trend = 'bullish'
            elif current_price < sma_20 < sma_50:
                trend = 'bearish'
            else:
                trend = 'neutral'
            
            # 检查突破
            breakout_signal = self.check_quick_breakout(closes_5m, current_price)
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'trend': trend,
                'volatility': float(volatility),
                'sma_20': float(sma_20),
                'sma_50': float(sma_50),
                'support': float(support),
                'resistance': float(resistance),
                'price_position': float(price_position),
                'price_change_1m': self.state['price_change_rates'][-1] if self.state['price_change_rates'] else 0,
                'breakout_signal': breakout_signal
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"市场分析失败: {e}")
            return None
    
    def check_quick_breakout(self, closes, current_price):
        """检查快速突破"""
        if not self.params['quick_breakout']['enabled']:
            return None
        
        period = self.params['quick_breakout']['breakout_period']
        multiplier = self.params['quick_breakout']['breakout_multiplier']
        
        if len(closes) < period:
            return None
        
        recent_high = np.max(closes[-period:])
        recent_low = np.min(closes[-period:])
        
        # 向上突破
        if current_price > recent_high * multiplier:
            return {
                'direction': 'LONG',
                'type': 'quick_breakout_up',
                'breakout_level': recent_high,
                'breakout_percent': (current_price / recent_high - 1) * 100
            }
        
        # 向下突破
        if current_price < recent_low / multiplier:
            return {
                'direction': 'SHORT',
                'type': 'quick_breakout_down',
                'breakout_level': recent_low,
                'breakout_percent': (1 - current_price / recent_low) * 100
            }
        
        return None
    
    def generate_signal(self, analysis):
        """生成超快交易信号"""
        if not analysis:
            return None
        
        # 快速检查限制
        if self.state['consecutive_losses'] >= self.params['consecutive_loss_limit']:
            return None
        
        if self.state['trades_today'] >= self.params['max_daily_trades']:
            return None
        
        trend = analysis['trend']
        price_position = analysis['price_position']
        volatility = analysis['volatility']
        breakout_signal = analysis.get('breakout_signal')
        
        signal = None
        
        # 1. 快速突破策略 (优先级最高)
        if breakout_signal:
            signal = {
                'direction': breakout_signal['direction'],
                'reason': f'快速突破: {breakout_signal["type"]} {breakout_signal["breakout_percent"]:.2f}%',
                'confidence': self.params['quick_breakout']['confidence'],
                'strategy': '快速突破'
            }
        
        # 2. 趋势跟踪
        elif not signal:
            if trend == 'bullish' and price_position < self.params['trend_following']['long_support_threshold']:
                signal = {
                    'direction': 'LONG',
                    'reason': f'上涨趋势，价格位置{price_position:.1%}',
                    'confidence': self.params['trend_following']['confidence'],
                    'strategy': '趋势跟踪'
                }
            elif trend == 'bearish' and price_position > self.params['trend_following']['short_resistance_threshold']:
                signal = {
                    'direction': 'SHORT',
                    'reason': f'下跌趋势，价格位置{price_position:.1%}',
                    'confidence': self.params['trend_following']['confidence'],
                    'strategy': '趋势跟踪'
                }
        
        # 3. 均值回归
        if not signal and self.params['mean_reversion']['enabled']:
            if trend == 'neutral' and volatility > self.params['mean_reversion']['volatility_threshold']:
                if price_position < self.params['mean_reversion']['long_support_threshold']:
                    signal = {
                        'direction': 'LONG',
                        'reason': f'震荡行情，价格在支撑区',
                        'confidence': self.params['mean_reversion']['confidence'],
                        'strategy': '均值回归'
                    }
                elif price_position > self.params['mean_reversion']['short_resistance_threshold']:
                    signal = {
                        'direction': 'SHORT',
                        'reason': f'震荡行情，价格在阻力区',
                        'confidence': self.params['mean_reversion']['confidence'],
                        'strategy': '均值回归'
                    }
        
        return signal
    
    def run(self):
        """运行超快主循环"""
        print('\n🚀 启动超快交易系统...')
        print('='*50)
        print('⚡ 10秒频率，实时响应市场变化')
        print('🎯 抓住每一个快速波动机会')
        print('='*50)
        
        iteration = 0
        while self.state['running']:
            try:
                iteration += 1
                start_time = time.time()
                
                print(f'\n⚡ 第{iteration}次检查 ({datetime.now().strftime("%H:%M:%S.%f")[:-3]})')
                print('-'*30)
                
                # 超快市场分析
                analysis = self.analyze_market()
                
                if analysis:
                    print(f'📈 实时市场:')
                    print(f'   价格: ${analysis["current_price"]:.2f}')
                    print(f'   趋势: {analysis["trend"]}')
                    print(f'   位置: {analysis["price_position"]:.1%}')
                    print(f'   波动率: {analysis["volatility"]:.2%}')
                    
                    if analysis.get('breakout_signal'):
                        print(f'   🚀 突破信号: {analysis["breakout_signal"]["type"]}')
                    
                    # 检查持仓
                    positions = self.exchange.fetch_positions([self.symbol])
                    has_position = False
                    for pos in positions:
                        if pos['symbol'] == self.symbol:
                            contracts = float(pos.get('contracts', 0))
                            if contracts > 0:
                                has_position = True
                                entry_price = float(pos.get('entryPrice', 0))
                                mark_price = float(pos.get('markPrice', 0))
                                unrealized_pnl = float(pos.get('unrealizedPnl', 0))
                                pnl_percent = (unrealized_pnl / (contracts * 0.01 * entry_price) * 100) if contracts > 0 and entry_price > 0 else 0
                                
                                print(f'📊 当前持仓:')
                                print(f'   方向: {pos.get("side", "N/A")}')
                                print(f'   数量: {contracts}张')
                                print(f'   盈亏: ${unrealized_pnl:.4f} ({pnl_percent:.2f}%)')
                                print(f'   入场: ${entry_price:.2f}')
                                print(f'   当前: ${mark_price:.2f}')
                                break
                    
                    if not has_position:
                        print('📊 当前持仓: 无')
                        
                        # 生成交易信号
                        signal = self.generate_signal(analysis)
                        if signal:
                            print(f'🎯 交易信号: {signal["direction"]}')
                            print(f'   策略: {signal.get("strategy", "N/A")}')
                            print(f'   原因: {signal["reason"]}')
                            print(f'   信心度: {signal["confidence"]*100:.0f}%')
                            
                            # 这里可以添加快速交易执行逻辑
                            # 暂时只显示信号
                        else:
                            print('🔄 等待合适机会...')
                
                # 计算执行时间
                execution_time = time.time() - start_time
                sleep_time = max(0.1, self.params['check_interval'] - execution_time)
                
                print(f'⏱️  执行时间: {execution_time:.2f}秒')
                print(f'💤 下次检查: {sleep_time:.1f}秒后')
                
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                print('\n🛑 用户中断，停止系统')
                self.state['running'] = False
                break
            except Exception as e:
                self.logger.error(f"主循环错误: {e}")
                time.sleep(self.params['check_interval'])
        
        print('\n✅ 超快交易系统已停止')

if __name__ == '__main__':
    trader = UltraFastTrader()
    trader.run()