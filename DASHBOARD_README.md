# 🚀 Freqtrade 交易系统面板

这是一个完整的交易系统监控面板，提供实时数据可视化、策略分析、风险监控等功能。

## 📋 功能特性

### 1. **系统概览**
- 实时显示系统状态（运行中/等待API/已停止）
- 交易所和交易对信息
- 资金余额和收益率
- 交易统计（总交易次数、胜率等）

### 2. **策略信息**
- 当前使用的策略详情
- 策略参数配置
- 买入/卖出条件
- 技术指标列表

### 3. **资金曲线**
- 实时资金变化图表
- 支持时间缩放
- 鼠标悬停查看详细数据
- 收益/亏损区域高亮显示

### 4. **交易统计**
- 胜率分析
- 平均盈利/亏损
- 盈亏比
- 最大回撤
- 夏普比率

### 5. **最近交易**
- 实时交易记录
- 买入/卖出标记
- 价格和仓位信息
- 时间戳显示

### 6. **风险指标**
- 策略健康度评估
- 风险提示
- 建议操作
- 性能警告

## 🚀 快速启动

### 方法一：使用启动脚本（推荐）
```bash
# 进入项目目录
cd /Users/anth6iu/freqtrade-trading

# 给脚本执行权限（首次运行）
chmod +x start_dashboard.sh

# 启动面板
./start_dashboard.sh
```

### 方法二：手动启动
```bash
# 进入项目目录
cd /Users/anth6iu/freqtrade-trading

# 激活虚拟环境
source venv/bin/activate

# 启动服务器
python3 dashboard_server.py
```

## 🌐 访问面板

启动成功后，在浏览器中访问：
```
http://localhost:8080/trading_dashboard.html
```

## 📊 API接口

面板提供以下API接口：

| 接口 | 描述 | 示例 |
|------|------|------|
| `/api/system-status` | 系统状态 | `http://localhost:8080/api/system-status` |
| `/api/backtest-results` | 回测结果 | `http://localhost:8080/api/backtest-results` |
| `/api/config` | 配置文件 | `http://localhost:8080/api/config` |
| `/api/strategy` | 策略信息 | `http://localhost:8080/api/strategy` |
| `/api/recent-trades` | 最近交易 | `http://localhost:8080/api/recent-trades` |
| `/api/equity-curve` | 资金曲线 | `http://localhost:8080/api/equity-curve` |

## 🔧 配置文件

### 主要配置文件
- `config/okx_backtest_config.json` - OKX回测配置
- `config/okx_futures_config.json` - OKX永续合约配置
- `config/simple_config.json` - 简单配置（已停用）

### 策略文件
- `user_data/strategies/SampleStrategy.py` - 交易策略

## 📈 数据文件

### 回测数据
- `backtest_results.json` - 回测结果数据
- `okx_btc_perpetual_5m.csv` - OKX历史数据（30天）

### 面板文件
- `trading_dashboard.html` - 主面板页面
- `dashboard_server.py` - 服务器程序
- `start_dashboard.sh` - 启动脚本

## 🛠️ 自定义配置

### 修改服务器端口
编辑 `dashboard_server.py`，修改第148行：
```python
def start_server(port=8080):  # 修改这里的端口号
```

### 添加新的API接口
在 `dashboard_server.py` 的 `TradingDashboardHandler` 类中添加新的 `do_GET` 分支。

### 修改面板样式
编辑 `trading_dashboard.html` 中的CSS部分。

## ⚠️ 注意事项

1. **API密钥**：面板目前处于等待API密钥状态，需要用户提供OKX API密钥后才能启动实时交易。

2. **回测数据**：当前显示的是模拟回测数据，实际数据需要运行回测脚本生成。

3. **网络代理**：系统配置了代理 `http://127.0.0.1:7897`，确保代理服务正常运行。

4. **虚拟环境**：建议在虚拟环境中运行，确保依赖包版本兼容。

5. **浏览器兼容**：建议使用Chrome或Firefox最新版本访问。

## 🔄 数据更新

面板每30秒自动刷新一次数据，包括：
- 系统状态
- 交易记录
- 资金曲线
- 统计信息

## 🎯 下一步计划

1. **实时交易集成**：连接OKX API，实现实时交易监控
2. **策略优化界面**：提供策略参数优化工具
3. **多策略支持**：支持同时监控多个交易策略
4. **报警系统**：价格预警、风险报警等功能
5. **移动端适配**：优化移动设备显示

## 🆘 故障排除

### 问题：无法访问面板
- 检查端口8080是否被占用
- 检查防火墙设置
- 确认Python服务器已启动

### 问题：API数据不显示
- 检查回测结果文件是否存在
- 确认虚拟环境已激活
- 查看浏览器控制台错误信息

### 问题：图表不显示
- 检查网络连接，确保能访问CDN
- 更新浏览器到最新版本
- 清除浏览器缓存

## 📞 支持

如有问题，请检查：
1. 服务器日志输出
2. 浏览器开发者工具控制台
3. 系统依赖包版本

---

**最后更新**：2026-02-24  
**版本**：1.0.0  
**状态**：开发中