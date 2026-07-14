# ==========================================================
# Easy Buy Account
# User Bot
# Version : 0.1
# Developer : ChatGPT
# ==========================================================

import os
import sqlite3
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ==========================================================
# CONFIG
# ==========================================================

BOT_TOKEN = "8656122440:AAGEvLbWD8k72zuZh21KonTQLws6mQk64Yc"

# Database

conn = sqlite3.connect("easybuy.db", check_same_thread=False)

cursor = conn.cursor()

cursor.execute("""

CREATE TABLE IF NOT EXISTS users(

id INTEGER PRIMARY KEY,

name TEXT,

balance INTEGER DEFAULT 0

)

""")

conn.commit()

ADMIN_ID = 8970306340

FORCE_JOIN = "@easy_buy_account"

SUPPORT = "@Junaid_Hasan_Admin"

COMMUNITY = "https://t.me/easy_buy_account"

DATABASE = "easybuy.db"

# ==========================================================
# LOG
# ==========================================================

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

# ==========================================================
# DATABASE
# ==========================================================

db = sqlite3.connect(
    DATABASE,
    check_same_thread=False
)

cursor = db.cursor()

# ==========================================================
# USERS
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS users(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER UNIQUE,

name TEXT,

username TEXT,

balance INTEGER DEFAULT 0,

joined TEXT

)

""")

# ==========================================================
# CATEGORY
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS categories(

id INTEGER PRIMARY KEY AUTOINCREMENT,

name TEXT

)

""")

# ==========================================================
# PRODUCTS
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS products(

id INTEGER PRIMARY KEY AUTOINCREMENT,

category INTEGER,

name TEXT,

price INTEGER,

warranty INTEGER

)

""")

# ==========================================================
# STOCK
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS stocks(

id INTEGER PRIMARY KEY AUTOINCREMENT,

product INTEGER,

account TEXT,

status INTEGER DEFAULT 0

)

""")

# ==========================================================
# PAYMENT
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS payments(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

trx TEXT,

amount INTEGER,

status TEXT

)

""")

# ==========================================================
# PURCHASE
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS purchases(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

product INTEGER,

account TEXT,

date TEXT

)

""")

db.commit()

print("Database Ready...")





from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ==========================
# CONFIG
# ==========================

BOT_TOKEN = "8656122440:AAGEvLbWD8k72zuZh21KonTQLws6mQk64Yc"

ADMIN_ID = 8970306340

CHANNEL_USERNAME = "@easy_buy_account"

# ==========================
# START
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    try:
        member = await context.bot.get_chat_member(
            CHANNEL_USERNAME,
            user.id
        )

        if member.status in ["left", "kicked"]:

            keyboard = [
                [
                    InlineKeyboardButton(
                        "📢 Join Channel",
                        url="https://t.me/easy_buy_account"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "✅ I've Joined",
                        callback_data="check_join"
                    )
                ]
            ]

            await update.message.reply_text(
                "🔒 প্রথমে আমাদের চ্যানেলে Join করুন।",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

    except:
        pass

    keyboard = [

        [
            InlineKeyboardButton(
                "🛒 Buy Account",
                callback_data="buy"
            )
        ],

        [
            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance"
            )
        ],

        [
            InlineKeyboardButton(
                "➕ Add Balance",
                callback_data="deposit"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 My Orders",
                callback_data="orders"
            )
        ],

        [
            InlineKeyboardButton(
                "👤 Profile",
                callback_data="profile"
            )
        ]

    ]

    await update.message.reply_text(

        f"👋 Welcome {user.first_name}\n\n"
        f"🛍 Easy Buy Account Store",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )

# ==========================
# CHECK JOIN
# ==========================

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    try:

        member = await context.bot.get_chat_member(
            CHANNEL_USERNAME,
            user.id
        )

        if member.status not in ["left", "kicked"]:

            keyboard = [

                [
                    InlineKeyboardButton(
                        "🛒 Buy Account",
                        callback_data="buy"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "💰 Balance",
                        callback_data="balance"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "➕ Add Balance",
                        callback_data="deposit"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "📦 My Orders",
                        callback_data="orders"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "👤 Profile",
                        callback_data="profile"
                    )
                ]

            ]

            await query.message.edit_text(

                "✅ Verification Successful",

                reply_markup=InlineKeyboardMarkup(keyboard)

            )

        else:

            await query.answer(
                "Join Channel First",
                show_alert=True
            )

    except:

        await query.answer(
            "Try Again",
            show_alert=True
        )

# ==========================
# MAIN
# ==========================

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    CallbackQueryHandler(
        check_join,
        pattern="check_join"
    )
)

print("Bot Running...")

app.run_polling()
