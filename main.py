import requests
import time
import os
import json
import random

TOKEN = os.getenv("BOT_TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}/"

offset = 0
CHANNEL_ID = "@mychannel"  # замените на свой канал или ID

# Загружаем 100000 фраз
with open("quotes.json", "r", encoding="utf-8") as f:
    QUOTES = json.load(f)

HEROES = ["Картман", "Кайл", "Стэн", "Кенни", "Рэнди"]
scores = {}

def get_updates(offset):
    response = requests.get(URL + "getUpdates", params={"offset": offset, "timeout": 1})
    return response.json()

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(URL + "sendMessage", data=data)

def ask_question(chat_id):
    quote = random.choice(QUOTES)
    correct_hero = quote["hero"]

    scores.setdefault(chat_id, {"score": 0, "answer": correct_hero})
    scores[chat_id]["answer"] = correct_hero

    buttons = [[{"text": hero, "callback_data": hero}] for hero in HEROES]
    reply_markup = {"inline_keyboard": buttons}

    send_message(
        chat_id,
        f"Угадай героя по цитате:\n\n«{quote['text']}»",
        reply_markup=reply_markup,
    )

def answer_callback(chat_id, user_answer):
    correct = scores[chat_id]["answer"]
    if user_answer == correct:
        scores[chat_id]["score"] += 1
        send_message(chat_id, f"✅ Правильно! Очки: {scores[chat_id]['score']}")
    else:
        send_message(chat_id, f"❌ Неправильно! Правильный ответ: {correct}")
    ask_question(chat_id)

def get_callback_query(update):
    if "callback_query" in update:
        return update["callback_query"]
    return None

def post_to_channel(text):
    send_message(CHANNEL_ID, text)

# Главный цикл
last_post_time = 0
POST_INTERVAL = 6 * 60 * 60  # каждые 6 часов

while True:
    updates = get_updates(offset)

    if "result" in updates:
        for update in updates["result"]:
            offset = update["update_id"] + 1

            # Команда /play
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")
                if text == "/play":
                    ask_question(chat_id)

            # Нажатие кнопки
            cb = get_callback_query(update)
            if cb:
                chat_id = cb["message"]["chat"]["id"]
                user_answer = cb["data"]
                answer_callback(chat_id, user_answer)

    # Автопостинг каждые 6 часов
    current_time = time.time()
    if current_time - last_post_time > POST_INTERVAL:
        quote = random.choice(QUOTES)
        post_to_channel(f"Цитата дня: «{quote['text']}» — {quote['hero']}")
        last_post_time = current_time

    time.sleep(1)
