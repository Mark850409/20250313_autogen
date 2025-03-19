from mcp.server import FastMCP
import io
import base64
import torch
from PIL import Image
import numpy as np
from transformers import (
    PaliGemmaProcessor,
    PaliGemmaForConditionalGeneration,
)
import logging
from typing import Optional

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 創建一個 MCP 服務器
mcp = FastMCP(
    "PaliGemma 圖像處理服務",
    timeout=300  # 設置為300秒（5分鐘）
)

# 檢查是否有可用的 GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"使用裝置: {device}")

# 初始化模型和處理器
model_id = "google/paligemma2-3b-mix-448"  # 使用較小的模型版本

try:
    # 確保使用 GPU，明確設置 torch.cuda
    if torch.cuda.is_available():
        torch.cuda.empty_cache()  # 清空 GPU 緩存
        logger.info(f"可用 GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU 記憶體總量: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        logger.info(f"目前 GPU 記憶體使用量: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
    
    # 使用混合精度來加速和節省 GPU 記憶體
    model = PaliGemmaForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,  # 在 GPU 上使用 float16 精度
        device_map="auto",
        low_cpu_mem_usage=True
    ).eval()
    
    processor = PaliGemmaProcessor.from_pretrained(model_id)
    
    # 確認模型是否在 GPU 上
    logger.info(f"模型設備: {next(model.parameters()).device}")
    if torch.cuda.is_available() and not str(next(model.parameters()).device).startswith('cuda'):
        logger.warning("警告：模型沒有正確加載到 GPU 上")
        # 嘗試手動將模型移到 GPU
        model = model.to('cuda')
        logger.info(f"手動移動後的模型設備: {next(model.parameters()).device}")
    
    logger.info("模型和處理器成功加載")
except Exception as e:
    logger.error(f"加載模型時出錯: {e}")
    raise

def process_image(
    image,
    task_type: str,
    question: Optional[str] = "",
    objects: Optional[str] = ""
):
    """處理圖片並返回結果"""
    try:
        # 在處理前清理GPU記憶體
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
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
        
        # 優化推理設定
        with torch.inference_mode(), torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
            generation = model.generate(
                **model_inputs,
                max_new_tokens=100,
                do_sample=False,
                num_beams=1,  # 減少beam search數量
                early_stopping=True  # 啟用早停
            )
        
        generation = generation[0][input_len:]
        result = processor.decode(generation, skip_special_tokens=True)
        
        # 處理完成後再次清理
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return result
    except Exception as e:
        return f"處理過程中出現錯誤: {str(e)}"

@mcp.tool()
def process_base64_image(
    base64_image: str, 
    task_type: str,
    question: Optional[str] = None,
    objects: Optional[str] = None
) -> str:
    """處理 Base64 編碼的圖像"""
    try:
        # 回報開始處理
        logger.info("開始處理圖像...")
        
        # 解碼和載入圖像
        if ',' in base64_image:
            base64_image = base64_image.split(',', 1)[1]
        
        logger.info("正在解碼Base64圖像...")
        image_data = base64.b64decode(base64_image)
        
        logger.info("正在載入圖像...")
        image = Image.open(io.BytesIO(image_data))
        
        logger.info("正在進行模型推理...")
        result = process_image(image, task_type, question, objects)
        
        logger.info("處理完成")
        return result
    except Exception as e:
        logger.error(f"處理圖像時出錯: {e}")
        return f"處理圖像時出錯: {str(e)}"

# 新增工具函數，來驗證 Base64 字串是否有效
@mcp.tool()
def validate_base64_image(base64_image: str) -> str:
    """
    驗證 Base64 編碼的圖像是否有效
    
    Args:
        base64_image (str): Base64 編碼的圖像
        
    Returns:
        str: 驗證結果
    """
    try:
        # 檢查 Base64 字串是否包含頭部信息
        if ',' in base64_image:
            base64_image = base64_image.split(',', 1)[1]
        
        # 嘗試解碼
        try:
            image_data = base64.b64decode(base64_image)
            logger.info(f"Base64 解碼成功，資料長度: {len(image_data)} 位元組")
        except Exception as e:
            return f"Base64 解碼錯誤: {str(e)}"
        
        # 嘗試打開圖像
        try:
            image = Image.open(io.BytesIO(image_data))
            format_info = f"格式: {image.format}, 大小: {image.size}, 模式: {image.mode}"
            logger.info(f"圖像成功載入，{format_info}")
            return f"Base64 圖像有效。{format_info}"
        except Exception as e:
            return f"Base64 解碼成功，但無法識別為有效圖像: {str(e)}"
            
    except Exception as e:
        return f"驗證過程中出現錯誤: {str(e)}"

# 新增工具函數，檢查 GPU 狀態
@mcp.tool()
def check_gpu_status() -> str:
    """
    檢查 GPU 狀態和記憶體使用情況
    
    Returns:
        str: GPU 狀態信息
    """
    if not torch.cuda.is_available():
        return "此系統未檢測到 GPU"
    
    gpu_info = []
    gpu_info.append(f"設備名稱: {torch.cuda.get_device_name(0)}")
    gpu_info.append(f"可用 GPU 數量: {torch.cuda.device_count()}")
    
    total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
    allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
    reserved_memory = torch.cuda.memory_reserved(0) / 1024**3
    free_memory = total_memory - allocated_memory
    
    gpu_info.append(f"總記憶體: {total_memory:.2f} GB")
    gpu_info.append(f"已分配記憶體: {allocated_memory:.2f} GB")
    gpu_info.append(f"已保留記憶體: {reserved_memory:.2f} GB")
    gpu_info.append(f"可用記憶體: {free_memory:.2f} GB")
    gpu_info.append(f"模型是否在 GPU 上: {'是' if str(next(model.parameters()).device).startswith('cuda') else '否'}")
    
    return "\n".join(gpu_info)

@mcp.tool()
def get_service_info() -> str:
    """獲取圖像處理服務的基本信息"""
    return f"""
【PaliGemma 圖像處理服務信息】

此服務使用 PaliGemma 模型提供以下功能：
1. 圖像描述 (describe)：自動描述圖像中的內容
2. 文字識別 (ocr)：識別圖像中的文字
3. 視覺問答 (answer)：根據圖像回答問題
4. 物體檢測 (detect)：檢測圖像中的特定物體

使用方法：
- 使用 process_base64_image 工具處理圖像
- 傳入 Base64 編碼的圖像和任務類型
- 根據任務類型提供必要的參數

技術細節：
- 模型：{model_id}
- 運行裝置：{device}
"""

@mcp.tool()
def get_supported_tasks() -> str:
    """獲取支持的任務類型說明"""
    return """
【支持的任務類型】

1. describe：描述圖像中的內容
   - 不需要額外參數
   - 例：process_base64_image(base64_image, "describe")
   
2. ocr：識別圖像中的文字
   - 不需要額外參數
   - 例：process_base64_image(base64_image, "ocr")
   
3. answer：根據圖像回答問題
   - 需要額外參數：question (問題文本)
   - 例：process_base64_image(base64_image, "answer", question="這張圖片中有什麼動物？")
   
4. detect：檢測圖像中的特定物體
   - 需要額外參數：objects (要檢測的物體，用逗號分隔)
   - 例：process_base64_image(base64_image, "detect", objects="貓,狗,人")
"""

# 新增批次處理功能
@mcp.tool()
def process_multiple_images(
    base64_images: list[str],
    task_type: str,
    question: Optional[str] = None,
    objects: Optional[str] = None
) -> list[str]:
    """批次處理多張圖像"""
    results = []
    for idx, base64_image in enumerate(base64_images):
        logger.info(f"處理第 {idx+1}/{len(base64_images)} 張圖像")
        result = process_base64_image(base64_image, task_type, question, objects)
        results.append(result)
    return results

if __name__ == "__main__":
    mcp.run() 