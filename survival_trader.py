#!/usr/bin/env python3
"""
生存交易系统核心引擎
目标: 200U → 1000U (30天)
策略: 趋势跟踪 + 均值回归混合
风控: 生存优先，成本覆盖第一
"""

import ccxt
import json
import time
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/survival_trader.log'),
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
    position_size: float  # 合约数量
    leverage: int
    reason: str
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

class SurvivalTrader:
    """生存优先的交易引擎"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.exchange = self._init_exchange()
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
        self.capital = self.config['meta']['initial_capital']
        self.equity_curve = []
        self.is_running = False
        
        # 性能指标
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'daily_pnl': 0.0,
            'costs_covered': False
        }
        
        logger.info(f"🚀 生存交易系统初始化 - 目标: {self.capital}U → {self.config['meta']['target_capital']}U")
        logger.info(f"📅 时间窗口: {self.config['meta']['start_date']} 至 {self.config['meta']['target_date']}")
        logger.info(f"🎯 日目标回报: {self.config['meta']['daily_target_return']*100:.1f}%")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _init_exchange(self) -> ccxt.Exchange:
        """初始化交易所连接"""
        exchange_config = {
            'apiKey': self.config['exchange']['api_key'],
            'secret': self.config['exchange']['secret'],
            'password': self.config['exchange']['passphrase'],
            'enableRateLimit': True,
            'options': {
                'defaultType': self.config['exchange']['default_type']
            }
        }
        
        # 添加代理配置
        if 'proxies' in self.config['exchange']:
            exchange_config['proxies'] = self.config['exchange']['proxies']
        
        return ccxt.okx(exchange_config)
    
    def calculate_position_size(self, signal: TradeSignal) -> float:
        """基于凯利公式和风险限制计算仓位大小"""
        base_position = self.config['trading']['position_sizing']['base_position']
        max_position = self.config['trading']['position_sizing']['max_position']
        
        # 凯利公式: f* = (bp - q) / b
        # 简化版: 基于置信度和风险调整
        kelly_fraction = min(
            signal.confidence * 0.5,  # 最大50%凯利
            max_position
        )
        
        # 应用风险限制
        risk_per_trade = abs(signal.entry_price - signal.stop_loss) / signal.entry_price
        max_risk_position = self.config['risk_management']['stop_loss']['initial'] / risk_per_trade
        
        position_size = min(
            kelly_fraction,
            max_risk_position,
            base_position * (1 + signal.confidence)
        )
        
        # 转换为合约数量
        contract_size = self._get_contract_size()
        return (self.capital * position_size * signal.leverage) / (signal.entry_price * contract_size)
    
    def _get_contract_size(self) -> float:
        """获取合约乘数"""
        market = self.exchange.market(self.config['exchange']['symbol'])
        return market['contractSize']
    
    def analyze_market(self) -> Optional[TradeSignal]:
        """分析市场并生成交易信号"""
        try:
            # 获取K线数据
            timeframe = self.config['trading']['base_timeframe']
            ohlcv = self.exchange.fetch_ohlcv(
                self.config['exchange']['symbol'],
                timeframe,
                limit=100
            )
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 计算技术指标
            df = self._calculate_indicators(df)
            
            # 生成信号
            signal = self._generate_signal(df)
            
            if signal and signal.confidence > 0.6:  # 置信度阈值
                logger.info(f"📡 生成交易信号: {signal.direction.value} | 置信度: {signal.confidence:.2f}")
                logger.info(f"   📊 理由: {signal.reason}")
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"市场分析错误: {e}")
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        # 移动平均线
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # ATR (波动率)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=14).mean()
        
        return df
    
    def _generate_signal(self, df: pd.DataFrame) -> Optional[TradeSignal]:
        """基于指标生成交易信号"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 趋势动量信号
        trend_signal = self._check_trend_momentum(latest, prev)
        
        # 均值回归信号
        mean_reversion_signal = self._check_mean_reversion(latest, prev)
        
        # 选择最佳信号
        signals = []
        if trend_signal:
            signals.append(trend_signal)
        if mean_reversion_signal:
            signals.append(mean_reversion_signal)
        
        if not signals:
            return None
        
        # 选择置信度最高的信号
        best_signal = max(signals, key=lambda x: x.confidence)
        
        # 设置止损止盈
        atr = latest['atr']
        if best_signal.direction == TradeDirection.LONG:
            stop_loss = best_signal.entry_price - (atr * 1.5)
            take_profit = best_signal.entry_price + (atr * 3.0)
        else:
            stop_loss = best_signal.entry_price + (atr * 1.5)
            take_profit = best_signal.entry_price - (atr * 3.0)
        
        best_signal.stop_loss = stop_loss
        best_signal.take_profit = take_profit
        
        # 计算动态杠杆(基于波动率)
        volatility = atr / latest['close']
        if volatility < 0.005:  # 低波动
            leverage = min(self.config['trading']['leverage']['max'], 15)
        elif volatility < 0.01:  # 中波动
            leverage = min(self.config['trading']['leverage']['max'], 10)
        else:  # 高波动
            leverage = self.config['trading']['leverage']['min']
        
        best_signal.leverage = leverage
        
        # 计算仓位大小
        best_signal.position_size = self.calculate_position_size(best_signal)
        
        return best_signal
    
    def _check_trend_momentum(self, latest, prev) -> Optional[TradeSignal]:
        """检查趋势动量信号"""
        signals = []
        
        # EMA金叉/死叉
        if latest['ema_20'] > latest['ema_50'] and prev['ema_20'] <= prev['ema_50']:
            signals.append((
                TradeDirection.LONG,
                0.7,
                "EMA金叉(20>50)，趋势转多"
            ))
        elif latest['ema_20'] < latest['ema_50'] and prev['ema_20'] >= prev['ema_50']:
            signals.append((
                TradeDirection.SHORT,
                0.7,
                "EMA死叉(20<50)，趋势转空"
            ))
        
        # MACD信号
        if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
            signals.append((
                TradeDirection.LONG,
                0.6,
                "MACD上穿信号线，动量转强"
            ))
        elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
            signals.append((
                TradeDirection.SHORT,
                0.6,
                "MACD下穿信号线，动量转弱"
            ))
        
        # RSI超买超卖
        if latest['rsi'] < 30:
            signals.append((
                TradeDirection.LONG,
                0.5,
                f"RSI超卖({latest['rsi']:.1f})，可能反弹"
            ))
        elif latest['rsi'] > 70:
            signals.append((
                TradeDirection.SHORT,
                0.5,
                f"RSI超买({latest['rsi']:.1f})，可能回调"
            ))
        
        if not signals:
            return None
        
        # 选择最强信号
        best_signal = max(signals, key=lambda x: x[1])
        return TradeSignal(
            direction=best_signal[0],
            confidence=best_signal[1],
            entry_price=latest['close'],
            stop_loss=0,
            take_profit=0,
            position_size=0,
            leverage=0,
            reason=best_signal[2],
            timestamp=datetime.now()
        )
    
    def _check_mean_reversion(self, latest, prev) -> Optional[TradeSignal]:
        """检查均值回归信号"""
        # 布林带触碰
        if latest['close'] <= latest['bb_lower']:
            return TradeSignal(
                direction=TradeDirection.LONG,
                confidence=0.65,
                entry_price=latest['close'],
                stop_loss=0,
                take_profit=0,
                position_size=0,
                leverage=0,
                reason=f"价格触及布林带下轨({latest['bb_lower']:.0f})，均值回归机会",
                timestamp=datetime.now()
            )
        elif latest['close'] >= latest['bb_upper']:
            return TradeSignal(
                direction=TradeDirection.SHORT,
                confidence=0.65,
                entry_price=latest['close'],
                stop_loss=0,
                take_profit=0,
                position_size=0,
                leverage=0,
                reason=f"价格触及布林带上轨({latest['bb_upper']:.0f})，均值回归机会",
                timestamp=datetime.now()
            )
        
        return None
    
    def execute_trade(self, signal: TradeSignal) -> bool:
        """执行交易"""
        try:
            symbol = self.config['exchange']['symbol']
            
            # 检查是否有相反方向持仓
            for pos_id, position in self.positions.items():
                if position.direction != signal.direction:
                    logger.info(f"⚠️ 存在相反方向持仓，先平仓: {pos_id}")
                    self.close_position(pos_id)
            
            # 设置杠杆
            self.exchange.set_leverage(signal.leverage, symbol)
            
            # 下单
            order_type = 'limit'  # 使用限价单减少滑点
            side = 'buy' if signal.direction == TradeDirection.LONG else 'sell'
            
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=signal.position_size,
                price=signal.entry_price
            )
            
            logger.info(f"✅ 订单执行: {side.upper()} {signal.position_size:.4f} @ ${signal.entry_price:,.0f}")
            logger.info(f"   🛡️ 止损: ${signal.stop_loss:,.0f} | 🎯 止盈: ${signal.take_profit:,.0f}")
            logger.info(f"   📈 杠杆: {signal.leverage}x | 理由: {signal.reason}")
            
            # 记录交易
            trade_record = {
                'id': order['id'],
                'timestamp': datetime.now().isoformat(),
                'direction': signal.direction.value,
                'entry_price': signal.entry_price,
                'position_size': signal.position_size,
                'leverage': signal.leverage,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'reason': signal.reason,
                'status': 'open'
            }
            self.trade_history.append(trade_record)
            
            # 创建持仓记录
            position_id = f"{symbol}_{order['id']}"
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
            
            self.metrics['total_trades'] += 1
            return True
            
        except Exception as e:
            logger.error(f"交易执行失败: {e}")
            return False
    
    def close_position(self, position_id: str, reason: str = "手动平仓") -> bool:
        """平仓"""
        try:
            position = self.positions[position_id]
            symbol = position.symbol
            
            # 反向平仓
            side = 'sell' if position.direction == TradeDirection.LONG else 'buy'
            
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=position.position_size
            )
            
            # 计算盈亏
            exit_price = order['price']
            pnl = self._calculate_pnl(position, exit_price)
            
            # 更新资金
            self.capital += pnl
            self.metrics['total_pnl'] += pnl
            
            if pnl > 0:
                self.metrics['winning_trades'] += 1
            else:
                self.metrics['losing_trades'] += 1
            
            # 记录交易
            for trade in self.trade_history:
                if trade['id'] == position_id.split('_')[-1]:
                    trade['exit_price'] = exit_price
                    trade['exit_time'] = datetime.now().isoformat()
                    trade['pnl'] = pnl
                    trade['pnl_percent'] = (pnl / self.capital) * 100
                    trade['status'] = 'closed'
                    trade['close_reason'] = reason
                    break
            
            # 移除持仓
            del self.positions[position_id]
            
            logger.info(f"📤 平仓完成: {position.direction.value}")
            logger.info(f"   💰 PNL: ${pnl:+.2f} ({((pnl/self.capital)*100):+.2f}%)")
            logger.info(f"   📊 理由: