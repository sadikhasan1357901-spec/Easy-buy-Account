# ==========================================================
# Easy Buy Account
# User Bot
# Version : 0.1
# ==========================================================

import logging
import sqlite3

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

BOT_TOKEN = "YOUR_NEW_BOT_TOKEN"

ADMIN_ID = 8970306340

FORCE_JOIN = "@easy_buy_account"

SUPPORT = "@Junaid_Hasan_Admin"

COMMUNITY = "https://t.me/easy_buy_account"

DATABASE = "easybuy.db"

# ==========================================================
# LOG
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ==========================================================
# DATABASE
# ==========================================================

db = sqlite3.connect(
    DATABASE,
    check_same_thread=False
)

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(

user_id INTEGER PRIMARY KEY,

name TEXT,

username TEXT,

balance INTEGER DEFAULT 0,

joined TEXT

)
""")

db.commit()

# ==========================================================
# FUNCTIONS
# ==========================================================

def register_user(user):

    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user.id,)
    )

    if cursor.fetchone() is None:

        cursor.execute(
            """
            INSERT INTO users
            VALUES(?,?,?,?,datetime('now'))
            """,
            (
                user.id,
                user.first_name,
                user.username,
                0
            )
        )

        db.commit()

def get_balance(user_id):

    cursor.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    )

    data = cursor.fetchone()

    if data:
        return data[0]

    return 0
