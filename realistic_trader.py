#!/usr/bin/env python3
"""
务实高杠杆交易引擎
目标: 200U → 400U (100%月回报)
核心: 三重确认 + 动态杠杆 + 严格风控
"""

import ccxt
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/realistic_trader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"

@dataclass
class TradeSignal:
    direction: TradeDirection
    confidence: float  # 0.0-1.0
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    leverage: int
    reasons: List[str]
    timestamp: datetime

@dataclass
class Position:
    symbol: str
    direction: TradeDirection
    entry_price: float
    entry_time: datetime
    position_size: float
    leverage: int
    stop_loss: float
    take_profit: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    status: str = "open"

class RealisticTrader:
    """务实高杠杆交易引擎"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.exchange = self._init_exchange()
        
        # 资金管理
        self.initial_capital = self.config['meta']['initial_capital']
        self.capital = self.initial_capital
        self.daily_pnl = 0
        self.weekly_pnl = 0
        self.total_pnl = 0
        
        # 交易管理
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
        self.equity_curve = [self.capital]
        self.dates = [datetime.now()]
        
        # 风险控制
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.daily_loss = 0
        self.max_drawdown = 0
        self.current_drawdown = 0
        
        # 性能指标
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'sharpe_ratio': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'largest_win': 0,
            'largest_loss': 0
        }
        
        # 状态标志
        self.is_running = False
        self.trading_paused = False
        self.pause_reason = ""
        self.pause_until = None
        
        logger.info(f"🚀 务实高杠杆交易系统初始化")
        logger.info(f"   目标: ${self.initial_capital} → ${self.config['meta']['target_capital']}")
        logger.info(f"   月回报目标: {self.config['meta']['monthly_target_return']*100}%")
        logger.info(f"   杠杆范围: {self.config['trading']['leverage']['min']}-{self.config['trading']['leverage']['max']}x")
        logger.info(f"   每日交易限制: {self.config['trading']['max_daily_trades']}次")
    
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _init_exchange(self) -> ccxt.Exchange:
        exchange_config = {
            'apiKey': self.config['exchange']['api_key'],
            'secret': self.config['exchange']['secret'],
            'password': self.config['exchange']['passphrase'],
            'enableRateLimit': True,
            'proxies': self.config['exchange']['proxies'],
            'options': {'defaultType': 'swap'}
        }
        return ccxt.okx(exchange_config)
    
    def check_trading_allowed(self) -> Tuple[bool, str]:
        """检查是否允许交易"""
        # 检查暂停状态
        if self.trading_paused:
            if self.pause_until and datetime.now() < self.pause_until:
                remaining = (self.pause_until - datetime.now()).total_seconds() / 60
                return False, f"交易暂停: {self.pause_reason} (剩余{remaining:.1f}分钟)"
            else:
                self.trading_paused = False
                self.pause_reason = ""
                self.pause_until = None
        
        # 检查每日交易限制
        if self.daily_trades >= self.config['trading']['max_daily_trades']:
            return False, f"达到每日交易限制: {self.daily_trades}/{self.config['trading']['max_daily_trades']}"
        
        # 检查连续亏损
        if self.consecutive_losses >= self.config['risk_management']['daily_level']['stop_trading_after_loss']:
            cooldown = self.config['trading']['cooldown_hours']
            self.pause_trading(cooldown, f"连续{self.consecutive_losses}次亏损")
            return False, f"连续亏损暂停: {self.consecutive_losses}次"
        
        # 检查日亏损限制
        daily_loss_limit = self.config['risk_management']['daily_level']['max_loss'] * self.initial_capital
        if self.daily_loss >= daily_loss_limit:
            self.pause_trading(24, f"达到日亏损限制: ${self.daily_loss:.2f}")
            return False, f"日亏损超限: ${self.daily_loss:.2f}"
        
        # 检查总回撤
        total_drawdown_limit = self.config['risk_management']['portfolio_level']['max_total_drawdown'] * self.initial_capital
        current_drawdown_value = self.current_drawdown * self.initial_capital
        if current_drawdown_value >= total_drawdown_limit:
            self.pause_trading(48, f"达到总回撤限制: {self.current_drawdown*100:.1f}%")
            return False, f"总回撤超限: {self.current_drawdown*100:.1f}%"
        
        return True, "允许交易"
    
    def pause_trading(self, hours: int, reason: str):
        """暂停交易"""
        self.trading_paused = True
        self.pause_reason = reason
        self.pause_until = datetime.now() + timedelta(hours=hours)
        logger.warning(f"⏸️ 交易暂停: {reason}，恢复时间: {self.pause_until}")
    
    def calculate_dynamic_leverage(self, volatility: float, signal_quality: float, 
                                  trend_strength: float) -> int:
        """计算动态杠杆"""
        base_leverage = self.config['trading']['leverage']['default']
        min_leverage = self.config['trading']['leverage']['min']
        max_leverage = self.config['trading']['leverage']['max']
        
        leverage = base_leverage
        
        # 波动率调整
        if volatility < 0.003:  # 低波动
            leverage += 8
        elif volatility > 0.008:  # 高波动
            leverage -= 10
        
        # 信号质量调整
        if signal_quality > 0.85:
            leverage += 5
        elif signal_quality < 0.7:
            leverage -= 5
        
        # 趋势强度调整
        if trend_strength > 0.01:  # 强趋势
            leverage += 5
        elif trend_strength < 0.002:  # 弱趋势
            leverage -= 5
        
        # 当前回撤调整
        if self.current_drawdown > 0.1:  # 回撤>10%
            leverage -= 10
        elif self.current_drawdown > 0.05:  # 回撤>5%
            leverage -= 5
        
        # 限制在范围内
        leverage = max(min_leverage, min(max_leverage, leverage))
        
        return leverage
    
    def generate_triple_confirmation_signal(self, df_15m: pd.DataFrame, df_1h: pd.DataFrame, 
                                           current_idx: int) -> Optional[TradeSignal]:
        """生成三重确认信号"""
        if current_idx < 2 or len(df_1h) < 2:
            return None
        
        current_15m = df_15m.iloc[current_idx]
        prev_15m = df_15m.iloc[current_idx-1]
        current_1h = df_1h.iloc[-1]
        prev_1h = df_1h.iloc[-2] if len(df_1h) > 1 else current_1h
        
        reasons = []
        confidence = 0
        
        # === 第一重确认: 趋势方向 ===
        trend_direction = None
        trend_strength = 0
        
        if current_1h['ema_20'] > current_1h['ema_50']:
            trend_direction = TradeDirection.LONG
            trend_strength = (current_1h['ema_20'] - current_1h['ema_50']) / current_1h['close']
            reasons.append(f"1h趋势: 多头 (强度: {trend_strength*100:.2f}%)")
            confidence += 0.25
        elif current_1h['ema_20'] < current_1h['ema_50']:
            trend_direction = TradeDirection.SHORT
            trend_strength = (current_1h['ema_50'] - current_1h['ema_20']) / current_1h['close']
            reasons.append(f"1h趋势: 空头 (强度: {trend_strength*100:.2f}%)")
            confidence += 0.25
        else:
            return None  # 趋势不明，放弃
        
        # === 第二重确认: 动量信号 ===
        momentum_signals = 0
        max_momentum = 0.2
        
        # EMA交叉
        if (trend_direction == TradeDirection.LONG and 
            current_15m['ema_20'] > current_15m['ema_50'] and 
            prev_15m['ema_20'] <= prev_15m['ema_50']):
            reasons.append("15m EMA金叉")
            momentum_signals += 1
            confidence += 0.1
        
        elif (trend_direction == TradeDirection.SHORT and 
              current_15m['ema_20'] < current_15m['ema_50'] and 
              prev_15m['ema_20'] >= prev_15m['ema_50']):
            reasons.append("15m EMA死叉")
            momentum_signals += 1
            confidence += 0.1
        
        # MACD信号
        if (trend_direction == TradeDirection.LONG and 
            current_15m['macd'] > current_15m['macd_signal'] and 
            prev_15m['macd'] <= prev_15m['macd_signal']):
            reasons.append("MACD金叉")
            momentum_signals += 1
            confidence += 0.08
        
        elif (trend_direction == TradeDirection.SHORT and 
              current_15m['macd'] < current_15m['macd_signal'] and 
              prev_15m['macd'] >= prev_15m['macd_signal']):
            reasons.append("MACD死叉")
            momentum_signals += 1
            confidence += 0.08
        
        # 需要至少2个动量信号
        if momentum_signals < 2:
            return None
        
        # === 第三重确认: 成交量与风险调整 ===
        
        # 成交量确认
        if current_15m['volume_ratio'] >= 1.5:
            reasons.append(f"成交量放大: {current_15m['volume_ratio']:.1f}倍")
            confidence += 0.15
        else:
            return None  # 成交量不足
        
        # RSI确认
        if trend_direction == TradeDirection.LONG and current_15m['rsi'] < 65:
            reasons.append(f"RSI正常: {current_15m['rsi']:.1f}")
            confidence += 0.1
        elif trend_direction == TradeDirection.SHORT and current_15m['rsi'] > 35:
            reasons.append(f"RSI正常: {current_15m['rsi']:.1f}")
            confidence += 0.1
        else:
            return None  # RSI极端
        
        # 波动率检查
        if current_15m['atr_percent'] > 0.015:
            return None  # 波动率过高
        
        # 布林带宽度检查
        if current_15m['bb_width'] < 0.015:
            return None  # 波动空间不足
        
        # 最终置信度检查
        if confidence < 0.7:
            return None
        
        # === 计算交易参数 ===
        entry_price = current_15m['close']
        atr = current_15m['atr']
        
        # 止损止盈
        if trend_direction == TradeDirection.LONG:
            stop_loss = entry_price - (atr * 1.2)  # 1.2倍ATR止损
            take_profit = entry_price + (atr * 2.4)  # 2.4倍ATR止盈 (2:1盈亏比)
        else:
            stop_loss = entry_price + (atr * 1.2)
            take_profit = entry_price - (atr * 2.4)
        
        # 计算杠杆
        volatility = current_15m['atr_percent']
        leverage = self.calculate_dynamic_leverage(volatility, confidence, trend_strength)
        
        # 计算仓位
        risk_per_trade = abs(entry_price - stop_loss) / entry_price
        max_risk_amount = self.config['risk_management']['position_level']['max_risk_per_trade'] * self.capital
        position_value = max_risk_amount / risk_per_trade
        
        # 考虑杠杆
        position_usd = position_value * leverage
        position_size = position_usd / entry_price  # BTC合约乘数为1
        
        # 确保最小交易量
        min_amount = 0.001
        if position_size < min_amount:
            position_size = min_amount
        
        return TradeSignal(
            direction=trend_direction,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            leverage=leverage,
            reasons=reasons,
            timestamp=datetime.now()
        )
    
    def execute_trade(self, signal: TradeSignal) -> bool:
        """执行交易"""
        allowed, reason = self.check_trading_allowed()
        if not allowed:
            logger.warning(f"交易被阻止: {reason}")
            return False
        
        try:
            symbol = self.config['exchange']['symbol']
            
            # 设置杠杆
            self.exchange.set_leverage(signal.leverage, symbol)
            
            # 下单
            side = 'buy' if signal.direction == TradeDirection.LONG else 'sell'
            order_type = 'limit'
            
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=signal.position_size,
                price=signal.entry_price
            )
            
            # 记录交易
            trade_id = order['id']
            position_id = f"{symbol}_{trade_id}"
            
            self.positions[position_id] = Position(
                symbol=symbol,
                direction=signal.direction,
                entry_price=signal.entry_price,
                entry_time=datetime.now(),
                position_size=signal.position_size,
                leverage=signal.leverage,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                current_price=signal.entry_price,
                unrealized_pnl=0.0
            )
            
            trade_record = {
                'id': trade_id,
                'time': datetime.now().isoformat(),
                'type': 'OPEN',
                'direction': signal.direction.value,
                'entry_price': signal.entry_price,
                'position_size': signal.position_size,
                'leverage': signal.leverage,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'reasons': signal.reasons,
                'confidence': signal.confidence,
                'status': 'open'
            }
            
            self.trade_history.append(trade_record)
            self.daily_trades += 1
            
            logger.info(f"✅ 开仓执行: {signal.direction.value}")
            logger.info(f"   价格: ${signal.entry_price:,.0f}")
            logger.info(f"   仓位: {signal.position_size:.4f} BTC")
            logger.info(f"   杠杆: {signal.leverage}x")
            logger.info(f"   止损: ${signal.stop_loss:,.0f}")
            logger.info(f"   止盈: ${signal.take_profit:,.0f}")
            logger.info(f"   理由: {' | '.join(signal.reasons)}")
            
            return True
            
        except Exception as e:
            logger.error(f"交易执行失败: {e}")
            return False
    
    def monitor_positions(self):
        """监控持仓，检查止损止盈"""
        if not self.positions:
            return
        
        current_time = datetime.now()
