#!/bin/bash
# ====================================================
# 简单复制脚本 - 一键打包所有必要文件
# ====================================================

set -e

echo "🚀 开始打包交易系统..."
echo "="*50

# 创建临时目录
TEMP_DIR="/tmp/trading_system_$(date +%s)"
mkdir -p "$TEMP_DIR"

echo "📁 创建临时目录: $TEMP_DIR"

# 复制交易系统文件
echo "📦 复制交易系统文件..."
rsync -av --exclude='venv/' --exclude='__pycache__/' --exclude='*.log' \
    --exclude='*.pyc' --exclude='.DS_Store' \
    /Users/$(whoami)/freqtrade-trading/ "$TEMP_DIR/freqtrade-trading/"

# 复制OpenClaw配置
echo "⚙️  复制OpenClaw配置..."
mkdir -p "$TEMP_DIR/.openclaw"
rsync -av /Users/$(whoami)/.openclaw/ "$TEMP_DIR/.openclaw/"

# 创建安装说明
cat > "$TEMP_DIR/README.txt" << 'EOF'
# 🚀 交易系统安装说明

## 文件清单
1. freqtrade-trading/ - 交易系统核心文件
2. .openclaw/ - OpenClaw配置文件

## 在新Mac上的安装步骤

### 1. 安装基础依赖
```bash
# 安装Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Node.js和Python
brew install node@22 python@3.9 git

# 安装OpenClaw
npm install -g openclaw
```

### 2. 复制文件到正确位置
```bash
# 复制交易系统
cp -r freqtrade-trading ~/

# 复制OpenClaw配置
cp -r .openclaw ~/
```

### 3. 设置Python环境
```bash
cd ~/freqtrade-trading
python3 -m venv venv
source venv/bin/activate
pip install ccxt numpy pandas flask requests python-telegram-bot
```

### 4. 配置API密钥
编辑 ~/freqtrade-trading/config/final_config.json:
```json
{
  "exchange": {
    "api_key": "YOUR_API_KEY",
    "secret": "YOUR_SECRET",
    "passphrase": "YOUR_PASSPHRASE",
    "proxies": {
      "http": "http://127.0.0.1:7897",
      "https": "http://127.0.0.1:7897"
    }
  }
}
```

### 5. 启动系统
```bash
cd ~/freqtrade-trading

# 创建启动脚本
cat > start_simple.sh << 'SCRIPT'
#!/bin/bash
source venv/bin/activate
python3 working_monitor.py > logs/monitor.log 2>&1 &
python3 ultra_fast_trader.py > logs/trader.log 2>&1 &
python3 trade_notifier.py > logs/notifier.log 2>&1 &
echo "✅ 系统已启动"
echo "🌐 监控面板: http://localhost:8084"
SCRIPT

chmod +x start_simple.sh
./start_simple.sh
```

### 6. 验证安装
```bash
# 检查进程
ps aux | grep -E "(working_monitor|ultra_fast|trade_notifier)"

# 访问监控面板
open http://localhost:8084
```

## 重要文件说明
- ultra_fast_trader.py: 10秒频率交易系统
- working_monitor.py: 监控面板 (端口8084)
- trade_notifier.py: Telegram通知器
- config/final_config.json: API配置 (需要编辑)

## 获取帮助
如有问题，检查日志文件:
- ~/freqtrade-trading/logs/trader.log
- ~/freqtrade-trading/logs/monitor.log
EOF

# 创建压缩包
echo "📦 创建压缩包..."
cd "$TEMP_DIR/.."
PACKAGE_NAME="trading_system_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$PACKAGE_NAME" "$(basename "$TEMP_DIR")"

echo ""
echo "✅ 打包完成!"
echo "📦 压缩包: $(pwd)/$PACKAGE_NAME"
echo ""
echo "📤 传输到新Mac的方法:"
echo ""
echo "1. 使用scp:"
echo "   scp $(pwd)/$PACKAGE_NAME 用户名@新Mac的IP:/tmp/"
echo ""
echo "2. 使用AirDrop或U盘"
echo ""
echo "3. 在新Mac上解压:"
echo "   tar -xzf /tmp/$PACKAGE_NAME -C /tmp/"
echo "   cd /tmp/trading_system_*"
echo "   查看 README.txt 获取安装说明"
echo ""
echo "💡 提示: 你的IP地址是: $(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | head -1 | awk '{print $2}')"

# 清理临时目录
rm -rf "$TEMP_DIR"