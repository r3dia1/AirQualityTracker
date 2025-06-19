import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime

# === OM2M 設定 ===
CSE_IP = "127.0.0.1"
CSE_PORT = 8080
CSE_ID = "in-cse"
CSE_NAME = "in-name"
AE_NAME = "SensorAE"
# SRC_CONTAINER = "airQualityData"
DST_AE = "AlertAE"
# DST_CONTAINER = "alertBox"
ORIGINATOR = "admin:admin"
INTERVAL = 30

# === API 端點 ===
# PULL_URL = f"http://{CSE_IP}:{CSE_PORT}/~/{CSE_ID}/{CSE_NAME}/{AE_NAME}/{SRC_CONTAINER}/la"
# PUSH_URL = f"http://{CSE_IP}:{CSE_PORT}/~/{CSE_ID}/{CSE_NAME}/{DST_AE}/{DST_CONTAINER}"

headers_get = {
    "X-M2M-Origin": ORIGINATOR,
    "Accept": "application/xml"
}
headers_post = {
    "X-M2M-Origin": ORIGINATOR,
    "Content-Type": "application/xml;ty=4"
}

# === AQI 分段表 ===
breakpoints = {
    "PM2.5": [(0.0, 15.4, 0, 50), (15.5, 35.4, 51, 100), (35.5, 54.4, 101, 150),
              (54.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500.4, 301, 500)],
    "PM10": [(0, 54, 0, 50), (55, 125, 51, 100), (126, 254, 101, 150),
             (255, 354, 151, 200), (355, 424, 201, 300), (425, 604, 301, 500)],
    "SO2": [(0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150),
            (186, 304, 151, 200), (305, 604, 201, 300), (605, 1004, 301, 500)],
    "NO2": [(0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150),
            (361, 649, 151, 200), (650, 1249, 201, 300), (1250, 2049, 301, 500)],
    "O3": [(0, 54, 0, 50), (55, 70, 51, 100), (71, 85, 101, 150),
           (86, 105, 151, 200), (106, 200, 201, 300), (201, 404, 301, 500)],
    "CO": [(0.0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150),
           (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300), (30.5, 50.4, 301, 500)]
}

def get_aqi(pollutant, value):
    for bp in breakpoints.get(pollutant, []):
        c_low, c_high, i_low, i_high = bp
        if c_low <= value <= c_high:
            return round((i_high - i_low) / (c_high - c_low) * (value - c_low) + i_low)
    return -1

def classify_level(aqi):
    if aqi <= 50:
        return " 1 (Good)"
    elif aqi <= 100:
        return " 2 (Moderate)"
    elif aqi <= 150:
        return " 3 (Unhealthy for Sensitive Groups)"
    elif aqi <= 200:
        return " 4 (Unhealthy)"
    elif aqi <= 300:
        return " 5 (Very Unhealthy)"
    else:
        return " 6 (Hazardous)"

# === 從 ContentInstance 的 <con> 裡解析 MiniML <obj> ===
def parse_miniml_con(con_str):
    data = {}
    root = ET.fromstring(con_str.strip())
    for elem in root.findall("str"):
        k = elem.attrib.get("name")
        v = elem.attrib.get("val")
        try:
            data[k] = float(v)
        except:
            data[k] = v
    return data

# === 將分析結果轉換為 <obj><str.../></obj> 結構並 escape ===
def build_miniml_obj(data):
    lines = ""
    for k, v in data.items():
        lines += f'&lt;str name="{k}" val="{v}"/&gt;\n'
    return f"&lt;obj&gt;\n{lines.strip()}\n&lt;/obj&gt;"

def ai_loop():
    area_dict = {"dongDistrictCnt":"alert1", "zongxyiDistrictCnt":"alert2", "nanDistrictCnt":"alert3", "beiDistrictCnt":"alert4"}
    while True:
        try:
            for area, alert in area_dict.items():
                PULL_URL = f"http://{CSE_IP}:{CSE_PORT}/~/{CSE_ID}/{CSE_NAME}/{AE_NAME}/{area}/la"
                r = requests.get(PULL_URL, headers=headers_get)
                if r.status_code != 200:
                    print("==> 資料拉取失敗", r.status_code)
                    time.sleep(INTERVAL)
                    continue

                root = ET.fromstring(r.text)
                con_str = root.find(".//con").text.strip()
                air_data = parse_miniml_con(con_str)
                print("📥 感測資料：", air_data)
                
                area_cnt = air_data["area"] + "Cnt"

                aqi_dict = {}
                for pol in ["PM2.5", "PM10", "SO2", "NO2", "O3", "CO"]:
                    if pol in air_data:
                        aqi_dict[pol] = get_aqi(pol, air_data[pol])

                if not aqi_dict:
                    print("⚠️ 無法計算 AQI")
                    continue
                    
                area = air_data.get("area", "unknown")

                main_pol = max(aqi_dict, key=aqi_dict.get)
                max_aqi = aqi_dict[main_pol]
                level = classify_level(max_aqi)

                result = {
                    "AQI": max_aqi,
                    "Level": level,
                    "MainPollutant": main_pol,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                xml_con = build_miniml_obj(result)
                xml_payload = f"""<m2m:cin xmlns:m2m="http://www.onem2m.org/xml/protocols">
      <cnf>message</cnf>
      <lbl>{area}</lbl>
      <con>{xml_con}</con>
    </m2m:cin>"""
                
                PUSH_URL = f"http://{CSE_IP}:{CSE_PORT}/~/{CSE_ID}/{CSE_NAME}/{DST_AE}/{alert}"

                r2 = requests.post(PUSH_URL, headers=headers_post, data=xml_payload)
                if r2.status_code in [200, 201]:
                    print("==> 成功上傳 AQI 結果：", result)
                else:
                    print("==> 上傳失敗", r2.status_code, r2.text)

        except Exception as e:
            print("⚠️ 發生錯誤：", e)

        time.sleep(INTERVAL)

if __name__ == "__main__":
    ai_loop()

