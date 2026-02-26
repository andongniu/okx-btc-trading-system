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


class SampleStrategy(IStrategy):
    """
    Simple sample strategy for demonstration.
    """
    INTERFACE_VERSION = 3

    timeframe = '5m'

    can_short: bool = False

    minimal_roi = {
        "0": 0.10,
        "30": 0.05,
        "60": 0.02,
        "120": 0
    }

    stoploss = -0.10

    trailing_stop = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = False

    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 30

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

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI using ta library
        dataframe['rsi'] = ta_lib.momentum.rsi(dataframe['close'], window=14)

        # Moving Averages using pandas rolling
        dataframe['sma20'] = dataframe['close'].rolling(window=20).mean()
        dataframe['sma50'] = dataframe['close'].rolling(window=50).mean()

        # Bollinger Bands using ta library
        bb = ta_lib.volatility.bollinger_hband_indicator(dataframe['close'], window=20, window_dev=2)
        dataframe['bb_upperband'] = ta_lib.volatility.bollinger_hband(dataframe['close'], window=20, window_dev=2)
        dataframe['bb_middleband'] = dataframe['close'].rolling(window=20).mean()
        dataframe['bb_lowerband'] = ta_lib.volatility.bollinger_lband(dataframe['close'], window=20, window_dev=2)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] < 30) &
                (dataframe['close'] < dataframe['sma20']) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] > 70) &
                (dataframe['close'] > dataframe['sma20']) &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1

        return dataframe