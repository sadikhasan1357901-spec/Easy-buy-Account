# ==========================================================
# Easy Buy Account
# Version : v1.0
# User + Admin Bot
# Python Telegram Bot v21.11
# SQLite Database
# ==========================================================

import sqlite3
import logging
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.constants import ParseMode

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ==========================================================
# BOT CONFIG
# ==========================================================

BOT_TOKEN = "8656122440:AAGEvLbWD8k72zuZh21KonTQLws6mQk64Yc"

ADMIN_ID = 8970306340

CHANNEL_USERNAME = "@easy_buy_account"

CHANNEL_LINK = "https://t.me/easy_buy_account"

SUPPORT = "@Junaid_Hasan_Admin"

DATABASE = "easybuy.db"

BOT_NAME = "Easy Buy Account"

VERSION = "1.0"

# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

print("=" * 50)
print(" Easy Buy Account")
print(" Version :", VERSION)
print("=" * 50)
print("Database :", DATABASE)
print("Starting Bot...")
print("=" * 50)

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS payments(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

trx TEXT UNIQUE,

amount INTEGER,

screenshot TEXT,

status TEXT

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
# PENDING DEPOSIT LIST
# ==========================================================

async def pending_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:

        return

    cursor.execute("""

        SELECT id,user_id,trx

        FROM payments

        WHERE status='Pending'

    """)

    data = cursor.fetchall()

    if len(data) == 0:

        await query.message.edit_text(

            "✅ No Pending Deposit."

        )

        return

    keyboard = []

    text = "💳 Pending Deposits\n\n"

    for row in data:

        pid = row[0]

        uid = row[1]

        trx = row[2]

        text += f"""
ID : {pid}
User : {uid}
TRX : {trx}

"""

        keyboard.append(

            [

                InlineKeyboardButton(

                    f"Approve #{pid}",

                    callback_data=f"approve_{pid}"

                ),

                InlineKeyboardButton(

                    f"Reject #{pid}",

                    callback_data=f"reject_{pid}"

                )

            ]

        )

    keyboard.append(

        [

            InlineKeyboardButton(

                "⬅ Back",

                callback_data="admin_home"

            )

        ]

    )

    await query.message.edit_text(

        text,

        reply_markup=InlineKeyboardMarkup(keyboard)

    )
    
# ==========================================================
# APPROVE DEPOSIT
# ==========================================================

async def approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    payment_id = int(query.data.split("_")[1])

    cursor.execute(
        "SELECT user_id, amount FROM payments WHERE id=?",
        (payment_id,)
    )

    data = cursor.fetchone()

    if not data:

        await query.answer("Payment Not Found", show_alert=True)
        return

    user_id = data[0]
    amount = data[1]

    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id=?",
        (amount, user_id)
    )

    cursor.execute(
        "UPDATE payments SET status='Approved' WHERE id=?",
        (payment_id,)
    )

    db.commit()

    try:

        await context.bot.send_message(

            chat_id=user_id,

            text=f"""
✅ Deposit Approved

💰 Amount : {amount} BDT

আপনার Balance সফলভাবে যোগ হয়েছে।
"""

        )

    except:
        pass

    await query.message.edit_text(
        "✅ Deposit Approved Successfully."
    )

# ==========================================================
# REJECT DEPOSIT
# ==========================================================

async def reject_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    payment_id = int(query.data.split("_")[1])

    cursor.execute(
        "UPDATE payments SET status='Rejected' WHERE id=?",
        (payment_id,)
    )

    db.commit()

    await query.message.edit_text(
        "❌ Deposit Rejected."
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

app.add_handler(

    CallbackQueryHandler(

        pending_deposit,

        pattern="pending_deposit"

    )

)
app.add_handler(
    CallbackQueryHandler(
        approve_deposit,
        pattern=r"^approve_\d+$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        reject_deposit,
        pattern=r"^reject_\d+$"
    )
)






print("Easy Buy Account Started...")

app.run_polling()
