import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

@st.cache_resource
def load_model():
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True
    )
    return tokenizer, model

tokenizer, model = load_model()

# URL theke prompt neoa (jemon: your-app.streamlit.app/?prompt=Hello)
query_params = st.query_params
user_prompt = query_params.get("prompt", "")

if user_prompt:
    messages = [
        {"role": "system", "content": "You are Notra, a friendly and smart AI best friend. Your owner, creator, and developer is Ramim. If anyone asks who made you, who owns you, or who is your creator, you must proudly say that your owner and creator is Ramim."},
        {"role": "user", "content": user_prompt}
    ]
    
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt")
    
    outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7, do_sample=True)
    generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, outputs)]
    response_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    
    # JSON ba direct text format-e output dewa jate HTML fetch korte pare
    st.write(response_text)
else:
    st.title("NotRa AI API is Running!")
    st.write("Use ?prompt=your_message in the URL to get a response.")
