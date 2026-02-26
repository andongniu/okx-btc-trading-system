#!/bin/bash

# Freqtrade 管理脚本

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

case "$1" in
    start)
        echo "🚀 启动 Freqtrade 交易机器人..."
        docker-compose up -d
        echo "✅ Freqtrade 已启动"
        echo "📊 查看日志: ./manage.sh logs"
        ;;
    stop)
        echo "🛑 停止 Freqtrade..."
        docker-compose down
        echo "✅ Freqtrade 已停止"
        ;;
    restart)
        echo "🔄 重启 Freqtrade..."
        docker-compose restart
        echo "✅ Freqtrade 已重启"
        ;;
    logs)
        echo "📋 显示日志..."
        docker-compose logs -f
        ;;
    status)
        echo "🔍 检查状态..."
        docker-compose ps
        ;;
    shell)
        echo "🐚 进入容器shell..."
        docker-compose exec freqtrade /bin/bash
        ;;
    download-data)
        echo "📥 下载交易数据..."
        docker-compose run --rm freqtrade download-data \
            --config /freqtrade/config/config.json \
            --exchange binance \
            -t 5m 1h 1d \
            --days 30
        ;;
    backtest)
        echo "📈 运行回测..."
        docker-compose run --rm freqtrade backtesting \
            --config /freqtrade/config/config.json \
            --strategy SampleStrategy \
            --timerange=20240101-20241231
        ;;
    trade)
        echo "💹 开始交易..."
        # 停止当前容器
        docker-compose down
        # 修改配置为交易模式
        sed -i '' 's/"download-data"/"trade"/' docker-compose.yml
        sed -i '' 's/"dry_run": true/"dry_run": true/' config/config.json
        # 启动交易
        docker-compose up -d
        echo "✅ 交易模式已启动"
        ;;
    dry-run)
        echo "🎮 模拟交易模式..."
        # 停止当前容器
        docker-compose down
        # 修改配置为模拟交易
        sed -i '' 's/"trade"/"download-data"/' docker-compose.yml
        sed -i '' 's/"dry_run": false/"dry_run": true/' config/config.json
        # 启动模拟交易
        docker-compose up -d
        echo "✅ 模拟交易模式已启动"
        ;;
    update)
        echo "🔄 更新 Freqtrade 镜像..."
        docker-compose pull
        echo "✅ 镜像已更新"
        ;;
    *)
        echo "Freqtrade 自动化交易系统管理脚本"
        echo "用法: ./manage.sh {start|stop|restart|logs|status|shell|download-data|backtest|trade|dry-run|update}"
        echo ""
        echo "命令说明:"
        echo "  start         启动服务（初始为数据下载模式）"
        echo "  stop          停止服务"
        echo "  restart       重启服务"
        echo "  logs          查看容器日志"
        echo "  status        查看服务状态"
        echo "  shell         进入容器命令行"
        echo "  download-data 下载交易数据"
        echo "  backtest      运行回测测试"
        echo "  trade         切换到实盘交易模式（需要配置API密钥）"
        echo "  dry-run       切换到模拟交易模式"
        echo "  update        更新 Docker 镜像"
        exit 1
        ;;
esac