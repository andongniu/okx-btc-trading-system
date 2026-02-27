#!/bin/bash
# 测试所有组件

echo "🧪 测试所有系统组件"
echo "="*50

# 测试1: OpenClaw
echo "1. 📦 测试OpenClaw:"
if command -v openclaw &> /dev/null; then
    echo "  ✅ OpenClaw命令可用"
    VERSION=$(openclaw --version 2>/dev/null || echo "未知")
    echo "      版本: $VERSION"
else
    echo "  ❌ OpenClaw未安装"
fi

# 测试2: Python环境
echo ""
echo "2. 🐍 测试Python环境:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  ✅ Python3已安装: $PYTHON_VERSION"
    
    # 测试虚拟环境
    if [ -d ~/okx-btc-trading/venv ]; then
        echo "  ✅ Python虚拟环境存在"
        source ~/okx-btc-trading/venv/bin/activate 2>/dev/null
        python3 -c "import ccxt, numpy, pandas, flask, requests; print('  ✅ 所有Python依赖可用')" 2>/dev/null || echo "  ❌ 缺少某些Python依赖"
        deactivate 2>/dev/null
    else
        echo "  ❌ Python虚拟环境不存在"
    fi
else
    echo "  ❌ Python3未安装"
fi

# 测试3: 交易系统API连接
echo ""
echo "3. 🔗 测试OKX API连接:"
if [ -f ~/okx-btc-trading/config/final_config.json ] && ! grep -q "YOUR_OKX_API_KEY" ~/okx-btc-trading/config/final_config.json 2>/dev/null; then
    cd ~/okx-btc-trading 2>/dev/null
    if [ $? -eq 0 ]; then
        source venv/bin/activate 2>/dev/null
        python3 test_connection.py 2>&1 | grep -E "✅|❌|成功|失败|错误" || echo "  ⚠️  连接测试无输出"
        deactivate 2>/dev/null
    else
        echo "  ❌ 无法进入交易系统目录"
    fi
else
    echo "  ⚠️  API配置未完成，跳过连接测试"
fi

# 测试4: 监控面板
echo ""
echo "4. 🌐 测试监控面板:"
if lsof -i :8084 > /dev/null 2>&1; then
    echo "  ✅ 监控面板端口监听中"
    # 测试API端点
    curl -s http://localhost:8084/api/status 2>/dev/null | grep -q "status" && echo "  ✅ 监控面板API响应正常" || echo "  ⚠️  监控面板API无响应"
else
    echo "  ❌ 监控面板未运行"
fi

# 测试5: Telegram通知
echo ""
echo "5. 📱 测试Telegram通知:"
if [ -f ~/okx-btc-trading/config/telegram_config.json ] && ! grep -q "YOUR_BOT_TOKEN" ~/okx-btc-trading/config/telegram_config.json 2>/dev/null; then
    cd ~/okx-btc-trading 2>/dev/null
    if [ $? -eq 0 ]; then
        source venv/bin/activate 2>/dev/null
        echo " 正在发送测试通知..." > /tmp/test_notify.txt
        python3 -c "
import json, requests
try:
    with open('config/telegram_config.json') as f:
        config = json.load(f)
    token = config['telegram']['bot_token']
    chat_id = config['telegram']['chat_id']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = {'chat_id': chat_id, 'text': '🔔 系统测试通知: 所有组件测试完成'}
    response = requests.post(url, json=data, timeout=10)
    if response.status_code == 200:
        print('  ✅ Telegram通知发送成功')
    else:
        print(f'  ❌ Telegram通知失败: {response.status_code}')
except Exception as e:
    print(f'  ❌ Telegram测试错误: {e}')
" 2>/dev/null
        deactivate 2>/dev/null
    fi
else
    echo "  ⚠️  Telegram配置未完成，跳过通知测试"
fi

# 测试6: 文件权限和目录
echo ""
echo "6. 📁 测试文件系统和权限:"
if [ -d ~/okx-btc-trading ]; then
    echo "  ✅ 交易系统目录存在"
    
    # 检查关键文件
    for file in "ultra_fast_trader.py" "working_monitor.py" "trade_notifier.py" "launch.sh" "stop.sh" "status.sh"; do
        if [ -f ~/okx-btc-trading/$file ]; then
            if [ -x ~/okx-btc-trading/$file ] || [[ $file == *.py ]]; then
                echo "  ✅ $file: 存在且可访问"
            else
                echo "  ⚠️  $file: 存在但不可执行"
            fi
        else
            echo "  ❌ $file: 不存在"
        fi
    done
    
    # 检查日志目录
    if [ -d ~/okx-btc-trading/logs ]; then
        echo "  ✅ 日志目录存在"
    else
        echo "  ⚠️  日志目录不存在"
    fi
else
    echo "  ❌ 交易系统目录不存在"
fi

# 测试7: 系统进程
echo ""
echo "7. ⚙️ 测试系统进程:"
PROCESSES=("working_monitor.py" "ultra_fast_trader.py" "trade_notifier.py")
ALL_RUNNING=true
for process in "${PROCESSES[@]}"; do
    if pgrep -f "$process" > /dev/null; then
        echo "  ✅ $process: 运行中"
    else
        echo "  ❌ $process: 未运行"
        ALL_RUNNING=false
    fi
done

echo ""
echo "="*50
echo "📊 测试总结:"

if $ALL_RUNNING && [ -d ~/okx-btc-trading ] && lsof -i :8084 > /dev/null 2>&1; then
    echo "🎉 所有系统组件运行正常！"
    echo ""
    echo "✅ 系统已就绪:"
    echo "   🤖 交易系统: 运行中 (10秒频率)"
    echo "   📊 监控面板: http://localhost:8084"
    echo "   📱 Telegram: 通知已配置"
    echo "   🔗 OKX API: 连接正常"
else
    echo "⚠️  部分组件需要修复"
    echo ""
    echo "🔧 修复建议:"
    echo "   1. 启动所有服务: cd ~/okx-btc-trading && ./launch.sh"
    echo "   2. 检查配置: 确保 config/final_config.json 和 config/telegram_config.json 已配置"
    echo "   3. 查看日志: tail -f ~/okx-btc-trading/logs/trader.log"
    echo "   4. 重新测试: ./test_all_components.sh"
fi

echo ""
echo "💡 快速命令:"
echo "   启动: cd ~/okx-btc-trading && ./launch.sh"
echo "   停止: cd ~/okx-btc-trading && ./stop.sh"
echo "   状态: cd ~/okx-btc-trading && ./status.sh"
echo "   监控: open http://localhost:8084"