import requests
import random
import time
from datetime import datetime
from itertools import cycle

# === 基本設定 ===
CSE_IP = "127.0.0.1"
CSE_PORT = 8282
CSE_ID = "mn-cse"
CSE_NAME = "mn-name"
AE_NAME = "SensorAE"
# CONTAINER = "airQualityData"
ORIGINATOR = "admin:admin"
INTERVAL = 10

headers = {
    "X-M2M-Origin": ORIGINATOR,
    "Content-Type": "application/xml;ty=4"
}

# === 模擬資料 ===
# 放在函式外部，讓它在每次呼叫時保留輪替狀態
district_cycle = cycle(["dongDistrict", "zongxyiDistrict", "nanDistrict", "beiDistrict"])

def generate_air_quality_data():
    return {
        "PM2.5": round(random.uniform(5, 80), 1),
        "PM10": round(random.uniform(10, 120), 1),
        "SO2": round(random.uniform(1, 50), 2),
        "NO2": round(random.uniform(5, 150), 2),
        "O3": round(random.uniform(10, 200), 2),
        "CO": round(random.uniform(0.1, 15.0), 2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "area": next(district_cycle)  # 每次呼叫輪下一個地區
    }

# === 將 dict 轉為 <str name="..." val="..."/> XML 字串 ===
def build_str_elements(data):
    xml_strs = ""
    for k, v in data.items():
        xml_strs += f'&lt;str name="{k}" val="{v}"/&gt;\n'
    return xml_strs

def upload_data():
    while True:
        data = generate_air_quality_data()
        area = data["area"]
        container_name = f"{area}Cnt"  # e.g., dongDistrictContainer
        url = f"http://{CSE_IP}:{CSE_PORT}/~/{CSE_ID}/{CSE_NAME}/{AE_NAME}/{container_name}"
	
        xml_inner = build_str_elements(data)

        xml_payload = f"""<m2m:cin xmlns:m2m="http://www.onem2m.org/xml/protocols">
  <cnf>message</cnf>
  <lbl>simulated</lbl>
  <con>
    &lt;obj&gt;
      {xml_inner.strip()}
    &lt;/obj&gt;
  </con>
</m2m:cin>"""

        response = requests.post(url, headers=headers, data=xml_payload)
        if response.status_code in [200, 201]:
            print("==> 成功上傳 XML Object 格式資料：", data)
        else:
            print("==> 上傳失敗:", response.status_code, response.text)

        time.sleep(INTERVAL)

if __name__ == "__main__":
    upload_data()
