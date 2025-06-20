# Air Quality Tracker
## System Arichitecture
系統架構如圖下：
![sys arch](https://github.com/r3dia1/AirQualityTracker/blob/main/sys%20arch.png)

由左到右：
1. Air Sensor Node：此感應器會收集包含 PM2.5, PM10, O3, SO2, CO, NO2 空氣數據。
2. MN-CSE：感測器會定期上傳空氣污染資料到SensorAE，AE裡面會包含台南四個區域的Container (東、中西、南、北)。
3. IN-CSE：當MN-CSE的SensorAE收到新資料時，IN-CSE會因為訂閱的機制也收到一樣的新資料。
4. Air Pollution Calculater：這個程式會根據空氣資料計算空氣品質AQI，並且根據對應的區域上傳到IN-CSE的AlertAE。
5. Air Quality Tracker App：空氣品質監控程式會和IN-CSE的AlertAE溝通取得最新的AQI資料
6. User：使用者可以用App來查詢各地區最新的AQI資料，並且透過內建的推薦功能來取得空氣品質良好的景點

## GUI
![app](https://github.com/r3dia1/AirQualityTracker/blob/main/app.jpg)

## Project Structure
```
AirQualityTracker/
├── README.md
├── Air_Quality_APP.apk   # 空氣品質APP
├── Air_Quality_APP.aia   # 空氣品質APP的aia file
├── node-red/             # node-red flow setup
│   ├── flow1.json
│   └── flow2.json
├── postman/              # postman setup
│   ├── AlertAE setup
│   ├── IN-CSE SensorAE setup
│   └── MN-CSE SensorAE setup
└── sensor_simulation/
    ├── airSensor         # 感測器模擬
    └── pollution_pred    # 模擬IN-CSE AQI計算
```


## Installation Steps
1. Resouce tree setup：把postman資料夾裡面的三個檔案分別做匯入，並且把對應的AE都推上Resource Tree。
2. Node-red setup：把node-red資料夾的兩個檔案匯入並做deploy。
3. Simulate air sensor：該程式會在合理的範圍隨機生成6項空氣品質的資料＆上傳至MN-CSE。  
   `python airSensor_v2.py`
5. AQI calculator：執行pollution_pred_in_v2.py，他會透過RESTful API的get方法來取得IN-CSE各地區的最新空氣數據，並且透過分段表來計算對應AQI。  
   `python pollution_pred_in_v2.py`
6. Run App：更改app裡面虛擬機IP的地址（用aia file），並重新build，再把空氣品質程式丟進手機模擬器執行即可。
