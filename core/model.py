import os
import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration, BitsAndBytesConfig
from peft import PeftModel

class ModelEngine:
    def __init__(self, base_model_id="Qwen/Qwen2.5-VL-7B-Instruct", adapter_path=None):
        """
        Initializes the VLM with 4-bit quantization and loads the LoRA adapter.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if self.device == "cpu":
            print("⚠️ [Model] WARNING: Running on CPU/MPS. 4-bit quantization (BitsAndBytes) strictly requires CUDA.")
            print("   This might crash or be extremely slow on a MacBook.")

        # Resolve Adapter Path
        # Defaults to groundhog/groundhog-qwen/
        if adapter_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up two levels: groundhog_agent/core -> groundhog_agent -> groundhog -> groundhog-qwen
            adapter_path = os.path.join(current_dir, "..", "groundhog-qwen")

        if not os.path.exists(adapter_path):
            raise FileNotFoundError(f"LoRA adapter not found at: {adapter_path}")

        # Configure 4-bit Quantization (Exact match to training)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        # Load Processor
        print(f"[Model] Loading Processor: {base_model_id}...")
        self.processor = AutoProcessor.from_pretrained(base_model_id, trust_remote_code=True)

        # 4. Load Base Model
        print(f"[Model] Loading Base Model (4-bit)...")
        self.base_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            base_model_id,
            device_map="auto",
            quantization_config=bnb_config,
            low_cpu_mem_usage=True
        )

        # Attach LoRA Adapter
        print(f"[Model] Loading LoRA Adapter from {adapter_path}...")
        self.model = PeftModel.from_pretrained(self.base_model, adapter_path)
        self.model.eval()
        print("[Model] ✅ Ready.")

    def predict(self, image: Image.Image, prompt_text: str):
        """
        Runs inference on a single example.
        
        Args:
            image (PIL.Image): The processed, resized image (1024x1280)
            prompt_text (str): The formatted prompt string (TASK + DOM)
        
        Returns:
            str: The raw generated text (usually a JSON string)
        """
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

        # process Inputs (Collate equivalent for single sample)
        inputs = self.processor(
            text=[text_input],
            images=[image],
            padding=True,
            return_tensors="pt",
        )
        
        # move inputs to GPU
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
        # strip input tokens from the output to get just the model's response
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