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

BOT_TOKEN = "YOUR_USER_BOT_TOKEN"

ADMIN_ID = 8970306340

FORCE_JOIN = "@easy_buy_account"

SUPPORT = "@YOUR_SUPPORT"

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
