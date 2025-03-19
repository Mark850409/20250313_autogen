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
    title="AutoGen多功能查詢API",
    description="使用AutoGen團隊進行天氣、新聞、知識查詢和文生圖的API",
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

# 定義各種請求模型
class WeatherRequest(BaseModel):
    location: str = "台北"
    detail: Optional[bool] = False

class NewsRequest(BaseModel):
    category: Optional[str] = None
    count: Optional[int] = 5

class KnowledgeRequest(BaseModel):
    question: str
    detail: Optional[bool] = False

class ImageGenRequest(BaseModel):
    prompt: str

# 載入不同功能的團隊配置
@app.on_event("startup")
async def startup_event():
    global weather_team, news_team, knowledge_team, image_team
    
    # 載入各個功能的團隊配置
    with open("json/weather_team.json", "r", encoding="utf-8") as f:
        weather_config = json.load(f)
    with open("json/news_team.json", "r", encoding="utf-8") as f:
        news_config = json.load(f)
    with open("json/knowledge_team.json", "r", encoding="utf-8") as f:
        knowledge_config = json.load(f)
    with open("json/image_team.json", "r", encoding="utf-8") as f:
        image_config = json.load(f)
    
    weather_team = BaseGroupChat.load_component(weather_config)
    news_team = BaseGroupChat.load_component(news_config)
    knowledge_team = BaseGroupChat.load_component(knowledge_config)
    image_team = BaseGroupChat.load_component(image_config)

# 定義天氣API路由
@app.get("/weather", response_class=JSONResponse, tags=["天氣查詢"])
async def get_weather(
    location: str = Query("台北", description="地點名稱"),
    detail: bool = Query(False, description="是否返回詳細天氣資訊")
):
    """
    查詢指定地點的天氣情況
    
    參數:
    - location: 地點名稱
    - detail: 是否返回詳細天氣資訊
    """
    try:
        query = f"{location}天氣"
        if detail:
            query += "詳細資訊"
        result = await weather_team.run(task=query)
        return {"status": "success", "location": location, "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 定義新聞API路由
@app.get("/news", response_class=JSONResponse, tags=["新聞查詢"])
async def get_news(
    category: Optional[str] = Query(None, description="新聞類別（科技、財經、體育等）"),
    count: int = Query(5, description="返回新聞數量", ge=1, le=20)
):
    """
    查詢最新新聞
    
    參數:
    - category: 新聞類別（科技、財經、體育等）
    - count: 返回新聞數量
    """
    try:
        query = f"最新{category if category else ''}新聞，返回{count}條"
        result = await news_team.run(task=query)
        return {"status": "success", "category": category, "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 定義知識查詢API路由
@app.get("/knowledge", response_class=JSONResponse, tags=["知識查詢"])
async def get_knowledge(
    question: str = Query(..., description="要查詢的問題"),
    detail: bool = Query(False, description="是否返回詳細解答")
):
    """
    查詢知識問題
    
    參數:
    - question: 要查詢的問題
    - detail: 是否返回詳細解答
    """
    try:
        result = await knowledge_team.run(task=question)
        return {"status": "success", "question": question, "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 定義文生圖API路由
@app.get("/image", response_class=JSONResponse, tags=["文生圖"])
async def generate_image(
    prompt: str = Query(..., description="圖片描述文字")
):
    """
    根據文字提示生成圖片
    
    參數:
    - prompt: 圖片描述文字
    """
    try:
        query = f"生成圖片：{prompt}"
        result = await image_team.run(task=query)
        return {"status": "success", "prompt": prompt, "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("autogen_api:app", host="0.0.0.0", port=8500, reload=True)

