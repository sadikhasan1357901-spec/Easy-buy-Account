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
    MessageHandler,
    ContextTypes,
    filters
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

BKASH_NUMBER = "01XXXXXXXXX"

NAGAD_NUMBER = "01XXXXXXXXX"

WAIT_TRX = 1

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

# ==========================================================
# PROFILE
# ==========================================================

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user

    cursor.execute(
        "SELECT balance, joined FROM users WHERE user_id=?",
        (user.id,)
    )

    data = cursor.fetchone()

    balance = data[0] if data else 0
    joined = data[1] if data else "Unknown"

    text = f"""
👤 <b>Your Profile</b>

🆔 User ID : <code>{user.id}</code>

🙍 Name : {user.first_name}

📛 Username : @{user.username if user.username else 'None'}

💰 Balance : {balance} BDT

📅 Joined : {joined}
"""

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="back_home"
            )
        ]
    ]

    await query.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==========================================================
# BALANCE
# ==========================================================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    amount = get_balance(query.from_user.id)

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Add Balance",
                callback_data="deposit"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="back_home"
            )
        ]
    ]

    await query.message.edit_text(
        f"💰 Your Current Balance\n\n<b>{amount} BDT</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==========================================================
# BACK HOME
# ==========================================================

async def back_home(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [

        [InlineKeyboardButton("🛒 Buy Account", callback_data="buy")],

        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("👤 Profile", callback_data="profile")
        ],

        [InlineKeyboardButton("➕ Add Balance", callback_data="deposit")],

        [InlineKeyboardButton("📦 My Orders", callback_data="orders")],

        [InlineKeyboardButton("♻ Replace", callback_data="replace")],

        [
            InlineKeyboardButton("☎ Support", url="https://t.me/Junaid_Hasan_Admin"),
            InlineKeyboardButton("📢 Community", url=COMMUNITY)
        ]
    ]

    await query.message.edit_text(
        "🏠 <b>Easy Buy Account</b>\n\nSelect an option:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================================================
# ADD BALANCE
# ==========================================================

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    text = f"""
💳 <b>Add Balance</b>

নিচের যেকোনো নম্বরে টাকা পাঠান।

📱 bKash: <code>{BKASH_NUMBER}</code>

📱 Nagad: <code>{NAGAD_NUMBER}</code>

টাকা পাঠানোর পর Transaction ID সাবমিট করুন।
"""

    keyboard = [

        [
            InlineKeyboardButton(
                "🧾 Submit Transaction ID",
                callback_data="submit_trx"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="back_home"
            )
        ]

    ]

    await query.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def submit_trx(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["waiting_trx"] = True

    await query.message.reply_text(
        "🧾 আপনার Transaction ID লিখে পাঠান।"
    )

async def receive_trx(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("waiting_trx"):
        return

    context.user_data["waiting_trx"] = False

    trx = update.message.text

    user = update.effective_user

    cursor.execute(
        "INSERT INTO payments(user_id,trx,amount,status) VALUES(?,?,?,?)",
        (
            user.id,
            trx,
            0,
            "Pending"
        )
    )


# ==========================================================
# ADMIN PANEL
# ==========================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ You are not Admin."
        )
        return

    keyboard = [

        [
            InlineKeyboardButton(
                "💰 Pending Deposits",
                callback_data="pending_deposit"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 Products",
                callback_data="products"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 Statistics",
                callback_data="stats"
            )
        ],

        [
            InlineKeyboardButton(
                "📢 Broadcast",
                callback_data="broadcast"
            )
        ],

        [
            InlineKeyboardButton(
                "⚙ Settings",
                callback_data="settings"
            )
        ]

    ]

    await update.message.reply_text(

        "👨‍💻 Easy Buy Account\n\nAdmin Panel",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )







    

    
    db.commit()

    await update.message.reply_text(
        "✅ Transaction ID জমা হয়েছে।\n\nAdmin যাচাই করার পর Balance যোগ হবে।"
    )

    text = f"""
🆕 নতুন Deposit Request

👤 {user.first_name}

🆔 {user.id}

🧾 TRX ID:
<code>{trx}</code>

Status : Pending
"""

    await context.bot.send_message(
        ADMIN_ID,
        text,
        parse_mode="HTML"
    )


# ==========================================================
# RUN BOT
# ==========================================================

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    CallbackQueryHandler(
        check_join,
        pattern="check_join"
    )
)

app.add_handler(
    CallbackQueryHandler(
        profile,
        pattern="profile"
    )
)

app.add_handler(
    CallbackQueryHandler(
        balance,
        pattern="balance"
    )
)

app.add_handler(
    CallbackQueryHandler(
        back_home,
        pattern="back_home"
    )
)

app.add_handler(
    CallbackQueryHandler(
        deposit,
        pattern="deposit"
    )
)

app.add_handler(
    CallbackQueryHandler(
        submit_trx,
        pattern="submit_trx"
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        receive_trx
    )
)

app.add_handler(
    CommandHandler(
        "admin",
        admin_panel
    )
)

print("Easy Buy Account Started...")

app.run_polling()
