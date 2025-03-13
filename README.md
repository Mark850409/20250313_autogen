# AutoGen 多代理框架系統

這是一個使用 AutoGen 框架開發的天氣查詢系統，能夠查詢指定城市的天氣狀況並使用 AI 助手進行對話。


## 相關連結

1. 懶得自己部署點擊此連結可以測試：https://myautogen.zeabur.app/
2. 官方Github說明：https://github.com/microsoft/autogen/tree/main

## 系統需求

- Python 3.9 或更高版本
- pip（Python 套件管理器）
- 虛擬環境工具（建議使用 venv 或 conda）

## 安裝步驟

1. 建立並啟動虛擬環境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

2. 安裝所需套件：
```bash
pip install -r requirement.txt
```

3. 設定環境變數：
- 複製 `.env.example` 檔案改為`.env`
- 加入以下設定：
```env
WEATHER_API_KEY=<WEATHER_API_KEY>
OLLAMA_API_KEY=<OLLAMA_API_KEY>
GEMINI_API_KEY=<GEMINI_API_KEY>
MODEL=<MODEL_NAME>
```

## 檔案說明

- `app.py`: 主要應用程式檔案，包含天氣查詢邏輯
- `Dockerfile`: Autogen本地部署

## 部署方式

1. autogenstudio GUI介面運行：
```bash
# Run AutoGen Studio on http://localhost:8000
autogenstudio ui --port 8000 --appdir ./my-app
```

2. 使用 Docker 部署：
```bash
# 建立 Docker 映像
docker build -t autogen-weather .

# 運行容器
docker run -d -p 8000:8000 \
  -e WEATHER_API_KEY=你的_WeatherAPI_金鑰 \
  -e GEMINI_API_KEY=你的_Gemini_API_金鑰 \
  -e MODEL=gemini-2.0-flash \
  autogen-weather
```

3. 使用 Zeabur 部署：
   - 將專案推送至 GitHub
   - 在 Zeabur 建立新專案
   - 選擇 GitHub 倉庫
   - 設定環境變數
   - 選擇部署分支

## API 使用說明

1. 啟動autogenstudio的 REST API
```bash
autogenstudio serve --team path/to/team.json --port 8084  
```
其中`path/to/team.json`改成AutoGen匯出的json檔案

2. 查詢天氣：
```bash
curl "http://localhost:8000/predict/taipei%20weather"
```
3. Swagger API 文件：
- 訪問 `http://localhost:8000/docs`
- 可以直接在網頁介面測試 API

## 注意事項

1. 環境變數設定：
   - 確保所有必要的環境變數都已正確設定
   - API 金鑰請妥善保管，不要上傳至版本控制系統

2. 編碼設定：
   - 所有檔案請使用 UTF-8 編碼儲存
   - 避免使用特殊字符

3. 錯誤處理：
   - 檢查 API 回應狀態
   - 確保網路連接正常
   - 查看日誌檔案進行除錯

## 常見問題解決

1. 編碼問題：
   - 確保所有檔案使用 UTF-8 編碼
   - 使用 `encoding="utf-8"` 開啟檔案

2. API 連接問題：
   - 檢查 API 金鑰是否正確
   - 確認網路連接狀態
   - 查看 API 呼叫限制

3. 部署問題：
   - 確保環境變數正確設定
   - 檢查防火牆設定
   - 確認端口是否被占用

## 更新日誌

- 2025/03/13: 初始版本發布
- 修正編碼問題
- 改進錯誤處理
- 更新文件說明 