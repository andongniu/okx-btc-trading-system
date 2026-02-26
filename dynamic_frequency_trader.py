#!/usr/bin/env python3
"""
动态频率交易系统 - 根据市场活跃度调整检查频率
"""

import ccxt
import json
import time
import numpy as np
from datetime import datetime
import logging
import os

class DynamicFrequencyTrader:
    def __init__(self):
        """初始化动态频率交易系统"""
        print('🚀 初始化动态频率交易系统...')
        print('📈 根据市场活跃度动态调整检查频率 (10-30秒)')
        
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
        
        # 🎯 动态频率参数
        self.frequency_params = {
            'base_interval': 10,  # 基础10秒
            'min_interval': 5,    # 最低5秒 (紧急情况)
            'max_interval': 30,   # 最高30秒 (平静期)
            
            # 根据波动率调整
            'volatility_adjustment': {
                'high': {'threshold': 0.8, 'interval': 8},    # >80%波动率: 8秒
                'medium': {'threshold': 0.4, 'interval': 12}, # 40-80%: 12秒
                'low': {'threshold': 0.2, 'interval': 20},    # 20-40%: 20秒
                'very_low': {'interval': 30}                  # <20%: 30秒
            },
            
            # 根据价格变化率调整
            'price_change_adjustment': {
                'rapid': {'threshold': 0.002, 'interval': 5},  # 0.2%以上变化: 5秒
                'fast': {'threshold': 0.001, 'interval': 8},   # 0.1-0.2%: 8秒
                'normal': {'threshold': 0.0005, 'interval': 12}, # 0.05-0.1%: 12秒
                'slow': {'interval': 20}                       # <0.05%: 20秒
            },
            
            # 根据持仓状态调整
            'position_adjustment': {
                'has_position': {'interval': 8},   # 有持仓: 8秒
                'no_position': {'interval': 15}    # 无持仓: 15秒
            },
            
            # 根据时间调整 (亚洲/欧洲/美洲交易时段)
            'time_adjustment': {
                'asia_session': {'start': 0, 'end': 8, 'interval': 15},    # 0-8点: 15秒
                'europe_session': {'start': 8, 'end': 16, 'interval': 10}, # 8-16点: 10秒
                'us_session': {'start': 16, 'end': 24, 'interval': 8},     # 16-24点: 8秒
                'overlap_session': {'interval': 5}                         # 重叠时段: 5秒
            }
        }
        
        # 🎯 激进交易参数 (保持)
        self.trade_params = {
            'min_position_size': 0.01,
            'max_position_size': 0.15,
            'risk_per_trade': 0.015,
            'max_daily_trades': 12,
            'consecutive_loss_limit': 5,
            'risk_reward_ratio_min': 1.2,
            
            'trend_following': {
                'long_support_threshold': 0.5,
                'short_resistance_threshold': 0.5,
                'confidence': 0.6
            },
            
            'mean_reversion': {
                'enabled': True,
                'volatility_threshold': 0.25,
                'long_support_threshold': 0.4,
                'short_resistance_threshold': 0.6,
                'confidence': 0.55
            }
        }
        
        # 状态跟踪
        self.state = {
            'running': True,
            'current_interval': self.frequency_params['base_interval'],
            'last_prices': [],  # 记录最近价格用于计算变化率
            'price_change_rate': 0,
            'volatility_history': [],
            'has_position': False,
            'trades_today': 0,
            'consecutive_losses': 0,
            'consecutive_wins': 0,
            'daily_pnl': 0.0,
            'active_positions': []
        }
        
        # 初始化日志
        self.setup_logging()
        
        print('✅ 动态频率交易系统初始化完成')
        print(f'📊 基础频率: {self.frequency_params["base_interval"]}秒')
        print(f'📈 动态范围: {self.frequency_params["min_interval"]}-{self.frequency_params["max_interval"]}秒')
        print(f'🎯 根据波动率、价格变化、持仓状态动态调整')
        print('🌐 监控面板: http://localhost:8084')
    
    def setup_logging(self):
        """设置日志"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/dynamic_frequency_trader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def calculate_dynamic_interval(self, analysis):
        """计算动态检查间隔"""
        if not analysis:
            return self.frequency_params['base_interval']
        
        intervals = []
        
        # 1. 根据波动率调整
        volatility = analysis.get('volatility', 0)
        if volatility > self.frequency_params['volatility_adjustment']['high']['threshold']:
            intervals.append(self.frequency_params['volatility_adjustment']['high']['interval'])
        elif volatility > self.frequency_params['volatility_adjustment']['medium']['threshold']:
            intervals.append(self.frequency_params['volatility_adjustment']['medium']['interval'])
        elif volatility > self.frequency_params['volatility_adjustment']['low']['threshold']:
            intervals.append(self.frequency_params['volatility_adjustment']['low']['interval'])
        else:
            intervals.append(self.frequency_params['volatility_adjustment']['very_low']['interval'])
        
        # 2. 根据价格变化率调整
        price_change = abs(self.state.get('price_change_rate', 0))
        if price_change > self.frequency_params['price_change_adjustment']['rapid']['threshold']:
            intervals.append(self.frequency_params['price_change_adjustment']['rapid']['interval'])
        elif price_change > self.frequency_params['price_change_adjustment']['fast']['threshold']:
            intervals.append(self.frequency_params['price_change_adjustment']['fast']['interval'])
        elif price_change > self.frequency_params['price_change_adjustment']['normal']['threshold']:
            intervals.append(self.frequency_params['price_change_adjustment']['normal']['interval'])
        else:
            intervals.append(self.frequency_params['price_change_adjustment']['slow']['interval'])
        
        # 3. 根据持仓状态调整
        if self.state['has_position']:
            intervals.append(self.frequency_params['position_adjustment']['has_position']['interval'])
        else:
            intervals.append(self.frequency_params['position_adjustment']['no_position']['interval'])
        
        # 4. 根据交易时段调整
        current_hour = datetime.now().hour
        if 0 <= current_hour < 8:
            intervals.append(self.frequency_params['time_adjustment']['asia_session']['interval'])
        elif 8 <= current_hour < 16:
            intervals.append(self.frequency_params['time_adjustment']['europe_session']['interval'])
        elif 16 <= current_hour < 24:
            intervals.append(self.frequency_params['time_adjustment']['us_session']['interval'])
        
        # 取最小值作为最终间隔 (最激进)
        final_interval = min(intervals)
        
        # 确保在最小和最大范围内
        final_interval = max(self.frequency_params['min_interval'], 
                           min(final_interval, self.frequency_params['max_interval']))
        
        return final_interval
    
    def analyze_market(self):
        """分析市场"""
        try:
            # 获取多种时间框架数据
            ohlcv_15m = self.exchange.fetch_ohlcv(self.symbol, '15m', limit=100)
            ohlcv_5m = self.exchange.fetch_ohlcv(self.symbol, '5m', limit=50)
            ohlcv_1m = self.exchange.fetch_ohlcv(self.symbol, '1m', limit=30)  # 用于计算短期变化
            
            closes_15m = np.array([c[4] for c in ohlcv_15m])
            closes_5m = np.array([c[4] for c in ohlcv_5m])
            closes_1m = np.array([c[4] for c in ohlcv_1m])
            
            current_price = closes_15m[-1]
            
            # 记录价格变化率 (1分钟变化)
            if len(self.state['last_prices']) >= 5:
                self.state['last_prices'].pop(0)
            self.state['last_prices'].append(current_price)
            
            if len(self.state['last_prices']) >= 2:
                price_change = (self.state['last_prices'][-1] - self.state['last_prices'][-2]) / self.state['last_prices'][-2]
                self.state['price_change_rate'] = price_change
            
            # 计算技术指标
            sma_20 = np.mean(closes_15m[-20:])
            sma_50 = np.mean(closes_15m[-50:])
            
            # 支撑阻力
            support = np.min(closes_15m[-20:])
            resistance = np.max(closes_15m[-20:])
            price_position = (current_price - support) / (resistance - support) if resistance != support else 0.5
            
            # 波动率 (15分钟年化)
            returns_15m = np.diff(closes_15m) / closes_15m[:-1]
            volatility = np.std(returns_15m) * np.sqrt(365 * 24 * 4)
            
            # 记录波动率历史
            if len(self.state['volatility_history']) >= 20:
                self.state['volatility_history'].pop(0)
            self.state['volatility_history'].append(volatility)
            
            # 趋势判断
            if current_price > sma_20 > sma_50:
                trend = 'bullish'
            elif current_price < sma_20 < sma_50:
                trend = 'bearish'
            else:
                trend = 'neutral'
            
            # 检查持仓状态
            positions = self.exchange.fetch_positions([self.symbol])
            self.state['has_position'] = False
            for pos in positions:
                if pos['symbol'] == self.symbol:
                    contracts = float(pos.get('contracts', 0))
                    if contracts > 0:
                        self.state['has_position'] = True
                        break
            
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
                'price_change_1m': self.state.get('price_change_rate', 0),
                'has_position': self.state['has_position']
            }
            
            # 计算动态间隔
            dynamic_interval = self.calculate_dynamic_interval(analysis)
            self.state['current_interval'] = dynamic_interval
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"市场分析失败: {e}")
            return None
    
    def generate_signal(self, analysis):
        """生成交易信号"""
        if not analysis:
            return None
        
        # 检查限制
        if self.state['consecutive_losses'] >= self.trade_params['consecutive_loss_limit']:
            return None
        
        if self.state['trades_today'] >= self.trade_params['max_daily_trades']:
            return None
        
        trend = analysis['trend']
        price_position = analysis['price_position']
        volatility = analysis['volatility']
        
        signal = None
        
        # 趋势跟踪
        if trend == 'bullish' and price_position < self.trade_params['trend_following']['long_support_threshold']:
            signal = {
                'direction': 'LONG',
                'reason': f'上涨趋势，价格在支撑区({price_position:.1%})',
                'confidence': self.trade_params['trend_following']['confidence'],
                'strategy': '趋势跟踪'
            }
        elif trend == 'bearish' and price_position > self.trade_params['trend_following']['short_resistance_threshold']:
            signal = {
                'direction': 'SHORT',
                'reason': f'下跌趋势，价格在阻力区({price_position:.1%})',
                'confidence': self.trade_params['trend_following']['confidence'],
                'strategy': '趋势跟踪'
            }
        
        # 均值回归
        elif self.trade_params['mean_reversion']['enabled'] and trend == 'neutral':
            if volatility > self.trade_params['mean_reversion']['volatility_threshold']:
                if price_position < self.trade_params['mean_reversion']['long_support_threshold']:
                    signal = {
                        'direction': 'LONG',
                        'reason': f'震荡行情，价格在支撑区({price_position:.1%})',
                        'confidence': self.trade_params['mean_reversion']['confidence'],
                        'strategy': '均值回归'
                    }
                elif price_position > self.trade_params['mean_reversion']['short_resistance_threshold']:
                    signal = {
                        'direction': 'SHORT',
                        'reason': f'震荡行情，价格在阻力区({price_position:.1%})',
                        'confidence': self.trade_params['mean_reversion']['confidence'],
                        'strategy': '均值回归'
                    }
        
        return signal
    
    def run(self):
        """运行主循环"""
        print('\n🚀 启动动态频率交易系统...')
        print('='*50)
        
        iteration = 0
        while self.state['running']:
            try:
                iteration += 1
                start_time = time.time()
                
                print(f'\n🔄 第{iteration}次检查 ({datetime.now().strftime("%H:%M:%S")})')
                print('-'*30)
                
                # 分析市场
                analysis = self.analyze_market()
                
                if analysis:
                    print(f'📈 市场分析:')
                    print(f'   价格: ${analysis["current_price"]:.2f}')
                    print(f'   趋势: {analysis["trend"]}')
                    print(f'   位置: {analysis["price_position"]:.1%}')
                    print(f'   波动率: {analysis["volatility"]:.2%}')
                    print(f'   1分钟变化: {analysis.get("price_change_1m", 0)*100:.3f}%')
                    print(f'   持仓状态: {"有" if analysis["has_position"] else "无"}')
                    
                    # 显示动态频率
                    print(f'⏱️  动态频率: {self.state["current_interval"]}秒')
                    
                    # 检查持仓
                    if not analysis['has_position']:
                        # 生成交易信号
                        signal = self.generate_signal(analysis)
                        if signal:
                            print(f'🎯 生成信号: {signal["direction"]}')
                            print(f'   原因: {signal["reason"]}')
                            print(f'   策略: {signal.get("strategy", "N/A")}')
                            print(f'   信心度: {signal["confidence"]*100:.0f}%')
                            
                            # 这里可以添加交易执行逻辑
                            # 为了简化，先只显示信号
                        else:
                            print('🔄 等待交易信号...')
                    else:
                        print('📊 已有持仓，密切监控中...')
                
                # 计算实际执行时间
                execution_time = time.time() - start_time
                sleep_time = max(0.1,