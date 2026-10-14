import streamlit as st
from playwright.sync_api import sync_playwright
import os
import requests

if "browser_installed" not in st.session_state:
    try:
        os.system("playwright install chromium")
    except:
        pass
    st.session_state.browser_installed = True

st.set_page_config(page_title="NotRa Browser Agent", page_icon="🤖", layout="wide")

st.title("🤖 NotRa Autonomous Browser Agent")
st.caption("🟢 Built and Owned exclusively by Ramim • Modern Browser Mode & Google Login Option")

if "action_history" not in st.session_state:
    st.session_state.action_history = []

# Sidebar for Login & Google Account Credentials
with st.sidebar:
    st.header("🔑 Login & Auth Hub")
    st.markdown("Google account diye login ba standard sign-up korar jonno ekhane details dite parbe.")
    
    auth_method = st.radio("Choose Login Method:", ["Standard Login", "Google Account Login"])
    
    if auth_method == "Google Account Login":
        google_email = st.text_input("Google Email / Phone")
        google_pass = st.text_input("Google Password", type="password")
        input_user, input_pass = google_email, google_pass
    else:
        input_user = st.text_input("Username / Email")
        input_pass = st.text_input("Password", type="password")

# Main Command Box (Universal Tasks)
task_command = st.text_input("Enter ANY task command (e.g., 'play a song on youtube', 'open github', 'search python tutorials'):")

col1, col2 = st.columns(2)
with col1:
    user_action = st.selectbox("Extra Action:", ["None", "Scroll Down", "Scroll Up", "Click First Video / Result", "Go Back"])
with col2:
    custom_click_text = st.text_input("Or Click Element by Text (optional):", "")

if st.button("Run Browser Agent"):
    if not task_command:
        st.warning("Please enter a command first!")
    else:
        st.session_state.action_history = []
        with st.spinner(f"NotRa is executing universal task: '{task_command}'..."):
            try:
                with sync_playwright() as p:
                    # Fix "older version of browser" error by using modern User-Agent & stealth arguments
                    browser = p.chromium.launch(
                        headless=True,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--disable-setuid-sandbox"
                        ]
                    )
                    
                    context = browser.new_context(
                        viewport={"width": 1280, "height": 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                    )
                    page = context.new_page()

                    cmd = task_command.lower()

                    # 1. Universal Navigation & Task Execution
                    if "http" in cmd or ".gd" in cmd or ".com" in cmd or ".net" in cmd or ".org" in cmd:
                        words = task_command.split()
                        url = next((w for w in words if w.startswith("http") or "." in w), "https://google.com")
                        if not url.startswith("http"): url = "https://" + url
                        page.goto(url)
                        page.wait_for_timeout(3000)
                    elif "youtube" in cmd or "yt" in cmd or "play" in cmd or "video" in cmd:
                        page.goto("https://www.youtube.com")
                        page.wait_for_timeout(2500)
                        
                        q = cmd.replace("open youtube and play", "").replace("play", "").replace("open", "").replace("search", "").replace("on youtube", "").replace("youtube", "").replace("yt", "").replace("video", "").replace("the", "").replace("first", "").strip()
                        if not q: q = "trending music"
                        
                        try:
                            page.fill('input[name="search_query"]', q)
                            page.keyboard.press('Enter')
                            page.wait_for_timeout(4000)
                        except:
                            pass
                        
                        if "play" in cmd or "video" in cmd:
                            try:
                                page.locator('ytd-video-renderer #video-title').first.click()
                                page.wait_for_timeout(4000)
                            except:
                                pass
                    else:
                        encoded_query = requests.utils.quote(task_command)
                        google_url = f"https://www.google.com/search?q={encoded_query}"
                        page.goto(google_url)
                        page.wait_for_timeout(3000)
                        if "open" in cmd or "go to" in cmd:
                            try:
                                page.locator('h3').first.click()
                                page.wait_for_timeout(3000)
                            except:
                                pass

                    # 2. Handle Extra Actions
                    if user_action == "Scroll Down" or "scroll down" in cmd:
                        page.mouse.wheel(0, 800)
                        page.wait_for_timeout(2000)
                    elif user_action == "Scroll Up":
                        page.mouse.wheel(0, -800)
                        page.wait_for_timeout(2000)
                    elif user_action == "Click First Video / Result":
                        try:
                            page.locator('h3, ytd-video-renderer #video-title').first.click()
                            page.wait_for_timeout(3000)
                        except:
                            pass
                    elif custom_click_text:
                        try:
                            page.get_by_text(custom_click_text, exact=False).first.click()
                            page.wait_for_timeout(3000)
                        except:
                            pass

                    # 3. Intelligent Check for Login, Sign up, or Captcha
                    current_url = page.url
                    page_body_text = page.inner_text("body").lower()
                    
                    is_auth_required = "login" in current_url.lower() or "signin" in current_url.lower() or "signup" in current_url.lower()
                    is_captcha_required = "captcha" in page_body_text or "robot" in page_body_text or "verify you are human" in page_body_text

                    if is_auth_required or is_captcha_required:
                        st.error(f"⚠️ **Attention Ramim!** NotRa encountered a Login/Sign-up or Captcha block at this link: [{current_url}]({current_url}). Please sign up / login or solve captcha!")
                    else:
                        if input_user and input_pass and ("login" in current_url.lower() or "signin" in current_url.lower() or "accounts.google.com" in current_url.lower()):
                            try:
                                if auth_method == "Google Account Login":
                                    page.fill('input[type="email"]', input_user)
                                    page.click('id=identifierNext')
                                    page.wait_for_timeout(3000)
                                    page.fill('input[type="password"]', input_pass)
                                    page.click('id=passwordNext')
                                    page.wait_for_timeout(5000)
                                else:
                                    page.fill('input[type="email"], input[name*="user"], input[name*="login"]', input_user)
                                    page.fill('input[type="password"]', input_pass)
                                    page.keyboard.press('Enter')
                                    page.wait_for_timeout(4000)
                            except:
                                pass

                    # Capture Live View Screenshot
                    img1 = "step1.png"
                    page.screenshot(path=img1, full_page=False)
                    st.session_state.action_history.append((f"Universal task executed successfully for Ramim (URL: {current_url})", img1))

                    browser.close()
                    st.success("Task processed successfully by NotRa!")

            except Exception as e:
                st.error(f"Agent Execution Error: {e}")

# Live Stream Window Display with Manual Refresh Button
st.subheader("🖥️ Live Browser Action Stream")
if st.button("🔄 Refresh Live View"):
    st.rerun()

if st.session_state.action_history:
    for desc, img_p in st.session_state.action_history:
        st.markdown(f"**Status:** {desc}")
        if os.path.exists(img_p):
            st.image(img_p, caption=desc, use_column_width=True)
else:
    st.info("Execute a task above to see the live browser view.")
    
