"""
Legacy LLM Adapter - 兼容旧版 llm_generate_func
把简单的 llm_generate_func(prompt) -> str 接口适配到新的 GenerateRequest/Response 系统
"""

import time
from phase3_types import GenerateRequest, GenerateResponse, TokenUsage


class LegacyLLMAdapter:
    """
    适配器：把旧版 llm_generate_func(prompt) 接到新接口
    
    用法：
        adapter = LegacyLLMAdapter(my_old_llm_func, model_id="gpt-4")
        response = adapter.generate(GenerateRequest(role="bull", prompt="..."))
    """
    
    def __init__(self, llm_generate_func, model_id: str = "legacy-mock"):
        self.llm_generate_func = llm_generate_func
        self.model_id = model_id
    
    def generate(self, req: GenerateRequest) -> GenerateResponse:
        """执行 LLM 调用，返回标准化响应"""
        t0 = time.time()
        
        try:
            text = self.llm_generate_func(req.prompt) or ""
            latency = int((time.time() - t0) * 1000)
            
            if not text.strip():
                return GenerateResponse(
                    ok=False,
                    text="",
                    model_id=self.model_id,
                    latency_ms=latency,
                    token_usage=TokenUsage(),
                    error_code="EMPTY_RESPONSE",
                    error_message="empty text"
                )
            
            return GenerateResponse(
                ok=True,
                text=text,
                model_id=self.model_id,
                latency_ms=latency,
                token_usage=TokenUsage(total_tokens=max(1, len(req.prompt) // 4))
            )
        
        except TimeoutError as e:
            return GenerateResponse(
                ok=False,
                text="",
                model_id=self.model_id,
                error_code="TIMEOUT",
                error_message=str(e)
            )
        
        except Exception as e:
            return GenerateResponse(
                ok=False,
                text="",
                model_id=self.model_id,
                error_code="MODEL_ERROR",
                error_message=str(e)
            )
