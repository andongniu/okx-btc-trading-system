#!/usr/bin/env python3
"""
自主交易系统 - 基于数据迭代策略，每笔订单都带止盈止损
"""

import ccxt
import json
import time
import logging
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional, Tuple
import threading

class AutonomousTradingSystem:
    def __init__(self):
        """初始化自主交易系统"""
        print('🚀 初始化自主交易系统...')
        
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
        self.contract_multiplier = 0.01  # 1张合约 = 0.01 BTC
        
        # 策略参数
        self.strategy_params = {
            'base_stop_loss_pct': 1.5,  # 基础止损百分比
            'base_take_profit_pct': 3.0,  # 基础止盈百分比
            'min_position_size': 0.01,  # 最小仓位（张）
            'max_position_size': 0.1,   # 最大仓位（张）
            'default_leverage': 10,     # 默认杠杆
            'max_leverage': 50,         # 最大杠杆
            'risk_per_trade': 0.01,     # 每笔交易风险（1%）
            'max_daily_trades': 5,      # 每日最大交易次数
            'cooldown_after_loss': 2,   # 亏损后冷却交易次数
        }
        
        # 交易历史
        self.trade_history = []
        self.daily_stats = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'trades_today': 0,
            'wins_today': 0,
            'losses_today': 0,
            'pnl_today': 0,
            'consecutive_losses': 0
        }
        
        # 策略状态
        self.strategy_state = {
            'market_trend': 'neutral',  # bullish, bearish, neutral
            'volatility_level': 'medium',  # low, medium, high
            'last_signal_time': None,
            'active_positions': [],
            'pending_orders': []
        }
        
        # 初始化日志
        self.setup_logging()
        
        print('✅ 自主交易系统初始化完成')
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/autonomous_trading.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze_market(self) -> Dict:
        """分析市场状态"""
        try:
            # 获取K线数据
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '15m', limit=100)
            closes = np.array([c[4] for c in ohlcv])
            
            # 计算技术指标
            sma_20 = np.mean(closes[-20:])
            sma_50 = np.mean(closes[-50:])
            current_price = closes[-1]
            
            # 计算波动率
            returns = np.diff(closes) / closes[:-1]
            volatility = np.std(returns) * np.sqrt(365 * 24 * 4)  # 年化波动率
            
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
            
            # 计算支撑阻力
            support = np.min(closes[-20:])
            resistance = np.max(closes[-20:])
            
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
                'price_position': (current_price - support) / (resistance - support) if resistance != support else 0.5
            }
            
            self.strategy_state['market_trend'] = trend
            self.strategy_state['volatility_level'] = vol_level
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"市场分析失败: {e}")
            return {}
    
    def generate_signal(self, market_analysis: Dict) -> Optional[Dict]:
        """生成交易信号"""
        if not market_analysis:
            return None
        
        current_price = market_analysis['current_price']
        trend = market_analysis['trend']
        vol_level = market_analysis['volatility_level']
        price_position = market_analysis['price_position']
        
        # 检查冷却期
        if self.daily_stats['consecutive_losses'] >= self.strategy_params['cooldown_after_loss']:
            self.logger.info("处于冷却期，暂停交易")
            return None
        
        # 检查每日交易限制
        if self.daily_stats['trades_today'] >= self.strategy_params['max_daily_trades']:
            self.logger.info("达到每日交易限制")
            return None
        
        signal = None
        
        # 基于趋势和价格位置的策略
        if trend == 'bullish' and price_position < 0.3:
            # 上涨趋势，价格在支撑附近
            signal = {
                'direction': 'LONG',
                'confidence': 0.7,
                'reason': '上涨趋势，价格接近支撑位',
                'entry_price': current_price,
                'stop_loss_pct': self.calculate_dynamic_stop_loss(vol_level, 'LONG'),
                'take_profit_pct': self.calculate_dynamic_take_profit(vol_level, 'LONG')
            }
        
        elif trend == 'bearish' and price_position > 0.7:
            # 下跌趋势，价格在阻力附近
            signal = {
                'direction': 'SHORT',
                'confidence': 0.7,
                'reason': '下跌趋势，价格接近阻力位',
                'entry_price': current_price,
                'stop_loss_pct': self.calculate_dynamic_stop_loss(vol_level, 'SHORT'),
                'take_profit_pct': self.calculate_dynamic_take_profit(vol_level, 'SHORT')
            }
        
        elif trend == 'neutral' and vol_level == 'high':
            # 高波动率，均值回归策略
            if price_position > 0.7:
                signal = {
                    'direction': 'SHORT',
                    'confidence': 0.6,
                    'reason': '高波动率，价格在阻力位，均值回归',
                    'entry_price': current_price,
                    'stop_loss_pct': self.calculate_dynamic_stop_loss(vol_level, 'SHORT'),
                    'take_profit_pct': self.calculate_dynamic_take_profit(vol_level, 'SHORT')
                }
            elif price_position < 0.3:
                signal = {
                    'direction': 'LONG',
                    'confidence': 0.6,
                    'reason': '高波动率，价格在支撑位，均值回归',
                    'entry_price': current_price,
                    'stop_loss_pct': self.calculate_dynamic_stop_loss(vol_level, 'LONG'),
                    'take_profit_pct': self.calculate_dynamic_take_profit(vol_level, 'LONG')
                }
        
        if signal:
            signal['position_size'] = self.calculate_position_size(signal)
            signal['leverage'] = self.calculate_leverage(vol_level)
            signal['risk_amount'] = self.calculate_risk_amount(signal)
            signal['potential_reward'] = self.calculate_potential_reward(signal)
            signal['risk_reward_ratio'] = signal['potential_reward'] / signal['risk_amount'] if signal['risk_amount'] > 0 else 0
            
            # 只接受风险回报比大于1.5的信号
            if signal['risk_reward_ratio'] < 1.5:
                self.logger.info(f"风险回报比过低: {signal['risk_reward_ratio']:.2f}")
                return None
        
        return signal
    
    def calculate_dynamic_stop_loss(self, vol_level: str, direction: str) -> float:
        """动态计算止损百分比"""
        base_sl = self.strategy_params['base_stop_loss_pct']
        
        # 根据波动率调整
        if vol_level == 'low':
            return base_sl * 0.8  # 低波动率，收紧止损
        elif vol_level == 'high':
            return base_sl * 1.5  # 高波动率，放宽止损
        else:
            return base_sl
    
    def calculate_dynamic_take_profit(self, vol_level: str, direction: str) -> float:
        """动态计算止盈百分比"""
        base_tp = self.strategy_params['base_take_profit_pct']
        
        # 根据波动率调整
        if vol_level == 'low':
            return base_tp * 0.8  # 低波动率，收紧止盈
        elif vol_level == 'high':
            return base_tp * 1.5  # 高波动率，放宽止盈
        else:
            return base_tp
    
    def calculate_position_size(self, signal: Dict) -> float:
        """计算仓位大小"""
        account_balance = self.get_account_balance()
        risk_amount = account_balance * self.strategy_params['risk_per_trade']
        
        # 计算基于风险的仓位
        position_value = risk_amount / (signal['stop_loss_pct'] / 100)
        position_contracts = position_value / (signal['entry_price'] * self.contract_multiplier)
        
        # 限制在最小和最大仓位之间
        position_contracts = max(
            self.strategy_params['min_position_size'],
            min(position_contracts, self.strategy_params['max_position_size'])
        )
        
        # 四舍五入到最小交易单位
        position_contracts = round(position_contracts * 100) / 100
        
        return position_contracts
    
    def calculate_leverage(self, vol_level: str) -> int:
        """计算杠杆"""
        base_leverage = self.strategy_params['default_leverage']
        
        # 根据波动率调整杠杆
        if vol_level == 'high':
            return min(base_leverage // 2, self.strategy_params['max_leverage'])
        elif vol_level == 'low':
            return min(base_leverage * 2, self.strategy_params['max_leverage'])
        else:
            return min(base_leverage, self.strategy_params['max_leverage'])
    
    def calculate_risk_amount(self, signal: Dict) -> float:
        """计算风险金额"""
        position_value = signal['position_size'] * signal['entry_price'] * self.contract_multiplier
        return position_value * (signal['stop_loss_pct'] / 100)
    
    def calculate_potential_reward(self, signal: Dict) -> float:
        """计算潜在盈利"""
        position_value = signal['position_size'] * signal['entry_price'] * self.contract_multiplier
        return position_value * (signal['take_profit_pct'] / 100)
    
    def get_account_balance(self) -> float:
        """获取账户余额"""
        balance = self.exchange.fetch_balance()
        return balance['total'].get('USDT', 0)
    
    def execute_trade(self, signal: Dict) -> bool:
        """执行交易"""
        try:
            direction = signal['direction']
            contracts = signal['position_size']
            leverage = signal['leverage']
            entry_price = signal['entry_price']
            stop_loss_pct = signal['stop_loss_pct']
            take_profit_pct = signal['take_profit_pct']
            
            # 计算止盈止损价格
            if direction == 'LONG':
                stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
                take_profit_price = entry_price * (1 + take_profit_pct / 100)
            else:
                stop_loss_price = entry_price * (1 + stop_loss_pct / 100)
                take_profit_price = entry_price * (1 - take_profit_pct / 100)
            
            # 设置杠杆
            self.exchange.set_leverage(leverage, self.symbol)
            
            # 执行市价单
            if direction == 'LONG':
                order = self.exchange.create_market_buy_order(self.symbol, contracts)
            else:
                order = self.exchange.create_market_sell_order(self.symbol, contracts)
            
            # 记录交易
            trade_record = {
                'trade_id': order['id'],
                'timestamp': datetime.now().isoformat(),
                'direction': direction,
                'contracts': contracts,
                'entry_price': entry_price,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price,
                'stop_loss_pct': stop_loss_pct,
                'take_profit_pct': take_profit_pct,
                'leverage': leverage,
                'reason': signal['reason'],
                'confidence': signal['confidence'],
                'risk_amount': signal['risk_amount'],
                'potential_reward': signal['potential_reward'],
                'risk_reward_ratio': signal['risk_reward_ratio'],
                'status': 'open'
            }
            
            self.trade_history.append(trade_record)
            self.daily_stats['trades_today'] += 1
            
            # 添加到活跃持仓
            self.strategy_state['active_positions'].append(trade_record)
            
            self.logger.info(f"✅ 交易执行成功: {direction} {contracts}张合约")
            self.logger.info(f"   入场价: ${entry_price:.2f}")
            self.logger.info(f"   止损价: ${stop_loss_price:.2f} (-{stop_loss_pct}%)")
            self.logger.info(f"   止盈价: ${take_profit_price:.2f} (+{take_profit_pct}%)")
            self.logger.info(f"   杠杆: {leverage}x")
            self.logger.info(f"   风险回报比: {signal['risk_reward_ratio']:.2f}")
            
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
                        # 检查是否需要平仓
                        self.check_position_triggers(pos, current_price)
            
        except Exception as e:
            self.logger.error(f"监控持仓失败: {e}")
    
    def check_position_triggers(self, position: Dict, current_price: float):
        """检查持仓触发条件"""
        entry_price = float(position.get('entryPrice', 0))
        side = position.get('side', '')
        
        if not entry_price or not side:
            return
        
        # 查找对应的交易记录
        for trade in self.strategy_state['active_positions'][:]:
            if abs(trade['entry_price'] - entry_price) < 1.0:  # 价格匹配
                stop_loss = trade['stop_loss_price']
                take_profit = trade['take_profit_price']
                
                should_close = False
                close_reason = ""
                
                if side == 'long':
                    if current_price <= stop_loss:
                        should_close = True
                        close_reason = "止损触发"
                    elif current_price >= take_profit:
                        should_close = True
                        close_reason = "止盈触发"
                else:  # short
                    if current_price >= stop_loss:
                        should_close = True
                        close_reason = "止损触发"
                    elif current_price <= take_profit:
                        should_close = True
                        close_reason = "止盈触发"
                
                if should_close:
                    self.close_position(position, trade, close_reason)
                    break
    
    def close_position(self, position: Dict, trade_record: Dict, reason: str):
        """平仓"""
        try:
            contracts = float(position.get('contracts', 0))
            side = position.get('side', '')
            
            if side == 'long':
                order = self.exchange.create_market_sell_order(self.symbol, contracts)
                close_side = '卖出平多'
            else:
                order = self.exchange.create_market_buy_order(self.symbol, contracts)
                close_side = '买入平空'
            
            # 获取成交价
            ticker = self.exchange.fetch_ticker(self.symbol)
            exit_price = ticker['last']
            
            # 计算盈亏
            entry_price = trade_record['entry_price']
            if side == 'long':
                pnl = (exit_price - entry_price) * contracts * self.contract_multiplier
            else:
                pnl