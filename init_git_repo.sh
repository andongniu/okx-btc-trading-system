#!/bin/bash
# ====================================================
# 初始化Git仓库并推送到GitHub
# ====================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_git_installed() {
    if ! command -v git &> /dev/null; then
        print_error "Git未安装"
        echo "请先安装Git:"
        echo "brew install git"
        exit 1
    fi
    print_success "Git已安装"
}

create_template_configs() {
    print_header "创建模板配置文件"
    
    # 备份原始配置文件
    if [ -f "config/final_config.json" ]; then
        cp config/final_config.json config/final_config.json.backup
        print_success "备份原始配置: config/final_config.json.backup"
    fi
    
    # 创建API配置模板
    cat > config/final_config.json.template << 'EOF'
{
  "exchange": {
    "api_key": "YOUR_OKX_API_KEY",
    "secret": "YOUR_OKX_SECRET",
    "passphrase": "YOUR_OKX_PASSPHRASE",
    "proxies": {
      "http": "http://127.0.0.1:7897",
      "https": "http://127.0.0.1:7897"
    }
  }
}
EOF
    print_success "创建API配置模板: config/final_config.json.template"
    
    # 创建Telegram配置模板
    cat > config/telegram_config.json.template << 'EOF'
{
  "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
  "chat_id": "YOUR_TELEGRAM_CHAT_ID"
}
EOF
    print_success "创建Telegram配置模板: config/telegram_config.json.template"
    
    # 创建环境变量模板
    cat > .env.template << 'EOF'
# OKX API配置
OKX_API_KEY=your_api_key_here
OKX_SECRET=your_secret_here
OKX_PASSPHRASE=your_passphrase_here

# Telegram配置
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# 代理配置
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897

# 交易参数
RISK_PER_TRADE=0.015
MAX_DAILY_TRADES=12
CHECK_INTERVAL=10
EOF
    print_success "创建环境变量模板: .env.template"
}

create_requirements() {
    print_header "创建Python依赖文件"
    
    cat > requirements.txt << 'EOF'
# 核心依赖
ccxt>=4.0.0
numpy>=1.21.0
pandas>=1.3.0
flask>=2.0.0
requests>=2.26.0
python-telegram-bot>=20.0

# 开发依赖
pytest>=7.0.0
black>=22.0.0
flake8>=4.0.0
mypy>=0.950

# 可选依赖
# matplotlib>=3.5.0  # 图表绘制
# seaborn>=0.11.0    # 数据可视化
# scikit-learn>=1.0  # 机器学习
EOF
    print_success "创建依赖文件: requirements.txt"
}

create_setup_script() {
    print_header "创建一键安装脚本"
    
    cat > setup.sh << 'EOF'
#!/bin/bash
# ====================================================
# OKX BTC交易系统一键安装脚本
# ====================================================

set -e

echo "🚀 开始安装OKX BTC交易系统..."
echo "="*50

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    echo "请先安装Python3: https://www.python.org/downloads/"
    exit 1
fi

# 检查Git
if ! command -v git &> /dev/null; then
    echo "❌ Git未安装"
    echo "请先安装Git: https://git-scm.com/downloads"
    exit 1
fi

# 创建项目目录
PROJECT_DIR="$HOME/okx-btc-trading"
if [ -d "$PROJECT_DIR" ]; then
    echo "📁 项目目录已存在: $PROJECT_DIR"
    read -p "是否覆盖? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "安装取消"
        exit 0
    fi
    rm -rf "$PROJECT_DIR"
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
echo "📁 创建项目目录: $PROJECT_DIR"

# 复制文件
echo "📦 复制文件..."
# 这里假设文件已经通过Git克隆或手动复制

# 创建Python虚拟环境
echo "🐍 创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📦 安装Python依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 配置API密钥
echo "🔑 配置API密钥..."
if [ ! -f "config/final_config.json" ]; then
    if [ -f "config/final_config.json.template" ]; then
        cp config/final_config.json.template config/final_config.json
        echo "请编辑 config/final_config.json 配置你的API密钥"
        echo "按回车键打开编辑器..."
        read -r
        
        # 使用默认编辑器
        if command -v nano &> /dev/null; then
            nano config/final_config.json
        elif command -v vim &> /dev/null; then
            vim config/final_config.json
        elif command -v vi &> /dev/null; then
            vi config/final_config.json
        else
            open config/final_config.json
        fi
    else
        echo "⚠️  未找到配置文件模板"
        echo "请手动创建 config/final_config.json"
    fi
fi

# 创建启动脚本
echo "🚀 创建启动脚本..."
cat > start.sh << 'SCRIPT_EOF'
#!/bin/bash
cd "$(dirname "$0")"

# 激活虚拟环境
source venv/bin/activate

echo "🚀 启动交易系统..."
echo "="*50

# 停止现有进程
pkill -f "working_monitor.py" 2>/dev/null || true
pkill -f "ultra_fast_trader.py" 2>/dev/null || true
pkill -f "trade_notifier.py" 2>/dev/null || true
sleep 2

# 创建日志目录
mkdir -p logs

# 启动监控面板
echo "📊 启动监控面板..."
python3 working_monitor.py > logs/monitor.log 2>&1 &
echo $! > logs/monitor.pid

# 启动交易系统
echo "🤖 启动交易系统..."
python3 ultra_fast_trader.py > logs/trader.log 2>&1 &
echo $! > logs/trader.pid

# 启动通知器
echo "📱 启动通知器..."
python3 trade_notifier.py > logs/notifier.log 2>&1 &
echo $! > logs/notifier.pid

echo ""
echo "✅ 所有系统已启动"
echo "🌐 监控面板: http://localhost:8084"
echo "📊 查看日志: tail -f logs/trader.log"
echo "🛑 停止命令: ./stop.sh"
SCRIPT_EOF

chmod +x start.sh

# 创建停止脚本
cat > stop.sh << 'STOP_EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "🛑 停止交易系统..."
echo "="*50

# 停止所有进程
pkill -f "working_monitor.py" 2>/dev/null || true
pkill -f "ultra_fast_trader.py" 2>/dev/null || true
pkill -f "trade_notifier.py" 2>/dev/null || true

# 删除PID文件
rm -f logs/*.pid 2>/dev/null || true

echo "✅ 所有系统已停止"
STOP_EOF

chmod +x stop.sh

# 创建状态检查脚本
cat > status.sh << 'STATUS_EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "📊 系统状态检查"
echo "="*50
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "项目目录: $(pwd)"
echo ""

# 检查进程
echo "🔍 进程状态:"
for script in "working_monitor.py" "ultra_fast_trader.py" "trade_notifier.py"; do
    if pgrep -f "$script" > /dev/null; then
        echo "  ✅ $script: 运行中"
    else
        echo "  ❌ $script: 未运行"
    fi
done

echo ""
echo "📈 端口状态:"
if lsof -i :8084 > /dev/null 2>&1; then
    echo "  ✅ 端口8084: 监听中"
else
    echo "  ❌ 端口8084: 未监听"
fi

echo ""
echo "📁 目录结构:"
echo "  $(find . -name "*.py" | wc -l) 个Python文件"
echo "  $(find . -name "*.sh" | wc -l) 个Shell脚本"
echo "  $(find . -name "*.log" | wc -l) 个日志文件"

echo ""
echo "💡 可用命令:"
echo "  ./start.sh    # 启动系统"
echo "  ./stop.sh     # 停止系统"
echo "  ./status.sh   # 检查状态"
echo "  tail -f logs/trader.log  # 查看实时日志"
STATUS_EOF

chmod +x status.sh

echo ""
echo "🎉 安装完成!"
echo "="*50
echo "📁 项目目录: $PROJECT_DIR"
echo "🚀 启动命令: cd $PROJECT_DIR && ./start.sh"
echo "🌐 监控面板: http://localhost:8084"
echo "📊 查看日志: tail -f $PROJECT_DIR/logs/trader.log"
echo ""
echo "🔧 后续步骤:"
echo "  1. 确保 config/final_config.json 已配置API密钥"
echo "  2. 如果需要代理，确保代理服务器运行"
echo "  3. 运行 ./start.sh 启动系统"
echo "  4. 访问 http://localhost:8084 查看监控面板"
EOF

    chmod +x setup.sh
    print_success "创建安装脚本: setup.sh"
}

init_git_repo() {
    print_header "初始化Git仓库"
    
    # 检查是否已经是Git仓库
    if [ -d ".git" ]; then
        print_warning "已经是Git仓库，重新初始化..."
        rm -rf .git
    fi
    
    # 初始化Git
    git init
    print_success "Git仓库初始化完成"
    
    # 添加文件
    print_header "添加文件到Git"
    
    # 先添加.gitignore
    git add .gitignore
    
    # 添加所有非敏感文件
    git add *.py *.sh *.md requirements.txt setup.sh
    git add config/*.template
    git add templates/
    
    # 提交初始版本
    git commit -m "初始提交: OKX BTC超快交易系统 v1.0

包含功能:
- 10秒频率交易系统 (ultra_fast_trader.py)
- 实时监控面板 (working_monitor.py)
- Telegram通知器 (trade_notifier.py)
- 一键安装脚本 (setup.sh)
- 完整文档和配置模板"
    
    print_success "提交初始版本完成"
    
    # 显示Git状态
    print_header "Git仓库状态"
    git status
    echo ""
    git log --oneline -5
}

setup_github() {
    print_header "设置GitHub仓库"
    
    echo "请先在GitHub上创建仓库:"
    echo "1. 访问 https://github.com/new"
    echo "2. 仓库名: okx-btc-trading-system"
    echo "3. 描述: OKX BTC超快交易系统 (10秒频率)"
    echo "4. 选择: Private (私有仓库)"
    echo "5. 不添加README/.gitignore"
    echo ""
    read -p "按回车键继续..." -r
    
    echo ""
    echo "📤 推送代码到GitHub:"
    echo ""
    echo "运行以下命令:"
    echo ""
    echo "  # 添加远程仓库"
    echo "  git remote add origin https://github.com/你的用户名/okx-btc-trading-system.git"
    echo ""
    echo "  # 推送代码"
    echo "  git push -u origin main"
    echo ""
    echo "💡 提示: 如果遇到错误，可能需要先创建main分支:"
    echo "  git branch -M main"
    echo ""
    
    read -p "是否现在设置远程仓库? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "请输入GitHub仓库URL:"
        read -r GITHUB_URL
        if [ -n "$GITHUB_URL" ]; then
            git remote add origin "$GITHUB_URL"
            git branch -M main
            git push -u origin main
            print_success "代码已推送到GitHub"
        fi
    fi
}

create_readme() {
    print_header "创建README.md"
    
    cat > README.md << 'EOF'
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
EOF
    print_success "创建README.md完成"
}

main() {
    print_header "OKX BTC交易系统Git仓库初始化"
    
    # 检查当前目录
    if [ ! -f "ultra_fast_trader.py" ]; then
        print_error "请在交易系统目录中运行此脚本"
        echo "当前目录: $(pwd)"
        echo "请切换到: cd ~/freqtrade-trading"
        exit 1
    fi
    
    check_git_installed
    create_template_configs
    create_requirements
    create_setup_script
    create_readme
    init_git_repo
    setup_github
    
    print_header "🎉 初始化完成!"
    echo ""
    echo "✅ Git仓库已初始化"
    echo "✅ 模板配置文件已创建"
    echo "✅ 安装脚本已生成"
    echo "✅ README文档已编写"
    echo ""
    echo "📁 项目已准备好推送到GitHub"
    echo ""
    echo "🚀 下一步:"
    echo "1. 在GitHub创建私有仓库: okx-btc-trading-system"
    echo "2. 运行推送命令:"
    echo "   git remote add origin https://github.com/你的用户名/okx-btc-trading-system.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
    echo "💡 提示: 使用 ./setup.sh 在新机器上一键安装"
}

# 运行主函数
main