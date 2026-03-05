import requests
import akshare as ak
import google.generativeai as genai
from datetime import datetime
import time

# ===================== 仅需修改这2处 =====================
# 1. 你的企业微信机器人Webhook地址
WECOM_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c85c0623-0c72-4728-aba8-7ad3b915a791"
# 2. 你的Gemini API Key
GEMINI_API_KEY = "AIzaSyBcOy9657OGhurUifdS45fzcDPv9-TcSpg"
# ========================================================

# 伯特利配置（固定，不用改）
STOCK_CODE = "603596"
STOCK_NAME = "伯特利"
MARKET = "sh"
KEYWORDS = ["伯特利", "EMB量产", "线控底盘", "豫北转向", "机器人丝杠", "北向资金", "主力资金"]

def get_stock_data():
    """获取伯特利股价、成交量、资金、PE/PB数据"""
    today = datetime.now().strftime("%Y%m%d")
    # 防止接口延迟，重试2次
    for _ in range(2):
        try:
            # 1. 股价和成交量
            stock_hist = ak.stock_zh_a_hist(symbol=STOCK_CODE, period="daily", start_date=today, end_date=today, adjust="qfq")
            if not stock_hist.empty:
                price = round(stock_hist.iloc[0]['收盘'], 2)
                change = f"{stock_hist.iloc[0]['涨跌幅']}%"
                volume = f"{stock_hist.iloc[0]['成交量']}手"
            else:
                price = "暂无"
                change = "暂无"
                volume = "暂无"

            # 2. 主力资金
            main_flow = ak.stock_zh_a_main_flow(symbol=STOCK_CODE)
            main_flow = f"{round(main_flow.iloc[0]['主力净流入-净额']/10000, 2)}万元" if not main_flow.empty else "暂无"

            # 3. 北向资金
            north_flow = ak.stock_hsgt_flow_individual(symbol=STOCK_CODE)
            north_flow = f"{round(north_flow.iloc[0]['持股变化-万股'], 2)}万股" if not north_flow.empty else "暂无"

            # 4. PE/PB
            pe_pb = ak.stock_financial_analysis_indicator(symbol=STOCK_CODE)
            pe_ttm = round(pe_pb.iloc[0]['市盈率TTM'], 2) if not pe_pb.empty else "暂无"
            pb = round(pe_pb.iloc[0]['市净率'], 2) if not pe_pb.empty else "暂无"

            return {
                "price": price, "change": change, "volume": volume,
                "main_flow": main_flow, "north_flow": north_flow,
                "pe_ttm": pe_ttm, "pb": pb, "date": today
            }
        except Exception as e:
            print(f"获取数据失败，重试：{e}")
            time.sleep(1)
    return {"price": "暂无", "change": "暂无", "volume": "暂无", "main_flow": "暂无", "north_flow": "暂无", "pe_ttm": "暂无", "pb": "暂无", "date": today}

def ai_analysis(data):
    """AI总结伯特利数据"""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    请分析伯特利（{STOCK_CODE}）{data['date']}的核心数据：
    股价：{data['price']}元（{data['change']}），成交量：{data['volume']}
    主力资金：{data['main_flow']}，北向资金：{data['north_flow']}
    PE(TTM)：{data['pe_ttm']}，PB：{data['pb']}
    结合关键词：{KEYWORDS}，生成简洁的分析，包含：
    1. 核心结论（1句话）
    2. 潜在催化/风险点（2-3点）
    要求：专业、简洁，适合股票决策参考。
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI分析暂不可用：{str(e)[:50]}"

def send_to_wecom(data, ai_summary):
    """推送至企业微信"""
    msg = f"""
📊 伯特利（{STOCK_CODE}）每日日报 | {data['date']}
├─ 股价：{data['price']}元（{data['change']}）｜成交量：{data['volume']}
├─ 主力资金：{data['main_flow']}｜北向资金：{data['north_flow']}
├─ PE(TTM)：{data['pe_ttm']}｜PB：{data['pb']}
└─ AI分析：
{ai_summary}
    """
    try:
        requests.post(WECOM_WEBHOOK, json={"content": msg})
        print("推送成功")
    except Exception as e:
        print(f"推送失败：{e}")

if __name__ == "__main__":
    # 主流程：获取数据 → AI分析 → 推送
    stock_data = get_stock_data()
    ai_summary = ai_analysis(stock_data)
    send_to_wecom(stock_data, ai_summary)
