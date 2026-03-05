# bote_li_report.py
import requests
import akshare as ak
import google.generativeai as genai
from datetime import datetime
import time

# ==================== 仅修改这2行 ====================
WECOM_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=575d3e28-525c-42af-aec0-19a1754c56ef"  # 你的Webhook（已填，核对是否正确）
GEMINI_API_KEY = "AIzaSyCrY0F19ay40FhvpBTmAcqzbj81E-jhKAI"  # 你的Gemini Key（已填，核对是否正确）
# =====================================================

# 伯特利固定配置
STOCK_CODE = "603596"
STOCK_NAME = "伯特利"
MARKET = "sh"
KEYWORDS = ["伯特利", "EMB量产", "线控底盘", "豫北转向", "机器人丝杠", "北向资金", "主力资金"]

def get_stock_data():
    today = datetime.now().strftime("%Y%m%d")
    for _ in range(2):
        try:
            # 股价+成交量
            stock_hist = ak.stock_zh_a_hist(symbol=STOCK_CODE, period="daily", start_date=today, end_date=today, adjust="qfq")
            price = round(stock_hist.iloc[0]['收盘'], 2) if not stock_hist.empty else "暂无"
            change = f"{stock_hist.iloc[0]['涨跌幅']}%" if not stock_hist.empty else "暂无"
            volume = f"{stock_hist.iloc[0]['成交量']}手" if not stock_hist.empty else "暂无"

            # 主力资金
            main_flow = ak.stock_zh_a_main_flow(symbol=STOCK_CODE)
            main_flow = f"{round(main_flow.iloc[0]['主力净流入-净额']/10000, 2)}万元" if not main_flow.empty else "暂无"

            # 北向资金
            north_flow = ak.stock_hsgt_flow_individual(symbol=STOCK_CODE)
            north_flow = f"{round(north_flow.iloc[0]['持股变化-万股'], 2)}万股" if not north_flow.empty else "暂无"

            # PE/PB
            pe_pb = ak.stock_financial_analysis_indicator(symbol=STOCK_CODE)
            pe_ttm = round(pe_pb.iloc[0]['市盈率TTM'], 2) if not pe_pb.empty else "暂无"
            pb = round(pe_pb.iloc[0]['市净率'], 2) if not pe_pb.empty else "暂无"

            return {"price": price, "change": change, "volume": volume, "main_flow": main_flow, "north_flow": north_flow, "pe_ttm": pe_ttm, "pb": pb, "date": today}
        except Exception as e:
            print(f"重试获取数据：{e}")
            time.sleep(1)
    return {"price": "暂无", "change": "暂无", "volume": "暂无", "main_flow": "暂无", "north_flow": "暂无", "pe_ttm": "暂无", "pb": "暂无", "date": today}

def ai_analysis(data):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""分析伯特利（{STOCK_CODE}）{data['date']}数据：
股价：{data['price']}元（{data['change']}），成交量：{data['volume']}
主力资金：{data['main_flow']}，北向资金：{data['north_flow']}
PE(TTM)：{data['pe_ttm']}，PB：{data['pb']}
结合关键词{KEYWORDS}，生成：
1. 1句话核心结论
2. 2-3个催化/风险点
要求简洁、专业，适合股票决策。"""
    try:
        response = model.generate_content(prompt, request_options={"timeout": 30})
        return response.text
    except Exception as e:
        return f"AI分析暂不可用：{str(e)[:50]}"

def send_wecom(data, ai_summary):
    msg = f"""
📊 伯特利（{STOCK_CODE}）每日日报 | {data['date']}
├─ 股价：{data['price']}元（{data['change']}）｜成交量：{data['volume']}
├─ 主力资金：{data['main_flow']}｜北向资金：{data['north_flow']}
├─ PE(TTM)：{data['pe_ttm']}｜PB：{data['pb']}
└─ AI分析：
{ai_summary}"""
    try:
        requests.post(WECOM_WEBHOOK, json={"content": msg})
        print("推送成功")
    except Exception as e:
        print(f"推送失败：{e}")

if __name__ == "__main__":
    stock_data = get_stock_data()
    ai_summary = ai_analysis(stock_data)
    send_wecom(stock_data, ai_summary)
