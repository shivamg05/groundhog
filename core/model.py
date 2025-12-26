import os
import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration, BitsAndBytesConfig
from peft import PeftModel

class ModelEngine:
    def __init__(self, model_id="Qwen/Qwen2.5-VL-7B-Instruct", adapter_path=None):
        """
        Initializes the VLM.
        
        Args:
            model_id (str): The Hugging Face ID or local path of the model to load.
                            If using a merged model, pass that ID here.
            adapter_path (str, optional): If using LoRA, pass the adapter ID/Path here.
                                          If None, it assumes model_id is a full model.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if self.device == "cpu":
            print("⚠️ [Model] WARNING: Running on CPU. 4-bit quantization requires CUDA.")

        #configure 4-bit Quantization
        # This keeps the model small (~6GB VRAM) even though it's the full 7B
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        # load Processor
        print(f"[Model] Loading Processor: {model_id}...")
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

        # load Model
        print(f"[Model] Loading Weights from: {model_id}...")
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_id,
            device_map="auto",
            quantization_config=bnb_config,
            low_cpu_mem_usage=True
        )

        # attach LoRA Adapter (ONLY if provided)
        if adapter_path:
            print(f"[Model] Loading LoRA Adapter from {adapter_path}...")
            self.model = PeftModel.from_pretrained(self.model, adapter_path)
        
        self.model.eval()
        print("[Model] ✅ Ready.")

    def predict(self, image: Image.Image, prompt_text: str):
        # format the conversation
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt_text},
                ],
            }
        ]

        # apply Chat Template
        text_input = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        # process Inputs
        inputs = self.processor(
            text=[text_input],
            images=[image],
            padding=True,
            return_tensors="pt",
        )
        
        inputs = inputs.to(self.device)

        # generate
        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,
                temperature=0.0
            )

        # decode
        input_len = inputs.input_ids.shape[1]
        generated_ids_trimmed = [
            out_ids[input_len:] for out_ids in generated_ids
        ]
        
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, 
            skip_special_tokens=True, 
            clean_up_tokenization_spaces=False
        )

        return output_text[0]