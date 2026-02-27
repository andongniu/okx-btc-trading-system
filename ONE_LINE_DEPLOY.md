# 🚀 给朋友的一键部署命令

## 📋 最简单的方式（复制这一行）

```bash
curl -sSL https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash
```

## 🔧 详细步骤说明

### 第一步：运行部署命令
朋友只需要在终端运行：
```bash
curl -sSL https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash
```

### 第二步：脚本会自动完成
1. ✅ 检查系统要求（macOS）
2. ✅ 安装必要软件（Homebrew, Git, Python）
3. ✅ 克隆代码仓库
4. ✅ 设置Python虚拟环境
5. ✅ 安装所有依赖
6. ✅ 创建配置文件模板

### 第三步：配置API密钥
脚本会提示朋友：
1. 打开OKX官网创建API密钥
2. 编辑配置文件填入密钥
3. 保存并继续

### 第四步：启动系统
脚本会自动：
1. 创建启动/停止/状态检查脚本
2. 测试系统功能
3. 显示完成摘要

## 📱 给朋友的完整指令

### 短信/微信发送这个：
```
安装OKX BTC交易系统，在Mac终端运行：

curl -sSL https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash

然后按照提示配置你的OKX API密钥。
启动后访问 http://localhost:8084 查看监控面板。
```

### 更详细的版本：
```markdown
# 🚀 OKX BTC交易系统安装指南

## 系统要求
- macOS 系统
- 稳定的网络连接
- OKX 账户（需要API密钥）

## 安装步骤

### 1. 一键安装
打开终端，运行：
```bash
curl -sSL https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash
```

### 2. 配置API密钥
安装过程中会提示：
1. 登录OKX官网: https://www.okx.com
2. 进入 API管理: 个人中心 → API → 创建API
3. 选择权限: 交易、读取
4. 复制: API Key, Secret Key, Passphrase
5. 填入配置文件

### 3. 启动系统
安装完成后：
```bash
cd ~/okx-btc-trading
./launch.sh
```

### 4. 访问监控面板
打开浏览器: http://localhost:8084

## 管理命令
```bash
# 启动系统
./launch.sh

# 停止系统
./stop.sh

# 检查状态
./status.sh

# 查看日志
tail -f logs/trader.log
```

## 获取帮助
- 查看文档: README.md
- 查看日志: logs/trader.log
- 联系: GitHub @andongniu
```

## ⚡ 替代方案

### 如果curl命令有问题
```bash
# 方法1: 使用wget
wget -qO- https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh | bash

# 方法2: 手动下载运行
curl -O https://raw.githubusercontent.com/andongniu/okx-btc-trading-system/main/deploy_for_friend.sh
chmod +x deploy_for_friend.sh
./deploy_for_friend.sh

# 方法3: 传统Git方式
git clone https://github.com/andongniu/okx-btc-trading-system.git
cd okx-btc-trading-system
./setup.sh
```

## 🔒 安全提醒

### 给朋友的注意事项
1. **API密钥安全**：不要分享给他人
2. **资金安全**：先小额测试，再增加资金
3. **代理设置**：如果需要，配置代理服务器
4. **定期备份**：备份配置文件和日志

### 系统特性
- ⚡ 10秒频率实时交易
- 📊 Web监控面板
- 📱 Telegram通知
- 🔒 自动风险控制
- 🤖 完全自主运行

## 📞 支持与帮助

### 常见问题
1. **安装失败**：检查网络连接和系统版本
2. **API连接失败**：检查代理和API密钥权限
3. **端口冲突**：修改 `working_monitor.py` 中的端口
4. **Python错误**：重新运行安装脚本

### 获取帮助
```bash
# 查看详细日志
tail -f ~/okx-btc-trading/logs/trader.log

# 测试连接
cd ~/okx-btc-trading
source venv/bin/activate
python3 test_connection.py
```

## 🎯 部署成功标志

朋友完成部署后应该看到：
1. ✅ 项目目录: `~/okx-btc-trading/`
2. ✅ 启动脚本: `launch.sh`, `stop.sh`, `status.sh`
3. ✅ 监控面板: http://localhost:8084
4. ✅ 日志文件: `logs/trader.log` 有内容

---

**现在你可以轻松地分享这个系统给朋友了！只需发送那一行curl命令即可。**