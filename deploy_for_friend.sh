#!/bin/bash
# ====================================================
# 朋友专用部署脚本 - OKX BTC交易系统
# 使用方法: curl -sSL https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash
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

check_requirements() {
    print_header "检查系统要求"
    
    # 检查操作系统
    if [[ "$(uname)" != "Darwin" ]]; then
        print_error "本系统仅支持macOS"
        echo "检测到的系统: $(uname)"
        exit 1
    fi
    print_success "操作系统: macOS"
    
    # 检查Homebrew
    if ! command -v brew &> /dev/null; then
        print_warning "Homebrew未安装，正在安装..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
        eval "$(/opt/homebrew/bin/brew shellenv)"
        print_success "Homebrew安装完成"
    else
        print_success "Homebrew已安装"
    fi
    
    # 检查Git
    if ! command -v git &> /dev/null; then
        print_warning "Git未安装，正在安装..."
        brew install git
        print_success "Git安装完成"
    else
        print_success "Git已安装"
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_warning "Python3未安装，正在安装..."
        brew install python@3.9
        print_success "Python3安装完成"
    else
        print_success "Python3已安装"
    fi
}

clone_repository() {
    print_header "克隆代码仓库"
    
    PROJECT_DIR="$HOME/okx-btc-trading"
    
    if [ -d "$PROJECT_DIR" ]; then
        print_warning "目录已存在: $PROJECT_DIR"
        read -p "是否覆盖? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "使用现有目录..."
        else
            rm -rf "$PROJECT_DIR"
        fi
    fi
    
    echo "正在从GitHub克隆代码..."
    git clone https://github.com/andongniu/okx-btc-trading-system.git "$PROJECT_DIR"
    
    if [ $? -eq 0 ]; then
        print_success "代码克隆完成: $PROJECT_DIR"
        cd "$PROJECT_DIR"
    else
        print_error "克隆失败，请检查网络连接"
        exit 1
    fi
}

setup_environment() {
    print_header "设置交易环境"
    
    # 创建Python虚拟环境
    if [ ! -d "venv" ]; then
        print_warning "创建Python虚拟环境..."
        python3 -m venv venv
        print_success "虚拟环境创建完成"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    print_warning "安装Python依赖..."
    pip install --upgrade pip
    pip install ccxt numpy pandas flask requests python-telegram-bot
    
    if [ $? -eq 0 ]; then
        print_success "Python依赖安装完成"
    else
        print_error "依赖安装失败"
        echo "尝试使用国内镜像..."
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ccxt numpy pandas flask requests python-telegram-bot
    fi
}

configure_api() {
    print_header "配置API密钥"
    
    CONFIG_FILE="config/final_config.json"
    TEMPLATE_FILE="config/final_config.json.template"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        if [ -f "$TEMPLATE_FILE" ]; then
            cp "$TEMPLATE_FILE" "$CONFIG_FILE"
            print_success "创建配置文件: $CONFIG_FILE"
            
            echo ""
            echo "🔑 现在需要配置你的OKX API密钥:"
            echo ""
            echo "1. 登录OKX官网: https://www.okx.com"
            echo "2. 进入 API管理: 个人中心 → API → 创建API"
            echo "3. 选择权限: 交易、读取"
            echo "4. 复制以下信息:"
            echo "   - API Key"
            echo "   - Secret Key"
            echo "   - Passphrase"
            echo ""
            echo "按回车键打开配置文件编辑器..."
            read -r
            
            # 使用默认编辑器
            if command -v nano &> /dev/null; then
                nano "$CONFIG_FILE"
            elif command -v vim &> /dev/null; then
                vim "$CONFIG_FILE"
            elif command -v vi &> /dev/null; then
                vi "$CONFIG_FILE"
            else
                open "$CONFIG_FILE"
            fi
            
            # 验证配置
            if grep -q "YOUR_OKX_API_KEY" "$CONFIG_FILE"; then
                print_warning "检测到未修改的API密钥模板"
                echo "请确保已替换所有 YOUR_* 为你的实际密钥"
            else
                print_success "API配置完成"
            fi
        else
            print_error "配置文件模板不存在"
            exit 1
        fi
    else
        print_success "配置文件已存在"
    fi
}

create_launch_scripts() {
    print_header "创建启动脚本"
    
    # 创建启动脚本
    cat > launch.sh << 'EOF'
#!/bin/bash
# 启动交易系统

cd "$(dirname "$0")"

echo "🚀 启动OKX BTC交易系统..."
echo "="*50

# 停止现有进程
pkill -f "working_monitor.py" 2>/dev/null || true
pkill -f "ultra_fast_trader.py" 2>/dev/null || true
pkill -f "trade_notifier.py" 2>/dev/null || true
sleep 2

# 激活虚拟环境
source venv/bin/activate

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
echo "📱 状态检查: ./status.sh"
EOF
    
    chmod +x launch.sh
    print_success "创建启动脚本: launch.sh"
    
    # 创建停止脚本
    cat > stop.sh << 'EOF'
#!/bin/bash
# 停止交易系统

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
EOF
    
    chmod +x stop.sh
    print_success "创建停止脚本: stop.sh"
    
    # 创建状态检查脚本
    cat > status.sh << 'EOF'
#!/bin/bash
# 检查系统状态

cd "$(dirname "$0")"

echo "📊 交易系统状态检查"
echo "="*50
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "系统版本: OKX BTC交易系统 v1.0"
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
echo "📈 服务状态:"
if lsof -i :8084 > /dev/null 2>&1; then
    echo "  ✅ 监控面板: 运行中 (端口8084)"
else
    echo "  ❌ 监控面板: 未运行"
fi

echo ""
echo "📁 文件状态:"
echo "  配置文件: $(test -f config/final_config.json && echo '✅ 存在' || echo '❌ 缺失')"
echo "  日志目录: $(test -d logs && echo '✅ 存在' || echo '❌ 缺失')"
echo "  虚拟环境: $(test -d venv && echo '✅ 存在' || echo '❌ 缺失')"

echo ""
echo "💡 管理命令:"
echo "  ./launch.sh    # 启动系统"
echo "  ./stop.sh      # 停止系统"
echo "  ./status.sh    # 检查状态"
echo "  tail -f logs/trader.log  # 查看实时日志"
EOF
    
    chmod +x status.sh
    print_success "创建状态脚本: status.sh"
}

test_system() {
    print_header "测试系统功能"
    
    source venv/bin/activate
    
    # 测试Python环境
    print_warning "测试Python环境..."
    python3 -c "import ccxt, numpy, pandas, flask; print('✅ Python环境正常')"
    
    # 测试API连接（如果已配置）
    if [ -f "config/final_config.json" ] && ! grep -q "YOUR_OKX_API_KEY" "config/final_config.json"; then
        print_warning "测试API连接..."
        if python3 -c "
import json, ccxt
try:
    with open('config/final_config.json') as f:
        config = json.load(f)
    exchange = ccxt.okx({
        'apiKey': config['exchange']['api_key'],
        'secret': config['exchange']['secret'],
        'password': config['exchange']['passphrase'],
        'enableRateLimit': True
    })
    time = exchange.fetch_time()
    print(f'✅ API连接成功')
except Exception as e:
    print(f'⚠️  API连接测试失败: {e}')
" 2>/dev/null; then
            print_success "API连接测试通过"
        else
            print_warning "API连接测试失败（可能需要配置代理或检查网络）"
        fi
    else
        print_warning "API配置未完成，跳过连接测试"
    fi
}

print_summary() {
    print_header "🎉 部署完成！"
    
    PROJECT_DIR="$(pwd)"
    
    echo -e "${GREEN}交易系统已成功部署到你的Mac！${NC}"
    echo ""
    echo "📁 项目目录: $PROJECT_DIR"
    echo "🐍 Python环境: $PROJECT_DIR/venv"
    echo "📊 日志文件: $PROJECT_DIR/logs/"
    echo ""
    echo "🚀 核心功能:"
    echo "  ⚡ 10秒频率交易系统 - 实时监控市场"
    echo "  📊 Web监控面板 - 本地端口8084"
    echo "  📱 Telegram通知 - 交易提醒"
    echo "  🔒 风险控制 - 自动止损止盈"
    echo ""
    echo "🔧 管理命令:"
    echo "  cd $PROJECT_DIR"
    echo "  ./launch.sh    # 启动所有服务"
    echo "  ./stop.sh      # 停止所有服务"
    echo "  ./status.sh    # 检查系统状态"
    echo ""
    echo "🌐 监控面板:"
    echo "  启动后访问: http://localhost:8084"
    echo ""
    echo "📊 查看日志:"
    echo "  tail -f $PROJECT_DIR/logs/trader.log"
    echo ""
    echo "⚠️  重要提醒:"
    echo "  1. 确保 config/final_config.json 已配置正确的API密钥"
    echo "  2. 如果需要代理，请确保代理服务器运行"
    echo "  3. 首次使用建议先小额测试"
    echo "  4. 定期检查日志文件"
    echo ""
    echo "📞 获取帮助:"
    echo "  查看文档: $PROJECT_DIR/README.md"
    echo "  查看日志: tail -f logs/trader.log"
    echo "  联系作者: GitHub @andongniu"
}

main() {
    print_header "OKX BTC交易系统 - 朋友专用部署"
    echo "版本: v1.0 | 作者: @andongniu"
    echo "GitHub: https://github.com/andongniu/okx-btc-trading-system"
    echo ""
    
    check_requirements
    clone_repository
    setup_environment
    configure_api
    create_launch_scripts
    test_system
    print_summary
}

# 运行主函数
main