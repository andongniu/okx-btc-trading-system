# 📋 复制交易系统到新Mac - 检查清单

## 🎯 目标
在另一台Mac上安装完全相同的OpenClaw配置和交易系统

## 📁 需要复制的文件清单

### **核心交易系统文件** (`~/freqtrade-trading/`)
```
✅ ultra_fast_trader.py          # 超快交易系统 (10秒频率)
✅ trade_notifier.py             # Telegram通知器
✅ working_monitor.py            # 监控面板 (端口8084)
✅ check_fast_system.py          # 系统检查脚本
✅ start_aggressive_trading.sh   # 启动脚本
✅ simple_copy.sh                # 本复制脚本
✅ copy_to_new_mac.sh            # 完整复制脚本
✅ quick_copy_guide.md           # 快速指南
```

### **配置文件** (`~/freqtrade-trading/config/`)
```
✅ final_config.json             # OKX API配置 (需要编辑API密钥)
✅ survival_config.json          # 生存模式配置
```

### **模板文件** (`~/freqtrade-trading/templates/`)
```
✅ autonomous_monitor.html       # 监控面板HTML
✅ autonomous_monitor.js         # 监控面板JavaScript
✅ realistic_dashboard_simple.html # 简化仪表板
```

### **OpenClaw配置** (`~/.openclaw/`)
```
✅ openclaw.json                 # OpenClaw主配置文件
✅ workspace/SOUL.md             # 人格定义
✅ workspace/USER.md             # 用户信息
✅ workspace/IDENTITY.md         # 身份定义
✅ workspace/MEMORY.md           # 长期记忆
✅ workspace/memory/2026-02-26.md # 今日记忆
```

## 🚀 快速复制方法

### **方法A：使用简单脚本** (推荐)
```bash
# 在第一台Mac上运行
cd ~/freqtrade-trading
./simple_copy.sh
```
这会创建一个包含所有文件的压缩包

### **方法B：手动复制关键文件**
```bash
# 1. 创建目录结构
mkdir -p ~/new-trading/{config,templates,logs}

# 2. 复制核心Python脚本
cp ~/freqtrade-trading/ultra_fast_trader.py ~/new-trading/
cp ~/freqtrade-trading/trade_notifier.py ~/new-trading/
cp ~/freqtrade-trading/working_monitor.py ~/new-trading/

# 3. 复制配置文件
cp ~/freqtrade-trading/config/final_config.json ~/new-trading/config/

# 4. 复制模板文件
cp ~/freqtrade-trading/templates/* ~/new-trading/templates/

# 5. 复制OpenClaw配置
cp ~/.openclaw/openclaw.json ~/.openclaw-new/
cp ~/.openclaw/workspace/* ~/.openclaw-new/workspace/
```

## 🔧 在新Mac上的安装步骤

### **1. 安装基础软件**
```bash
# 安装Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Node.js
brew install node@22
echo 'export PATH="/opt/homebrew/opt/node@22/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 安装Python
brew install python@3.9

# 安装Git
brew install git
```

### **2. 安装OpenClaw**
```bash
npm install -g openclaw
openclaw --version  # 验证安装
```

### **3. 设置交易系统**
```bash
# 创建目录
mkdir -p ~/freqtrade-trading
cd ~/freqtrade-trading

# 复制所有文件到正确位置
# (使用从第一台Mac复制的文件)

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install ccxt numpy pandas flask requests python-telegram-bot
```

### **4. 配置API密钥**
编辑 `~/freqtrade-trading/config/final_config.json`:
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

### **5. 创建启动脚本**
```bash
cd ~/freqtrade-trading

cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate

# 停止现有进程
pkill -f "working_monitor.py" 2>/dev/null || true
pkill -f "ultra_fast_trader.py" 2>/dev/null || true
pkill -f "trade_notifier.py" 2>/dev/null || true
sleep 2

# 启动监控面板
python3 working_monitor.py > logs/monitor.log 2>&1 &

# 启动交易系统
python3 ultra_fast_trader.py > logs/trader.log 2>&1 &

# 启动通知器
python3 trade_notifier.py > logs/notifier.log 2>&1 &

echo "✅ 交易系统已启动"
echo "🌐 监控面板: http://localhost:8084"
echo "📊 查看日志: tail -f logs/trader.log"
EOF

chmod +x start.sh
```

### **6. 启动系统**
```bash
cd ~/freqtrade-trading
mkdir -p logs
./start.sh
```

### **7. 验证安装**
```bash
# 检查进程
ps aux | grep -E "(working_monitor|ultra_fast|trade_notifier)"

# 检查端口
lsof -i :8084

# 访问监控面板
open http://localhost:8084

# 查看日志
tail -f logs/trader.log
```

## ⚠️ 重要注意事项

### **API密钥安全**
- 不要将 `final_config.json` 提交到Git
- 在新机器上重新输入API密钥
- 确保代理配置正确

### **网络配置**
- 确保新Mac可以访问OKX API
- 如果需要代理，配置相同的代理设置
- 测试网络连接: `curl https://api.okx.com`

### **文件权限**
```bash
# 确保脚本可执行
chmod +x ~/freqtrade-trading/*.sh
chmod +x ~/freqtrade-trading/*.py
```

### **Python环境**
```bash
# 如果遇到Python问题
cd ~/freqtrade-trading
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install ccxt numpy pandas flask requests python-telegram-bot
```

## 🔍 故障排除

### **问题：OpenClaw安装失败**
```bash
# 检查Node.js版本
node --version

# 使用npm镜像
npm config set registry https://registry.npmmirror.com
npm install -g openclaw
```

### **问题：Python包安装失败**
```bash
# 使用国内镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install ccxt numpy pandas flask
```

### **问题：端口8084被占用**
```bash
# 修改监控面板端口
sed -i '' 's/8084/8085/g' working_monitor.py
```

### **问题：API连接失败**
```bash
# 测试连接
cd ~/freqtrade-trading
source venv/bin/activate
python3 -c "
import ccxt
exchange = ccxt.okx()
print(exchange.fetch_time())
"
```

## 📞 获取帮助

如果遇到问题：

1. **查看日志文件**：
   ```bash
   tail -f ~/freqtrade-trading/logs/trader.log
   tail -f ~/freqtrade-trading/logs/monitor.log
   ```

2. **检查系统状态**：
   ```bash
   ps aux | grep -E "(python|openclaw)"
   lsof -i :8084
   ```

3. **验证环境**：
   ```bash
   python3 --version
   node --version
   openclaw --version
   ```

4. **测试网络**：
   ```bash
   curl https://api.okx.com
   curl -x http://127.0.0.1:7897 https://api.okx.com
   ```

## 🎉 完成标志

安装成功时，你应该能看到：

1. ✅ OpenClaw命令可用：`openclaw --version`
2. ✅ Python环境正常：可以导入ccxt等包
3. ✅ 监控面板可访问：http://localhost:8084
4. ✅ 交易系统运行：`ps aux` 显示相关进程
5. ✅ 日志文件正常生成：`logs/trader.log` 有内容

---

*最后更新: 2026-02-26*