# Telegram Math Bot by Cytra

import json
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ====== CONFIG ======
import os
TOKEN = os.getenv("TOKEN")

# ====== STORAGE ======

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ====== MATH ======

def generate_question():
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    op = random.choice(["+", "-"])

    if op == "+":
        correct = a + b
    else:
        correct = a - b

    options = [correct]
    while len(options) < 4:
        fake = random.randint(correct - 10, correct + 10)
        if fake not in options:
            options.append(fake)
    random.shuffle(options)

    return f"{a} {op} {b} = ?", correct, options

# ====== BOT ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am Cytra's Math Bot. Send a message to continue.")

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = str(update.message.from_user.id)

    # Check lock
    if user_id in data:
        locked_until = data[user_id].get("locked_until", 0)
        if time.time() < locked_until:
            remaining = int((locked_until - time.time()) / 3600)
            await update.message.reply_text(f"Wrong answer before. Wait {remaining}h until next try.")
            return

    # Generate q
    q, correct, options = generate_question()
    data[user_id] = {"correct": correct, "locked_until": 0, "verified": False}
    save_data(data)

    btns = [[InlineKeyboardButton(str(o), callback_data=str(o))] for o in options]
    markup = InlineKeyboardMarkup(btns)

    await update.message.reply_text(q, reply_markup=markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    data = load_data()
    if user_id not in data:
        await query.edit_message_text("Send a message first to get a question.")
        return

    correct = data[user_id]["correct"]
    choice = int(query.data)

    if choice == correct:
        data[user_id]["verified"] = True
        save_data(data)
        await query.edit_message_text("✅ Correct! You may now send messages.")
    else:
        data[user_id]["locked_until"] = time.time() + LOCK_DURATION
        save_data(data)
        await query.edit_message_text("❌ Wrong! You are locked for 24 hours.")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = str(update.message.from_user.id)

    # Check verification
    if user_id in data and data[user_id].get("verified", False):
        await update.message.reply_text(update.message.text)
    else:
        await ask_question(update, context)

# ====== MAIN ======
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    print("Bot started... (Made by Cytra)")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
