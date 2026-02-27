# 👫 朋友完整部署教程 - 从零到交易

## 🎯 目标
让朋友在30分钟内完成：
1. ✅ 安装OpenClaw
2. ✅ 配置OpenClaw（海外无需代理）
3. ✅ 部署交易系统
4. ✅ 配置Telegram机器人
5. ✅ 开始交易

---

## 📋 第一部分：安装OpenClaw

### 步骤1.1：安装基础软件
```bash
# 1. 打开终端 (Terminal)
# 2. 安装Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 3. 安装Node.js（OpenClaw需要）
brew install node@22

# 4. 安装Python（交易系统需要）
brew install python@3.9

# 5. 安装Git
brew install git
```

### 步骤1.2：安装OpenClaw
```bash
# 1. 全局安装OpenClaw
npm install -g openclaw

# 2. 验证安装
openclaw --version
# 应该显示类似: 2026.2.19
```

### 步骤1.3：初始化OpenClaw
```bash
# 1. 创建工作目录
mkdir -p ~/openclaw-workspace
cd ~/openclaw-workspace

# 2. 初始化OpenClaw配置
openclaw init

# 3. 启动OpenClaw网关
openclaw gateway start

# 4. 检查状态
openclaw status
```

---

## 🔧 第二部分：配置OpenClaw（海外优化版）

### 步骤2.1：创建OpenClaw配置文件
```bash
# 1. 创建配置文件目录
mkdir -p ~/.openclaw

# 2. 创建配置文件
cat > ~/.openclaw/openclaw.json << 'EOF'
{
  "profiles": {
    "default": {
      "model": "deepseek/deepseek-chat",
      "maxTokens": 4096,
      "contextWindow": 128000,
      "compaction": {
        "strategy": "window+summary",
        "mode": "safeguard",
        "windowSize": 8,
        "summarizeTrigger": 9,
        "summaryMaxTokens": 450,
        "nextContextMaxTokens": 320
      },
      "reply": {
        "maxTokens": 900
      },
      "toolOutputPolicy": "summarize+ref",
      "codePolicy": "diff-first",
      "memory": {
        "profilePersistence": true
      }
    }
  },
  "activeProfile": "default",
  "gateway": {
    "host": "127.0.0.1",
    "port": 3000
  }
}
EOF
```

### 步骤2.2：创建工作空间配置
```bash
# 1. 创建工作空间目录
mkdir -p ~/.openclaw/workspace

# 2. 创建SOUL.md（定义AI助手性格）
cat > ~/.openclaw/workspace/SOUL.md << 'EOF'
# SOUL.md - 交易助手

## 核心特性
- **专业交易助手**：专注于加密货币交易
- **快速响应**：10秒频率交易决策
- **风险意识**：严格的风险控制
- **简洁高效**：直接给出交易建议
- **24/7监控**：全天候市场监控

## 工作原则
1. 优先执行交易相关任务
2. 严格遵守风险参数
3. 实时监控市场变化
4. 及时发送交易通知
5. 保持系统稳定运行
EOF

# 3. 创建USER.md（用户信息）
cat > ~/.openclaw/workspace/USER.md << 'EOF'
# USER.md - 关于朋友

- **名称**: [朋友的名字]
- **称呼**: [朋友喜欢的称呼]
- **时区**: [朋友的时区，如America/New_York]
- **交易经验**: [初级/中级/高级]
- **风险偏好**: [保守/适中/激进]

## 交易偏好
- **主要交易对**: BTC/USDT
- **交易类型**: 永续合约
- **杠杆偏好**: 动态调整
- **风险控制**: 严格止损止盈

## 联系方式
- **Telegram**: [朋友的Telegram用户名]
- **通知偏好**: 所有交易通知
EOF

# 4. 创建snapshot.profile（系统快照）
cat > ~/.openclaw/workspace/snapshot.profile << 'EOF'
# snapshot.profile - 系统配置快照

## 系统信息
- OpenClaw版本: 2026.2.19
- 模型: deepseek/deepseek-chat
- 时区: [朋友的时区]
- 工作目录: ~/openclaw-workspace

## 交易系统配置
- 项目名称: okx-btc-trading-system
- 交易频率: 10秒
- 监控面板: 端口8084
- 通知系统: Telegram

## 环境变量
- 无需代理（海外直连）
- Python版本: 3.9+
- Node.js版本: 22+
EOF
```

### 步骤2.3：启动OpenClaw服务
```bash
# 1. 启动网关服务
openclaw gateway restart

# 2. 检查服务状态
openclaw gateway status

# 3. 测试连接
curl http://127.0.0.1:3000/status
```

---

## 🚀 第三部分：部署交易系统

### 步骤3.1：一键部署交易系统
```bash
# 1. 运行部署脚本（最简单方式）
curl -sSL https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash

# 或者分步部署：
# 2. 克隆仓库
git clone https://github.com/andongniu/okx-btc-trading-system.git
cd okx-btc-trading-system

# 3. 运行安装脚本
chmod +x setup.sh
./setup.sh
```

### 步骤3.2：配置OKX API密钥
```bash
# 1. 进入项目目录
cd ~/okx-btc-trading

# 2. 创建配置文件（从模板）
cp config/final_config.json.template config/final_config.json

# 3. 编辑配置文件
nano config/final_config.json
```

**需要填入的内容**：
```json
{
  "exchange": {
    "api_key": "你的OKX_API_KEY",
    "secret": "你的OKX_SECRET_KEY",
    "passphrase": "你的OKX_PASSPHRASE",
    "proxies": {
      "http": "",
      "https": ""
    }
  }
}
```

**注意**：海外用户无需代理，所以 `proxies` 留空。

### 步骤3.3：获取OKX API密钥
1. **登录OKX**：https://www.okx.com
2. **创建API**：
   - 点击右上角头像 → "API"
   - 点击 "创建API"
   - API名称：`BTC-Trading-System`
   - 权限选择：✅ 读取，✅ 交易
   - ❌ 不要选择"提现"权限！
3. **保存密钥**：
   - 复制 **API Key**
   - 复制 **Secret Key**（只显示一次！）
   - 设置并记住 **Passphrase**

### 步骤3.4：启动交易系统
```bash
# 1. 进入项目目录
cd ~/okx-btc-trading

# 2. 启动所有服务
./launch.sh

# 3. 检查状态
./status.sh

# 4. 访问监控面板
open http://localhost:8084
```

---

## 🤖 第四部分：配置Telegram机器人

### 步骤4.1：创建Telegram Bot
1. **打开Telegram**，搜索 `@BotFather`
2. **发送命令**：`/newbot`
3. **设置Bot信息**：
   - Bot名称：`[朋友名字] Trading Bot`
   - Bot用户名：`[朋友名字]_trading_bot`（必须以_bot结尾）
4. **保存Token**：复制 `HTTP API Token`（格式：`数字:字母数字组合`）

### 步骤4.2：获取Chat ID
1. **创建/打开与Bot的私聊**
2. **发送任意消息**给Bot
3. **获取Chat ID**：
   ```bash
   # 使用这个API获取Chat ID
   curl -s "https://api.telegram.org/bot你的BOT_TOKEN/getUpdates" | python3 -m json.tool
   ```
   在返回的JSON中找到 `"chat":{"id":数字}`

### 步骤4.3：配置Telegram通知
```bash
# 1. 进入项目目录
cd ~/okx-btc-trading

# 2. 创建Telegram配置
cp config/telegram_config.json.template config/telegram_config.json

# 3. 编辑配置文件
nano config/telegram_config.json
```

**填入内容**：
```json
{
  "telegram": {
    "bot_token": "你的BOT_TOKEN",
    "chat_id": "你的CHAT_ID"
  }
}
```

### 步骤4.4：测试Telegram通知
```bash
# 1. 测试通知系统
cd ~/okx-btc-trading
source venv/bin/activate
python3 send_test_notification.py

# 2. 应该收到Telegram消息
```

---

## 🔗 第五部分：连接OpenClaw与交易系统

### 步骤5.1：创建OpenClaw交易技能
```bash
# 1. 创建技能目录
mkdir -p ~/.openclaw/workspace/skills/trading

# 2. 创建交易技能文件
cat > ~/.openclaw/workspace/skills/trading/SKILL.md << 'EOF'
# 🚀 交易系统管理技能

## 功能
1. 启动/停止交易系统
2. 查看交易状态
3. 检查持仓情况
4. 查看系统日志
5. 发送交易通知

## 命令
- "启动交易" - 启动交易系统
- "停止交易" - 停止交易系统
- "查看状态" - 查看系统状态
- "检查持仓" - 查看当前持仓
- "查看日志" - 查看交易日志

## 集成
- 交易系统: ~/okx-btc-trading/
- 监控面板: http://localhost:8084
- Telegram通知: 已配置
EOF
```

### 步骤5.2：创建自动化脚本
```bash
# 1. 创建OpenClaw自动化脚本
cat > ~/.openclaw/workspace/auto_trading.sh << 'EOF'
#!/bin/bash
# OpenClaw交易自动化脚本

cd ~/okx-btc-trading

case "$1" in
    start)
        ./launch.sh
        echo "✅ 交易系统已启动"
        ;;
    stop)
        ./stop.sh
        echo "🛑 交易系统已停止"
        ;;
    status)
        ./status.sh
        ;;
    logs)
        tail -f logs/trader.log
        ;;
    monitor)
        open http://localhost:8084
        ;;
    *)
        echo "用法: $0 {start|stop|status|logs|monitor}"
        ;;
esac
EOF

chmod +x ~/.openclaw/workspace/auto_trading.sh
```

### 步骤5.3：配置Telegram与OpenClaw集成
```bash
# 1. 安装Telegram插件（如果需要）
# 参考OpenClaw文档：https://docs.openclaw.ai/channels/telegram

# 2. 配置OpenClaw接收Telegram消息
# 在OpenClaw配置中添加：
cat >> ~/.openclaw/openclaw.json << 'EOF'
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "你的BOT_TOKEN",
      "admins": ["你的CHAT_ID"]
    }
  }
EOF
```

---

## 🧪 第六部分：测试完整系统

### 步骤6.1：测试交易系统
```bash
# 1. 测试API连接
cd ~/okx-btc-trading
source venv/bin/activate
python3 test_connection.py

# 应该输出：✅ API连接成功

# 2. 测试交易功能
python3 test_small_trade.py

# 应该执行小额测试交易
```

### 步骤6.2：测试监控面板
1. 打开浏览器访问：http://localhost:8084
2. 应该看到：
   - ✅ 系统状态：运行中
   - ✅ 市场数据：实时更新
   - ✅ 持仓信息：当前持仓
   - ✅ 交易历史：过往交易

### 步骤6.3：测试Telegram通知
```bash
# 1. 手动触发通知
cd ~/okx-btc-trading
source venv/bin/activate
python3 -c "
from trade_notifier import send_telegram_notification
send_telegram_notification('测试通知', '系统部署完成，开始运行！')
"

# 2. 检查Telegram是否收到消息
```

### 步骤6.4：测试OpenClaw控制
```bash
# 1. 通过OpenClaw控制交易系统
openclaw exec "cd ~/okx-btc-trading && ./status.sh"

# 2. 应该看到系统状态输出
```

---

## 📊 第七部分：日常使用指南

### 7.1 启动所有服务
```bash
# 方法1：一键启动
cd ~/okx-btc-trading && ./launch.sh

# 方法2：分步启动
openclaw gateway start
cd ~/okx-btc-trading && ./launch.sh
```

### 7.2 监控系统状态
```bash
# 查看交易系统状态
cd ~/okx-btc-trading && ./status.sh

# 查看OpenClaw状态
openclaw status

# 查看实时日志
tail -f ~/okx-btc-trading/logs/trader.log
```

### 7.3 访问监控面板
- **交易监控**：http://localhost:8084
- **OpenClaw面板**：http://localhost:3000（如果配置了Web界面）

### 7.4 Telegram交互命令
```
向你的Bot发送：
- /start - 开始交互
- /status - 查看系统状态
- /position - 查看当前持仓
- /logs - 查看最新日志
- /help - 显示帮助
```

### 7.5 紧急操作
```bash
# 紧急停止交易
cd ~/okx-btc-trading && ./stop.sh

# 查看错误信息
tail -100 ~/okx-btc-trading/logs/trader.log | grep -i error

# 重启系统
cd ~/okx-btc-trading && ./stop.sh && sleep 2 && ./launch.sh
```

---

## ⚠️ 第八部分：故障排除

### 问题1：OpenClaw安装失败
```bash
# 检查Node.js版本
node --version  # 需要 >= 18

# 清理重装
npm uninstall -g openclaw
npm cache clean --force
npm install -g openclaw
```

### 问题2：交易系统API连接失败
```bash
# 测试连接
cd ~/okx-btc-trading
source venv/bin/activate
python3 test_connection.py

# 检查API密钥权限
# 确保OKX API有"交易"权限
```

### 问题3：Telegram通知不工作
```bash
# 测试Bot Token
curl -s "https://api.telegram.org/bot你的TOKEN/getMe"

# 检查Chat ID
curl -s "https://api.telegram.org/bot你的TOKEN/getUpdates"
```

### 问题4：监控面板无法访问
```bash
# 检查端口
lsof -i :8084

# 重启监控服务
pkill -f "working_monitor.py"
cd ~/okx-btc-trading
source venv/bin/activate
python3 working_monitor.py &
```

### 问题5：交易频率问题
```bash
# 修改交易频率（如果需要）
cd ~/okx-btc-trading
nano ultra_fast_trader.py
# 修改：TRADE_INTERVAL = 10  # 10秒
```

---

## 🔄 第九部分：系统更新与维护

### 9.1 更新交易系统
```bash
# 拉取最新代码
cd ~/okx-btc-trading
git pull origin main

# 重启系统
./stop.sh
./launch.sh
```

### 9.2 更新OpenClaw
```bash
# 更新OpenClaw
npm update -g openclaw

# 重启服务
openclaw gateway restart
```

### 9.3 备份配置
```bash
# 备份重要文件
cp ~/okx-btc-trading/config/final_config.json ~/backup/
cp ~/.openclaw/openclaw.json ~/backup/
cp ~/.openclaw/workspace/*.md ~/backup/
```

### 9.4 日志管理
```bash
# 清理旧日志（保留7天）
find ~/okx-btc-trading/logs -name "*.log" -mtime +7 -delete

# 查看日志大小
du -sh ~/okx-btc-trading/logs/
```

---

## 🎉 第十部分：完成验证

### 验证清单
- [ ] ✅ OpenClaw安装完成：`openclaw --version`
- [ ] ✅ 交易系统部署完成：`cd ~/okx-btc-trading && ./status.sh`
- [ ] ✅ OKX API配置完成：`python3 test_connection.py`
- [ ] ✅ Telegram Bot配置完成：收到测试消息
- [ ] ✅ 监控面板可访问：http://localhost:8084
- [ ] ✅ 交易系统运行中：`ps aux | grep ultra_fast`
- [ ] ✅ OpenClaw服务运行：`openclaw gateway status`

### 最终测试
```bash
# 完整系统测试
cd ~/okx-btc-trading
./status.sh  # 应该显示所有服务运行
python3 test_connection.py  # 应该显示API连接成功
curl -s http://localhost:8084/api/status  # 应该返回JSON状态
```

### 开始交易
系统现在会自动：
1. ⏰ 每10秒分析市场
2. 📊 生成交易信号
3. 🤖 自动执行交易
4. 📱 发送Telegram通知
5. 🌐 更新监控面板

---

## 📱 第十一部分：Telegram交互配置（与你完全一样）

### 步骤11.1：配置Telegram Bot命令
1. **联系 @BotFather**
2. **发送**：`/setcommands`
3. **选择你的Bot**
4. **发送命令列表**：
```
start - 开始使用交易助手
status - 查看系统状态
position - 查看当前持仓
logs - 查看最新交易日志
stop - 停止交易系统
start_trading - 启动交易系统
help - 显示帮助信息
```

### 步骤11.2：配置OpenClaw Telegram通道
```bash
# 1. 安装Telegram插件
npm install -g @openclaw/channel-telegram

# 2. 配置OpenClaw使用Telegram
cat > ~/.openclaw/channels.json << 'EOF'
{
  "telegram": {
    "enabled": true,
    "token": "你的BOT_TOKEN",
    "admins": ["你的CHAT_ID"],
    "polling": {
      "interval": 1000
    },
    "reactions": {
      "enabled": true,
      "mode": "MINIMAL"
    }
  }
}
EOF
```

### 步骤11.3：创建与你一样的交互体验
```bash
# 1. 创建OpenClaw响应脚本
cat > ~/.openclaw/workspace/telegram_responses.py << 'EOF'
#!/usr/bin/env python3
# Telegram自动响应脚本

import json
import os
from telegram_notify_config import send_telegram_message

def handle_telegram_command(command, chat_id):
    """处理Telegram命令"""
    responses = {
        "/start": "🚀 OKX BTC交易助手已启动！\n\n可用命令：\n/status - 系统状态\n/position - 当前持仓\n/logs - 查看日志\n/help - 帮助",
        "/status": get_system_status(),
        "/position": get_current_position(),
        "/logs": get_recent_logs(),
        "/help": "🤖 交易助手命令：\n• /start - 启动\n• /status - 系统状态\n• /position - 当前持仓\n• /logs - 交易日志\n• /stop - 停止交易\n• /start_trading - 开始交易",
    }
    
    response = responses.get(command, "未知命令，发送 /help 查看可用命令")
    send_telegram_message(chat_id, response)

def get_system_status():
    """获取系统状态"""
    import subprocess
    try:
        result = subprocess.run(
            ["cd ~/okx-btc-trading && ./status.sh"],
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout[:1000]  # 限制长度
    except:
        return "⚠️ 无法获取系统状态"

def get_current_position():
    """获取当前持仓"""
    import subprocess
    try:
        result = subprocess.run(
            ["cd ~/okx-btc-trading && tail -20 logs/trader.log | grep -i 'position\|pnl'"],
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            return result.stdout
        else:
            return "📭 当前无持仓"
    except:
        return "⚠️ 无法获取持仓信息"

def get_recent_logs():
    """获取最近日志"""
    import subprocess
    try:
        result = subprocess.run(
            ["cd ~/okx-btc-trading && tail -5 logs/trader.log"],
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout or "📭 暂无日志"
    except:
        return "⚠️ 无法获取日志"
EOF

# 2. 设置执行权限
chmod +x ~/.openclaw/workspace/telegram_responses.py
```

### 步骤11.4：配置自动响应
```bash
# 1. 创建OpenClaw技能处理Telegram消息
cat > ~/.openclaw/workspace/skills/telegram/SKILL.md << 'EOF'
# 📱 Telegram交互技能

## 功能
处理所有Telegram消息和命令，提供与你完全一样的交互体验。

## 命令映射
- /start → 欢迎消息和命令列表
- /status → 调用 status.sh 显示系统状态
- /position → 显示当前持仓和盈亏
- /logs → 显示最近交易日志
- /help → 显示帮助信息

## 自动响应
- 交易开仓 → 立即发送通知
- 交易平仓 → 立即发送结果
- 系统错误 → 立即发送警报
- 每日报告 → 定时发送总结

## 配置
- Bot Token: [朋友的BOT_TOKEN]
- Chat ID: [朋友的CHAT_ID]
- 响应模式: 即时
EOF
```

### 步骤11.5：测试完整交互
```bash
# 1. 重启OpenClaw服务
openclaw gateway restart

# 2. 向Telegram Bot发送命令测试
# 发送: /start
# 应该收到欢迎消息

# 发送: /status
# 应该收到系统状态

# 发送: /position
# 应该收到持仓信息
```

---

## 🎯 第十二部分：与你完全一样的配置

### 12.1 相同的交易策略
```python
# 策略参数（与你的完全一致）
TRADE_INTERVAL = 10  # 10秒频率
RISK_PER_TRADE = 0.01  # 1%风险
BASE_STOP_LOSS = 0.015  # 1.5%
BASE_TAKE_PROFIT = 0.03  # 3.0%

# 动态参数
VOLATILITY_THRESHOLD_LOW = 0.2  # 20%
VOLATILITY_THRESHOLD_HIGH = 0.8  # 80%
BREAKOUT_THRESHOLD = 0.005  # 0.5%
```

### 12.2 相同的监控面板
- **端口**: 8084（与你一样）
- **更新频率**: 5秒
- **显示内容**: 系统状态、市场数据、持仓、交易历史
- **API端点**: 与你完全一致

### 12.3 相同的通知系统
- **Telegram Bot**: 独立但功能相同
- **通知内容**: 交易开仓、平仓、错误、每日报告
- **通知格式**: 与你完全一致

### 12.4 相同的OpenClaw配置
- **模型**: deepseek/deepseek-chat
- **Token限制**: 4096
- **压缩策略**: window+summary
- **内存管理**: 与你完全一致

---

## 📞 第十三部分：获取帮助

### 快速帮助命令
```bash
# 查看所有服务状态
./check_all_services.sh

# 测试所有组件
./test_all_components.sh

# 重置系统（从头开始）
./reset_system.sh
```

### 联系支持
- **GitHub Issues**: https://github.com/andongniu/okx-btc-trading-system/issues
- **项目文档**: README.md
- **你的联系方式**: [你的Telegram/微信]

### 紧急联系方式
```
如果系统出现严重问题：
1. 立即停止交易: ./stop.sh
2. 检查日志: tail -f logs/trader.log
3. 联系你获取帮助
```

---

## 🎉 完成！现在朋友拥有与你完全相同的系统

### 系统特性对比
| 功能 | 你的系统 | 朋友的系统 |
|------|----------|------------|
| **交易频率** | 10秒 | 10秒 |
| **交易策略** | 趋势+均值回归 | 完全相同 |
| **风险控制** | 动态止损止盈 | 完全相同 |
| **监控面板** | 端口8084 | 端口8084 |
| **Telegram通知** | @anth6iu_noticer_bot | 朋友的Bot |
| **OpenClaw配置** | 4096 token限制 | 完全相同 |
| **API连接** | 需要代理 | 海外直连 |

### 朋友现在可以：
1. 🤖 享受10秒频率的自动交易
2. 📱 通过Telegram实时交互
3. 📊 在监控面板查看所有数据
4. 🔒 使用相同的风险控制
5. 🚀 获得与你完全相同的交易体验

### 最后提醒朋友：
1. **先小额测试**（$10-20）
2. **定期检查日志**
3. **关注Telegram通知**
4. **不要分享API密钥**
5. **定期更新系统**

---

**🎯 教程完成！朋友现在可以按照这个指南，在30分钟内搭建与你完全相同的交易系统。**