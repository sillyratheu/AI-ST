import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Page Configuration (Gemini Style Title & Layout)
st.set_page_config(
    page_title="NotRa - Your Best Friend",
    page_icon="🤖",
    layout="centered"
)

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

# 1. API Mode Check: URL-e ?prompt=... thakle shudhu raw text output diye stop hobe
query_params = st.query_params
api_prompt = query_params.get("prompt", "")

if api_prompt:
    tokenizer, model = load_model()
    messages = [
        {"role": "system", "content": "You are Notra, a friendly and smart AI best friend. Your owner, creator, and developer is Ramim. If anyone asks who made you, who owns you, or who is your creator, you must proudly say that your owner and creator is Ramim."},
        {"role": "user", "content": api_prompt}
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt")
    
    outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7, do_sample=True)
    generated_ids = [output_ids[len(input_ids):] for output_ids, user_outputs in zip(inputs.input_ids, outputs)]
    # Safe unpacking for generated response
    response_text = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
    
    # Return pure text for external API use
    st.write(response_text)
    st.stop()


# 2. Normal Web UI Mode (Gemini Style)
tokenizer, model = load_model()

st.title("NotRa - Your Best Friend")
st.caption("🟢 Online • Built by Ramim")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey there! I'm NotRa, your best friend. What's on your mind today?"}
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User chat input box (Gemini style bottom input)
if prompt := st.chat_input("Ask NotRa anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("NotRa is thinking..."):
            full_messages = [
                {"role": "system", "content": "You are Notra, a friendly and smart AI best friend. Your owner, creator, and developer is Ramim. If anyone asks who made you, who owns you, or who is your creator, you must proudly say that your owner and creator is Ramim."}
            ]
            for m in st.session_state.messages:
                full_messages.append({"role": m["role"], "content": m["content"]})
            
            text = tokenizer.apply_chat_template(full_messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer([text], return_tensors="pt")
            outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7, do_sample=True)
            
            response_text = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
            
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
