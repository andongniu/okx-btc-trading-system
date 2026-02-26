#!/usr/bin/env python3
"""
Telegram通知配置
"""

import os
import json

def get_telegram_config():
    """获取Telegram配置"""
    # 检查环境变量
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if bot_token and chat_id:
        return {
            'bot_token': bot_token,
            'chat_id': chat_id,
            'source': 'environment'
        }
    
    # 检查配置文件
    config_path = 'config/telegram_config.json'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return {
                    'bot_token': config.get('bot_token'),
                    'chat_id': config.get('chat_id'),
                    'source': 'config_file'
                }
        except:
            pass
    
    return None

def send_telegram_message(message, config=None):
    """发送Telegram消息"""
    if config is None:
        config = get_telegram_config()
    
    if not config or not config.get('bot_token') or not config.get('chat_id'):
        print(f"📱 Telegram通知 (模拟): {message[:100]}...")
        return False
    
    try:
        import requests
        
        bot_token = config['bot_token']
        chat_id = config['chat_id']
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Telegram通知发送成功")
            return True
        else:
            print(f"❌ Telegram通知发送失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram通知错误: {e}")
        return False

# 测试函数
def test_telegram_notification():
    """测试Telegram通知"""
    print("🔧 测试Telegram通知功能...")
    
    config = get_telegram_config()
    if config:
        print(f"✅ 找到Telegram配置 (来源: {config['source']})")
        print(f"   Bot Token: {config['bot_token'][:10]}...")
        print(f"   Chat ID: {config['chat_id']}")
        
        # 发送测试消息
        test_message = """
🤖 <b>自主交易系统测试通知</b>

<b>系统状态:</b>
• 测试时间: 2026-02-25 16:20
• 状态: 正常运行
• 账户余额: $200.00

<b>监控面板:</b>
http://localhost:8084

<i>这是一条测试消息，确认通知功能正常。</i>
        """
        
        success = send_telegram_message(test_message, config)
        if success:
            print("🎉 Telegram通知测试成功！")
        else:
            print("⚠️  Telegram通知测试失败，使用模拟模式")
    else:
        print("⚠️  未找到Telegram配置，使用模拟模式")
        print("   请设置环境变量:")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")
        print("   或创建 config/telegram_config.json 文件")

if __name__ == '__main__':
    test_telegram_notification()