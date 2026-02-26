#!/bin/bash
# ====================================================
# 复制交易系统到新Mac的完整脚本
# 用法: 
#   1. 在第一台Mac上运行: ./copy_to_new_mac.sh prepare
#   2. 在第二台Mac上运行: ./copy_to_new_mac.sh install
# ====================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
SOURCE_USER="$(whoami)"
SOURCE_IP="$(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | head -1 | awk '{print $2}')"
SOURCE_DIR="/Users/${SOURCE_USER}/freqtrade-trading"
OPENCLAW_DIR="/Users/${SOURCE_USER}/.openclaw"
BACKUP_DIR="/tmp/trading_system_backup_$(date +%Y%m%d_%H%M%S)"
PACKAGE_FILE="/tmp/trading_system_package.tar.gz"

# 函数定义
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

check_dependencies() {
    print_header "检查依赖"
    
    # 检查Homebrew
    if ! command -v brew &> /dev/null; then
        print_error "Homebrew未安装"
        echo "请先安装Homebrew:"
        echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    else
        print_success "Homebrew已安装"
    fi
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        print_warning "Node.js未安装，将在安装阶段安装"
    else
        print_success "Node.js已安装"
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_warning "Python3未安装，将在安装阶段安装"
    else
        print_success "Python3已安装"
    fi
    
    # 检查Git
    if ! command -v git &> /dev/null; then
        print_warning "Git未安装，将在安装阶段安装"
    else
        print_success "Git已安装"
    fi
}

prepare_backup() {
    print_header "第一步：在第一台Mac上准备备份"
    
    # 检查源目录是否存在
    if [ ! -d "$SOURCE_DIR" ]; then
        print_error "交易系统目录不存在: $SOURCE_DIR"
        exit 1
    fi
    
    if [ ! -d "$OPENCLAW_DIR" ]; then
        print_error "OpenClaw目录不存在: $OPENCLAW_DIR"
        exit 1
    fi
    
    # 创建备份目录
    mkdir -p "$BACKUP_DIR"
    print_success "创建备份目录: $BACKUP_DIR"
    
    # 备份交易系统
    print_header "备份交易系统文件"
    rsync -av --exclude='venv/' --exclude='__pycache__/' --exclude='*.log' \
        "$SOURCE_DIR/" "$BACKUP_DIR/freqtrade-trading/"
    print_success "交易系统文件备份完成"
    
    # 备份OpenClaw配置
    print_header "备份OpenClaw配置"
    rsync -av "$OPENCLAW_DIR/" "$BACKUP_DIR/.openclaw/"
    print_success "OpenClaw配置备份完成"
    
    # 创建安装脚本
    print_header "创建安装脚本"
    cat > "$BACKUP_DIR/install_on_new_mac.sh" << 'EOF'
#!/bin/bash
# ====================================================
# 在新Mac上安装交易系统的脚本
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

# 获取当前用户名
CURRENT_USER=$(whoami)
INSTALL_DIR="/Users/${CURRENT_USER}/freqtrade-trading"
OPENCLAW_INSTALL_DIR="/Users/${CURRENT_USER}/.openclaw"

install_dependencies() {
    print_header "安装系统依赖"
    
    # 安装Homebrew（如果未安装）
    if ! command -v brew &> /dev/null; then
        print_warning "安装Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
        eval "$(/opt/homebrew/bin/brew shellenv)"
        print_success "Homebrew安装完成"
    else
        print_success "Homebrew已安装"
    fi
    
    # 安装Node.js
    if ! command -v node &> /dev/null; then
        print_warning "安装Node.js..."
        brew install node@22
        echo 'export PATH="/opt/homebrew/opt/node@22/bin:$PATH"' >> ~/.zshrc
        export PATH="/opt/homebrew/opt/node@22/bin:$PATH"
        print_success "Node.js安装完成"
    else
        print_success "Node.js已安装"
    fi
    
    # 安装Python
    if ! command -v python3 &> /dev/null; then
        print_warning "安装Python..."
        brew install python@3.9
        brew install pipx
        pipx ensurepath
        print_success "Python安装完成"
    else
        print_success "Python已安装"
    fi
    
    # 安装Git
    if ! command -v git &> /dev/null; then
        print_warning "安装Git..."
        brew install git
        print_success "Git安装完成"
    else
        print_success "Git已安装"
    fi
}

install_openclaw() {
    print_header "安装OpenClaw"
    
    if ! command -v openclaw &> /dev/null; then
        print_warning "安装OpenClaw..."
        npm install -g openclaw
        print_success "OpenClaw安装完成"
    else
        print_success "OpenClaw已安装"
    fi
    
    # 验证安装
    openclaw --version
}

restore_files() {
    print_header "恢复文件"
    
    # 恢复交易系统文件
    if [ -d "freqtrade-trading" ]; then
        print_warning "恢复交易系统文件..."
        mkdir -p "$INSTALL_DIR"
        cp -r freqtrade-trading/* "$INSTALL_DIR/"
        print_success "交易系统文件恢复完成"
    else
        print_error "未找到交易系统文件"
        exit 1
    fi
    
    # 恢复OpenClaw配置
    if [ -d ".openclaw" ]; then
        print_warning "恢复OpenClaw配置..."
        mkdir -p "$OPENCLAW_INSTALL_DIR"
        cp -r .openclaw/* "$OPENCLAW_INSTALL_DIR/"
        print_success "OpenClaw配置恢复完成"
    else
        print_warning "未找到OpenClaw配置，将使用默认配置"
    fi
}

setup_python_environment() {
    print_header "设置Python环境"
    
    cd "$INSTALL_DIR"
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        print_warning "创建Python虚拟环境..."
        python3 -m venv venv
        print_success "虚拟环境创建完成"
    else
        print_success "虚拟环境已存在"
    fi
    
    # 激活虚拟环境并安装依赖
    print_warning "安装Python依赖..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install ccxt numpy pandas flask requests python-telegram-bot
    print_success "Python依赖安装完成"
}

configure_api_keys() {
    print_header "配置API密钥"
    
    CONFIG_FILE="$INSTALL_DIR/config/final_config.json"
    
    if [ -f "$CONFIG_FILE" ]; then
        print_warning "请编辑API配置文件: $CONFIG_FILE"
        echo "需要配置以下信息:"
        echo "1. OKX API Key"
        echo "2. OKX Secret"
        echo "3. OKX Passphrase"
        echo ""
        echo "按回车键继续..."
        read -r
        
        # 使用默认编辑器打开文件
        if command -v nano &> /dev/null; then
            nano "$CONFIG_FILE"
        elif command -v vim &> /dev/null; then
            vim "$CONFIG_FILE"
        elif command -v vi &> /dev/null; then
            vi "$CONFIG_FILE"
        else
            open "$CONFIG_FILE"
        fi
        
        print_success "API配置完成"
    else
        print_error "配置文件不存在: $CONFIG_FILE"
        print_warning "请手动创建配置文件"
    fi
}

create_startup_scripts() {
    print_header "创建启动脚本"
    
    cd "$INSTALL_DIR"
    
    # 创建启动脚本
    cat > start_all.sh << 'START_EOF'
#!/bin/bash
# 启动所有交易系统组件

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
MONITOR_PID=$!
echo "   进程ID: $MONITOR_PID"

# 启动交易系统
echo "🤖 启动交易系统..."
python3 ultra_fast_trader.py > logs/trader.log 2>&1 &
TRADER_PID=$!
echo "   进程ID: $TRADER_PID"

# 启动通知器
echo "📱 启动通知器..."
python3 trade_notifier.py > logs/notifier.log 2>&1 &
NOTIFIER_PID=$!
echo "   进程ID: $NOTIFIER_PID"

# 保存PID文件
echo "$MONITOR_PID" > logs/monitor.pid
echo "$TRADER_PID" > logs/trader.pid
echo "$NOTIFIER_PID" > logs/notifier.pid

echo ""
echo "✅ 所有系统已启动"
echo "🌐 监控面板: http://localhost:8084"
echo "📊 查看日志: tail -f logs/trader.log"
echo "🛑 停止命令: ./stop_all.sh"
START_EOF
    
    chmod +x start_all.sh
    print_success "创建启动脚本: start_all.sh"
    
    # 创建停止脚本
    cat > stop_all.sh << 'STOP_EOF'
#!/bin/bash
# 停止所有交易系统组件

cd "$(dirname "$0")"

echo "🛑 停止交易系统..."
echo "="*50

# 读取PID文件并停止进程
for component in monitor trader notifier; do
    PID_FILE="logs/${component}.pid"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "停止 ${component} (PID: $PID)..."
            kill "$PID"
            sleep 1
            if kill -0 "$PID" 2>/dev/null; then
                echo "强制停止 ${component}..."
                kill -9 "$PID"
            fi
            rm -f "$PID_FILE"
            echo "✅ ${component} 已停止"
        else
            echo "⚠️  ${component} 进程不存在"
            rm -f "$PID_FILE"
        fi
    else
        echo "⚠️  ${component} PID文件不存在"
    fi
done

# 确保所有相关进程已停止
pkill -f "working_monitor.py" 2>/dev/null || true
pkill -f "ultra_fast_trader.py" 2>/dev/null || true
pkill -f "trade_notifier.py" 2>/dev/null || true

echo ""
echo "✅ 所有系统已停止"
STOP_EOF
    
    chmod +x stop_all.sh
    print_success "创建停止脚本: stop_all.sh"
    
    # 创建状态检查脚本
    cat > check_status.sh << 'STATUS_EOF'
#!/bin/bash
# 检查系统状态

cd "$(dirname "$0")"

echo "📊 系统状态检查"
echo "="*50
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查进程
echo "🔍 进程状态:"
for component in "working_monitor.py" "ultra_fast_trader.py" "trade_notifier.py"; do
    if pgrep -f "$component" > /dev/null; then
        echo "  ✅ $component: 运行中"
    else
        echo "  ❌ $component: 未运行"
    fi
done

echo ""
echo "📈 端口状态:"
if lsof -i :8084 > /dev/null 2>&1; then
    echo "  ✅ 端口8084: 监听中 (监控面板)"
else
    echo "  ❌ 端口8084: 未监听"
fi

echo ""
echo "📁 日志文件:"
for log in logs/trader.log logs/monitor.log logs/notifier.log; do
    if [ -f "$log" ]; then
        size=$(du -h "$log" | cut -f1)
        lines=$(wc -l < "$log" 2>/dev/null || echo "0")
        echo "  📄 $log: $size, $lines 行"
    else
        echo "  📄 $log: 不存在"
    fi
done

echo ""
echo "💡 命令提示:"
echo "  启动: ./start_all.sh"
echo "  停止: ./stop_all.sh"
echo "  监控: tail -f logs/trader.log"
echo "  面板: http://localhost:8084"
STATUS_EOF
    
    chmod +x check_status.sh
    print_success "创建状态检查脚本: check_status.sh"
}

test_system() {
    print_header "测试系统"
    
    cd "$INSTALL_DIR"
    
    # 测试Python环境
    print_warning "测试Python环境..."
    source venv/bin/activate
    python3 -c "import ccxt, numpy, pandas, flask; print('✅ Python依赖测试通过')"
    
    # 测试API连接（需要先配置API密钥）
    if [ -f "config/final_config.json" ]; then
        print_warning "测试API连接..."
        if python3 -c "
import json, ccxt
with open('config/final_config.json') as f:
    config = json.load(f)
exchange = ccxt.okx({
    'apiKey': config['exchange']['api_key'],
    'secret': config['exchange']['secret'],
    'password': config['exchange']['passphrase'],
    'enableRateLimit': True,
    'proxies': config['exchange']['proxies']
})
try:
    time = exchange.fetch_time()
    print(f'✅ API连接成功，服务器时间: {time}')
except Exception as e:
    print(f'❌ API连接失败: {e}')
" 2>/dev/null; then
            print_success "API连接测试通过"
        else
            print_warning "API连接测试失败（可能需要先配置API密钥）"
        fi
    fi
    
    # 测试OpenClaw
    print_warning "测试OpenClaw..."
    if command -v openclaw &> /dev/null; then
        openclaw --version
        print_success "OpenClaw测试通过"
    else
        print_error "OpenClaw未安装"
    fi
}

print_summary() {
    print_header "安装完成摘要"
    
    echo -e "${GREEN}🎉 交易系统安装完成！${NC}"
    echo ""
    echo "📁 安装目录: $INSTALL_DIR"
    echo "⚙️  OpenClaw配置: $OPENCLAW_INSTALL_DIR"
    echo ""
    echo "🚀 可用命令:"
    echo "  cd $INSTALL_DIR"
    echo "  ./start_all.sh    # 启动所有系统"
    echo "  ./stop_all.sh     # 停止所有系统"
    echo "  ./check_status.sh # 检查系统状态"
    echo ""
    echo "🌐 监控面板: http://localhost:8084"
    echo "📊 查看日志: tail -f $INSTALL_DIR/logs/trader.log"
    echo ""
    echo "⚠️  重要提醒:"
    echo "  1. 请确保已配置 config/final_config.json 中的API密钥"
    echo "  2. 如果需要代理，请确保代理服务器运行"
    echo "  3. 首次运行前建议先测试系统"
    echo ""
    echo "📝 后续步骤:"
    echo "  1. 配置API密钥"
    echo "  2. 运行 ./start_all.sh 启动系统"
    echo "  3. 访问 http://localhost:8084 查看监控面板"
}

main() {
    print_header "在新Mac上安装交易系统"
    
    # 检查是否在备份目录中运行
    if [ ! -d "freqtrade-trading" ] && [ ! -d ".openclaw" ]; then
        print_error "请在备份目录中运行此脚本"
        echo "请先将备份文件复制到新Mac，然后进入备份目录运行:"
        echo "cd /path/to/backup/directory"
        echo "./install_on_new_mac.sh"
        exit 1
    fi
    
    install_dependencies
    install_openclaw
    restore_files
    setup_python_environment
    configure_api_keys
    create_startup_scripts
    test_system
    print_summary
}

# 运行主函数
main
EOF
    
    chmod +x "$BACKUP_DIR/install_on_new_mac.sh"
    print_success "安装脚本创建完成: $BACKUP_DIR/install_on_new_mac.sh"
    
    # 创建传输包
    print_header "创建传输包"
    cd "$BACKUP_DIR/.."
    tar -czf "$PACKAGE_FILE" "$(basename "$BACKUP_DIR")"
    print_success "传输包创建完成: $PACKAGE_FILE"
    
    # 显示传输说明
    print_header "传输说明"
    echo -e "${GREEN}✅ 备份准备完成！${NC}"
    echo ""
    echo "📦 传输包位置: $PACKAGE_FILE"
    echo "📁 备份目录: $BACKUP_DIR"
    echo ""
    echo "📤 传输到新Mac的方法:"
    echo ""
    echo "方法1: 使用scp命令传输"
    echo "----------------------------------------"
    echo "在新Mac上运行:"
    echo "scp ${SOURCE_USER}@${SOURCE_IP}:${PACKAGE_FILE} /tmp/"
    echo ""
    echo "方法2: 使用U盘或外部硬盘"
    echo "----------------------------------------"
    echo "复制整个目录: $BACKUP_DIR"
    echo ""
    echo "方法3: 使用云存储"
    echo "----------------------------------------"
    echo "上传到Google Drive/Dropbox等"
    echo ""
    echo "🚀 在新Mac上的安装步骤:"
    echo "1. 将备份文件复制到新Mac"
    echo "2. 解压备份文件: tar -xzf /tmp/trading_system_package.tar.gz -C /tmp/"
    echo "3. 进入备份目录: cd /tmp/trading_system_backup_*"
    echo "4. 运行安装脚本: ./install_on_new_mac.sh"
    echo ""
    echo "📋 需要手动配置的信息:"
    echo "1. OKX API密钥 (在 config/final_config.json 中)"
    echo "2. Telegram Bot Token (如果需要)"
    echo "3. 代理服务器配置 (如果需要)"
}

install_on_new_mac() {
    print_header "第二步：在新Mac上安装"
    
    # 检查是否在备份目录中
    if [ ! -f "install_on_new_mac.sh" ]; then
        print_error "未找到安装脚本"
        echo "请确保你在备份目录中运行此命令"
        echo "或者使用: ./copy_to_new_mac.sh install /path/to/backup/directory"
        exit 1
    fi
    
    # 运行安装脚本
    ./install_on_new_mac.sh
}

# 主函数
main() {
    case "$1" in
        "prepare")
            prepare_backup
            ;;
        "install")
            if [ -n "$2" ]; then
                cd "$2"
            fi
            install_on_new_mac
            ;;
        *)
            echo "用法:"
            echo "  在第一台Mac上准备备份: ./copy_to_new_mac.sh prepare"
            echo "  在新Mac上安装: ./copy_to_new_mac.sh install [备份目录路径]"
            echo ""
            echo "示例:"
            echo "  1. 在第一台Mac上: ./copy_to_new_mac.sh prepare"
            echo "  2. 复制备份文件到新Mac"
            echo "  3. 在新Mac上: ./copy_to_new_mac.sh install /path/to/backup"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"