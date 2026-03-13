"""
vision_client.py - 多模态视觉识别

主线：豆包 1.6 Flash（仆用）/ 豆包 2.0 Lite（主用）
兜底：OCR（pytesseract，仅在多模态失败时启用）

豆包 API 兼容 OpenAI 格式，base_url 指向火山引擎。
"""
import base64
import json
import time
from typing import Literal


class VisionClient:
    def __init__(self, config: dict):
        self.api_key = config['api_key']
        self.api_base = config.get('api_base', 'https://ark.cn-beijing.volces.com/api/v3')
        self.servant_model = config.get('servant_model', 'doubao-1.6-flash')
        self.master_model = config.get('master_model', 'doubao-2.0-lite')
        self.ocr_fallback = config.get('ocr_fallback', True)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base
                )
            except ImportError:
                raise RuntimeError("openai package required: pip install openai")
        return self._client

    def analyze(
        self,
        image_bytes: bytes,
        prompt: str,
        role: Literal['servant', 'master'] = 'servant',
        timeout: int = 15
    ) -> dict:
        """
        分析截图，返回结构化结果。

        role='servant' → 豆包 1.6 Flash（快，用于初步感知）
        role='master'  → 豆包 2.0 Lite（深，用于决策判断）
        """
        model = self.servant_model if role == 'servant' else self.master_model
        img_b64 = base64.b64encode(image_bytes).decode()

        try:
            client = self._get_client()
            resp = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        },
                        {
                            "type": "text",
                            "text": prompt + "\n\n请用 JSON 格式回答。"
                        }
                    ]
                }],
                max_tokens=512,
                timeout=timeout
            )
            raw = resp.choices[0].message.content
            return _parse_json(raw)

        except Exception as e:
            if self.ocr_fallback:
                return self._ocr_fallback(image_bytes, str(e))
            return {'error': str(e), 'raw': None}

    def _ocr_fallback(self, image_bytes: bytes, reason: str) -> dict:
        """OCR 兜底，仅在多模态失败时触发"""
        try:
            import pytesseract
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes))
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            return {
                'ocr_fallback': True,
                'fallback_reason': reason,
                'text': text.strip()
            }
        except Exception as ocr_err:
            return {
                'ocr_fallback': True,
                'fallback_reason': reason,
                'ocr_error': str(ocr_err),
                'text': ''
            }


def _parse_json(text: str) -> dict:
    """从模型输出中提取 JSON"""
    text = text.strip()
    # 去掉 markdown 代码块
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text
    try:
        return json.loads(text)
    except Exception:
        return {'raw': text}
