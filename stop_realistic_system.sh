#!/bin/bash
# 停止务实交易系统

echo "🛑 停止务实交易系统..."
echo "=========================================="

# 查找并停止相关进程
pids=$(ps aux | grep -E "realistic_dashboard\.py|realistic_trader\.py" | grep -v grep | awk '{print $2}')

if [ -z "$pids" ]; then
    echo "✅ 没有找到运行中的交易进程"
else
    echo "找到进程: $pids"
    kill $pids 2>/dev/null
    sleep 2
    
    # 检查是否停止
    running=$(ps aux | grep -E "realistic_dashboard\.py|realistic_trader\.py" | grep -v grep)
    if [ -z "$running" ]; then
        echo "✅ 所有交易进程已停止"
    else
        echo "⚠️  强制停止剩余进程..."
        kill -9 $pids 2>/dev/null
        echo "✅ 强制停止完成"
    fi
fi

# 清理PID文件
rm -f /tmp/realistic_trader.pid 2>/dev/null

echo ""
echo "📋 系统状态:"
echo "   交易系统: 已停止"
echo "   监控面板: 已关闭"
echo "   端口释放: 8080"
echo ""
echo "📊 日志文件位置:"
echo "   logs/realistic_trader.log - 交易日志"
echo "   logs/ 目录 - 其他日志文件"
echo ""
echo "🔧 如需重新启动:"
echo "   ./start_realistic_system.sh"
echo ""
echo "✅ 系统停止完成"