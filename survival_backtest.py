#!/usr/bin/env python3
"""
生存策略回测系统
使用过去30天数据测试200U→1000U策略
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SurvivalBacktest:
    """生存策略回测引擎"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.exchange = self._init_exchange()
        self.capital = self.config['meta']['initial_capital']
        self.initial_capital = self.capital
        self.positions = []
        self.trade_history = []
        self.equity_curve = [self.capital]
        self.dates = []
        
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
    
    def fetch_historical_data(self, days: int = 30) -> pd.DataFrame:
        """获取历史K线数据"""
        logger.info(f"📊 获取过去{days}天历史数据...")
        
        symbol = self.config['exchange']['symbol']
        timeframe = self.config['trading']['base_timeframe']
        
        # 计算开始时间
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 获取数据
        all_ohlcv = []
        current_time = start_time
        
        while current_time < end_time:
            try:
                since = int(current_time.timestamp() * 1000)
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, 
                    timeframe, 
                    since=since, 
                    limit=1000
                )
                
                if not ohlcv:
                    break
                    
                all_ohlcv.extend(ohlcv)
                current_time = datetime.fromtimestamp(ohlcv[-1][0] / 1000)
                
                logger.info(f"  已获取: {len(all_ohlcv)} 根K线")
                
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break
        
        # 转换为DataFrame
        df = pd.DataFrame(
            all_ohlcv, 
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        logger.info(f"✅ 数据获取完成: {len(df)} 根K线")
        logger.info(f"  时间范围: {df.index[0]} 至 {df.index[-1]}")
        logger.info(f"  最新价格: ${df['close'].iloc[-1]:,.2f}")
        
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        logger.info("📈 计算技术指标...")
        
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
        
        logger.info("✅ 指标计算完成")
        return df
    
    def generate_signal(self, row: pd.Series, prev_row: pd.Series) -> Tuple[str, float, str]:
        """生成交易信号"""
        signals = []
        
        # 趋势动量信号
        # EMA金叉/死叉
        if row['ema_20'] > row['ema_50'] and prev_row['ema_20'] <= prev_row['ema_50']:
            signals.append(('LONG', 0.7, 'EMA金叉(20>50)'))
        elif row['ema_20'] < row['ema_50'] and prev_row['ema_20'] >= prev_row['ema_50']:
            signals.append(('SHORT', 0.7, 'EMA死叉(20<50)'))
        
        # MACD信号
        if row['macd'] > row['macd_signal'] and prev_row['macd'] <= prev_row['macd_signal']:
            signals.append(('LONG', 0.6, 'MACD上穿信号线'))
        elif row['macd'] < row['macd_signal'] and prev_row['macd'] >= prev_row['macd_signal']:
            signals.append(('SHORT', 0.6, 'MACD下穿信号线'))
        
        # RSI超买超卖
        if row['rsi'] < 30:
            signals.append(('LONG', 0.5, f'RSI超卖({row["rsi"]:.1f})'))
        elif row['rsi'] > 70:
            signals.append(('SHORT', 0.5, f'RSI超买({row["rsi"]:.1f})'))
        
        # 布林带触碰
        if row['close'] <= row['bb_lower']:
            signals.append(('LONG', 0.65, f'触及布林带下轨'))
        elif row['close'] >= row['bb_upper']:
            signals.append(('SHORT', 0.65, f'触及布林带上轨'))
        
        if not signals:
            return ('FLAT', 0, '无信号')
        
        # 选择置信度最高的信号
        best_signal = max(signals, key=lambda x: x[1])
        return best_signal
    
    def calculate_position_size(self, capital: float, signal_conf: float, 
                               entry_price: float, stop_loss: float, 
                               leverage: int = 10) -> float:
        """计算仓位大小"""
        base_position = self.config['trading']['position_sizing']['base_position']
        max_position = self.config['trading']['position_sizing']['max_position']
        
        # 凯利公式简化版
        kelly_fraction = min(signal_conf * 0.5, max_position)
        
        # 风险限制
        risk_per_trade = abs(entry_price - stop_loss) / entry_price
        max_risk_position = self.config['risk_management']['stop_loss']['initial'] / risk_per_trade
        
        position_size = min(kelly_fraction, max_risk_position, base_position * (1 + signal_conf))
        
        # 转换为合约数量
        contract_size = 1  # BTC合约乘数为1
        return (capital * position_size * leverage) / (entry_price * contract_size)
    
    def run_backtest(self, df: pd.DataFrame):
        """运行回测"""
        logger.info("🚀 开始回测...")
        
        position = None
        entry_price = 0
        entry_time = None
        position_size = 0
        direction = 'FLAT'
        leverage = 10
        
        for i in range(1, len(df)):
            current_row = df.iloc[i]
            prev_row = df.iloc[i-1]
            current_time = df.index[i]
            
            # 生成信号
            signal, confidence, reason = self.generate_signal(current_row, prev_row)
            
            # 如果有持仓，检查止损止盈
            if position:
                current_price = current_row['close']
                
                # 计算止损止盈
                if direction == 'LONG':
                    stop_loss = entry_price * (1 - 0.03)  # 3%止损
                    take_profit = entry_price * (1 + 0.06)  # 6%止盈
                    
                    # 检查止损
                    if current_price <= stop_loss:
                        pnl = (current_price - entry_price) * position_size
                        self.close_position(current_time, current_price, pnl, '止损触发')
                        position = None
                    
                    # 检查止盈
                    elif current_price >= take_profit:
                        pnl = (current_price - entry_price) * position_size
                        self.close_position(current_time, current_price, pnl, '止盈触发')
                        position = None
                
                else:  # SHORT
                    stop_loss = entry_price * (1 + 0.03)
                    take_profit = entry_price * (1 - 0.06)
                    
                    if current_price >= stop_loss:
                        pnl = (entry_price - current_price) * position_size
                        self.close_position(current_time, current_price, pnl, '止损触发')
                        position = None
                    
                    elif current_price <= take_profit:
                        pnl = (entry_price - current_price) * position_size
                        self.close_position(current_time, current_price, pnl, '止盈触发')
                        position = None
            
            # 如果没有持仓，检查开仓信号
            if not position and signal != 'FLAT' and confidence > 0.6:
                # 计算动态杠杆
                volatility = current_row['atr'] / current_row['close']
                if volatility < 0.005:
                    leverage = min(15, self.config['trading']['leverage']['max'])
                elif volatility < 0.01:
                    leverage = min(10, self.config['trading']['leverage']['max'])
                else:
                    leverage = self.config['trading']['leverage']['min']
                
                # 计算止损
                atr = current_row['atr']
                if signal == 'LONG':
                    stop_loss_price = current_row['close'] - (atr * 1.5)
                else:
                    stop_loss_price = current_row['close'] + (atr * 1.5)
                
                # 计算仓位
                position_size = self.calculate_position_size(
                    self.capital, confidence, 
                    current_row['close'], stop_loss_price, 
                    leverage
                )
                
                # 开仓
                position = {
                    'direction': signal,
                    'entry_price': current_row['close'],
                    'entry_time': current_time,
                    'position_size': position_size,
                    'leverage': leverage,
                    'stop_loss': stop_loss_price,
                    'reason': reason
                }
                
                self.trade_history.append({
                    'time': current_time,
                    'type': 'OPEN',
                    'direction': signal,
                    'price': current_row['close'],
                    'size': position_size,
                    'leverage': leverage,
                    'reason': reason
                })
                
                logger.debug(f"开仓: {signal} @ ${current_row['close']:,.0f} | 杠杆: {leverage}x | 理由: {reason}")
            
            # 记录资金曲线
            if position:
                # 计算浮动盈亏
                if direction == 'LONG':
                    unrealized_pnl = (current_row['close'] - entry_price) * position_size
                else:
                    unrealized_pnl = (entry_price - current_row['close']) * position_size
                
                current_equity = self.capital + unrealized_pnl
            else:
                current_equity = self.capital
            
            self.equity_curve.append(current_equity)
            self.dates.append(current_time)
        
        logger.info("✅ 回测完成")
    
    def close_position(self, time, price, pnl, reason):
        """平仓"""
        self.capital += pnl
        
        self.trade_history.append({
            'time': time,
            'type': 'CLOSE',
            'price': price,
            'pnl': pnl,
            'reason': reason
        })
        
        logger.debug(f"平仓: ${price:,.0f} | PNL: ${pnl:+.2f} | 理由: {reason}")
    
    def calculate_metrics(self):
        """计算回测指标"""
        logger.info("📊 计算回测指标...")
        
        # 提取交易记录
        trades = [t for t in self.trade_history if t['type'] == 'CLOSE']
        
        if not trades:
            logger.warning("⚠️ 没有交易记录")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'final_capital': self.capital,
                'total_return': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }
        
        # 基础指标
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]
        
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        
        # 计算最大回撤
        equity_array = np.array(self.equity_curve)
        peak = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - peak) / peak
        max_drawdown = np.min(drawdown)
        
        # 计算夏普比率 (简化版)
        returns = np.diff(equity_array) / equity_array[:-1]
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(365) if len(returns) > 1 else 0
        
        metrics = {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades) * 100,
            'total_pnl': total_pnl,
            'final_capital': self.capital,
            'total_return': total_return * 100,
            'max_drawdown': max_drawdown * 100,
            'sharpe_ratio': sharpe_ratio,
            'avg_win': np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0,
            'avg_loss': np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0,
            'profit_factor': abs(sum(t['pnl'] for t in winning_trades) / 
                               sum(t['pnl'] for t in losing_trades)) if losing_trades else float('inf')
        }
        
        return metrics
    
    def plot_results(self, df: pd.DataFrame, metrics: Dict):
        """绘制回测结果图表"""
        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        
        # 价格和信号图
        ax1 = axes[0]
        ax1.plot(df.index, df['close'], label='BTC价格', linewidth=1)
        ax1.plot(df.index, df['ema_20'], label='EMA20', alpha=0.7, linewidth=0.8)
        ax1.plot(df.index, df['ema_50'], label='EMA50', alpha=0.7, linewidth=0.8)
        ax1.fill_between(df.index, df['bb_lower'], df['bb_upper'], alpha=0.2, label='布林带')
        
        # 标记交易
        for trade in self.trade_history:
            if trade['type'] == 'OPEN':
                color = 'green' if trade['direction'] == 'LONG' else 'red'
                marker = '^' if trade['direction'] == 'LONG' else 'v'
                ax1.scatter(trade['time'], trade['price'], color=color, marker=marker, s=50)
        
        ax1.set_title('BTC价格与交易信号')
        ax1.set_ylabel('价格 ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # RSI图
        ax2 = axes[1]
        ax2.plot(df.index, df['rsi'], label='RSI', linewidth=1)
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='超买线')
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='超卖线')