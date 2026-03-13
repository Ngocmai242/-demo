import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class FashionLLM:
    """
    LLM Interface for providing fashion advice.
    Optimized for Gemma 3 or Llama 4.
    """
    def __init__(self, model_id="google/gemma-3-4b-it"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading LLM {model_id} on {self.device}...")
        
        # Using 4-bit quantization if bitsandbytes is available
        try:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, 
                quantization_config=bnb_config,
                device_map="auto"
            )
        except Exception:
            # Fallback for systems without bitsandbytes or GPU
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, 
                torch_dtype=torch.float32 if self.device.type == 'cpu' else torch.bfloat16,
                device_map="auto"
            )

        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

    def generate_advice(self, user_info):
        """
        user_info: dict with keys {gender, body_shape, measurements}
        """
        m = user_info['measurements']
        prompt = f"""Bạn là chuyên gia tư vấn thời trang cao cấp. Dựa trên thông tin sau:
- Giới tính: {user_info['gender']}
- Dáng người: {user_info['body_shape']}
- Số đo chi tiết: Vai {m['shoulder']}cm, Ngực {m['chest']}cm, Eo {m['waist']}cm, Hông {m['hip']}cm.

Hãy gợi ý 3 bộ trang phục từ Shopee phù hợp để tôn lên ưu điểm và che khuyết điểm. 
Đối với mỗi bộ trang phục, hãy cung cấp:
1. Tên set đồ.
2. Tại sao nó phù hợp với số đo trên.

Trả về kết quả dưới dạng JSON có cấu trúc như sau:
{{
  "recommendations": [
    {{ "title": "Set 1", "reason": "..." }},
    {{ "title": "Set 2", "reason": "..." }},
    {{ "title": "Set 3", "reason": "..." }}
  ]
}}
"""
        # Gemma 3 specific prompt formatting if needed
        # inputs = self.tokenizer.apply_chat_template([{"role": "user", "content": prompt}], return_tensors="pt").to(self.device)
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=400,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract JSON part from response
        try:
            import json
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            return json.loads(response[json_start:json_end])
        except Exception:
            return {"raw_text": response}
