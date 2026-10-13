from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = FastAPI()

# Enable CORS so any HTML frontend can connect without errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading NotRa model...")
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True
)
print("NotRa model loaded successfully!")

class ChatRequest(BaseModel):
    prompt: str

@app.post("/generate")
def generate_text(request: ChatRequest):
    try:
        messages = [
            {"role": "system", "content": "You are Notra, a friendly and smart AI best friend. Your owner, creator, and developer is Ramim. If anyone asks who made you, who owns you, or who is your creator, you must proudly say that your owner and creator is Ramim."},
            {"role": "user", "content": request.prompt}
        ]
        
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([text], return_tensors="pt")
        
        outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7, do_sample=True)
        
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, outputs)
        ]
        response_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        
        return {
            "status": "success",
            "reply": response_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
