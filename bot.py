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

BOT_TOKEN = "8656122440:AAGEvLbWD8k72zuZh21KonTQLws6mQk64Yc"

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
# ==========================================================
# START COMMAND
# ==========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    register_user(user)

    try:

        member = await context.bot.get_chat_member(
            FORCE_JOIN,
            user.id
        )

        if member.status in ["left", "kicked"]:

            keyboard = [

                [
                    InlineKeyboardButton(
                        "📢 Join Channel",
                        url=COMMUNITY
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

                "🔒 Please join our channel first.",

                reply_markup=InlineKeyboardMarkup(keyboard)

            )

            return

    except Exception:

        pass

    await show_main_menu(update.message)


# ==========================================================
# MAIN MENU
# ==========================================================

async def show_main_menu(message):

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
            ),
            InlineKeyboardButton(
                "👤 Profile",
                callback_data="profile"
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
                "♻ Replace",
                callback_data="replace"
            )
        ],

        [
            InlineKeyboardButton(
                "☎ Support",
                url="https://t.me/Junaid_Hasan_Admin"
            ),

            InlineKeyboardButton(
                "📢 Community",
                url=COMMUNITY
            )
        ]

    ]

    await message.reply_text(

        "🏠 Welcome to Easy Buy Account\n\n"
        "Choose an option below.",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )


# ==========================================================
# CHECK JOIN
# ==========================================================

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    try:

        member = await context.bot.get_chat_member(
            FORCE_JOIN,
            user.id
        )

        if member.status not in ["left", "kicked"]:

            await query.message.delete()

            await show_main_menu(query.message)

        else:

            await query.answer(

                "❌ Join the channel first.",

                show_alert=True

            )

    except Exception:

        await query.answer(

            "⚠ Try Again",

            show_alert=True

        )
