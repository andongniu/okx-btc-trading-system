# 🚀 快速复制交易系统到新Mac

## 📋 简化版步骤

### **第一步：在第一台Mac上准备**

```bash
# 1. 进入交易系统目录
cd ~/freqtrade-trading

# 2. 创建备份包
./copy_to_new_mac.sh prepare
```

这会创建：
- 备份包：`/tmp/trading_system_package.tar.gz`
- 安装脚本：在备份目录中

### **第二步：传输文件到新Mac**

选择一种方法：

#### **方法A：使用scp（推荐）**
```bash
# 在新Mac上运行：
scp 用户名@第一台Mac的IP:/tmp/trading_system_package.tar.gz /tmp/
```

#### **方法B：使用U盘**
1. 复制 `/tmp/trading_system_package.tar.gz` 到U盘
2. 复制到新Mac的 `/tmp/` 目录

#### **方法C：使用AirDrop**
直接AirDrop传输文件

### **第三步：在新Mac上安装**

```bash
# 1. 解压备份包
cd /tmp
tar -xzf trading_system_package.tar.gz

# 2. 进入备份目录（名称类似 trading_system_backup_20260226_0930）
cd trading_system_backup_*

# 3. 运行安装脚本
./install_on_new_mac.sh
```

### **第四步：配置API密钥**

安装完成后：
```bash
cd ~/freqtrade-trading
nano config/final_config.json
```

编辑以下内容：
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

### **第五步：启动系统**

```bash
cd ~/freqtrade-trading
./start_all.sh
```

### **第六步：验证安装**

```bash
# 检查状态
./check_status.sh

# 查看日志
tail -f logs/trader.log

# 访问监控面板
open http://localhost:8084
```

---

## 🔧 手动复制文件清单（如果脚本失败）

如果脚本有问题，手动复制这些文件：

### **必须复制的文件：**

#### **交易系统核心文件**
```
~/freqtrade-trading/
├── ultra_fast_trader.py          # 超快交易系统
├── trade_notifier.py             # Telegram通知器
├── working_monitor.py            # 监控面板
├── check_fast_system.py          # 系统检查
├── start_aggressive_trading.sh   # 启动脚本
├── config/final_config.json      # API配置（需要编辑）
└── templates/                    # HTML模板目录
```

#### **OpenClaw配置文件**
```
~/.openclaw/
├── openclaw.json                 # OpenClaw主配置
└── workspace/                    # 工作空间文件
    ├── SOUL.md
    ├── USER.md
    ├── IDENTITY.md
    ├── MEMORY.md
    └── memory/2026-02-26.md
```

### **手动安装依赖**

在新Mac上运行：

```bash
# 1. 安装基础工具
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install node@22 python@3.9 git

# 2. 安装OpenClaw
npm install -g openclaw

# 3. 创建Python环境
cd ~/freqtrade-trading
python3 -m venv venv
source venv/bin/activate
pip install ccxt numpy pandas flask requests python-telegram-bot
```

---

## ⚠️ 常见问题解决

### **问题1：scp连接失败**
```bash
# 检查第一台Mac的IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# 确保SSH服务开启
sudo systemsetup -setremotelogin on
```

### **问题2：Python依赖安装失败**
```bash
# 更新pip
pip install --upgrade pip

# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ccxt numpy pandas flask
```

### **问题3：端口8084被占用**
```bash
# 修改监控面板端口
sed -i '' 's/8084/8085/g' working_monitor.py
```

### **问题4：API连接失败**
```bash
# 测试代理
curl -x http://127.0.0.1:7897 https://api.okx.com

# 检查API密钥格式
# 确保没有多余的空格或引号
```

---

## 📱 快速命令参考

### **日常管理**
```bash
# 启动所有服务
cd ~/freqtrade-trading && ./start_all.sh

# 停止所有服务
./stop_all.sh

# 检查状态
./check_status.sh

# 查看实时日志
tail -f logs/trader.log
```

### **故障排查**
```bash
# 检查进程
ps aux | grep -E "(working_monitor|ultra_fast|trade_notifier)"

# 检查端口
lsof -i :8084

# 检查Python环境
source venv/bin/activate
python3 -c "import ccxt; print(ccxt.__version__)"
```

### **重新安装**
```bash
# 完全重新安装
cd ~/freqtrade-trading
./stop_all.sh
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install ccxt numpy pandas flask requests python-telegram-bot
./start_all.sh
```

---

## 🎯 验证安装成功

运行以下检查：

```bash
# 1. 检查OpenClaw
openclaw --version

# 2. 检查Python环境
cd ~/freqtrade-trading
source venv/bin/activate
python3 -c "import ccxt; print('✅ Python环境正常')"

# 3. 启动系统
./start_all.sh

# 4. 检查进程
./check_status.sh

# 5. 访问监控面板
open http://localhost:8084
```

如果所有检查通过，说明安装成功！

---

## 📞 获取帮助

如果遇到问题：

1. **查看详细日志**：`tail -f ~/freqtrade-trading/logs/trader.log`
2. **检查错误信息**：复制完整的错误信息
3. **验证网络连接**：确保可以访问OKX API
4. **检查API密钥**：确保密钥正确且未过期

---

*最后更新: 2026-02-26*