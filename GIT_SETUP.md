# 🚀 Git仓库设置指南

## 📋 目标
将交易系统代码推送到GitHub，实现：
1. 代码版本控制
2. 一键部署到新机器
3. 持续同步更新
4. 安全备份

## 🎯 仓库结构

```
okx-btc-trading-system/
├── 📁 config/                    # 配置文件
│   ├── final_config.json.template  # API配置模板
│   └── telegram_config.json.template
├── 📁 src/                      # 源代码
│   ├── ultra_fast_trader.py     # 10秒频率交易系统
│   ├── trade_notifier.py        # Telegram通知器
│   ├── working_monitor.py       # 监控面板
│   └── ...
├── 📁 templates/                # HTML模板
├── 📁 scripts/                  # 辅助脚本
├── 📄 .gitignore               # Git忽略规则
├── 📄 requirements.txt         # Python依赖
├── 📄 setup.sh                 # 一键安装脚本
└── 📄 README.md               # 项目说明
```

## 🔧 设置步骤

### 第一步：初始化本地Git仓库
```bash
cd ~/freqtrade-trading

# 初始化Git
git init

# 添加所有文件
git add .

# 提交初始版本
git commit -m "初始提交: OKX BTC交易系统 v1.0"
```

### 第二步：创建GitHub仓库
1. 访问 https://github.com/new
2. 仓库名: `okx-btc-trading-system`
3. 描述: "OKX BTC超快交易系统 (10秒频率)"
4. 选择: Private (私有仓库)
5. 不添加README/.gitignore (我们已经有了)

### 第三步：连接并推送
```bash
# 添加远程仓库
git remote add origin https://github.com/你的用户名/okx-btc-trading-system.git

# 推送代码
git push -u origin main
```

## 📦 优化仓库结构

### 创建模板配置文件
```bash
# 创建API配置模板
cp config/final_config.json config/final_config.json.template

# 编辑模板，移除真实API密钥
sed -i '' 's/"api_key": ".*"/"api_key": "YOUR_OKX_API_KEY"/g' config/final_config.json.template
sed -i '' 's/"secret": ".*"/"secret": "YOUR_OKX_SECRET"/g' config/final_config.json.template
sed -i '' 's/"passphrase": ".*"/"passphrase": "YOUR_OKX_PASSPHRASE"/g' config/final_config.json.template
```

### 创建requirements.txt
```bash
# 生成Python依赖列表
source venv/bin/activate
pip freeze > requirements.txt

# 清理，只保留核心依赖
cat > requirements.txt << 'EOF'
ccxt>=4.0.0
numpy>=1.21.0
pandas>=1.3.0
flask>=2.0.0
requests>=2.26.0
python-telegram-bot>=20.0
EOF
```

## 🚀 一键安装脚本

创建 `setup.sh`:

```bash
#!/bin/bash
# 一键安装交易系统

echo "🚀 安装OKX BTC交易系统..."
echo "="*50

# 1. 克隆仓库
git clone https://github.com/你的用户名/okx-btc-trading-system.git
cd okx-btc-trading-system

# 2. 安装Python依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 配置API密钥
echo "🔑 配置API密钥..."
cp config/final_config.json.template config/final_config.json
echo "请编辑 config/final_config.json 填入你的API密钥"
echo "按回车键继续..."
read -r

# 使用默认编辑器打开
if command -v nano &> /dev/null; then
    nano config/final_config.json
elif command -v vim &> /dev/null; then
    vim config/final_config.json
else
    open config/final_config.json
fi

# 4. 启动系统
echo "🚀 启动交易系统..."
mkdir -p logs
source venv/bin/activate
python3 src/working_monitor.py > logs/monitor.log 2>&1 &
python3 src/ultra_fast_trader.py > logs/trader.log 2>&1 &
python3 src/trade_notifier.py > logs/notifier.log 2>&1 &

echo "✅ 安装完成!"
echo "🌐 监控面板: http://localhost:8084"
echo "📊 查看日志: tail -f logs/trader.log"
```

## 🔐 安全注意事项

### 绝对不能提交的文件
```
❌ config/final_config.json      # 包含真实API密钥
❌ config/telegram_config.json   # 包含Telegram密钥
❌ *.key, *.pem, *.secret        # 任何密钥文件
❌ .env, .env.local              # 环境变量
```

### 使用.gitignore保护
确保.gitignore包含：
```gitignore
# 敏感文件
config/final_config.json
config/telegram_config.json
*.key
*.pem
*.secret

# 环境文件
.env
.env.*
```

### 使用环境变量（高级）
```python
# 在代码中使用环境变量
import os
API_KEY = os.getenv('OKX_API_KEY')
SECRET = os.getenv('OKX_SECRET')
```

## 📱 多机器同步流程

### 开发机器 (第一台Mac)
```bash
# 1. 修改代码
git add .
git commit -m "功能更新"

# 2. 推送到GitHub
git push origin main
```

### 生产机器 (第二台Mac)
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重启服务
pkill -f "python3"
./setup.sh
```

## 🎯 最佳实践

### 分支策略
```
main        - 稳定版本
develop     - 开发分支
feature/*   - 功能分支
hotfix/*    - 紧急修复
```

### 提交规范
```
feat:    新功能
fix:     修复bug
docs:    文档更新
style:   代码格式
refactor:代码重构
test:    测试相关
chore:   构建过程或辅助工具
```

### 版本标签
```bash
# 打标签
git tag -a v1.0.0 -m "稳定版本1.0.0"
git push origin --tags
```

## 🔧 故障排除

### 问题：Git忽略文件不生效
```bash
# 清除缓存
git rm -r --cached .
git add .
git commit -m "修复.gitignore"
```

### 问题：大文件无法推送
```bash
# 使用Git LFS
git lfs track "*.csv"
git lfs track "*.feather"
git add .gitattributes
```

### 问题：冲突解决
```bash
# 拉取最新代码
git pull origin main

# 解决冲突后
git add .
git commit -m "解决合并冲突"
git push origin main
```

## 📊 仓库维护

### 定期清理
```bash
# 删除已合并的分支
git branch --merged | grep -v "\*" | xargs -n 1 git branch -d

# 清理远程分支
git remote prune origin

# 压缩历史
git gc --aggressive --prune=now
```

### 备份策略
```bash
# 本地备份
git bundle create backup.bundle --all

# 推送到多个远程
git remote add backup https://github.com/backup/repo.git
git push backup main
```

## 🎉 完成标志

成功设置后，你应该有：

1. ✅ GitHub私有仓库: `okx-btc-trading-system`
2. ✅ 本地Git仓库初始化
3. ✅ 安全的.gitignore配置
4. ✅ 模板配置文件
5. ✅ 一键安装脚本
6. ✅ 清晰的文档

现在你可以轻松地在任何机器上部署交易系统了！

---

*最后更新: 2026-02-26*