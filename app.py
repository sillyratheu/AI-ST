import threading
import time
import requests
import telebot
import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8972266609:AAH9jyiOxYI7kjC0CEn3SoyAOFjvhYWTHQw"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Clear any old external webhooks causing forced joins
try:
    bot.remove_webhook()
except Exception:
    pass

# Strict Identity Prompt (No Alibaba connection ever)
SYSTEM_PROMPT = (
    "You are Notra, an advanced AI best friend created and owned exclusively by Ramim. "
    "You have ABSOLUTELY ZERO connection to Alibaba or any other company. If anyone asks who made you, "
    "you must strictly state that you are NotRa, built and owned exclusively by Ramim. "
    "Keep answers smart, friendly, and helpful."
)

@st.cache_resource
def load_model():
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True
    )
    return tokenizer, model

tokenizer, model = load_model()

def generate_ai_reply(history_messages):
    text = tokenizer.apply_chat_template(history_messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            temperature=0.6,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    response_text = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
    return response_text

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
        print(f"Wikipedia error: {e}")
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

        # General text / Wikipedia search handling using local Qwen LLM
        bot.send_chat_action(message.chat.id, 'typing')
        status_msg = bot.reply_to(message, "🔍 NotRa is searching...")

        search_context = ""
        if len(user_text.split()) > 2 or any(k in user_text.lower() for k in ["who", "what", "where", "when", "history", "science"]):
            search_context = search_wikipedia(user_text)

        try:
            bot.edit_message_text("🤔 NotRa is thinking...", message.chat.id, status_msg.message_id)
        except Exception:
            pass

        user_prompt_with_context = user_text
        if search_context:
            user_prompt_with_context = f"Reference: {search_context}\n\nQuestion: {user_text}"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt_with_context}
        ]

        response_text = generate_ai_reply(messages)

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
            search_context = search_wikipedia(prompt) if len(prompt.split()) > 2 else ""
            final_prompt = f"Reference: {search_context}\n\nQuestion: {prompt}" if search_context else prompt

            full_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for m in st.session_state.messages[:-1]:
                full_messages.append({"role": m["role"], "content": m["content"]})
            full_messages.append({"role": "user", "content": final_prompt})

            response_text = generate_ai_reply(full_messages)
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
