#!/bin/bash
# 重置系统（从头开始）

echo "🔄 重置交易系统"
echo "="*50

read -p "⚠️  这将停止所有服务并清理配置。继续？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作取消"
    exit 1
fi

# 步骤1: 停止所有服务
echo ""
echo "1. 🛑 停止所有服务..."
if [ -d ~/okx-btc-trading ]; then
    cd ~/okx-btc-trading
    ./stop.sh 2>/dev/null || true
    echo "  ✅ 交易系统已停止"
else
    echo "  ⚠️  交易系统目录不存在"
fi

# 停止OpenClaw
openclaw gateway stop 2>/dev/null || true
echo "  ✅ OpenClaw已停止"

# 步骤2: 备份重要配置
echo ""
echo "2. 💾 备份重要配置..."
BACKUP_DIR="$HOME/trading_system_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f ~/okx-btc-trading/config/final_config.json ]; then
    cp ~/okx-btc-trading/config/final_config.json "$BACKUP_DIR/"
    echo "  ✅ 备份API配置"
fi

if [ -f ~/okx-btc-trading/config/telegram_config.json ]; then
    cp ~/okx-btc-trading/config/telegram_config.json "$BACKUP_DIR/"
    echo "  ✅ 备份Telegram配置"
fi

if [ -f ~/.openclaw/openclaw.json ]; then
    cp ~/.openclaw/openclaw.json "$BACKUP_DIR/"
    echo "  ✅ 备份OpenClaw配置"
fi

echo "  备份位置: $BACKUP_DIR"

# 步骤3: 清理旧系统
echo ""
echo "3. 🧹 清理旧系统..."
if [ -d ~/okx-btc-trading ]; then
    read -p "  删除整个交易系统目录？ (~/okx-btc-trading) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf ~/okx-btc-trading
        echo "  ✅ 交易系统目录已删除"
    else
        echo "  ⚠️  保留交易系统目录"
    fi
fi

# 清理OpenClaw配置（可选）
read -p "  清理OpenClaw配置？ (~/.openclaw) (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ~/.openclaw
    echo "  ✅ OpenClaw配置已清理"
else
    echo "  ⚠️  保留OpenClaw配置"
fi

# 步骤4: 重新安装
echo ""
echo "4. 🚀 重新安装系统..."
echo ""
echo "选择安装方式:"
echo "  1) 一键部署 (推荐)"
echo "  2) 分步部署"
echo "  3) 退出"
read -p "选择 (1-3): " choice

case $choice in
    1)
        echo "开始一键部署..."
        curl -sSL https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash
        ;;
    2)
        echo "开始分步部署..."
        echo ""
        echo "第一步: 克隆仓库"
        git clone https://github.com/andongniu/okx-btc-trading-system.git ~/okx-btc-trading
        cd ~/okx-btc-trading
        
        echo ""
        echo "第二步: 运行安装脚本"
        chmod +x setup.sh
        ./setup.sh
        
        echo ""
        echo "第三步: 恢复配置（如果需要）"
        if [ -d "$BACKUP_DIR" ]; then
            read -p "从备份恢复配置？ (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cp "$BACKUP_DIR/final_config.json" config/ 2>/dev/null || true
                cp "$BACKUP_DIR/telegram_config.json" config/ 2>/dev/null || true
                cp "$BACKUP_DIR/openclaw.json" ~/.openclaw/ 2>/dev/null || true
                echo "  ✅ 配置已恢复"
            fi
        fi
        
        echo ""
        echo "第四步: 配置系统"
        echo "请编辑以下文件:"
        echo "  ~/okx-btc-trading/config/final_config.json - OKX API配置"
        echo "  ~/okx-btc-trading/config/telegram_config.json - Telegram配置"
        echo "  ~/.openclaw/openclaw.json - OpenClaw配置"
        
        read -p "按回车键继续..."
        ;;
    3)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

# 步骤5: 启动系统
echo ""
echo "5. 🎯 启动系统..."
if [ -d ~/okx-btc-trading ]; then
    cd ~/okx-btc-trading
    ./launch.sh
else
    echo "  ❌ 交易系统目录不存在，请先完成安装"
fi

# 步骤6: 验证
echo ""
echo "6. ✅ 验证安装..."
if [ -d ~/okx-btc-trading ]; then
    cd ~/okx-btc-trading
    ./status.sh
else
    echo "  ❌ 无法验证，目录不存在"
fi

echo ""
echo "="*50
echo "🔄 重置完成！"
echo ""
echo "📋 下一步:"
echo "  1. 访问监控面板: http://localhost:8084"
echo "  2. 测试系统: ./test_all_components.sh"
echo "  3. 查看日志: tail -f logs/trader.log"
echo "  4. 备份位置: $BACKUP_DIR"
echo ""
echo "⚠️  重要提醒:"
echo "  - 如果从备份恢复了配置，请验证API密钥是否正确"
echo "  - 确保Telegram Bot已正确配置"
echo "  - 首次交易建议先小额测试"
echo ""
echo "📞 获取帮助:"
echo "  - 查看文档: README.md"
echo "  - 测试组件: ./test_all_components.sh"
echo "  - 联系支持: GitHub Issues 或 你的朋友"