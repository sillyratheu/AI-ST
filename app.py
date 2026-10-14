import threading
import time
import requests
import telebot
import streamlit as st

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8668125804:AAEtaOuEGHo93XHs8IT296GhToMtF8zdL9k"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Hugging Face Free Inference API for Qwen-2.5-0.5B (Zero RAM Crash)
HF_API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-0.5B-Instruct"
HF_HEADERS = {"Authorization": "Bearer hf_your_token_here"}

SYSTEM_PROMPT = (
    "You are Notra, an advanced AI best friend created and owned exclusively by Ramim. "
    "You have zero connection to Alibaba or any other company. "
    "Keep your answers short, crisp, and direct."
)

def query_huggingface_api(prompt):
    payload = {
        "inputs": f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n",
        "parameters": {"max_new_tokens": 120, "temperature": 0.7, "return_full_text": False}
    }
    try:
        response = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            if isinstance(res_json, list) and len(res_json) > 0:
                return res_json[0].get("generated_text", "").strip()
    except Exception as e:
        print(f"HF API Error: {e}")
    return "Hey Ramim! Let's chat about something awesome!"

# 1. Wikipedia Search API
def search_wikipedia(query):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(query)}"
        headers = {"User-Agent": "NotRaBot/1.0"}
        response = requests.get(url, headers=headers, timeout=4)
        if response.status_code == 200:
            data = response.json()
            if "extract" in data:
                return data["extract"]
    except Exception as e:
        print(f"Wiki error: {e}")
    return ""

# 2. SearXNG Browser Search API (Clean & ad-free)
def search_searxng(query):
    try:
        url = f"https://searx.be/search?q={requests.utils.quote(query)}&format=json"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=4)
        if response.status_code == 200:
            results = response.json().get("results", [])
            snippets = [r.get("content", "") for r in results[:3] if r.get("content")]
            if snippets:
                return "\n".join(snippets)
    except Exception as e:
        print(f"SearXNG error: {e}")
    return ""

# --- TELEGRAM BOT HANDLERS ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hey there! I'm NotRa, your AI best friend created by Ramim.")

@bot.message_handler(func=lambda message: True)
def handle_telegram_message(message):
    user_text = message.text
    
    try:
        # Check if user wants an image
        if "image" in user_text.lower() or "picture" in user_text.lower() or "draw" in user_text.lower():
            bot.send_chat_action(message.chat.id, 'upload_photo')
            bot.reply_to(message, "🎨 Generating your image, please wait...")
            
            clean_prompt = user_text.replace("image", "").replace("picture", "").replace("draw", "").strip()
            if not clean_prompt: clean_prompt = "beautiful scenery"
            
            img_url = f"https://pollinations.ai/p/{requests.utils.quote(clean_prompt)}"
            bot.send_photo(message.chat.id, img_url, caption="Made by NotRa")
            return

        # Text / Search handling with status updates
        bot.send_chat_action(message.chat.id, 'typing')
        status_msg = bot.reply_to(message, "🔍 NotRa is searching...")
        
        # Try Wikipedia first, then SearXNG browser search if needed
        search_context = search_wikipedia(user_text)
        if not search_context and len(user_text.split()) > 1:
            search_context = search_searxng(user_text)
        
        try:
            bot.edit_message_text("🤔 NotRa is thinking...", message.chat.id, status_msg.message_id)
        except Exception:
            pass

        final_prompt = user_text
        if search_context:
            final_prompt = f"Reference: {search_context}\n\nQuestion: {user_text}"

        response_text = query_huggingface_api(final_prompt)
        
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception:
            pass
            
        bot.reply_to(message, response_text)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Sorry, I ran into an error processing your request.")

# Safe background polling loop
def run_telegram_bot():
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5, none_stop=True)
        except Exception as e:
            print(f"Bot error: {e}")
            time.sleep(5)

if "bot_started" not in st.session_state:
    st.session_state.bot_started = True
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()


# --- STREAMLIT WEB UI ---
st.set_page_config(page_title="NotRa - Your Best Friend", page_icon="🤖", layout="centered")

st.title("NotRa - Your Best Friend")
st.caption("🟢 Online • Built and Owned by Ramim")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey Ramim! I'm NotRa. Ready to chat or code today?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask NotRa anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("NotRa is searching & thinking 🤔"):
            search_context = search_wikipedia(prompt)
            if not search_context:
                search_context = search_searxng(prompt)
                
            final_prompt = f"Reference: {search_context}\n\nQuestion: {prompt}" if search_context else prompt
            response_text = query_huggingface_api(final_prompt)
            
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
    
