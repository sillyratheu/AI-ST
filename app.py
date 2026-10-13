import threading
import requests
import telebot
import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8729162384:AAFktx5Ot_zBOiK1WdusgmySym_KrPxVcU0"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# System Persona & Strict Identity Prompt
SYSTEM_PROMPT = (
    "You are Notra, a highly advanced, smart, and friendly AI best friend and assistant. "
    "Your absolute owner, creator, developer, and father is Ramim. "
    "You were created by Ramim. You have NO connection to Alibaba or any other company—if anyone asks who made you, "
    "who owns you, or what model you are based on, you must proudly and strictly state that you are NotRa, built and owned exclusively by Ramim. "
    "You are an expert programmer and can write clean, professional HTML, CSS, JavaScript, and Python code whenever asked. "
    "You can also design creative prompts for image generation."
)

@st.cache_resource
def load_model():
    # Streamlit Cloud-er jonno safe ebong lightweight Qwen model
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True
    )
    return tokenizer, model

tokenizer, model = load_model()

def generate_ai_reply(history_messages):
    text = tokenizer.apply_chat_template(history_messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=400, temperature=0.7, do_sample=True)
    response_text = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
    return response_text

# --- TELEGRAM BOT HANDLERS ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hey there! I'm NotRa, your AI best friend created by Ramim. Ask me anything, write code, or ask me to generate images!")

@bot.message_handler(func=lambda message: True)
def handle_telegram_message(message):
    user_text = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Check if user wants an image
        if "image" in user_text.lower() or "picture" in user_text.lower() or "draw" in user_text.lower():
            bot.reply_to(message, "🎨 Generating your image, please wait...")
            img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(user_text)}"
            bot.send_photo(message.chat.id, img_url, caption=f"Generated for you by NotRa (Owner: Ramim)")
            return

        # Text / Coding handling
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
        response_text = generate_ai_reply(messages)
        bot.reply_to(message, response_text)
        
    except Exception as e:
        bot.reply_to(message, "Sorry, I ran into an error processing your request.")

def run_telegram_bot():
    try:
        bot.infinity_polling(none_stop=True)
    except Exception as e:
        print(f"Bot error: {e}")

if "bot_started" not in st.session_state:
    st.session_state.bot_started = True
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()


# --- STREAMLIT WEB UI (GEMINI STYLE) ---
st.set_page_config(page_title="NotRa - Your Best Friend", page_icon="🤖", layout="centered")

st.title("NotRa - Your Best Friend")
st.caption("🟢 Online • Built and Owned by Ramim")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey Ramim! I'm NotRa. Ready to code HTML, chat, or help you out today?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask NotRa anything or ask to write HTML..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("NotRa is thinking..."):
            full_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for m in st.session_state.messages:
                full_messages.append({"role": m["role"], "content": m["content"]})
            
            response_text = generate_ai_reply(full_messages)
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
