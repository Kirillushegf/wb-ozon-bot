import requests
import time
import os
from flask import Flask
from threading import Thread

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

def send(chat_id, text, reply_markup=None):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        if reply_markup:
            data["reply_markup"] = reply_markup
        requests.post(url, json=data, timeout=10)
    except:
        pass

def start_keyboard():
    return {"inline_keyboard": [[{"text": "🔍 НАЧАТЬ ПОИСК", "callback_data": "start"}]]}

def main():
    last_id = 0
    print("✅ Бот запущен")
    
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset": last_id + 1, "timeout": 25}, timeout=30)
            data = r.json()
            if data.get("ok"):
                for upd in data["result"]:
                    last_id = upd["update_id"] + 1
                    
                    if "callback_query" in upd:
                        cb = upd["callback_query"]
                        chat_id = str(cb["message"]["chat"]["id"])
                        cb_data = cb["data"]
                        
                        if cb_data == "start":
                            send(chat_id, "🔍 <b>Напишите название товара</b>\n\nНапример: письменный стол")
                        
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", json={"callback_query_id": cb["id"]})
                    
                    elif "message" in upd:
                        msg = upd["message"]
                        chat_id = str(msg["chat"]["id"])
                        text = msg.get("text", "").strip()
                        
                        if text == "/start":
                            welcome_text = """
🔍 <b>ТВОЙ ПОМОЩНИК В ПОИСКЕ</b>

<b>КАК РАБОТАЮ:</b>
Напиши название товара, и я дам ссылки на WB и Ozon с сортировкой от дешёвых к дорогим.

<b>ПРИМЕРЫ:</b>
• письменный стол
• игровой компьютер
• наушники
• стиральная машина

<b>💰 Экономь время — не листай сотни страниц.</b>
"""
                            send(chat_id, welcome_text, reply_markup=start_keyboard())
                        
                        elif len(text) > 2:
                            wb_link = f"https://www.wildberries.ru/catalog/0/search.aspx?search={text.replace(' ', '%20')}&sort=priceup"
                            ozon_link = f"https://www.ozon.ru/search/?text={text.replace(' ', '+')}&sort=price_asc"
                            
                            msg = f"🔍 <b>{text}</b>\n\n"
                            msg += f"🟣 <b>Wildberries (сначала дешёвые):</b>\n{wb_link}\n\n"
                            msg += f"🟢 <b>Ozon (сначала дешёвые):</b>\n{ozon_link}\n\n"
                            msg += f"👉 Переходи по ссылкам и выбирай."
                            
                            send(chat_id, msg)
                        
                        else:
                            send(chat_id, "❌ Слишком короткий запрос. Напиши хотя бы 3 буквы.")
            time.sleep(0.5)
        except:
            time.sleep(5)

@app.route('/')
def home():
    return "OK", 200

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Нет токена")
    else:
        Thread(target=run).start()
        main()
