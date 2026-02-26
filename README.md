# 🚀 OKX BTC超快交易系统

基于OpenClaw的自动化BTC交易系统，采用10秒频率实时监控市场，实现自主交易决策。

## ✨ 特性

- ⚡ **10秒超快频率** - 实时响应市场变化
- 🤖 **完全自主** - 自动分析、决策、执行
- 📊 **实时监控** - Web面板实时显示状态
- 📱 **Telegram通知** - 交易事件即时通知
- 🔒 **多层风控** - 动态止损止盈，风险控制
- 🎯 **多策略融合** - 趋势跟踪 + 均值回归 + 突破策略

## 📁 项目结构

```
okx-btc-trading-system/
├── 📁 config/                    # 配置文件
│   ├── final_config.json.template  # API配置模板
│   └── telegram_config.json.template
├── 📁 logs/                     # 日志文件 (git忽略)
├── 📁 templates/                # HTML模板
├── 📄 ultra_fast_trader.py     # 10秒频率交易系统
├── 📄 trade_notifier.py        # Telegram通知器
├── 📄 working_monitor.py       # 监控面板 (端口8084)
├── 📄 requirements.txt         # Python依赖
├── 📄 setup.sh                 # 一键安装脚本
├── 📄 start.sh                 # 启动脚本
├── 📄 stop.sh                  # 停止脚本
└── 📄 status.sh                # 状态检查脚本
```

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/你的用户名/okx-btc-trading-system.git
cd okx-btc-trading-system
```

### 2. 一键安装
```bash
./setup.sh
```

### 3. 配置API密钥
编辑 `config/final_config.json`:
```json
{
  "exchange": {
    "api_key": "你的OKX_API_KEY",
    "secret": "你的OKX_SECRET",
    "passphrase": "你的OKX_PASSPHRASE",
    "proxies": {
      "http": "http://127.0.0.1:7897",
      "https": "http://127.0.0.1:7897"
    }
  }
}
```

### 4. 启动系统
```bash
./start.sh
```

### 5. 访问监控面板
打开浏览器: http://localhost:8084

## 🔧 系统配置

### 交易参数
- **检查频率**: 10秒
- **单笔风险**: 1.5%
- **每日最大交易**: 12次
- **杠杆范围**: 5x-25x (动态调整)
- **风险回报比**: ≥1.2:1

### 交易策略
1. **趋势跟踪** - 上涨趋势在支撑位做多，下跌趋势在阻力位做空
2. **均值回归** - 高波动率震荡行情中交易
3. **突破策略** - 价格突破近期高低点时交易

## 📊 监控与日志

### 实时监控
- Web面板: http://localhost:8084
- 显示: 价格、持仓、盈亏、交易历史

### 日志文件
```bash
# 查看交易日志
tail -f logs/trader.log

# 查看监控日志
tail -f logs/monitor.log

# 查看通知日志
tail -f logs/notifier.log
```

## ⚙️ 管理命令

```bash
# 启动所有服务
./start.sh

# 停止所有服务
./stop.sh

# 检查系统状态
./status.sh

# 查看实时日志
tail -f logs/trader.log
```

## 🔒 安全注意事项

### 绝对不能提交的文件
- `config/final_config.json` - 包含真实API密钥
- `config/telegram_config.json` - 包含Telegram密钥
- 任何 `.key`, `.pem`, `.secret` 文件
- `.env` 环境变量文件

### 使用模板文件
仓库包含模板文件:
- `config/final_config.json.template` - API配置模板
- `config/telegram_config.json.template` - Telegram配置模板
- `.env.template` - 环境变量模板

## 🐛 故障排除

### 常见问题
1. **API连接失败** - 检查代理设置和API密钥
2. **端口8084被占用** - 修改 `working_monitor.py` 中的端口
3. **Python依赖问题** - 重新安装: `pip install -r requirements.txt`
4. **Git推送失败** - 检查网络和仓库权限

### 查看详细错误
```bash
# 查看完整错误日志
cat logs/trader.log | grep -A 5 -B 5 "ERROR\|Exception"

# 测试API连接
python3 -c "import ccxt; exchange = ccxt.okx(); print(exchange.fetch_time())"
```

## 🔄 更新系统

### 从GitHub拉取更新
```bash
git pull origin main

# 重启服务
./stop.sh
./start.sh
```

### 提交更改
```bash
# 开发新功能
git checkout -b feature/新功能
# ... 修改代码 ...
git add .
git commit -m "feat: 添加新功能"
git push origin feature/新功能
```

## 📞 支持与贡献

### 报告问题
1. 查看现有Issue
2. 创建新Issue，包含:
   - 错误日志
   - 复现步骤
   - 系统环境

### 贡献代码
1. Fork仓库
2. 创建功能分支
3. 提交Pull Request

## 📄 许可证

私有仓库 - 仅供个人使用

## 🙏 致谢

- [OpenClaw](https://openclaw.ai) - AI助手框架
- [CCXT](https://github.com/ccxt/ccxt) - 加密货币交易库
- [OKX](https://www.okx.com) - 交易平台

---

*最后更新: 2026-02-26*
