// 自主交易监控面板 JavaScript

let updateInterval = null;

// 更新系统状态
function updateSystemStatus(strategy) {
    const status = strategy.status || 'waiting_for_signal';
    const statusMap = {
        'waiting_for_signal': '等待信号',
        'position_open': '持仓中',
        'signal_generated': '信号生成'
    };
    
    document.getElementById('strategyStatus').textContent = statusMap[status] || status;
    
    // 更新策略状态显示
    const systemStatus = document.getElementById('systemStatus');
    if (status === 'position_open') {
        systemStatus.className = 'strategy-status strategy-position';
        systemStatus.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 10px;">持仓中</div>
            <div style="color: #666; font-size: 0.9em;">系统正在监控持仓...</div>
        `;
    } else if (status === 'signal_generated') {
        systemStatus.className = 'strategy-status strategy-signal';
        systemStatus.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 10px;">信号生成</div>
            <div style="color: #666; font-size: 0.9em;">系统已生成交易信号...</div>
        `;
    } else {
        systemStatus.className = 'strategy-status strategy-waiting';
        systemStatus.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 10px;">等待交易信号</div>
            <div style="color: #666; font-size: 0.9em;">系统正在分析市场数据...</div>
        `;
    }
    
    // 更新策略统计
    document.getElementById('dailyTrades').textContent = strategy.daily_trades || 0;
    document.getElementById('consecutiveWins').textContent = strategy.consecutive_wins || 0;
    document.getElementById('consecutiveLosses').textContent = strategy.consecutive_losses || 0;
}

// 更新仪表盘数据
async function updateDashboard() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // 更新系统状态
        document.getElementById('uptime').textContent = data.system_info.uptime || '00:00:00';
        document.getElementById('totalTrades').textContent = data.system_info.total_trades || 0;
        document.getElementById('winRate').textContent = `${(data.system_info.win_rate || 0).toFixed(1)}%`;
        document.getElementById('lastUpdate').textContent = new Date(data.last_update).toLocaleTimeString();
        
        // 更新账户信息
        document.getElementById('totalBalance').textContent = `$${(data.account.total_balance || 0).toFixed(2)}`;
        document.getElementById('availableBalance').textContent = `$${(data.account.available_balance || 0).toFixed(2)}`;
        document.getElementById('usedBalance').textContent = `$${(data.account.used_balance || 0).toFixed(2)}`;
        document.getElementById('equity').textContent = `$${(data.account.equity || 0).toFixed(2)}`;
        
        // 更新市场数据
        document.getElementById('btcPrice').textContent = `$${(data.market.btc_price || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        
        const change = data.market.btc_change || 0;
        const changeClass = change >= 0 ? 'positive' : 'negative';
        document.getElementById('btcChange').className = `value ${changeClass}`;
        document.getElementById('btcChange').textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
        
        // 翻译趋势
        const trendMap = {
            'bullish': '上涨',
            'bearish': '下跌',
            'neutral': '中性'
        };
        document.getElementById('marketTrend').textContent = trendMap[data.market.trend] || data.market.trend || '中性';
        document.getElementById('marketUpdate').textContent = new Date(data.market.timestamp).toLocaleTimeString();
        
        // 更新持仓
        updatePositions(data.positions);
        
        // 更新交易记录
        updateTrades(data.trade_history);
        
        // 更新策略状态
        updateSystemStatus(data.strategy);
        
        // 更新最后刷新时间
        document.getElementById('lastRefresh').textContent = new Date().toLocaleTimeString();
        
    } catch (error) {
        console.error('更新仪表盘失败:', error);
        showAlert('数据更新失败，请检查网络连接', 'warning');
    }
}

// 显示警报
function showAlert(message, type = 'info') {
    const container = document.getElementById('strategyAlerts');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert-box alert-${type}`;
    alertDiv.innerHTML = `
        <div>${message}</div>
        <div style="font-size: 0.8em;">${new Date().toLocaleTimeString()}</div>
    `;
    container.insertBefore(alertDiv, container.firstChild);
    
    // 限制最多显示3条警报
    if (container.children.length > 3) {
        container.removeChild(container.lastChild);
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始更新
    updateDashboard();
    
    // 每5秒自动更新
    updateInterval = setInterval(updateDashboard, 5000);
    
    showAlert('自主交易监控面板加载完成', 'info');
});

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});