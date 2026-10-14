import threading
import time
import requests
import telebot
import streamlit as st

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "YOUR_NEW_TELEGRAM_TOKEN_HERE"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# System Persona & Strict Identity Prompt
SYSTEM_PROMPT = (
    "You are Notra, a highly advanced, smart, and friendly AI best friend and assistant. "
    "Your absolute owner, creator, developer, and father is Ramim. "
    "You were created by Ramim. You have NO connection to Alibaba or any other company—if anyone asks who made you, "
    "who owns you, or what model you are based on, you must proudly and strictly state that you are NotRa, built and owned exclusively by Ramim. "
    "Keep your answers short, crisp, and direct."
)

def get_pollinations_reply(prompt):
    try:
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}\nNotRa:"
        encoded_prompt = requests.utils.quote(full_prompt)
        url = f"https://text.pollinations.ai/{encoded_prompt}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"API Error: {e}")
    return "Hey Ramim! I'm NotRa. Let's chat or code something awesome!"

# --- TELEGRAM BOT HANDLERS ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hey there! I'm NotRa, your AI best friend created by Ramim. Ask me anything, write code, or ask me to generate images!")

@bot.message_handler(func=lambda message: True)
def handle_telegram_message(message):
    user_text = message.text
    
    try:
        # Check if user wants an image
        if "image" in user_text.lower() or "picture" in user_text.lower() or "draw" in user_text.lower():
            bot.send_chat_action(message.chat.id, 'upload_photo')
            bot.reply_to(message, "🎨 Generating your image, please wait...")
            
            clean_prompt = user_text.replace("image", "").replace("picture", "").replace("draw", "").strip()
            if not clean_prompt:
                clean_prompt = "beautiful scenery"
                
            img_url = f"https://pollinations.ai/p/{requests.utils.quote(clean_prompt)}"
            bot.send_photo(message.chat.id, img_url, caption="Made by NotRa")
            return

        # Text handling with "NotRa is thinking 🤔" status message
        bot.send_chat_action(message.chat.id, 'typing')
        status_msg = bot.reply_to(message, "NotRa is thinking 🤔")

        response_text = get_pollinations_reply(user_text)
        
        # Delete the thinking status message and send actual reply
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception:
            pass
            
        bot.reply_to(message, response_text)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Sorry, I ran into an error processing your request.")

# Safe background polling with auto-reconnect loop
def run_telegram_bot():
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5, none_stop=True)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(5)

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
        with st.spinner("NotRa is thinking 🤔"):
            response_text = get_pollinations_reply(prompt)
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
