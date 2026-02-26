#!/usr/bin/env python3
"""
精准高杠杆策略
目标: 200U → 600U (200%月回报)
核心: 低频率 + 高杠杆 + 高质量信号
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HighLeverageStrategy:
    """精准高杠杆交易策略"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.exchange = self._init_exchange()
        self.capital = self.config['meta']['initial_capital']
        self.initial_capital = self.capital
        self.positions = []
        self.trade_history = []
        self.equity_curve = [self.capital]
        self.daily_trades = 0
        self.daily_pnl = 0
        self.consecutive_losses = 0
        
        logger.info(f"🎯 精准高杠杆策略初始化")
        logger.info(f"   目标: ${self.initial_capital} → ${self.config['meta']['target_capital']}")
        logger.info(f"   月回报目标: {self.config['meta']['monthly_target_return']*100}%")
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # 更新为高杠杆配置
        config['trading']['leverage'] = {
            'min': 50,
            'max': 80,
            'default': 60,
            'volatility_adjusted': True
        }
        
        config['trading']['position_sizing'] = {
            'base_position': 0.15,  # 15%基础仓位
            'max_position': 0.25,   # 25%最大仓位
            'pyramid_factor': 0.3   # 金字塔加仓系数
        }
        
        config['risk_management']['stop_loss'] = {
            'initial': -0.02,      # 2%止损
            'trailing': -0.01,     # 1%追踪止损
            'max_daily': -0.08,    # 8%日最大亏损
            'max_total': -0.20     # 20%总最大回撤
        }
        
        config['risk_management']['take_profit'] = {
            'initial': 0.04,       # 4%止盈 (2:1盈亏比)
            'trailing': 0.02,      # 2%追踪止盈
            'scale_out': [0.5, 0.3, 0.2]  # 分批平仓
        }
        
        config['strategy']['timeframes'] = ['15m', '1h', '4h']  # 多时间框架
        config['strategy']['max_daily_trades'] = 3  # 每日最多3次
        config['strategy']['cooldown_hours'] = 4    # 连续亏损后冷却
        
        return config
    
    def _init_exchange(self) -> ccxt.Exchange:
        """初始化交易所"""
        exchange_config = {
            'apiKey': self.config['exchange']['api_key'],
            'secret': self.config['exchange']['secret'],
            'password': self.config['exchange']['passphrase'],
            'enableRateLimit': True,
            'proxies': self.config['exchange']['proxies'],
            'options': {'defaultType': 'swap'}
        }
        return ccxt.okx(exchange_config)
    
    def fetch_multi_timeframe_data(self, symbol: str, days: int = 30) -> Dict[str, pd.DataFrame]:
        """获取多时间框架数据"""
        logger.info(f"📊 获取{symbol} {days}天多时间框架数据...")
        
        timeframes = self.config['strategy']['timeframes']
        data = {}
        
        for tf in timeframes:
            all_ohlcv = []
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            current = start_time
            
            while current < end_time:
                try:
                    since = int(current.timestamp() * 1000)
                    ohlcv = self.exchange.fetch_ohlcv(symbol, tf, since=since, limit=1000)
                    
                    if not ohlcv:
                        break
                    
                    all_ohlcv.extend(ohlcv)
                    current = datetime.fromtimestamp(ohlcv[-1][0] / 1000)
                    
                except Exception as e:
                    logger.error(f"获取{tf}数据失败: {e}")
                    break
            
            if all_ohlcv:
                df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                data[tf] = df
                logger.info(f"  {tf}: {len(df)} 根K线")
        
        return data
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        # 移动平均线
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()
        df['ema_100'] = df['close'].ewm(span=100).mean()
        
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
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # 成交量指标
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # ATR (波动率)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=14).mean()
        df['atr_percent'] = df['atr'] / df['close']
        
        return df
    
    def calculate_leverage(self, df_15m: pd.DataFrame, df_1h: pd.DataFrame, 
                          df_4h: pd.DataFrame, current_idx: int) -> int:
        """计算动态杠杆"""
        base_leverage = self.config['trading']['leverage']['default']
        max_leverage = self.config['trading']['leverage']['max']
        
        current_15m = df_15m.iloc[current_idx]
        current_1h = df_1h.iloc[-1] if len(df_1h) > 0 else None
        current_4h = df_4h.iloc[-1] if len(df_4h) > 0 else None
        
        leverage = base_leverage
        
        # 1. 趋势强度加分
        if current_1h is not None:
            trend_strength = abs(current_1h['ema_20'] - current_1h['ema_50']) / current_1h['close']
            if trend_strength > 0.005:  # 趋势明显
                leverage += 5
        
        # 2. 波动率调整
        volatility = current_15m['atr_percent']
        if volatility < 0.003:  # 低波动
            leverage += 10
        elif volatility > 0.01:  # 高波动
            leverage -= 10
        
        # 3. 成交量确认
        if current_15m['volume_ratio'] > 1.5:  # 成交量放大50%
            leverage += 5
        
        # 4. 多时间框架共振
        if (current_1h is not None and current_4h is not None and
            ((current_15m['ema_20'] > current_15m['ema_50'] and 
              current_1h['ema_20'] > current_1h['ema_50'] and
              current_4h['ema_20'] > current_4h['ema_50']) or
             (current_15m['ema_20'] < current_15m['ema_50'] and 
              current_1h['ema_20'] < current_1h['ema_50'] and
              current_4h['ema_20'] < current_4h['ema_50']))):
            leverage += 10
        
        # 限制在范围内
        leverage = max(self.config['trading']['leverage']['min'], 
                      min(max_leverage, leverage))
        
        return leverage
    
    def check_entry_conditions(self, df_15m: pd.DataFrame, df_1h: pd.DataFrame, 
                              df_4h: pd.DataFrame, current_idx: int) -> Tuple[Optional[str], float, str]:
        """检查入场条件（必须全部满足）"""
        conditions = []
        current_15m = df_15m.iloc[current_idx]
        prev_15m = df_15m.iloc[current_idx-1] if current_idx > 0 else None
        current_1h = df_1h.iloc[-1] if len(df_1h) > 0 else None
        current_4h = df_4h.iloc[-1] if len(df_4h) > 0 else None
        
        if prev_15m is None:
            return None, 0, "数据不足"
        
        # 条件1: 1小时趋势方向
        if current_1h is not None:
            if current_1h['ema_20'] > current_1h['ema_50']:
                trend_direction = 'LONG'
                conditions.append(('趋势', '多头', 0.3))
            elif current_1h['ema_20'] < current_1h['ema_50']:
                trend_direction = 'SHORT'
                conditions.append(('趋势', '空头', 0.3))
            else:
                return None, 0, "趋势不明"
        else:
            return None, 0, "缺少1小时数据"
        
        # 条件2: 15分钟入场信号
        signal_found = False
        signal_strength = 0
        signal_reason = ""
        
        # EMA交叉信号
        if (current_15m['ema_20'] > current_15m['ema_50'] and 
            prev_15m['ema_20'] <= prev_15m['ema_50'] and
            trend_direction == 'LONG'):
            signal_found = True
            signal_strength += 0.2
            signal_reason += "EMA金叉"
        
        elif (current_15m['ema_20'] < current_15m['ema_50'] and 
              prev_15m['ema_20'] >= prev_15m['ema_50'] and
              trend_direction == 'SHORT'):
            signal_found = True
            signal_strength += 0.2
            signal_reason += "EMA死叉"
        
        # MACD信号
        if (current_15m['macd'] > current_15m['macd_signal'] and 
            prev_15m['macd'] <= prev_15m['macd_signal'] and
            trend_direction == 'LONG'):
            signal_found = True
            signal_strength += 0.15
            signal_reason += "+MACD金叉"
        
        elif (current_15m['macd'] < current_15m['macd_signal'] and 
              prev_15m['macd'] >= prev_15m['macd_signal'] and
              trend_direction == 'SHORT'):
            signal_found = True
            signal_strength += 0.15
            signal_reason += "+MACD死叉"
        
        # 布林带突破
        if (current_15m['close'] > current_15m['bb_upper'] and 
            prev_15m['close'] <= prev_15m['bb_upper'] and
            trend_direction == 'LONG'):
            signal_found = True
            signal_strength += 0.15
            signal_reason += "+布林带上破"
        
        elif (current_15m['close'] < current_15m['bb_lower'] and 
              prev_15m['close'] >= prev_15m['bb_lower'] and
              trend_direction == 'SHORT'):
            signal_found = True
            signal_strength += 0.15
            signal_reason += "+布林带下破"
        
        if not signal_found:
            return None, 0, "无入场信号"
        
        conditions.append(('信号', signal_reason, signal_strength))
        
        # 条件3: 成交量确认 (必须放大50%+)
        if current_15m['volume_ratio'] >= 1.5:
            conditions.append(('成交量', f"放大{current_15m['volume_ratio']:.1f}倍", 0.2))
        else:
            return None, 0, f"成交量不足: {current_15m['volume_ratio']:.1f}倍"
        
        # 条件4: 关键价位突破 (简化版)
        bb_width = current_15m['bb_width']
        if bb_width > 0.02:  # 布林带宽度>2%，说明有波动空间
            conditions.append(('波动空间', f"布林带宽度{bb_width*100:.1f}%", 0.1))
        else:
            return None, 0, f"波动空间不足: {bb_width*100:.1f}%"
        
        # 条件5: RSI确认
        if trend_direction == 'LONG' and current_15m['rsi'] < 70:
            conditions.append(('RSI', f"{current_15m['rsi']:.1f}(未超买)", 0.1))
        elif trend_direction == 'SHORT' and current_15m['rsi'] > 30:
            conditions.append(('RSI', f"{current_15m['rsi']:.1f}(未超卖)", 0.1))
        else:
            rsi_status = "超买" if trend_direction == 'LONG' else "超卖"
            return None, 0, f"RSI{rsi_status}: {current_15m['rsi']:.1f}"
        
        # 计算总置信度
        total_confidence = sum(conf for _, _, conf in conditions)
        
        # 必须达到最低置信度
        if total_confidence >= 0.8:  # 80%置信度
            reason = " | ".join([f"{name}:{desc}" for name, desc, _ in conditions])
            return trend_direction, total_confidence, reason
        else:
            return None, 0, f"置信度不足: {total_confidence:.2f}"
    
    def calculate_position_size(self, capital: float, confidence: float, 
                               entry_price: float, stop_loss: float, 
                               leverage: int) -> float:
        """计算仓位大小"""
        base_position = self.config['trading']['position_sizing']['base_position']
        max_position = self.config['trading']['position_sizing']['max_position']
        
        # 基于置信度调整仓位
        confidence_factor = min(confidence / 0.8, 1.5)  # 最高1.5倍
        position_pct = min(base_position * confidence_factor, max_position)
        
        # 转换为合约数量 (BTC合约乘数为1)
        contract_size = 1
        position_usd = capital * position_pct * leverage
        position_size = position_usd / (entry_price * contract_size)
        
        # 确保满足最小交易量
        market = self.exchange.market(self.config['exchange']['symbol'])
        min_amount = market['limits']['amount']['min']
        
        if position_size < min_amount:
            position_size = min_amount
            logger.warning(f"⚠️ 仓位小于最小交易量，调整为: {position_size}")
        
        return position_size
    
    def run_backtest(self, data: Dict[str, pd.DataFrame], days: int = 30):
        """运行回测"""
        logger.info("🚀 开始精准高杠杆策略回测...")
        
        if '15m' not in data or '1h' not in data:
            logger.error