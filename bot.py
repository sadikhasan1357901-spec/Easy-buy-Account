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

# ==========================================================
# USERS
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS users(

user_id INTEGER PRIMARY KEY,

name TEXT,

username TEXT,

balance INTEGER DEFAULT 0,

joined TEXT,

ban INTEGER DEFAULT 0

)

""")

# ==========================================================
# CATEGORIES
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS categories(

id INTEGER PRIMARY KEY AUTOINCREMENT,

name TEXT UNIQUE

)

""")

# ==========================================================
# PRODUCTS
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS products(

id INTEGER PRIMARY KEY AUTOINCREMENT,

category_id INTEGER,

name TEXT,

price INTEGER,

warranty INTEGER,

description TEXT

)

""")

# ==========================================================
# STOCK
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS stocks(

id INTEGER PRIMARY KEY AUTOINCREMENT,

product_id INTEGER,

account TEXT,

status INTEGER DEFAULT 0

)

""")

# ==========================================================
# PAYMENTS
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS payments(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

trx TEXT UNIQUE,

amount INTEGER,

screenshot TEXT,

status TEXT,

date TEXT

)

""")

# ==========================================================
# PURCHASES
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS purchases(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

product_id INTEGER,

account TEXT,

price INTEGER,

date TEXT

)

""")

# ==========================================================
# REPLACE REQUEST
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS replace_requests(

id INTEGER PRIMARY KEY AUTOINCREMENT,

purchase_id INTEGER,

user_id INTEGER,

reason TEXT,

status TEXT

)

""")
# ==========================================================
# REPLACE REQUESTS
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS replace_requests(

id INTEGER PRIMARY KEY AUTOINCREMENT,

order_id INTEGER,

user_id INTEGER,

reason TEXT,

status TEXT DEFAULT 'Pending'
created_at TEXT
admin_note TEXT
)

""")
# ==========================================================
# SETTINGS
# ==========================================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS settings(

id INTEGER PRIMARY KEY,

force_join INTEGER DEFAULT 1,

maintenance INTEGER DEFAULT 0

)

""")

cursor.execute(
    "INSERT OR IGNORE INTO settings(id) VALUES(1)"
)

db.commit()

print("✅ Database Ready")

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def register_user(user):

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user.id,)
    )

    data = cursor.fetchone()

    if data is None:

        cursor.execute(
            """
            INSERT INTO users
            (
                user_id,
                name,
                username,
                balance,
                joined
            )
            VALUES(?,?,?,?,?)
            """,
            (
                user.id,
                user.first_name,
                user.username,
                0,
                datetime.now().strftime("%d-%m-%Y %H:%M")
            )
        )

        db.commit()


# ==========================================================
# GET BALANCE
# ==========================================================

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
# UPDATE BALANCE
# ==========================================================

def update_balance(user_id, amount):

    cursor.execute(
        """
        UPDATE users
        SET balance = balance + ?
        WHERE user_id=?
        """,
        (
            amount,
            user_id
        )
    )

    db.commit()


# ==========================================================
# CHECK BAN
# ==========================================================

def is_banned(user_id):

    cursor.execute(
        """
        SELECT ban
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )

    data = cursor.fetchone()

    if data:

        return data[0] == 1

    return False


# ==========================================================
# USER INFO
# ==========================================================

def get_user(user_id):

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )

    return cursor.fetchone()


# ==========================================================
# TOTAL USERS
# ==========================================================

def total_users():

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    return cursor.fetchone()[0]


# ==========================================================
# TOTAL PRODUCTS
# ==========================================================

def total_products():

    cursor.execute(
        "SELECT COUNT(*) FROM products"
    )

    return cursor.fetchone()[0]


# ==========================================================
# TOTAL CATEGORIES
# ==========================================================

def total_categories():

    cursor.execute(
        "SELECT COUNT(*) FROM categories"
    )

    return cursor.fetchone()[0]


# ==========================================================
# TOTAL SALES
# ==========================================================

def total_sales():

    cursor.execute(
        "SELECT COUNT(*) FROM purchases"
    )

    return cursor.fetchone()[0]


# ==========================================================
# SETTINGS
# ==========================================================

def maintenance_mode():

    cursor.execute(
        """
        SELECT maintenance
        FROM settings
        WHERE id=1
        """
    )

    data = cursor.fetchone()

    return data[0]


def force_join_enabled():

    cursor.execute(
        """
        SELECT force_join
        FROM settings
        WHERE id=1
        """
    )

    data = cursor.fetchone()

    return data[0]

# ==========================================================
# START COMMAND
# ==========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    # Register User
    register_user(user)

    # Ban Check
    if is_banned(user.id):

        await update.message.reply_text(
            "🚫 আপনার অ্যাকাউন্ট Suspend করা হয়েছে।"
        )
        return

    # Maintenance Mode
    if maintenance_mode() == 1 and user.id != ADMIN_ID:

        await update.message.reply_text(
            "🛠 Bot বর্তমানে Maintenance Mode-এ আছে।\n\nঅনুগ্রহ করে পরে আবার চেষ্টা করুন।"
        )
        return

    # Force Join
    if force_join_enabled():

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
                            url=CHANNEL_LINK
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

                    "🔒 বট ব্যবহার করার আগে আমাদের Channel Join করুন।",

                    reply_markup=InlineKeyboardMarkup(keyboard)

                )

                return

        except:

            pass

    await home_menu(update.message)


# ==========================================================
# HOME MENU
# ==========================================================

async def home_menu(message):

    keyboard = [

        [
            InlineKeyboardButton(
                "🛒 Buy ID",
                callback_data="buy_id"
            ),

            InlineKeyboardButton(
                "💼 Buy BM",
                callback_data="buy_bm"
            )

        ],

        [
            InlineKeyboardButton(
                "🌍 VPN Service",
                callback_data="vpn"
            )
        ],

        [
            InlineKeyboardButton(
                "👤 Profile",
                callback_data="profile"
            ),

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
                "📦 Purchase History",
                callback_data="history"
            )
        ],

        [
            InlineKeyboardButton(
                "♻ Replace Request",
                callback_data="replace"
            )
        ],

        [
            InlineKeyboardButton(
                "🆘 Support",
                url=f"https://t.me/{SUPPORT.replace('@','')}"
            ),


            [
    InlineKeyboardButton(
        "📦 My Orders",
        callback_data="orders"
    )
],
            
            InlineKeyboardButton(
                "👥 Community",
                url=CHANNEL_LINK
            )
        ]

    ]

    await message.reply_text(

        f"""
🛍 <b>{BOT_NAME}</b>

Welcome to Easy Buy Account.

Choose an option below.
""",

        parse_mode=ParseMode.HTML,

        reply_markup=InlineKeyboardMarkup(keyboard)

    )


# ==========================================================
# CHECK JOIN
# ==========================================================

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    try:

        member = await context.bot.get_chat_member(

            CHANNEL_USERNAME,

            query.from_user.id

        )

        if member.status not in [

            "left",

            "kicked"

        ]:

            await query.message.delete()

            await home_menu(query.message)

        else:

            await query.answer(

                "❌ আগে Channel Join করুন।",

                show_alert=True

            )

    except:

        await query.answer(

            "⚠ আবার চেষ্টা করুন।",

            show_alert=True

            )

# ==========================================================
# PROFILE
# ==========================================================

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user

    balance = get_balance(user.id)

    text = f"""
👤 <b>Your Profile</b>

🆔 ID : <code>{user.id}</code>

🙍 Name : {user.first_name}

📛 Username : @{user.username if user.username else "None"}

💰 Balance : {balance} BDT
"""

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="home"
            )
        ]
    ]

    await query.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==========================================================
# BALANCE
# ==========================================================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    money = get_balance(query.from_user.id)

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
                callback_data="home"
            )
        ]
    ]

    await query.message.edit_text(
        f"""
💰 <b>Your Balance</b>

Current Balance :
<b>{money} BDT</b>
""",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==========================================================
# DEPOSIT
# ==========================================================

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "📝 Submit Deposit",
                callback_data="submit_trx"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="home"
            )
        ]
    ]

    await query.message.edit_text(
        """
💳 <b>bKash Deposit</b>

📱 Number:
017XXXXXXXX

নিচের বাটনে চাপ দিয়ে Deposit Request দিন।
""",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==========================================================
# BACK HOME
# ==========================================================

async def back_home(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    await query.message.delete()

    await home_menu(query.message)

# ==========================================================
# SUBMIT DEPOSIT
# ==========================================================

async def submit_trx(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    context.user_data.clear()

    set_state(context, "deposit_amount")

    await query.message.edit_text(
        "💰 আপনি কত টাকা Deposit করেছেন?\n\nউদাহরণ:\n500"
    )

# ==========================================================
# RECEIVE AMOUNT
# ==========================================================

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_state(context) != "deposit_amount":
        return

    if not update.message.text.isdigit():

        await update.message.reply_text(
            "❌ শুধু সংখ্যা লিখুন।"
        )

        return

    context.user_data["amount"] = int(update.message.text)

    set_state(context, "deposit_trx")

    await update.message.reply_text(
        "🧾 এখন আপনার Transaction ID পাঠান।"
    )
# ==========================================================
# RECEIVE TRX
# ==========================================================

async def receive_trx(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_state(context) != "deposit_trx":
        return

    trx = update.message.text.strip()

    cursor.execute(
        "SELECT id FROM payments WHERE trx=?",
        (trx,)
    )

    if cursor.fetchone():

        await update.message.reply_text(
            "❌ এই Transaction ID আগে ব্যবহার হয়েছে।"
        )

        return

    context.user_data["trx"] = trx

    set_state(context, "deposit_photo")

    await update.message.reply_text(
        "📷 এখন Payment Screenshot পাঠান।"
    )

# ==========================================================
# RECEIVE SCREENSHOT
# ==========================================================

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get("deposit_step") != "photo":
        return

    if not update.message.photo:

        await update.message.reply_text(
            "❌ Screenshot পাঠান।"
        )

        return

    photo = update.message.photo[-1].file_id

    cursor.execute(
        """
        INSERT INTO payments(
            user_id,
            trx,
            amount,
            screenshot,
            status,
            date
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            update.effective_user.id,
            context.user_data["trx"],
            context.user_data["amount"],
            photo,
            "Pending",
            datetime.now().strftime("%d-%m-%Y %H:%M")
        )
    )

        db.commit()

    clear_state(context)
    context.user_data.clear()

    await update.message.reply_text(
        "✅ Deposit Request সফলভাবে জমা হয়েছে。\n\nAdmin যাচাই করার পরে Balance যোগ করা হবে।"
    )

# ==========================================================
# ADMIN PANEL
# ==========================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ আপনি Admin নন।"
        )

        return

    keyboard = [

        [
            InlineKeyboardButton(
                "💳 Pending Deposit",
                callback_data="pending_deposit"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 Products",
                callback_data="admin_products"
            ),

            InlineKeyboardButton(
                "📂 Categories",
                callback_data="admin_categories"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Users",
                callback_data="admin_users"
            ),

            InlineKeyboardButton(
                "📊 Statistics",
                callback_data="admin_stats"
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

        f"""
👨‍💻 <b>{BOT_NAME}</b>

Admin Control Panel

👥 Users : {total_users()}

📂 Categories : {total_categories()}

📦 Products : {total_products()}

🛒 Sales : {total_sales()}
""",

        parse_mode=ParseMode.HTML,

        reply_markup=InlineKeyboardMarkup(keyboard)

    )

# ==========================================================
# PENDING DEPOSIT
# ==========================================================

async def pending_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    cursor.execute("""

    SELECT

    id,

    user_id,

    trx,

    amount

    FROM payments

    WHERE status='Pending'

    ORDER BY id DESC

    """)

    rows = cursor.fetchall()

    if len(rows) == 0:

        await query.message.edit_text(

            "✅ কোনো Pending Deposit নেই।"

        )

        return

    keyboard = []

    text = "💳 Pending Deposit List\n\n"

    for row in rows:

        pid = row[0]

        uid = row[1]

        trx = row[2]

        amount = row[3]

        text += f"""

ID : {pid}

User : {uid}

Amount : {amount} BDT

TRX : {trx}

"""

        keyboard.append([

            InlineKeyboardButton(

                f"✅ Approve #{pid}",

                callback_data=f"approve_{pid}"

            ),

            InlineKeyboardButton(

                f"❌ Reject #{pid}",

                callback_data=f"reject_{pid}"

            )

        ])

    keyboard.append([

        InlineKeyboardButton(

            "⬅ Back",

            callback_data="admin_home"

        )

    ])

    await query.message.edit_text(

        text,

        reply_markup=InlineKeyboardMarkup(keyboard)

        )

# ==========================================================
# ADMIN HOME
# ==========================================================

async def admin_home(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    keyboard = [

        [

            InlineKeyboardButton(
                "💳 Pending Deposit",
                callback_data="pending_deposit"
            )

        ],

        [

            InlineKeyboardButton(
                "📦 Products",
                callback_data="admin_products"
            ),

            InlineKeyboardButton(
                "📂 Categories",
                callback_data="admin_categories"
            )

        ],

        [

            InlineKeyboardButton(
                "👥 Users",
                callback_data="admin_users"
            ),

            InlineKeyboardButton(
                "📊 Statistics",
                callback_data="admin_stats"
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

    await query.message.edit_text(

        f"""
👨‍💻 <b>{BOT_NAME}</b>

Admin Control Panel

👥 Users : {total_users()}

📂 Categories : {total_categories()}

📦 Products : {total_products()}

🛒 Sales : {total_sales()}
""",

        parse_mode=ParseMode.HTML,

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

    cursor.execute("""
    SELECT
    user_id,
    amount,
    status
    FROM payments
    WHERE id=?
    """,(payment_id,))

    data = cursor.fetchone()

    if not data:

        await query.answer(
            "Payment Not Found",
            show_alert=True
        )
        return

    user_id = data[0]
    amount = data[1]
    status = data[2]

    if status != "Pending":

        await query.answer(
            "Already Processed",
            show_alert=True
        )
        return

    update_balance(user_id, amount)

    cursor.execute("""
    UPDATE payments
    SET status='Approved'
    WHERE id=?
    """,(payment_id,))

    db.commit()

    try:

        await context.bot.send_message(

            user_id,

            f"""
✅ Deposit Approved

💰 Amount : {amount} BDT

আপনার Balance সফলভাবে যোগ করা হয়েছে।
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

    cursor.execute("""
    SELECT
    user_id,
    status
    FROM payments
    WHERE id=?
    """,(payment_id,))

    data = cursor.fetchone()

    if not data:

        await query.answer(
            "Payment Not Found",
            show_alert=True
        )
        return

    user_id = data[0]
    status = data[1]

    if status != "Pending":

        await query.answer(
            "Already Processed",
            show_alert=True
        )
        return

    cursor.execute("""
    UPDATE payments
    SET status='Rejected'
    WHERE id=?
    """,(payment_id,))

    db.commit()

    try:

        await context.bot.send_message(

            user_id,

            """
❌ আপনার Deposit Request Reject করা হয়েছে।

প্রয়োজনে Support-এ যোগাযোগ করুন।
"""
        )

    except:
        pass

    await query.message.edit_text(
        "❌ Deposit Rejected."
    )

# ==========================================================
# ADMIN COMMAND
# ==========================================================

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    CommandHandler(
        "admin",
        admin_panel
    )
        )

# ==========================================================
# CALLBACK HANDLERS
# ==========================================================

app.add_handler(
    CallbackQueryHandler(
        check_join,
        pattern="^check_join$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        profile,
        pattern="^profile$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        balance,
        pattern="^balance$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        deposit,
        pattern="^deposit$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        submit_trx,
        pattern="^submit_trx$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        back_home,
        pattern="^home$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        pending_deposit,
        pattern="^pending_deposit$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        admin_home,
        pattern="^admin_home$"
    )
)

app.add_handler(
    CallbackQueryHandler(
        approve_deposit,
        pattern="^approve_"
    )
)

app.add_handler(
    CallbackQueryHandler(
        reject_deposit,
        pattern="^reject_"
    )
)

# ==========================================================
# MESSAGE HANDLERS
# ==========================================================
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text_router
    )
)

app.add_handler(
    MessageHandler(
        filters.PHOTO,
        photo_router
    )
)

# ==========================================================
# CATEGORY PANEL
# ==========================================================

async def admin_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    cursor.execute(
        "SELECT id,name FROM categories ORDER BY id"
    )

    rows = cursor.fetchall()

    text = "📂 Category List\n\n"

    keyboard = []

    if rows:

        for row in rows:

            text += f"• {row[1]}\n"

    else:

        text += "No Category Found."

    keyboard.append([
        InlineKeyboardButton(
            "➕ Add Category",
            callback_data="add_category"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅ Back",
            callback_data="admin_home"
        )
    ])

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================================================
# ADD CATEGORY
# ==========================================================

async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    set_state(context, "category")

    await query.message.edit_text(

        "📂 নতুন Category Name লিখুন।"

    )

# ==========================================================
# RECEIVE CATEGORY
# ==========================================================

async def receive_category(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_state(context) != "category":

        return

    name = update.message.text.strip()

    cursor.execute(

        "SELECT id FROM categories WHERE name=?",

        (name,)

    )

    if cursor.fetchone():

        await update.message.reply_text(

            "❌ এই Category আগে থেকেই আছে।"

        )

        return

    cursor.execute(

        "INSERT INTO categories(name) VALUES(?)",

        (name,)

    )

    db.commit()

    clear_state(context)
context.user_data.clear()

    await update.message.reply_text(

        f"✅ Category Added\n\n{name}"

    )

# ==========================================================
# DELETE CATEGORY
# ==========================================================

async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    cid = int(query.data.split("_")[2])

    cursor.execute(

        "DELETE FROM categories WHERE id=?",

        (cid,)

    )

    db.commit()

    await query.message.edit_text(

        "✅ Category Deleted."

    )

# ==========================================================
# USER STATE
# ==========================================================

def set_state(context, state):

    context.user_data["state"] = state


def get_state(context):

    return context.user_data.get("state")


def clear_state(context):

    context.user_data.pop("state", None)

# ==========================================================
# TEXT ROUTER
# ==========================================================

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    state = get_state(context)

    if state == "deposit_amount":
        return await receive_amount(update, context)

    elif state == "deposit_trx":
        return await receive_trx(update, context)

    elif state == "category":
        return await receive_category(update, context)

    else:
        elif state == "product_name":
    return await receive_product_name(update, context)

elif state == "product_price":
    return await receive_product_price(update, context)

elif state == "product_warranty":
    return await receive_product_warranty(update, context)

elif state == "product_description":
    return await receive_product_description(update, context)
        return

# ==========================================================
# PHOTO ROUTER
# ==========================================================

async def photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    state = get_state(context)

    if state == "deposit_photo":
        return await receive_photo(update, context)

    return

# ==========================================================
# PRODUCT PANEL
# ==========================================================

async def admin_products(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    cursor.execute("""
    SELECT
        products.id,
        products.name,
        products.price,
        categories.name
    FROM products
    LEFT JOIN categories
    ON products.category_id = categories.id
    ORDER BY products.id DESC
    """)

    rows = cursor.fetchall()

    text = "📦 Product List\n\n"

    keyboard = []

    if rows:

        for row in rows:

            text += f"""
🆔 {row[0]}
📦 {row[1]}
📂 {row[3]}
💰 {row[2]} BDT

"""

    else:

        text += "No Product Found."

    keyboard.append([
        InlineKeyboardButton(
            "➕ Add Product",
            callback_data="add_product"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅ Back",
            callback_data="admin_home"
        )
    ])

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================================================
# ADD PRODUCT
# ==========================================================

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    cursor.execute(
        "SELECT id,name FROM categories"
    )

    rows = cursor.fetchall()

    if not rows:

        await query.message.edit_text(
            "❌ আগে একটি Category তৈরি করুন।"
        )

        return

    keyboard = []

    for row in rows:

        keyboard.append([
            InlineKeyboardButton(
                row[1],
                callback_data=f"select_category_{row[0]}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅ Back",
            callback_data="admin_products"
        )
    ])

    await query.message.edit_text(
        "📂 Product-এর Category নির্বাচন করুন।",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================================================
# SELECT CATEGORY
# ==========================================================

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    category_id = int(query.data.split("_")[2])

    context.user_data["product_category"] = category_id

    set_state(context, "product_name")

    await query.message.edit_text(
        "📝 এখন Product Name লিখুন।"
                    )
# ==========================================================
# RECEIVE PRODUCT NAME
# ==========================================================

async def receive_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_state(context) != "product_name":
        return

    name = update.message.text.strip()

    if len(name) < 2:

        await update.message.reply_text(
            "❌ Product Name খুব ছোট।"
        )
        return

    context.user_data["product_name"] = name

    set_state(context, "product_price")

    await update.message.reply_text(
        "💰 Product Price লিখুন (শুধু সংখ্যা)।"
    )

# ==========================================================
# RECEIVE PRODUCT PRICE
# ==========================================================

async def receive_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_state(context) != "product_price":
        return

    if not update.message.text.isdigit():

        await update.message.reply_text(
            "❌ শুধু সংখ্যা লিখুন।"
        )
        return

    price = int(update.message.text)

    if price <= 0:

        await update.message.reply_text(
            "❌ Price অবশ্যই ১ বা তার বেশি হতে হবে।"
        )
        return

    context.user_data["product_price"] = price

    set_state(context, "product_warranty")

    await update.message.reply_text(
        "🛡 Warranty (দিন) লিখুন।"
    )

# ==========================================================
# RECEIVE WARRANTY
# ==========================================================

async def receive_product_warranty(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_state(context) != "product_warranty":
        return

    if not update.message.text.isdigit():

        await update.message.reply_text(
            "❌ শুধু সংখ্যা লিখুন।"
        )
        return

    warranty = int(update.message.text)

    if warranty < 0:

        await update.message.reply_text(
            "❌ Warranty ভুল।"
        )
        return

    context.user_data["product_warranty"] = warranty

    set_state(context, "product_description")

    await update.message.reply_text(
        "📝 Product Description লিখুন।"
    )

# ==========================================================
# RECEIVE DESCRIPTION
# ==========================================================

async def receive_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_state(context) != "product_description":
        return

    description = update.message.text.strip()

    if len(description) == 0:

        await update.message.reply_text(
            "❌ Description লিখুন।"
        )
        return

    if "product_category" not in context.user_data:

        await update.message.reply_text(
            "❌ Category পাওয়া যায়নি। আবার শুরু করুন।"
        )
        clear_state(context)
        context.user_data.clear()
        return

    category = context.user_data["product_category"]
    name = context.user_data["product_name"]
    price = context.user_data["product_price"]
    warranty = context.user_data["product_warranty"]

    cursor.execute(
        """
        INSERT INTO products(
            category_id,
            name,
            price,
            warranty,
            description
        )
        VALUES(?,?,?,?,?)
        """,
        (
            category,
            name,
            price,
            warranty,
            description
        )
    )

    db.commit()

    clear_state(context)
    context.user_data.clear()

    await update.message.reply_text(
        f"""
✅ Product সফলভাবে যোগ হয়েছে।

📦 Name : {name}

💰 Price : {price} BDT

🛡 Warranty : {warranty} Days
"""
    )

# ==========================================================
# UPLOAD STOCK
# ==========================================================

async def upload_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    cursor.execute(
        "SELECT id, name FROM products ORDER BY name"
    )

    products = cursor.fetchall()

    if not products:
        await query.message.edit_text(
            "❌ আগে একটি Product তৈরি করুন।"
        )
        return

    keyboard = []

    for pid, name in products:
        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=f"stock_product_{pid}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅ Back",
            callback_data="admin_products"
        )
    ])

    await query.message.edit_text(
        "📦 যে Product-এ Stock যোগ করবেন সেটি নির্বাচন করুন।",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================================================
# SELECT STOCK PRODUCT
# ==========================================================

async def select_stock_product(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    product_id = int(query.data.split("_")[2])

    context.user_data["stock_product"] = product_id

    set_state(context, "stock_upload")

    await query.message.edit_text(
        "📄 এখন .txt File পাঠান।"
    )

# ==========================================================
# RECEIVE TXT
# ==========================================================

async def receive_stock_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_state(context) != "stock_upload":
        return

    document = update.message.document

    if document is None:
        return

    if not document.file_name.endswith(".txt"):

        await update.message.reply_text(
            "❌ শুধু TXT File গ্রহণযোগ্য।"
        )

        return

    file = await document.get_file()

    await file.download_to_drive("stock.txt")

    await update.message.reply_text(
        "✅ TXT File Upload হয়েছে।"
    )

    set_state(context, "stock_import")

# ==========================================================
# IMPORT STOCK
# ==========================================================

async def import_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_state(context) != "stock_import":
        return

    product = context.user_data["stock_product"]

    count = 0

    with open("stock.txt", "r", encoding="utf-8") as f:

        for line in f:

            account = line.strip()

            if not account:
                continue

            cursor.execute(
                "SELECT id FROM stocks WHERE account=?",
                (account,)
            )

            if cursor.fetchone():
                continue

            cursor.execute(
                """
                INSERT INTO stocks(
                    product,
                    account,
                    status
                )
                VALUES(?,?,0)
                """,
                (
                    product,
                    account
                )
            )

            count += 1

    db.commit()

    clear_state(context)

    context.user_data.clear()

    await update.message.reply_text(
        f"✅ {count} টি Stock সফলভাবে Import হয়েছে।"
    )

# ==========================================================
# BUY PRODUCT
# ==========================================================

async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    cursor.execute("""
        SELECT id,name,price
        FROM products
        ORDER BY name
    """)

    products = cursor.fetchall()

    if not products:
        await query.message.edit_text("❌ কোনো Product পাওয়া যায়নি।")
        return

    keyboard = []

    for pid, name, price in products:
        keyboard.append([
            InlineKeyboardButton(
                f"{name} - {price} BDT",
                callback_data=f"buy_{pid}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅ Back",
            callback_data="home"
        )
    ])

    await query.message.edit_text(
        "🛒 একটি Product নির্বাচন করুন।",
        reply_markup=InlineKeyboardMarkup(keyboard)
            )

# ==========================================================
# CONFIRM PURCHASE
# ==========================================================

async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_")[1])

    cursor.execute(
        "SELECT name,price FROM products WHERE id=?",
        (product_id,)
    )

    product = cursor.fetchone()

    if not product:
        await query.answer("Product Not Found", show_alert=True)
        return

    name, price = product

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Confirm",
                callback_data=f"confirmbuy_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="home"
            )
        ]
    ]

    await query.message.edit_text(
        f"""
📦 Product : {name}

💰 Price : {price} BDT

আপনি কি Purchase করতে চান?
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================================================
# AUTO DELIVERY
# ==========================================================

async def auto_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_")[1])
    user_id = query.from_user.id

    balance = get_balance(user_id)

    cursor.execute(
        "SELECT name,price FROM products WHERE id=?",
        (product_id,)
    )

    product = cursor.fetchone()

    if not product:
        await query.answer("Product নেই", show_alert=True)
        return

    name, price = product

    if balance < price:
        await query.answer("❌ Balance পর্যাপ্ত নয়।", show_alert=True)
        return

    cursor.execute("""
        SELECT id,account
        FROM stocks
        WHERE product=? AND status=0
        LIMIT 1
    """, (product_id,))

    stock = cursor.fetchone()

    if not stock:
        await query.answer("❌ Stock শেষ।", show_alert=True)
        return

    stock_id, account = stock

    # Balance কাটুন
    update_balance(user_id, -price)

    # Stock Sold
    cursor.execute(
        "UPDATE stocks SET status=1 WHERE id=?",
        (stock_id,)
    )

    # Purchase History
    cursor.execute("""
        INSERT INTO purchases(user_id,product,account,date)
        VALUES(?,?,?,?)
    """, (
        user_id,
        product_id,
        account,
        datetime.now().strftime("%d-%m-%Y %H:%M")
    ))

    db.commit()

    await query.message.edit_text(
        f"""
✅ Purchase Successful

📦 Product : {name}

🔑 Account:

<code>{account}</code>
""",
        parse_mode=ParseMode.HTML
    )

# ==========================================================
# MY ORDERS
# ==========================================================

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    cursor.execute("""
        SELECT
            purchases.id,
            products.name,
            purchases.date
        FROM purchases
        JOIN products
        ON purchases.product = products.id
        WHERE purchases.user_id=?
        ORDER BY purchases.id DESC
    """, (query.from_user.id,))

    rows = cursor.fetchall()

    if not rows:

        await query.message.edit_text(
            "📦 আপনার এখনো কোনো Order নেই।"
        )
        return

    keyboard = []

    for order_id, product_name, order_date in rows:

        keyboard.append([
            InlineKeyboardButton(
                f"{product_name} | {order_date}",
                callback_data=f"order_{order_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅ Back",
            callback_data="home"
        )
    ])

    await query.message.edit_text(
        "📜 আপনার Order List",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================================================
# ORDER DETAILS
# ==========================================================

async def order_details(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    order_id = int(query.data.split("_")[1])

    cursor.execute("""
        SELECT
            products.name,
            purchases.account,
            purchases.date
        FROM purchases
        JOIN products
        ON purchases.product = products.id
        WHERE purchases.id=?
        AND purchases.user_id=?
    """, (
        order_id,
        query.from_user.id
    ))

    row = cursor.fetchone()

    if not row:

        await query.answer(
            "Order পাওয়া যায়নি।",
            show_alert=True
        )
        return

    product_name, account, order_date = row

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="orders"
            )
        ]
    ]
[
    InlineKeyboardButton(
        "♻ Replace",
        callback_data=f"replace_{order_id}"
    )
],
    await query.message.edit_text(
        f"""
📦 Product
{product_name}

📅 Purchase Date
{order_date}

🔑 Delivered Account

<code>{account}</code>
""",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================================================
# REPLACE REQUEST
# ==========================================================

async def replace_request(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    order_id = int(query.data.split("_")[1])

    cursor.execute("""
        SELECT id
        FROM purchases
        WHERE id=? AND user_id=?
    """, (order_id, query.from_user.id))

    if not cursor.fetchone():

        await query.answer(
            "Order পাওয়া যায়নি।",
            show_alert=True
        )
        return

    context.user_data["replace_order"] = order_id

    set_state(context, "replace_reason")

    await query.message.edit_text(
        "📝 Replace-এর কারণ লিখুন।"
    )

# ==========================================================
# RECEIVE REPLACE REASON
# ==========================================================

async def receive_replace_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_state(context) != "replace_reason":
        return

    reason = update.message.text.strip()

    if len(reason) < 5:

        await update.message.reply_text(
            "❌ অন্তত ৫ অক্ষরের কারণ লিখুন।"
        )

        return

    order_id = context.user_data["replace_order"]

    cursor.execute("""
        INSERT INTO replace_requests(
            order_id,
            user_id,
            reason,
            status
        )
        VALUES(?,?,?,?)
    """, (
        order_id,
        update.effective_user.id,
        reason,
        "Pending"
    ))

    db.commit()

    clear_state(context)

    context.user_data.clear()

    await update.message.reply_text(
        "✅ Replace Request পাঠানো হয়েছে।"
    )

# ==========================================================
# REPLACE LIST
# ==========================================================

async def replace_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    cursor.execute("""
        SELECT
            id,
            user_id,
            status
        FROM replace_requests
        WHERE status='Pending'
    """)

    rows = cursor.fetchall()

    if not rows:

        await query.message.edit_text(
            "✅ কোনো Pending Replace নেই।"
        )

        return

    keyboard = []

    for rid, uid, status in rows:

        keyboard.append([

            InlineKeyboardButton(
                f"Replace #{rid}",
                callback_data=f"replace_view_{rid}"
            )

        ])

    await query.message.edit_text(

        "♻ Pending Replace Requests",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )

# ==========================================================
# VIEW REPLACE REQUEST
# ==========================================================

async def view_replace(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    replace_id = int(query.data.split("_")[2])

    cursor.execute("""
    SELECT
        rr.id,
        rr.user_id,
        rr.order_id,
        rr.reason,
        p.product
    FROM replace_requests rr
    JOIN purchases p
    ON rr.order_id = p.id
    WHERE rr.id=?
    """, (replace_id,))

    row = cursor.fetchone()

    if not row:
        await query.answer("Request Not Found", show_alert=True)
        return

    rid, user_id, order_id, reason, product_id = row

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Approve",
                callback_data=f"replace_ok_{rid}"
            ),
            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"replace_no_{rid}"
            )
        ]
    ]

    await query.message.edit_text(
        f"""
♻ Replace Request

Request ID : {rid}

User ID : {user_id}

Order ID : {order_id}

Reason :

{reason}
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================================================
# APPROVE REPLACE
# ==========================================================

async def approve_replace(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    replace_id = int(query.data.split("_")[2])

    cursor.execute("""
    SELECT
        rr.user_id,
        p.product
    FROM replace_requests rr
    JOIN purchases p
    ON rr.order_id = p.id
    WHERE rr.id=?
    """, (replace_id,))

    data = cursor.fetchone()

    if not data:
        return

    user_id, product_id = data

    cursor.execute("""
    SELECT
        id,
        account
    FROM stocks
    WHERE product=?
    AND status=0
    LIMIT 1
    """, (product_id,))

    stock = cursor.fetchone()

    if not stock:

        await query.answer(
            "Stock শেষ।",
            show_alert=True
        )

        return

    stock_id, account = stock

    cursor.execute(
        "UPDATE stocks SET status=1 WHERE id=?",
        (stock_id,)
    )

    cursor.execute(
        "UPDATE replace_requests SET status='Approved' WHERE id=?",
        (replace_id,)
    )

    db.commit()

    try:

        await context.bot.send_message(

            user_id,

            f"""
✅ Replace Approved

নতুন Account

<code>{account}</code>
""",

            parse_mode="HTML"

        )

    except:
        pass

    await query.message.edit_text(
        "✅ Replace Approved."
    )

# ==========================================================
# REJECT REPLACE
# ==========================================================

async def reject_replace(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    replace_id = int(query.data.split("_")[2])

    cursor.execute(
        "UPDATE replace_requests SET status='Rejected' WHERE id=?",
        (replace_id,)
    )

    db.commit()

    await query.message.edit_text(
        "❌ Replace Rejected."
    )


# ==========================================================
# RUN BOT
# ==========================================================

print("===================================")
print(" Easy Buy Account Started")
print("===================================")

app.run_polling()


