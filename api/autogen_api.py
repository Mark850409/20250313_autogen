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
    query: str = Query(..., description="搜索關鍵字"),
    num_results: int = Query(5, description="返回結果數量", ge=1, le=5),
    category: str = Query("web", description="搜索類別"),
    search_type: str = Query("keyword", description="搜索類型")
):
    """
    查詢新聞
    
    參數:
    - query: 搜索關鍵字
    - num_results: 返回結果數量（1-5條）
    - category: 搜索類別，預設為"web"
    - search_type: 搜索類型，預設為"keyword"
    """
    try:
        search_query = f"搜索{category}類別的{query}相關新聞，返回{num_results}條"
        result = await news_team.run(task=search_query)
        return {
            "status": "success", 
            "query": query,
            "category": category,
            "search_type": search_type,
            "result": result
        }
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

