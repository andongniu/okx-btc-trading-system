#!/bin/bash
# 务实高杠杆交易系统启动脚本

echo "🚀 启动务实高杠杆交易系统"
echo "=========================================="
echo "目标: 200U → 400U (100%月回报)"
echo "策略: 三重确认 + 动态杠杆 + 严格风控"
echo "=========================================="

# 检查环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在"
    echo "   创建: python3 -m venv venv"
    echo "   激活: source venv/bin/activate"
    echo "   安装: pip install ccxt pandas numpy flask"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查配置文件
if [ ! -f "config/final_config.json" ]; then
    echo "❌ 配置文件不存在: config/final_config.json"
    exit 1
fi

# 检查核心文件
if [ ! -f "realistic_trader.py" ]; then
    echo "❌ 交易引擎不存在: realistic_trader.py"
    exit 1
fi

# 创建必要目录
mkdir -p logs templates

# 测试API连接
echo ""
echo "🔐 测试OKX API连接..."
python3 -c "
import ccxt
import json

try:
    with open('config/final_config.json', 'r') as f:
        config = json.load(f)
    
    exchange = ccxt.okx({
        'apiKey': config['exchange']['api_key'],
        'secret': config['exchange']['secret'],
        'password': config['exchange']['passphrase'],
        'enableRateLimit': True,
        'proxies': config['exchange']['proxies'],
        'options': {'defaultType': 'swap'}
    })
    
    # 测试连接
    ticker = exchange.fetch_ticker(config['exchange']['symbol'])
    print('✅ API连接成功')
    print(f'   当前价格: \${ticker[\"last\"]:,.2f}')
    print(f'   24h涨跌: {ticker[\"percentage\"]:.2f}%')
    
    # 检查余额
    balance = exchange.fetch_balance()
    usdt = balance.get('total', {}).get('USDT', 0)
    print(f'   账户余额: {usdt:.2f} USDT')
    
    if usdt < 200:
        print('⚠️  余额不足，需要转入至少200 USDT')
    
except Exception as e:
    print(f'❌ API连接失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ API测试失败"
    exit 1
fi

# 显示系统信息
echo ""
echo "📋 系统配置:"
echo "   初始资金: \$200"
echo "   目标资金: \$400"
echo "   时间框架: 15分钟 + 1小时"
echo "   杠杆范围: 35-55倍"
echo "   每日限制: 3次交易"
echo "   止损: 1.5%"
echo "   止盈: 3.0% (2:1盈亏比)"

# 启动选项
echo ""
echo "🎮 启动选项:"
echo "1. 仅启动监控仪表盘"
echo "2. 启动模拟交易测试"
echo "3. 启动完整交易系统 (实盘)"
echo "4. 运行策略回测"
echo ""
read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo "📊 启动监控仪表盘..."
        if [ ! -f "realistic_dashboard.py" ]; then
            echo "❌ 仪表盘文件不存在"
            echo "   创建: realistic_dashboard.py"
            exit 1
        fi
        python3 realistic_dashboard.py &
        DASH_PID=$!
        echo "✅ 仪表盘已启动 (PID: $DASH_PID)"
        echo "🌐 访问: http://localhost:8080"
        echo "🛑 停止: kill $DASH_PID"
        ;;
    2)
        echo "🧪 启动模拟交易测试..."
        echo "⚠️  模拟交易模式开发中"
        echo "📊 先启动监控仪表盘..."
        python3 realistic_dashboard.py &
        DASH_PID=$!
        echo "✅ 仪表盘已启动 (PID: $DASH_PID)"
        echo "🌐 访问: http://localhost:8080"
        ;;
    3)
        echo "🚀 启动完整交易系统..."
        echo "⚠️  实盘交易有风险！请确认:"
        echo "   1. 账户余额 ≥ 200 USDT"
        echo "   2. 理解所有风险"
        echo "   3. 准备好紧急停止"
        echo ""
        read -p "确认启动实盘交易? (y/N): " confirm
        if [[ $confirm != "y" && $confirm != "Y" ]]; then
            echo "❌ 已取消"
            exit 0
        fi
        echo "📊 启动监控仪表盘..."
        python3 realistic_dashboard.py &
        DASH_PID=$!
        echo "✅ 仪表盘已启动 (PID: $DASH_PID)"
        echo "🌐 访问: http://localhost:8080"
        echo "⚠️  实盘交易引擎开发中..."
        ;;
    4)
        echo "📈 运行策略回测..."
        if [ ! -f "run_realistic_backtest.py" ]; then
            echo "❌ 回测脚本不存在"
            echo "   创建: run_realistic_backtest.py"
            exit 1
        fi
        python3 run_realistic_backtest.py
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

# 显示重要信息
echo ""
echo "=========================================="
echo "📋 重要信息:"
echo "   项目: 200U→400U务实交易挑战"
echo "   时间: 30天 (至2026-03-27)"
echo "   策略: 三重确认高杠杆"
echo "   风险: 高但可控"
echo ""
echo "⚠️  风险警告:"
echo "   1. 高杠杆放大亏损风险"
echo "   2. 加密货币波动剧烈"
echo "   3. 可能损失全部资金"
echo "   4. 仅使用可承受损失的资金"
echo ""
echo "🆘 紧急停止:"
echo "   1. 浏览器访问仪表盘点击停止"
echo "   2. 命令行: kill [PID]"
echo "   3. 直接关闭终端"
echo ""
echo "📞 监控指标:"
echo "   日亏损限制: \$12 (6%)"
echo "   总回撤限制: \$40 (20%)"
echo "   连续亏损暂停: 2次"
echo "   成本覆盖目标: 第3天前"
echo "=========================================="

# 保存PID文件
echo $DASH_PID > /tmp/realistic_trader.pid 2>/dev/null || true

echo ""
echo "✅ 系统启动完成"
echo "   查看日志: tail -f logs/realistic_trader.log"
echo "   监控状态: http://localhost:8080"
echo "   停止系统: ./stop_realistic_system.sh"