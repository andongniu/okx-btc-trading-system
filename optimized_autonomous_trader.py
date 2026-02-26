#!/usr/bin/env python3
"""
优化版自主交易系统 - 更激进的策略参数
"""

import ccxt
import json
import time
import numpy as np
from datetime import datetime
import logging
import os

class OptimizedAutonomousTrader:
    def __init__(self):
        """初始化优化版交易系统"""
        print('🚀 初始化优化版自主交易系统...')
        print('📈 采用温和优化方案 (提高机会，保持风控)')
        
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
        
        # 🎯 优化后的策略参数
        self.params = {
            'check_interval': 45,  # 缩短检查间隔到45秒
            'min_position_size': 0.01,
            'max_position_size': 0.1,
            'risk_per_trade': 0.01,  # 保持1%风险
            'max_daily_trades': 8,   # 提高每日交易限制
            'consecutive_loss_limit': 4,  # 放宽连续亏损限制
            
            # 🎯 优化后的信号条件
            'trend_following': {
                'long_support_threshold': 0.4,   # 原0.3 → 0.4
                'short_resistance_threshold': 0.6,  # 原0.7 → 0.6
                'confidence': 0.65  # 原0.7 → 0.65
            },
            
            'mean_reversion': {
                'enabled': True,
                'volatility_threshold': 0.3,  # 原0.4 → 0.3
                'long_support_threshold': 0.35,  # 原0.3 → 0.35
                'short_resistance_threshold': 0.65,  # 原0.7 → 0.65
                'confidence': 0.55  # 原0.6 → 0.55
            },
            
            'breakout_strategy': {
                'enabled': True,  # 新增突破策略
                'breakout_period': 20,
                'breakout_multiplier': 1.02,  # 突破2%开单
                'confidence': 0.6
            },
            
            # 🎯 优化后的风险参数
            'risk_reward_ratio_min': 1.3,  # 原1.5 → 1.3
            'volatility_adjustment': {
                'low': {'threshold': 0.3, 'stop_loss': 1.0, 'take_profit': 2.0, 'leverage': 20},
                'medium': {'threshold': 0.7, 'stop_loss': 1.3, 'take_profit': 2.6, 'leverage': 15},
                'high': {'threshold': 1.0, 'stop_loss': 1.8, 'take_profit': 3.6, 'leverage': 8}
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
                'trend_following_signals': 0,
                'mean_reversion_signals': 0,
                'breakout_signals': 0,
                'rejected_signals': 0
            }
        }
        
        # 初始化日志
        self.setup_logging()
        
        print('✅ 优化版自主交易系统初始化完成')
        print(f'📊 检查间隔: {self.params["check_interval"]}秒 (原60秒)')
        print(f'💰 风险控制: {self.params["risk_per_trade"]*100}%每笔交易')
        print(f'📈 每日交易限制: {self.params["max_daily_trades"]}次 (原5次)')
        print(f'🎯 支撑区阈值: <{self.params["trend_following"]["long_support_threshold"]*100}% (原<30%)')
        print(f'🎯 阻力区阈值: >{self.params["trend_following"]["short_resistance_threshold"]*100}% (原>70%)')
        print(f'📊 最小风险回报比: {self.params["risk_reward_ratio_min"]}:1 (原1.5:1)')
        print(f'🌐 监控面板: http://localhost:8084')
        print(f'📱 Telegram通知: @anth6iu_noticer_bot')
    
    def setup_logging(self):
        """设置日志"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/optimized_trader.log'),
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
            if volatility < self.params['volatility_adjustment']['low']['threshold']:
                vol_level = 'low'
            elif volatility < self.params['volatility_adjustment']['medium']['threshold']:
                vol_level = 'medium'
            else:
                vol_level = 'high'
            
            # 检查突破
            breakout_signal = self.check_breakout(closes, current_price)
            
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
                'price_position': float(price_position),
                'breakout_signal': breakout_signal
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
        
        # 检查向上突破
        recent_high = np.max(closes[-period:])
        if current_price > recent_high * multiplier:
            return {
                'direction': 'LONG',
                'type': 'breakout_up',
                'breakout_level': recent_high,
                'breakout_percent': (current_price / recent_high - 1) * 100
            }
        
        # 检查向下突破
        recent_low = np.min(closes[-period:])
        if current_price < recent_low / multiplier:
            return {
                'direction': 'SHORT',
                'type': 'breakout_down',
                'breakout_level': recent_low,
                'breakout_percent': (1 - current_price / recent_low) * 100
            }
        
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
        volatility = analysis['volatility']
        breakout_signal = analysis.get('breakout_signal')
        
        signal = None
        
        # 🎯 策略1: 突破策略 (新增)
        if breakout_signal and self.params['breakout_strategy']['enabled']:
            signal = {
                'direction': breakout_signal['direction'],
                'reason': f'价格突破{breakout_signal["type"]}，突破幅度{breakout_signal["breakout_percent"]:.2f}%',
                'confidence': self.params['breakout_strategy']['confidence'],
                'strategy': '突破策略'
            }
            self.state['strategy_stats']['breakout_signals'] += 1
        
        # 🎯 策略2: 趋势跟踪 (优化参数)
        elif trend == 'bullish' and price_position < self.params['trend_following']['long_support_threshold']:
            signal = {
                'direction': 'LONG',
                'reason': f'上涨趋势，价格在支撑区({price_position:.1%}<{self.params["trend_following"]["long_support_threshold"]*100}%)',
                'confidence': self.params['trend_following']['confidence'],
                'strategy': '趋势跟踪'
            }
            self.state['strategy_stats']['trend_following_signals'] += 1
        
        elif trend == 'bearish' and price_position > self.params['trend_following']['short_resistance_threshold']:
            signal = {
                'direction': 'SHORT',
                'reason': f'下跌趋势，价格在阻力区({price_position:.1%}>{self.params["trend_following"]["short_resistance_threshold"]*100}%)',
                'confidence': self.params['trend_following']['confidence'],
                'strategy': '趋势跟踪'
            }
            self.state['strategy_stats']['trend_following_signals'] += 1
        
        # 🎯 策略3: 均值回归 (优化参数)
        elif self.params['mean_reversion']['enabled']:
            if trend == 'neutral' and volatility > self.params['mean_reversion']['volatility_threshold']:
                if price_position < self.params['mean_reversion']['long_support_threshold']:
                    signal = {
                        'direction': 'LONG',
                        'reason': f'震荡行情+高波动率，价格在支撑区({price_position:.1%}<{self.params["mean_reversion"]["long_support_threshold"]*100}%)',
                        'confidence': self.params['mean_reversion']['confidence'],
                        'strategy': '均值回归'
                    }
                    self.state['strategy_stats']['mean_reversion_signals'] += 1
                elif price_position > self.params['mean_reversion']['short_resistance_threshold']:
                    signal = {
                        'direction': 'SHORT',
                        'reason': f'震荡行情+高波动率，价格在阻力区({price_position:.1%}>{self.params["mean_reversion"]["short_resistance_threshold"]*100}%)',
                        'confidence': self.params['mean_reversion']['confidence'],
                        'strategy': '均值回归'
                    }
                    self.state['strategy_stats']['mean_reversion_signals'] += 1
        
        return signal
    
    def calculate_trade_params(self, signal, analysis):
        """计算交易参数"""
        if not signal or not analysis:
            return None
        
        current_price = analysis['current_price']
        vol_level = analysis['volatility_level']
        
        # 根据波动率设置止盈止损
        vol_params = self.params['volatility_adjustment'][vol_level]
        stop_loss_pct = vol_params['stop_loss']
        take_profit_pct = vol_params['take_profit']
        leverage = vol_params['leverage']
        
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
        
        # 检查风险回报比
        if trade_params['risk_reward_ratio'] < self.params['risk_reward_ratio_min']:
            self.logger.info(f"风险回报比过低: {trade_params['risk_reward_ratio']:.2f} < {self.params['risk_reward_ratio_min']}")
            self.state['strategy_stats']['rejected_signals'] += 1
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
                'stop_loss_price': trade_params['stop_loss_price'],
                'take_profit_price': trade_params['take_profit_price'],
                'stop_loss_pct': trade_params['stop_loss_pct'],
                'take_profit_pct': trade_params['take_profit_pct'],
                'leverage': trade_params['leverage'],
                'reason': signal['reason'],
                'strategy': signal.get('strategy', 'N/A'),
                '