# 👫 给朋友部署交易系统 - 完整指南

## 🎯 目标
让朋友在10分钟内完成交易系统部署

## 📋 部署前准备

### 朋友需要：
1. ✅ macOS 电脑
2. ✅ OKX 账户（如果没有，需要注册）
3. ✅ 稳定的网络连接
4. ✅ 终端（Terminal）基本操作

### 你需要给朋友：
1. ✅ 部署命令（一行代码）
2. ✅ OKX API创建指南
3. ✅ 基本使用说明

## 🚀 三种部署方式

### 方式1：一键部署（最推荐）
```bash
curl -sSL https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash
```

### 方式2：分步部署
```bash
# 1. 克隆代码
git clone https://github.com/andongniu/okx-btc-trading-system.git
cd okx-btc-trading-system

# 2. 运行安装脚本
chmod +x setup.sh
./setup.sh

# 3. 配置API
cp config/final_config.json.template config/final_config.json
# 编辑配置文件填入API密钥

# 4. 启动系统
./start.sh
```

### 方式3：手动部署（适合技术人员）
```bash
# 完整手动流程
git clone https://github.com/andongniu/okx-btc-trading-system.git
cd okx-btc-trading-system
python3 -m venv venv
source venv/bin/activate
pip install ccxt numpy pandas flask requests python-telegram-bot
# ... 配置和启动
```

## 📱 给朋友的完整消息模板

### 短信/微信模板：
```
🚀 OKX BTC自动交易系统安装指南

1. 打开终端（Terminal）
2. 运行这个命令：
curl -sSL https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash

3. 按照提示：
   - 安装必要软件（自动）
   - 配置OKX API密钥（需要你的OKX账户）
   - 启动系统

4. 完成后访问：
   http://localhost:8084

需要帮助随时问我！
```

### 详细版消息：
```
# 🎯 OKX BTC交易系统部署

## 系统特性
- ⚡ 10秒频率实时交易
- 📊 Web监控面板（本地8084端口）
- 📱 Telegram交易通知
- 🔒 自动风险控制
- 🤖 完全自主运行

## 安装步骤

### 1. 一键安装
打开终端，运行：
```bash
curl -sSL https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash
```

### 2. 配置API密钥
安装过程中会提示你：
1. 登录OKX官网（https://www.okx.com）
2. 创建API：个人中心 → API → 创建API
3. 权限选择：交易、读取
4. 复制：API Key, Secret Key, Passphrase
5. 填入配置文件

### 3. 启动和使用
```bash
# 进入项目目录
cd ~/okx-btc-trading

# 启动系统
./launch.sh

# 查看状态
./status.sh

# 查看日志
tail -f logs/trader.log
```

### 4. 访问监控面板
浏览器打开：http://localhost:8084

## 管理命令
- `./launch.sh` - 启动系统
- `./stop.sh` - 停止系统  
- `./status.sh` - 检查状态
- `tail -f logs/trader.log` - 实时日志

## 安全提醒
1. 🔐 API密钥不要分享给他人
2. 💰 先小额测试，再增加资金
3. 📊 定期检查日志和监控面板
4. 🔄 保持系统更新

有问题随时联系我！
```

## 🔑 OKX API创建指南（给朋友）

### 步骤1：登录OKX
1. 访问：https://www.okx.com
2. 登录你的账户

### 步骤2：创建API
1. 点击右上角头像 → "API"
2. 点击 "创建API"
3. 填写API名称：`BTC-Trading-System`
4. 选择权限：
   - ✅ 读取
   - ✅ 交易
   - ❌ 提现（不要选！）

### 步骤3：获取密钥
1. 复制 **API Key**
2. 复制 **Secret Key**（只显示一次！）
3. 设置并记住 **Passphrase**

### 步骤4：配置系统
安装过程中会打开配置文件，填入：
```json
{
  "exchange": {
    "api_key": "你的API Key",
    "secret": "你的Secret Key", 
    "passphrase": "你的Passphrase",
    "proxies": {
      "http": "http://127.0.0.1:7897",
      "https": "http://127.0.0.1:7897"
    }
  }
}
```

## ⚠️ 常见问题解答

### Q1：安装失败怎么办？
```bash
# 检查网络
ping github.com

# 手动下载脚本
curl -O https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh
chmod +x deploy_for_friend.sh
./deploy_for_friend.sh
```

### Q2：API连接失败？
```bash
# 测试连接
cd ~/okx-btc-trading
source venv/bin/activate
python3 test_connection.py

# 检查代理设置
# 如果需要代理，编辑 config/final_config.json
```

### Q3：端口8084被占用？
```bash
# 修改端口
cd ~/okx-btc-trading
sed -i '' 's/8084/8085/g' working_monitor.py
# 然后访问 http://localhost:8085
```

### Q4：如何更新系统？
```bash
cd ~/okx-btc-trading
git pull origin main
./stop.sh
./launch.sh
```

## 🎯 部署成功验证

朋友完成部署后，检查：

### 基础检查
```bash
cd ~/okx-btc-trading
./status.sh
```
应该显示：
- ✅ working_monitor.py: 运行中
- ✅ ultra_fast_trader.py: 运行中  
- ✅ trade_notifier.py: 运行中
- ✅ 端口8084: 监听中

### 功能检查
1. 访问 http://localhost:8084 能看到监控面板
2. `logs/trader.log` 文件有内容更新
3. 系统能正常获取市场数据

## 🔧 高级配置（可选）

### 配置Telegram通知
1. 创建Telegram Bot（找 @BotFather）
2. 获取Bot Token和Chat ID
3. 配置 `telegram_notify_config.py`

### 修改交易参数
编辑 `ultra_fast_trader.py`：
- 检查频率（默认10秒）
- 风险比例（默认1.5%）
- 杠杆设置（动态调整）

### 添加代理支持
如果网络需要代理：
```json
"proxies": {
  "http": "http://你的代理IP:端口",
  "https": "http://你的代理IP:端口"
}
```

## 📊 系统监控和维护

### 日常检查
```bash
# 查看系统状态
./status.sh

# 查看实时日志
tail -f logs/trader.log

# 检查错误
grep -i error logs/trader.log
```

### 定期维护
1. 每周检查日志文件大小
2. 每月更新Python依赖
3. 定期备份配置文件

### 故障恢复
```bash
# 完全重新安装
cd ~/okx-btc-trading
./stop.sh
rm -rf venv
./setup.sh
./launch.sh
```

## 🎉 完成标志

朋友成功部署的标志：
1. ✅ 项目目录：`~/okx-btc-trading/` 存在
2. ✅ 启动脚本：`launch.sh`, `stop.sh`, `status.sh` 可用
3. ✅ 监控面板：http://localhost:8084 可访问
4. ✅ 日志文件：`logs/trader.log` 有实时输出
5. ✅ 系统进程：所有Python进程正常运行

## 📞 支持渠道

### 快速帮助
```bash
# 查看完整错误
tail -100 logs/trader.log

# 测试组件
cd ~/okx-btc-trading
source venv/bin/activate
python3 test_connection.py
```

### 联系支持
- GitHub Issues: https://github.com/andongniu/okx-btc-trading-system/issues
- 文档: README.md 和项目文档
- 直接联系你（作为推荐人）

---

**现在你可以轻松地分享这个交易系统给任何朋友了！只需发送那一行curl命令，剩下的脚本会自动完成。**