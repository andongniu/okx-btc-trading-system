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
