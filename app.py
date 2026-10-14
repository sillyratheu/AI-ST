import threading
import time
import re
import requests
import telebot
import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from youtubesearchpython import VideosSearch
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8668125804:AAEtaOuEGHo93XHs8IT296GhToMtF8zdL9k"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Strict Identity Prompt (Zero Alibaba connection ever)
SYSTEM_PROMPT = (
    "You are Notra, an advanced AI best friend created and owned exclusively by Ramim. "
    "You have ABSOLUTELY ZERO connection to Alibaba or any other company. If anyone asks who made you, "
    "you must strictly state that you are NotRa, built and owned exclusively by Ramim. "
    "You can browse websites, search YouTube, and summarize content when asked. Keep answers smart and helpful."
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

tokenizer, model = load_model()

def generate_ai_reply(history_messages):
    text = tokenizer.apply_chat_template(history_messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.6,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
    response_text = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
    return response_text

def search_youtube(query):
    try:
        clean_q = query.lower().replace("search", "").replace("on youtube", "").replace("youtube", "").strip()
        videosSearch = VideosSearch(clean_q, limit=2)
        results = videosSearch.result().get('result', [])
        info = []
        for v in results:
            info.append(f"Title: {v.get('title')}\nLink: {v.get('link')}\nDuration: {v.get('duration')}")
        if info:
            return "\n---\n".join(info)
    except Exception as e:
        print(f"YouTube search error: {e}")
    return ""

def scrape_website(url):
    try:
        if not url.startswith("http"):
            url = "https://" + url
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=6)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator=' ', strip=True)
            return text[:3000]
    except Exception as e:
        print(f"Web scraping error: {e}")
    return ""

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

        # Check if user provided a web link (e.g., ramims.work.gd)
        url_match = re.search(r'(https?://[^\s]+|[\w-]+\.[\w-]+(?:/\S*)?)', user_text)
        if url_match and ("http" in user_text or ".gd" in user_text or ".com" in user_text or ".net" in user_text or ".org" in user_text):
            target_url = url_match.group(0)
            bot.send_chat_action(message.chat.id, 'typing')
            status_msg = bot.reply_to(message, "NotRa is opening and browsing the website 🌐🪄")
            
            web_content = scrape_website(target_url)
            
            try:
                bot.edit_message_text("🤔 NotRa is thinking...", message.chat.id, status_msg.message_id)
            except Exception:
                pass

            prompt_text = f"Here is the content scraped from the website ({target_url}):\n{web_content}\n\nPlease summarize this website nicely for Ramim."
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text}
            ]
            response_text = generate_ai_reply(messages)
            
            try:
                bot.delete_message(message.chat.id, status_msg.message_id)
            except Exception:
                pass
                
            bot.reply_to(message, response_text)
            return

        # Check if user wants to search YouTube
        if "youtube" in user_text.lower() or "yt" in user_text.lower():
            bot.send_chat_action(message.chat.id, 'typing')
            status_msg = bot.reply_to(message, "NotRa is searching on YouTube 🔍🪄")
            
            yt_data = search_youtube(user_text)
            
            try:
                bot.edit_message_text("🤔 NotRa is thinking...", message.chat.id, status_msg.message_id)
            except Exception:
                pass

            prompt_text = f"Here are the YouTube search results for '{user_text}':\n{yt_data}\n\nPlease summarize these videos nicely for Ramim with their links."
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text}
            ]
            response_text = generate_ai_reply(messages)
            
            try:
                bot.delete_message(message.chat.id, status_msg.message_id)
            except Exception:
                pass
                
            bot.reply_to(message, response_text)
            return

        # General text / Wikipedia search handling
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
st.
    
