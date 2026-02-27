#!/bin/bash
# 检查所有服务状态

echo "🔍 检查所有服务状态"
echo "="*50

# 检查OpenClaw
echo "📦 OpenClaw状态:"
if command -v openclaw &> /dev/null; then
    echo "  ✅ OpenClaw已安装"
    openclaw --version
else
    echo "  ❌ OpenClaw未安装"
fi

if openclaw gateway status 2>/dev/null | grep -q "running"; then
    echo "  ✅ OpenClaw网关运行中"
else
    echo "  ❌ OpenClaw网关未运行"
fi

echo ""
echo "🤖 交易系统状态:"
if [ -d ~/okx-btc-trading ]; then
    echo "  ✅ 交易系统目录存在"
    cd ~/okx-btc-trading 2>/dev/null && ./status.sh 2>/dev/null || echo "  ❌ 无法检查交易系统状态"
else
    echo "  ❌ 交易系统目录不存在"
fi

echo ""
echo "🌐 网络服务状态:"
# 检查监控面板
if lsof -i :8084 > /dev/null 2>&1; then
    echo "  ✅ 监控面板运行中 (端口8084)"
    echo "      访问: http://localhost:8084"
else
    echo "  ❌ 监控面板未运行"
fi

# 检查OpenClaw网关
if lsof -i :3000 > /dev/null 2>&1; then
    echo "  ✅ OpenClaw网关运行中 (端口3000)"
else
    echo "  ❌ OpenClaw网关未运行"
fi

echo ""
echo "📱 Telegram配置:"
if [ -f ~/okx-btc-trading/config/telegram_config.json ]; then
    if grep -q "YOUR_BOT_TOKEN" ~/okx-btc-trading/config/telegram_config.json; then
        echo "  ⚠️  Telegram配置未完成 (使用模板)"
    else
        echo "  ✅ Telegram配置已完成"
    fi
else
    echo "  ❌ Telegram配置文件不存在"
fi

echo ""
echo "🔑 OKX API配置:"
if [ -f ~/okx-btc-trading/config/final_config.json ]; then
    if grep -q "YOUR_OKX_API_KEY" ~/okx-btc-trading/config/final_config.json; then
        echo "  ⚠️  OKX API配置未完成 (使用模板)"
    else
        echo "  ✅ OKX API配置已完成"
    fi
else
    echo "  ❌ OKX API配置文件不存在"
fi

echo ""
echo "📊 进程状态:"
for process in "working_monitor.py" "ultra_fast_trader.py" "trade_notifier.py"; do
    if pgrep -f "$process" > /dev/null; then
        echo "  ✅ $process: 运行中"
    else
        echo "  ❌ $process: 未运行"
    fi
done

echo ""
echo "💡 建议操作:"
echo "  1. 如果OpenClaw未安装: npm install -g openclaw"
echo "  2. 如果交易系统未部署: curl -sSL https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash"
echo "  3. 如果服务未运行: cd ~/okx-btc-trading && ./launch.sh"
echo "  4. 如果配置未完成: 编辑 ~/okx-btc-trading/config/final_config.json"