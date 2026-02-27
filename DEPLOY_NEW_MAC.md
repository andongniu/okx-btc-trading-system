# 🚀 在新Mac上部署交易系统 - 极简指南

## 📋 只需3步

### 第一步：克隆Git仓库
```bash
# 克隆私有仓库（需要GitHub访问权限）
git clone https://github.com/你的用户名/okx-btc-trading-system.git
cd okx-btc-trading-system
```

### 第二步：一键安装
```bash
# 运行安装脚本
chmod +x setup.sh
./setup.sh
```

### 第三步：配置和启动
```bash
# 1. 配置API密钥
nano config/final_config.json
# 填入你的OKX API密钥

# 2. 启动系统
./start.sh

# 3. 访问监控面板
open http://localhost:8084
```

## 🔧 详细步骤

### 1. 安装基础软件（如果尚未安装）
```bash
# 安装Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Node.js和Python
brew install node@22 python@3.9 git

# 安装OpenClaw
npm install -g openclaw
```

### 2. 克隆代码
```bash
# 使用HTTPS（需要输入GitHub密码）
git clone https://github.com/你的用户名/okx-btc-trading-system.git

# 或使用SSH（需要配置SSH密钥）
git clone git@github.com:你的用户名/okx-btc-trading-system.git
```

### 3. 运行安装脚本
安装脚本 `setup.sh` 会自动：
- ✅ 创建Python虚拟环境
- ✅ 安装所有依赖包
- ✅ 生成启动/停止脚本
- ✅ 创建日志目录

### 4. 配置API密钥
编辑 `config/final_config.json`：
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

### 5. 启动系统
```bash
./start.sh
```
输出：
```
🚀 启动交易系统...
==================================================
📊 启动监控面板...
   进程ID: 12345
🤖 启动交易系统...
   进程ID: 12346
📱 启动通知器...
   进程ID: 12347

✅ 所有系统已启动
🌐 监控面板: http://localhost:8084
📊 查看日志: tail -f logs/trader.log
🛑 停止命令: ./stop.sh
```

## 📊 验证安装

### 检查系统状态
```bash
./status.sh
```
输出：
```
📊 系统状态检查
==================================================
检查时间: 2026-02-26 22:30:00
项目目录: /Users/你/okx-btc-trading-system

🔍 进程状态:
  ✅ working_monitor.py: 运行中
  ✅ ultra_fast_trader.py: 运行中
  ✅ trade_notifier.py: 运行中

📈 端口状态:
  ✅ 端口8084: 监听中

📁 目录结构:
  102 个Python文件
  15 个Shell脚本
  3 个日志文件
```

### 查看实时日志
```bash
tail -f logs/trader.log
```

### 访问监控面板
打开浏览器：http://localhost:8084

## ⚡ 日常管理命令

### 启动/停止
```bash
# 启动所有服务
./start.sh

# 停止所有服务
./stop.sh

# 重启服务
./stop.sh && sleep 2 && ./start.sh
```

### 查看状态
```bash
# 检查进程
ps aux | grep -E "(working_monitor|ultra_fast|trade_notifier)"

# 检查端口
lsof -i :8084

# 查看系统状态
./status.sh
```

### 查看日志
```bash
# 实时查看交易日志
tail -f logs/trader.log

# 查看监控日志
tail -f logs/monitor.log

# 查看错误日志
grep -i error logs/trader.log
```

## 🔄 更新系统

### 从GitHub拉取更新
```bash
# 拉取最新代码
git pull origin main

# 重启服务
./stop.sh
./start.sh
```

### 提交更改（在第一台机器上）
```bash
# 添加更改
git add .

# 提交
git commit -m "更新说明"

# 推送到GitHub
git push origin main
```

## ⚠️ 常见问题

### 问题1：Git克隆需要认证
```bash
# 使用个人访问令牌代替密码
# 生成令牌: GitHub Settings → Developer settings → Personal access tokens
git clone https://你的用户名:令牌@github.com/你的用户名/okx-btc-trading-system.git
```

### 问题2：Python依赖安装失败
```bash
# 手动安装
cd okx-btc-trading-system
python3 -m venv venv
source venv/bin/activate
pip install ccxt numpy pandas flask requests python-telegram-bot
```

### 问题3：端口8084被占用
```bash
# 修改监控面板端口
sed -i '' 's/8084/8085/g' working_monitor.py
# 然后访问 http://localhost:8085
```

### 问题4：API连接失败
```bash
# 测试连接
cd okx-btc-trading-system
source venv/bin/activate
python3 test_connection.py
```

## 🎯 系统特性

### 当前运行的版本
- ⚡ **10秒频率** - 超快市场响应
- 🤖 **完全自主** - 自动交易决策
- 📊 **实时监控** - Web面板显示
- 📱 **Telegram通知** - 即时提醒
- 🔒 **风险控制** - 动态止损止盈

### 核心文件
```
ultra_fast_trader.py     # 🚀 10秒交易系统
working_monitor.py       # 📊 监控面板
trade_notifier.py        # 📱 Telegram通知
config/final_config.json # 🔑 API配置 (需要编辑)
```

## 📞 获取帮助

### 查看详细日志
```bash
# 查看完整错误信息
cat logs/trader.log | tail -100

# 搜索特定错误
grep -A 10 -B 5 "ERROR\|Exception\|Traceback" logs/trader.log
```

### 测试组件
```bash
# 测试Python环境
source venv/bin/activate
python3 -c "import ccxt, numpy, pandas; print('✅ 环境正常')"

# 测试API连接
python3 test_connection.py

# 测试监控面板
python3 working_monitor.py --test
```

### 重新安装
```bash
# 完全重新安装
./stop.sh
rm -rf venv
./setup.sh
./start.sh
```

---

**🎉 现在你可以在任何Mac上部署完全相同的交易系统了！**