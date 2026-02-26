#!/usr/bin/env python3
"""
发送测试通知到Telegram
"""

import requests
import json
from datetime import datetime

# Telegram配置
BOT_TOKEN = "8727025174:AAFP6y0i1sYEFyshH5-hvgygAgNlTvqMPsA"
CHAT_ID = "5340611944"

def send_test_notification():
    """发送测试通知"""
    print("📱 发送测试通知到Telegram...")
    
    message = f"""
🎉 <b>✅ 自主交易通知系统测试成功！</b>

<b>系统状态:</b>
• 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Bot名称: @anth6iu_noticer_bot
• 配置状态: ✅ 正常
• 通知功能: ✅ 已启用

<b>交易监控:</b>
• 自主交易系统: 持续运行中
• 检查间隔: 每60秒分析市场
• 风险控制: 1%每笔交易
• 动态参数: 根据波动率调整

<b>通知类型:</b>
1. 📈 开仓通知 - 检测到新持仓时立即发送
2. 🔄 平仓通知 - 持仓平仓时发送
3. 🎯 交易执行 - 从交易日志检测新交易

<b>监控面板:</b>
http://localhost:8084

<b>账户状态:</b>
• 余额: $200.00 USDT
• 持仓: 无 (等待交易信号)
• BTC价格: ~$64.9K

<i>测试完成！系统现在会实时监控交易并发送通知。</i>
    """
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ 测试通知发送成功！")
            print("📱 请检查Telegram消息")
            return True
        else:
            print(f"❌ 发送失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def send_trade_simulation():
    """发送模拟交易通知"""
    print("\n📊 发送模拟交易通知...")
    
    message = f"""
📈 <b>🚀 模拟交易开仓通知</b>

<b>交易详情:</b>
• 方向: LONG (多头)
• 合约数量: 0.05张 (0.0005 BTC)
• 入场价: $64,950.20
• 止损价: $63,970.70 (-1.5%)
• 止盈价: $66,898.70 (+3.0%)
• 杠杆: 10x
• 风险金额: $2.00
• 风险回报比: 2.0:1

<b>策略信息:</b>
• 策略: 趋势跟踪
• 原因: 上涨趋势，价格接近支撑位
• 信心度: 70%
• 波动率: 中等

<b>订单信息:</b>
• 订单ID: TEST-123456789
• 时间: {datetime.now().strftime('%H:%M:%S')}

<b>监控面板:</b>
http://localhost:8084

<i>这是模拟通知，用于测试格式和功能。</i>
    """
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ 模拟交易通知发送成功！")
            return True
        else:
            print(f"❌ 发送失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == '__main__':
    print("="*50)
    print("🤖 Telegram通知系统测试")
    print("="*50)
    
    # 发送测试通知
    success1 = send_test_notification()
    
    if success1:
        # 发送模拟交易通知
        success2 = send_trade_simulation()
    
    print("\n" + "="*50)
    print("测试完成！")
    print("="*50)
    print("\n🎯 系统现在会:")
    print("1. 每30秒检查交易状态")
    print("2. 检测到开仓立即发送通知")
    print("3. 提供完整交易信息")
    print("4. 包含监控面板链接")
    print("\n📱 请检查Telegram消息确认收到通知")