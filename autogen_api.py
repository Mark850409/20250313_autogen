import json
import asyncio
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from autogen_agentchat.teams import BaseGroupChat

# 創建FastAPI應用
app = FastAPI(
    title="AutoGen團隊查詢API",
    description="使用AutoGen團隊進行各種查詢的通用API，包括但不限於天氣、新聞、知識等資訊",
    version="1.0.0"
)

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定義請求模型
class WeatherRequest(BaseModel):
    location: str = "台北"
    detail: Optional[bool] = False

# 定義通用請求模型
class QueryRequest(BaseModel):
    question: str
    parameters: Optional[dict] = None

# 載入團隊配置
@app.on_event("startup")
async def startup_event():
    global team
    # 使用 UTF-8 編碼讀取 JSON 檔案
    with open("AutoGenTools.json", "r", encoding="utf-8") as f:
        team_config = json.load(f)
    
    team = BaseGroupChat.load_component(team_config)

# 定義API路由
@app.get("/query", response_class=JSONResponse, tags=["通用查詢"])
async def get_query(question: str = Query("台北天氣?", description="要查詢的問題")):
    """
    向AutoGen團隊提出查詢問題，可以是天氣、新聞、知識等各種問題
    
    例如：
    - 台北天氣?
    - 最新科技新聞?
    - 如何學習Python?
    """
    try:
        result = await team.run(task=question)
        return {"status": "success", "question": question, "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# 保留原始的main函數，但改為可選執行
async def original_main():
    # 使用 UTF-8 編碼讀取 JSON 檔案
    with open("weather_new.json", "r", encoding="utf-8") as f:
        team_config = json.load(f)
    
    team = BaseGroupChat.load_component(team_config)
    
    # 執行團隊任務
    result = await team.run(task="台北天氣?")
    print(result)

if __name__ == "__main__":
    # 啟動FastAPI服務
    uvicorn.run("autogen_api:app", host="0.0.0.0", port=8500, reload=True)
    
    # 如果要執行原始的main函數，可以取消下面這行的註釋
    # asyncio.run(original_main())

