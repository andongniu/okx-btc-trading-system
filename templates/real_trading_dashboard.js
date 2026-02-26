// 真实交易监控面板 JavaScript

let updateInterval = null;

// 更新持仓显示
function updatePositions(positions) {
    const container = document.getElementById('positionsContainer');
    
    if (!positions || positions.length === 0) {
        container.innerHTML = '<div style="color: #666; text-align: center; padding: 20px;">无持仓</div>';
        return;
    }
    
    let html = '';
    positions.forEach(pos => {
        const btcAmount = pos.btc_amount || (pos.contracts * 0.01);
        const pnl = pos.unrealized_pnl || 0;
        const pnlClass = pnl >= 0 ? 'positive' : 'negative';
        const pnlSign = pnl >= 0 ? '+' : '';
        const positionClass = pos.side === 'long' ? 'position-long' : 'position-short';
        
        html += `
            <div class="position-item ${positionClass}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${pos.side === 'long' ? '📈 多头' : '📉 空头'}</strong>
                        <div style="font-size: 0.9em; color: #666;">
                            ${pos.contracts} 张合约 (${btcAmount.toFixed(4)} BTC)
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div class="${pnlClass}" style="font-weight: bold;">
                            ${pnlSign}$${pnl.toFixed(4)}
                        </div>
                        <div style="font-size: 0.9em; color: #666;">
                            杠杆: ${pos.leverage || 1}x
                        </div>
                    </div>
                </div>
                <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                    <div>入场价: $${pos.entry_price.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    <div>当前价: $${pos.current_price.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    <div>保证金: $${(pos.margin || 0).toFixed(2)}</div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// 更新交易记录
function updateTrades(trades) {
    const container = document.getElementById('tradesContainer');
    
    if (!trades || trades.length === 0) {
        container.innerHTML = '<div style="color: #666; text-align: center; padding: 20px;">无交易记录</div>';
        return;
    }
    
    let html = '';
    trades.slice(0, 10).forEach(trade => {
        const btcAmount = trade.btc_amount || (trade.contracts * 0.01);
        const pnl = trade.pnl || 0;
        const tradeClass = pnl > 0 ? 'trade-profit' : pnl < 0 ? 'trade-loss' : '';
        
        html += `
            <div class="trade-item ${tradeClass}">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <strong>${trade.direction === 'LONG' ? '买入' : trade.direction === 'SHORT' ? '卖出' : '平仓'}</strong>
                        <div style="font-size: 0.8em; color: #666;">${trade.time}</div>
                    </div>
                    <div style="text-align: right;">
                        <div>${trade.contracts} 张</div>
                        <div style="font-size: 0.8em; color: #666;">${trade.leverage || 1}x</div>
                    </div>
                </div>
                <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                    ${btcAmount.toFixed(4)} BTC | ${trade.status || '已执行'}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// 更新警报
function updateAlerts(alerts) {
    const container = document.getElementById('alertsContainer');
    
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<div class="alert-item alert-info">无系统消息</div>';
        return;
    }
    
    let html = '';
    alerts.slice(0, 5).forEach(alert => {
        const alertClass = `alert-${alert.level}`;
        html += `
            <div class="alert-item ${alertClass}">
                <div><strong>${alert.time}</strong> - ${alert.message}</div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// 更新仪表盘数据
async function updateDashboard() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // 更新状态徽章
        const statusMap = {
            'ready': 'status-ready',
            'trading': 'status-trading',
            'paused': 'status-paused',
            'stopped': 'status-stopped'
        };
        
        const badge = document.getElementById('statusBadge');
        badge.className = `status-badge ${statusMap[data.system_status] || 'status-ready'}`;
        badge.textContent = `状态: ${data.system_status === 'ready' ? '准备就绪' : 
                            data.system_status === 'trading' ? '交易中' : 
                            data.system_status === 'paused' ? '已暂停' : '已停止'}`;
        
        // 更新资金信息
        document.getElementById('currentCapital').textContent = `$${data.capital.toFixed(2)}`;
        document.getElementById('dailyPnl').textContent = `$${data.daily_pnl.toFixed(2)}`;
        document.getElementById('totalPnl').textContent = `$${data.total_pnl.toFixed(2)}`;
        
        // 更新市场数据
        document.getElementById('btcPrice').textContent = `$${data.market_data.btc_price.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        const changeClass = data.market_data.btc_change >= 0 ? 'positive' : 'negative';
        document.getElementById('btcChange').className = `value ${changeClass}`;
        document.getElementById('btcChange').textContent = `${data.market_data.btc_change >= 0 ? '+' : ''}${data.market_data.btc_change.toFixed(2)}%`;
        document.getElementById('updateTime').textContent = new Date(data.market_data.timestamp).toLocaleTimeString();
        
        // 更新风险指标
        document.getElementById('winRate').textContent = `${data.risk_indicators.win_rate.toFixed(1)}%`;
        document.getElementById('profitFactor').textContent = data.risk_indicators.profit_factor.toFixed(2);
        document.getElementById('maxDrawdown').textContent = `${data.risk_indicators.max_drawdown.toFixed(1)}%`;
        document.getElementById('riskExposure').textContent = `${(data.risk_indicators.risk_exposure * 100).toFixed(1)}%`;
        
        // 更新进度条
        const progress = ((data.capital - 200) / 200) * 100;
        const progressFill = document.getElementById('progressFill');
        progressFill.style.width = `${Math.max(0, Math.min(100, progress))}%`;
        progressFill.textContent = `${progress.toFixed(1)}%`;
        
        // 更新持仓
        updatePositions(data.positions);
        
        // 更新交易记录
        updateTrades(data.recent_trades);
        
        // 更新警报
        updateAlerts(data.alerts);
        
        // 更新最后刷新时间
        document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        
        // 更新按钮状态
        updateButtonStates(data.system_status);
        
    } catch (error) {
        console.error('更新仪表盘失败:', error);
        addAlert('数据更新失败，请检查网络连接', 'error');
    }
}

// 更新按钮状态
function updateButtonStates(systemStatus) {
    const isTrading = systemStatus === 'trading';
    const isReady = systemStatus === 'ready';
    
    // 交易控制按钮
    document.getElementById('btnLong').disabled = !isTrading;
    document.getElementById('btnShort').disabled = !isTrading;
    document.getElementById('btnClose').disabled = !isTrading;
    document.getElementById('btnTest').disabled = !isTrading;
    
    // 系统控制按钮
    document.getElementById('btnStart').disabled = !isReady;
    document.getElementById('btnStop').disabled = !isTrading;
}

// 添加警报
function addAlert(message, type = 'info') {
    const container = document.getElementById('alertsContainer');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert-item alert-${type}`;
    alertDiv.innerHTML = `
        <div><strong>${new Date().toLocaleTimeString()}</strong> - ${message}</div>
    `;
    container.insertBefore(alertDiv, container.firstChild);
    
    // 限制最多显示5条警报
    if (container.children.length > 5) {
        container.removeChild(container.lastChild);
    }
}

// 系统控制函数
async function startTrading() {
    try {
        const response = await fetch('/api/start_trading', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        addAlert(result.message, 'success');
        updateDashboard();
    } catch (error) {
        addAlert(`启动交易失败: ${error.message}`, 'error');
    }
}

async function stopTrading() {
    try {
        const response = await fetch('/api/stop_trading', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        addAlert(result.message, 'warning');
        updateDashboard();
    } catch (error) {
        addAlert(`暂停交易失败: ${error.message}`, 'error');
    }
}

async function emergencyStop() {
    if (!confirm('确定要紧急停止吗？这将平掉所有持仓！')) {
        return;
    }
    
    try {
        const response = await fetch('/api/emergency_stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        addAlert(result.message, 'critical');
        updateDashboard();
    } catch (error) {
        addAlert(`紧急停止失败: ${error.message}`, 'error');
    }
}

// 交易执行函数
async function executeTrade(direction) {
    const contracts = parseFloat(document.getElementById('contractsInput').value);
    const leverage = parseInt(document.getElementById('leverageSelect').value);
    
    if (contracts < 0.01) {
        addAlert('合约数量不能小于0.01张', 'error');
        return;
    }
    
    if (!confirm(`确认${direction === 'LONG' ? '买入开多' : '卖出开空'} ${contracts}张合约，使用${leverage}倍杠杆？`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/execute_trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ direction, contracts, leverage })
        });
        const result = await response.json();
        
        if (result.status === 'executed') {
            addAlert(result.message, 'success');
        } else {
            addAlert(result.message, 'error');
        }
        
        updateDashboard();
    } catch (error) {
        addAlert(`交易执行失败: ${error.message}`, 'error');
    }
}

async function closePositions() {
    if (!confirm('确定要平掉所有持仓吗？')) {
        return;
    }
    
    try {
        const response = await fetch('/api/close_positions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        
        if (result.status === 'closed') {
            addAlert(result.message, 'success');
        } else {
            addAlert(result.message, 'error');
        }
        
        updateDashboard();
    } catch (error) {
        addAlert(`平仓失败: ${error.message}`, 'error');
    }
}

async function testTrade() {
    if (!confirm('执行测试交易（最小交易量，5倍杠杆）？')) {
        return;
    }
    
    try {
        const response = await fetch('/api/test_small_trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        
        if (result.status === 'test_executed') {
            addAlert(result.message, 'success');
        } else {
            addAlert(result.message, 'error');
        }
        
        updateDashboard();
    } catch (error) {
        addAlert(`测试交易失败: ${error.message}`, 'error');
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始更新
    updateDashboard();
    
    // 每5秒自动更新
    updateInterval = setInterval(updateDashboard, 5000);
    
    addAlert('真实交易监控面板加载完成', 'info');
});

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});
