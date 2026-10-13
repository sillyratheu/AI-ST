import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

st.title("NotRa AI Chatbot")
st.write("Powered by NotRa Local Model on Streamlit")

# Model load korar jonno caching use kora jate bar bar load na hoy
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

with st.spinner("Loading NotRa model... Please wait..."):
    tokenizer, model = load_model()

# Chat interface
user_prompt = st.text_input("Ask NotRa anything:")

if user_prompt:
    with st.spinner("NotRa is thinking..."):
        inputs = tokenizer(user_prompt, return_tensors="pt")
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.7,
            do_sample=True
        )
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        st.subheader("Response:")
        st.write(response_text)
