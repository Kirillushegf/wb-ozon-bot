import requests
import re
import time
import os
import json
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

def search_wb(query):
    try:
        url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&curr=rub&dest=-1257786&query={query}&resultset=catalog&sort=priceup&spp=30"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=8)
        data = r.json()
        products = data.get("data", {}).get("products", [])
        if not products:
            return None
        cheapest = products[0]
        price = cheapest.get("salePriceU", 0) // 100
        name = cheapest.get("name", "Товар")
        product_id = cheapest.get("id")
        return {
            "name": name[:60],
            "price": price,
            "url": f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
        }
    except:
        return None

def search_ozon(query):
    try:
        search_url = f"https://www.ozon.ru/search/?text={query.replace(' ', '+')}&sort=price_asc"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(search_url, headers=headers, timeout=8)
        product_id_match = re.search(r'/product/(\d+)', r.text)
        if not product_id_match:
            return None
        product_id = product_id_match.group(1)
        price_match = re.search(r'"price":"(\d+)"', r.text)
        price = int(price_match.group(1)) if price_match else 0
        return {
            "name": f"Товар с Ozon",
            "price": price,
            "url": f"https://www.ozon.ru/product/{product_id}"
        }
    except:
        return None

def start_keyboard():
    return {"inline_keyboard": [[{"text": "🔍 НАЧАТЬ ПОИСК", "callback_data": "start_search"}]]}

def main():
    last_id = 0
    print("✅ Бот запущен")
    user_queries = {}
    
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
                        
                        if cb_data == "start_search":
                            send(chat_id, "🔍 <b>Напишите название товара</b>\n\nНапример:\n• письменный стол\n• игровой компьютер\n• наушники беспроводные")
                        
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", json={"callback_query_id": cb["id"]})
                    
                    elif "message" in upd:
                        msg = upd["message"]
                        chat_id = str(msg["chat"]["id"])
                        text = msg.get("text", "").strip()
                        
                        if text == "/start":
                            welcome_text = """
🔍 <b>ТВОЙ ПОМОЩНИК В ПОИСКЕ ВЫГОДНЫХ ЦЕН</b>

Я ищу товары на <b>Wildberries</b> и <b>Ozon</b> и нахожу самый дешёвый вариант.

<b>⚡ КАК РАБОТАЮ:</b>
1️⃣ Нажми на кнопку «Начать поиск»
2️⃣ Напиши название товара
3️⃣ Получи ссылку на лучшую цену

<b>📝 ПРИМЕРЫ:</b>
• письменный стол
• игровой компьютер
• стиральная машина
• беспроводные наушники

<b>💰 Экономь время и деньги!</b>
"""
                            send(chat_id, welcome_text, reply_markup=start_keyboard())
                        
                        elif len(text) > 2:
                            send(chat_id, f"🔍 Ищу <b>{text}</b> на маркетплейсах...")
                            
                            wb = search_wb(text)
                            ozon = search_ozon(text)
                            
                            results = []
                            if wb:
                                results.append(("🟣 Wildberries", wb))
                            if ozon:
                                results.append(("🟢 Ozon", ozon))
                            
                            if not results:
                                send(chat_id, f"❌ Ничего не найдено для <b>{text}</b>\nПопробуйте другой запрос.")
                                continue
                            
                            results.sort(key=lambda x: x[1]["price"])
                            best_platform, best_item = results[0]
                            
                            msg = f"🏆 <b>ЛУЧШЕЕ ПРЕДЛОЖЕНИЕ</b>\n\n"
                            msg += f"📦 {best_item['name']}\n"
                            msg += f"💰 Цена: <b>{best_item['price']:,} ₽</b>\n"
                            msg += f"🛍️ Площадка: {best_platform}\n\n"
                            msg += f"👉 <a href='{best_item['url']}'>КУПИТЬ ПО ЭТОЙ ЦЕНЕ</a>"
                            
                            send(chat_id, msg)
                            
                            if len(results) > 1:
                                other_msg = f"📊 <b>Другие варианты:</b>\n"
                                for platform, item in results[1:]:
                                    other_msg += f"{platform}: {item['price']:,} ₽\n"
                                send(chat_id, other_msg)
                        
                        elif text:
                            send(chat_id, "❌ Слишком короткий запрос. Напишите хотя бы 3 буквы.")
            time.sleep(0.5)
        except Exception as e:
            print(f"Ошибка: {e}")
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