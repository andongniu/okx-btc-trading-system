#!/usr/bin/env python3
"""
激进版交易系统 - 抓住更多市场机会
"""

import ccxt
import json
import time
import numpy as np
from datetime import datetime
import logging
import os

class AggressiveTrader:
    def __init__(self):
        """初始化激进版交易系统"""
        print('🚀 初始化激进版自主交易系统...')
        print('📈 采用激进优化方案 (大幅提高交易机会)')
        
        # 加载配置
        with open('config/final_config.json', 'r') as f:
            self.config = json.load(f)
        
        # 初始化交易所
        self.exchange = ccxt.okx({
            'apiKey': config['exchange']['api_key'],
            'secret': config['exchange']['secret'],
            'password': config['exchange']['passphrase'],
            'enableRateLimit': True,
            'proxies': config['exchange']['proxies'],
            'options': {'defaultType': 'swap'}
        })
        
        self.symbol = 'BTC/USDT:USDT'
        self.contract_multiplier = 0.01
        
        # 🎯 激进参数配置
        self.params = {
            'check_interval': 30,  # 30秒检查一次
            'min_position_size': 0.01,
            'max_position_size': 0.15,  # 提高最大仓位
            'risk_per_trade': 0.015,  # 1.5%风险 (原1%)
            'max_daily_trades': 12,   # 大幅提高
            'consecutive_loss_limit': 5,
            
            # 🎯 激进信号条件
            'trend_following': {
                'long_support_threshold': 0.5,   # 支撑区<50%
                'short_resistance_threshold': 0.5,  # 阻力区>50%
                'confidence': 0.6
            },
            
            'mean_reversion': {
                'enabled': True,
                'volatility_threshold': 0.25,  # 更低阈值
                'long_support_threshold': 0.4,
                'short_resistance_threshold': 0.6,
                'confidence': 0.55
            },
            
            'breakout_strategy': {
                'enabled': True,
                'breakout_period': 15,
                'breakout_multiplier': 1.01,  # 1%突破就开单
                'confidence': 0.6
            },
            
            'momentum_strategy': {
                'enabled': True,  # 新增动量策略
                'momentum_period': 10,
                'momentum_threshold': 0.005,  # 0.5%动量
                'confidence': 0.55
            },
            
            # 🎯 激进风险参数
            'risk_reward_ratio_min': 1.2,  # 更低要求
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
            'strategy_stats': {
                'trend_following': 0,
                'mean_reversion': 0,
                'breakout': 0,
                'momentum': 0,
                'rejected': 0
            }
        }
        
        # 初始化日志
        self.setup_logging()
        
        print('✅ 激进版交易系统初始化完成')
        print('='*50)
        print('📊 核心优化:')
        print(f'   • 检查间隔: {self.params["check_interval"]}秒 (大幅缩短)')
        print(f'   • 单笔风险: {self.params["risk_per_trade"]*100}% (提高50%)')
        print(f'   • 每日交易: {self.params["max_daily_trades"]}次 (大幅提高)')
        print(f'   • 支撑/阻力: 50%线 (原30%/70%)')
        print(f'   • 风险回报比: {self.params["risk_reward_ratio_min"]}:1 (降低要求)')
        print(f'   • 新增策略: 突破 + 动量')
        print('='*50)
        print(f'🌐 监控面板: http://localhost:8084')
        print(f'📱 Telegram通知: @anth6iu_noticer_bot')
    
    def setup_logging(self):
        """设置日志"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/aggressive_trader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze_market(self):
        """分析市场"""
        try:
            # 获取多种时间框架数据
            ohlcv_15m = self.exchange.fetch_ohlcv(self.symbol, '15m', limit=100)
            ohlcv_5m = self.exchange.fetch_ohlcv(self.symbol, '5m', limit=100)
            
            closes_15m = np.array([c[4] for c in ohlcv_15m])
            closes_5m = np.array([c[4] for c in ohlcv_5m])
            
            current_price = closes_15m[-1]
            
            # 计算技术指标
            sma_20_15m = np.mean(closes_15m[-20:])
            sma_50_15m = np.mean(closes_15m[-50:])
            sma_10_5m = np.mean(closes_5m[-10:])
            
            # 支撑阻力
            support_15m = np.min(closes_15m[-20:])
            resistance_15m = np.max(closes_15m[-20:])
            price_position = (current_price - support_15m) / (resistance_15m - support_15m) if resistance_15m != support_15m else 0.5
            
            # 波动率
            returns_15m = np.diff(closes_15m) / closes_15m[:-1]
            volatility = np.std(returns_15m) * np.sqrt(365 * 24 * 4)
            
            # 趋势判断
            if current_price > sma_20_15m > sma_50_15m:
                trend = 'bullish'
            elif current_price < sma_20_15m < sma_50_15m:
                trend = 'bearish'
            else:
                trend = 'neutral'
            
            # 短期动量
            momentum_5m = (current_price - closes_5m[-10]) / closes_5m[-10]
            
            # 波动率分级
            if volatility < self.params['volatility_adjustment']['low']['threshold']:
                vol_level = 'low'
            elif volatility < self.params['volatility_adjustment']['medium']['threshold']:
                vol_level = 'medium'
            else:
                vol_level = 'high'
            
            # 检查各种信号
            breakout_signal = self.check_breakout(closes_15m, current_price)
            momentum_signal = self.check_momentum(closes_5m, current_price, momentum_5m)
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'trend': trend,
                'volatility_level': vol_level,
                'volatility': float(volatility),
                'sma_20': float(sma_20_15m),
                'sma_50': float(sma_50_15m),
                'sma_10_5m': float(sma_10_5m),
                'support': float(support_15m),
                'resistance': float(resistance_15m),
                'price_position': float(price_position),
                'momentum_5m': float(momentum_5m),
                'breakout_signal': breakout_signal,
                'momentum_signal': momentum_signal
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"市场分析失败: {e}")
            return None
    
    def check_breakout(self, closes, current_price):
        """检查突破信号"""
        if not self.params['breakout_strategy']['enabled']:
            return None
        
        period = self.params['breakout_strategy']['breakout_period']
        multiplier = self.params['breakout_strategy']['breakout_multiplier']
        
        if len(closes) < period:
            return None
        
        recent_high = np.max(closes[-period:])
        recent_low = np.min(closes[-period:])
        
        # 向上突破
        if current_price > recent_high * multiplier:
            return {
                'direction': 'LONG',
                'type': 'breakout_up',
                'breakout_level': recent_high,
                'breakout_percent': (current_price / recent_high - 1) * 100
            }
        
        # 向下突破
        if current_price < recent_low / multiplier:
            return {
                'direction': 'SHORT',
                'type': 'breakout_down',
                'breakout_level': recent_low,
                'breakout_percent': (1 - current_price / recent_low) * 100
            }
        
        return None
    
    def check_momentum(self, closes, current_price, momentum):
        """检查动量信号"""
        if not self.params['momentum_strategy']['enabled']:
            return None
        
        threshold = self.params['momentum_strategy']['momentum_threshold']
        
        if momentum > threshold:
            return {
                'direction': 'LONG',
                'type': 'momentum_up',
                'momentum_percent': momentum * 100
            }
        elif momentum < -threshold:
            return {
                'direction': 'SHORT',
                'type': 'momentum_down',
                'momentum_percent': abs(momentum) * 100
            }
        
        return None
    
    def generate_signal(self, analysis):
        """生成交易信号"""
        if not analysis:
            return None
        
        # 检查限制
        if self.state['consecutive_losses'] >= self.params['consecutive_loss_limit']:
            return None
        
        if self.state['trades_today'] >= self.params['max_daily_trades']:
            return None
        
        trend = analysis['trend']
        price_position = analysis['price_position']
        volatility = analysis['volatility']
        breakout_signal = analysis.get('breakout_signal')
        momentum_signal = analysis.get('momentum_signal')
        
        signal = None
        
        # 1. 突破策略 (优先级最高)
        if breakout_signal:
            signal = {
                'direction': breakout_signal['direction'],
                'reason': f'突破策略: {breakout_signal["type"]} {breakout_signal["breakout_percent"]:.2f}%',
                'confidence': self.params['breakout_strategy']['confidence'],
                'strategy': '突破'
            }
            self.state['strategy_stats']['breakout'] += 1
        
        # 2. 动量策略
        elif momentum_signal and not signal:
            signal = {
                'direction': momentum_signal['direction'],
                'reason': f'动量策略: {momentum_signal["type"]} {momentum_signal["momentum_percent"]:.2f}%',
                'confidence': self.params['momentum_strategy']['confidence'],
                'strategy': '动量'
            }
            self.state['strategy_stats']['momentum'] += 1
        
        # 3. 趋势跟踪
        elif not signal:
            if trend == 'bullish' and price_position < self.params['trend_following']['long_support_threshold']:
                signal = {
                    'direction': 'LONG',
                    'reason': f'趋势跟踪: 上涨趋势，价格位置{price_position:.1%}',
                    'confidence': self.params['trend_following']['confidence'],
                    'strategy': '趋势'
                }
                self.state['strategy_stats']['trend_following'] += 1
            elif trend == 'bearish' and price_position > self.params['trend_following']['short_resistance_threshold']:
                signal = {
                    'direction': 'SHORT',
                    'reason': f'趋势跟踪: 下跌趋势，价格位置{price_position:.1%}',
                    'confidence': self.params['trend_following']['confidence'],
                    'strategy': '趋势'
                }
                self.state['strategy_stats']['trend_following'] += 1
        
        # 4. 均值回归
        if not signal and self.params['mean_reversion']['enabled']:
            if trend == 'neutral' and volatility > self.params['mean_reversion']['volatility_threshold']:
                if price_position < self.params['mean_reversion']['long_support_threshold']:
                    signal = {
                        'direction': 'LONG',
                        'reason': f'均值回归: 震荡行情，价格在支撑区',
                        'confidence': self.params['mean_reversion']['confidence'],
                        'strategy': '均值回归'
                    }
                    self.state['strategy_stats']['mean_reversion'] += 1
                elif price_position > self.params['mean_reversion']['short_resistance_threshold']:
                    signal = {
                        'direction': 'SHORT',
                        'reason': f'均值回归: 震荡行情，价格在阻力区',
                        'confidence': self.params['mean_reversion']['confidence'],
                        'strategy': '均值回归'
                    }
                    self.state['strategy_stats']['mean_reversion'] += 1
        
        return signal
    
    def calculate_trade_params(self, signal, analysis):
        """计算交易参数"""
        if not signal or not analysis:
            return None
        
        current_price = analysis['current_price']
        vol_level = analysis['volatility_level']
        
        # 获取风险参数
        vol_params = self.params['volatility_adjustment'][vol_level]
        stop_loss_pct = vol_params['stop_loss']
        take_profit_pct = vol_params['take_profit']
        leverage = vol_params['leverage']
        
        # 获取账户余额
        balance = self.exchange.fetch_balance()
        total_balance = balance['total'].get('USDT', 0)
        
        # 计算仓位
        risk_amount = total_balance * self.params['risk_per_trade']
        position_value = risk_amount / (stop_loss_pct / 100)
        contracts = position_value / (current_price * self.contract_multiplier)
        
        # 限制仓位
        contracts = max(self.params['min_position_size'], 
                       min(contracts, self.params['max_position_size']))
        contracts = round(contracts * 100) / 100
        
        # 计算止盈止损
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
            'risk_reward_ratio': take_profit_pct / stop_loss_pct
        }
        
        # 检查风险回报比
        if trade_params['risk_reward_ratio'] < self.params['risk_reward_ratio_min']:
            self.state['strategy_stats']['rejected'] += 1
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
                'stop_loss_price': trade_loss_price,
                'take_profit_price': trade_params['take_profit_price'],
                'stop_loss_pct': trade_params['stop_loss_pct'],
                'take_profit_pct': trade_params['take_profit_pct'],
                'leverage': trade_params['leverage'],
                'reason': signal['reason'],
                'strategy': signal.get('strategy