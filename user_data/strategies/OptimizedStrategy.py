# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

# --------------------------------
# Add your lib to import here
import ta as ta_lib
from freqtrade.persistence import Trade


class OptimizedStrategy(IStrategy):
    """
    优化的交易策略 - 结合多个技术指标
    1. RSI超买超卖
    2. 移动平均线交叉
    3. MACD信号
    4. 布林带突破
    5. 成交量确认
    """
    INTERFACE_VERSION = 3

    timeframe = '5m'

    can_short: bool = False

    # 优化的止盈参数
    minimal_roi = {
        "0": 0.15,      # 立即止盈15%
        "15": 0.10,     # 15分钟后止盈10%
        "30": 0.05,     # 30分钟后止盈5%
        "60": 0.02,     # 60分钟后止盈2%
        "120": 0        # 120分钟后平仓
    }

    # 止损设置
    stoploss = -0.08  # 8%止损

    # 追踪止损
    trailing_stop = True
    trailing_stop_positive = 0.05
    trailing_stop_positive_offset = 0.08
    trailing_only_offset_is_reached = True

    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 50  # 需要更多数据计算指标

    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }

    # 策略参数
    rsi_buy = IntParameter(25, 35, default=30, space="buy")
    rsi_sell = IntParameter(65, 75, default=70, space="sell")
    macd_fast = IntParameter(10, 15, default=12, space="buy")
    macd_slow = IntParameter(20, 26, default=26, space="buy")
    macd_signal = IntParameter(7, 10, default=9, space="buy")
    bb_period = IntParameter(18, 22, default=20, space="buy")
    bb_std = DecimalParameter(1.8, 2.2, default=2.0, space="buy")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI指标
        dataframe['rsi'] = ta_lib.momentum.rsi(dataframe['close'], window=14)
        
        # 移动平均线
        dataframe['sma_fast'] = dataframe['close'].rolling(window=20).mean()
        dataframe['sma_slow'] = dataframe['close'].rolling(window=50).mean()
        dataframe['ema_fast'] = dataframe['close'].ewm(span=12).mean()
        dataframe['ema_slow'] = dataframe['close'].ewm(span=26).mean()
        
        # MACD指标
        macd = ta_lib.trend.macd(dataframe['close'], window_slow=26, window_fast=12, window_sign=9)
        dataframe['macd'] = macd
        dataframe['macd_signal'] = ta_lib.trend.macd_signal(dataframe['close'], window_slow=26, window_fast=12, window_sign=9)
        dataframe['macd_diff'] = ta_lib.trend.macd_diff(dataframe['close'], window_slow=26, window_fast=12, window_sign=9)
        
        # 布林带
        bb_period = self.bb_period.value
        bb_std = self.bb_std.value
        dataframe['bb_upper'] = ta_lib.volatility.bollinger_hband(dataframe['close'], window=bb_period, window_dev=bb_std)
        dataframe['bb_middle'] = dataframe['close'].rolling(window=bb_period).mean()
        dataframe['bb_lower'] = ta_lib.volatility.bollinger_lband(dataframe['close'], window=bb_period, window_dev=bb_std)
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_middle']
        
        # 成交量指标
        dataframe['volume_sma'] = dataframe['volume'].rolling(window=20).mean()
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']
        
        # ATR指标（波动率）
        dataframe['atr'] = ta_lib.volatility.average_true_range(dataframe['high'], dataframe['low'], dataframe['close'], window=14)
        
        # 价格位置指标
        dataframe['price_position'] = (dataframe['close'] - dataframe['bb_lower']) / (dataframe['bb_upper'] - dataframe['bb_lower'])
        
        # 趋势强度指标
        dataframe['trend_strength'] = abs(dataframe['sma_fast'] - dataframe['sma_slow']) / dataframe['atr']
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        多条件买入信号：
        1. RSI超卖
        2. 价格在布林带下轨附近
        3. MACD金叉或即将金叉
        4. 成交量放大确认
        5. 短期均线上穿长期均线
        """
        dataframe.loc[
            (
                # RSI条件
                (dataframe['rsi'] < self.rsi_buy.value) &
                
                # 价格位置条件（在布林带下轨附近）
                (dataframe['price_position'] < 0.2) &
                
                # MACD条件（金叉或即将金叉）
                ((dataframe['macd'] > dataframe['macd_signal']) | 
                 ((dataframe['macd'] < dataframe['macd_signal']) & 
                  (dataframe['macd'].shift(1) > dataframe['macd_signal'].shift(1)))) &
                
                # 成交量确认
                (dataframe['volume_ratio'] > 1.2) &
                
                # 趋势条件（短期均线上穿长期均线）
                (dataframe['sma_fast'] > dataframe['sma_slow']) &
                
                # 波动率过滤（避免高波动期）
                (dataframe['atr'] / dataframe['close'] < 0.02) &
                
                # 趋势强度过滤
                (dataframe['trend_strength'] > 0.5) &
                
                # 确保有成交量
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        多条件卖出信号：
        1. RSI超买
        2. 价格在布林带上轨附近
        3. MACD死叉或即将死叉
        4. 成交量萎缩
        5. 短期均线下穿长期均线
        """
        dataframe.loc[
            (
                # RSI条件
                (dataframe['rsi'] > self.rsi_sell.value) &
                
                # 价格位置条件（在布林带上轨附近）
                (dataframe['price_position'] > 0.8) &
                
                # MACD条件（死叉或即将死叉）
                ((dataframe['macd'] < dataframe['macd_signal']) | 
                 ((dataframe['macd'] > dataframe['macd_signal']) & 
                  (dataframe['macd'].shift(1) < dataframe['macd_signal'].shift(1)))) &
                
                # 成交量确认
                (dataframe['volume_ratio'] < 0.8) &
                
                # 趋势条件（短期均线下穿长期均线）
                (dataframe['sma_fast'] < dataframe['sma_slow']) &
                
                # 确保有成交量
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1

        return dataframe

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                           proposed_stake: float, min_stake: Optional[float], max_stake: float,
                           leverage: float, entry_tag: Optional[str], side: str,
                           **kwargs) -> float:
        """
        自定义仓位管理：根据ATR调整仓位大小
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        
        if len(dataframe) > 0:
            current_atr = dataframe['atr'].iloc[-1]
            current_price = dataframe['close'].iloc[-1]
            
            # 根据波动率调整仓位：波动率越高，仓位越小
            atr_ratio = current_atr / current_price
            
            if atr_ratio < 0.01:
                # 低波动，正常仓位
                stake_multiplier = 1.0
            elif atr_ratio < 0.02:
                # 中等波动，减少仓位
                stake_multiplier = 0.7
            else:
                # 高波动，大幅减少仓位
                stake_multiplier = 0.4
            
            adjusted_stake = proposed_stake * stake_multiplier
            
            # 确保在最小和最大限制内
            if min_stake is not None:
                adjusted_stake = max(adjusted_stake, min_stake)
            adjusted_stake = min(adjusted_stake, max_stake)
            
            return adjusted_stake
        
        return proposed_stake