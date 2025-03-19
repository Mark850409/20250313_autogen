import io
import base64
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import torch
from PIL import Image
import numpy as np
from transformers import (
    PaliGemmaProcessor,
    PaliGemmaForConditionalGeneration,
)
import uvicorn

app = FastAPI(
    title="PaliGemma API",
    description="API 介面用於使用 PaliGemma 2 模型處理圖像",
    version="1.0.0",
)

# 允許跨域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 檢查是否有可用的 GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"使用裝置: {device}")

# 初始化模型和處理器
model_id = "google/paligemma2-3b-mix-448"  # 使用較小的模型版本

try:
    # 使用更保守的加載設置
    model = PaliGemmaForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.float32,  # 使用 float32 而不是 bfloat16 以提高兼容性
        device_map="auto",
        low_cpu_mem_usage=True
    ).eval()
    
    processor = PaliGemmaProcessor.from_pretrained(model_id)
    print("模型和處理器成功加載")
except Exception as e:
    print(f"加載模型時出錯: {e}")
    raise

class ImageResponse(BaseModel):
    result: str

async def process_image_file(
    file: UploadFile,
    task_type: str,
    question: Optional[str] = None,
    objects: Optional[str] = None
):
    """處理上傳的圖像文件"""
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        result = process_image(image, task_type, question, objects)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理圖像時出錯: {str(e)}")

def process_image(
    image,
    task_type: str,
    question: Optional[str] = "",
    objects: Optional[str] = ""
):
    """處理圖片並返回結果"""
    try:
        # 根據任務類型構建prompt
        if task_type == "describe":
            prompt = "describe en"
        elif task_type == "ocr":
            prompt = "ocr"
        elif task_type == "answer":
            if not question:
                return "使用 answer 任務時需要提供問題"
            prompt = f"answer en {question}"
        elif task_type == "detect":
            if not objects:
                return "使用 detect 任務時需要提供物體"
            prompt = f"detect {objects}"
        else:
            return "請選擇有效的任務類型: describe, ocr, answer, detect"
        
        # 確保圖像是PIL格式
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # 準備模型輸入
        model_inputs = processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        )
        
        # 將輸入移到正確的裝置上
        model_inputs = {k: v.to(device) for k, v in model_inputs.items()}
        
        input_len = model_inputs["input_ids"].shape[-1]
        
        # 生成結果
        with torch.inference_mode():
            generation = model.generate(
                **model_inputs,
                max_new_tokens=100,
                do_sample=False
            )
            generation = generation[0][input_len:]
            result = processor.decode(generation, skip_special_tokens=True)
        
        return result
    except Exception as e:
        return f"處理過程中出現錯誤: {str(e)}"

@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API 文檔")

@app.post("/api/process_image", response_model=ImageResponse, tags=["PaliGemma"])
async def api_process_image(
    file: UploadFile = File(..., description="要處理的圖像文件"),
    task_type: str = Form(..., description="任務類型: describe(描述圖像), ocr(文字識別), answer(回答問題), detect(檢測物體)"),
    question: Optional[str] = Form(None, description="當 task_type 為 'answer' 時的問題"),
    objects: Optional[str] = Form(None, description="當 task_type 為 'detect' 時要檢測的物體，用分號分隔")
):
    """
    處理上傳的圖像並根據選定的任務類型返回結果
    """
    return await process_image_file(file, task_type, question, objects)

@app.post("/api/process_base64", response_model=ImageResponse, tags=["PaliGemma"])
async def api_process_base64(
    base64_image: str = Form(..., description="Base64 編碼的圖像"),
    task_type: str = Form(..., description="任務類型: describe(描述圖像), ocr(文字識別), answer(回答問題), detect(檢測物體)"),
    question: Optional[str] = Form(None, description="當 task_type 為 'answer' 時的問題"),
    objects: Optional[str] = Form(None, description="當 task_type 為 'detect' 時要檢測的物體，用分號分隔")
):
    """
    處理 Base64 編碼的圖像並根據選定的任務類型返回結果
    """
    try:
        image_data = base64.b64decode(base64_image)
        image = Image.open(io.BytesIO(image_data))
        result = process_image(image, task_type, question, objects)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理圖像時出錯: {str(e)}")

@app.get("/api/health", tags=["系統"])
async def health_check():
    """
    API 健康狀態檢查
    """
    return {"status": "healthy", "device": device}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8100, reload=True) 