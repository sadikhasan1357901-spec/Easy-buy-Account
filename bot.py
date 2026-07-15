import os
import logging
import sqlite3
import json
from datetime import datetime
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyParameters
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURATION
# ==========================================
BOT_TOKEN = "8656122440:AAGEvLbWD8k72zuZh21KonTQLws6mQk64Yc"  # Replace with your Bot Token
ADMIN_ID = 8970306340                # Replace with Admin Telegram ID (Integer)
DB_NAME = "digital_shop.db"

# Conversation States
(
    # User States
    STATE_DEPOSIT_PROOF,
    STATE_REPLACE_REASON,
    # Admin States
    STATE_ADMIN_BROADCAST,
    STATE_ADMIN_SEARCH_USER,
    STATE_ADMIN_EDIT_BAL_ID,
    STATE_ADMIN_EDIT_BAL_AMT,
    STATE_ADMIN_SET_FORCE_JOIN,
    STATE_ADMIN_SET_PAYMENT_NO,
    STATE_ADMIN_SET_SUPPORT,
    STATE_ADMIN_SET_COMMUNITY,
    # Category Management
    STATE_ADD_CAT_NAME,
    STATE_EDIT_CAT_ID,
    STATE_EDIT_CAT_NAME,
    STATE_DEL_CAT_ID,
    # Product Management
    STATE_ADD_PROD_CAT,
    STATE_ADD_PROD_NAME,
    STATE_ADD_PROD_DESC,
    STATE_ADD_PROD_PRICE,
    STATE_ADD_PROD_WARRANTY,
    STATE_ADD_PROD_IMG,
    STATE_EDIT_PROD_ID,
    STATE_EDIT_PROD_FIELD,
    STATE_EDIT_PROD_VAL,
    STATE_DEL_PROD_ID,
    # Stock Management
    STATE_STOCK_PROD_ID,
    STATE_STOCK_TXT,
) = range(26)

# ==========================================
# DATABASE INITIALIZATION
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0.0,
            is_banned INTEGER DEFAULT 0,
            joined_date TEXT
        )
    """)
    
    # Payments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            proof_file_id TEXT,
            status TEXT DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED
            created_at TEXT
        )
    """)
    
    # Categories Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)
    
    # Products Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT,
            description TEXT,
            price REAL,
            warranty TEXT,
            image_file_id TEXT DEFAULT NULL,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )
    """)
    
    # Stocks Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            data TEXT,
            is_sold INTEGER DEFAULT 0,
            sold_to INTEGER DEFAULT NULL,
            sold_at TEXT DEFAULT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)
    
    # Purchases Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            stock_id INTEGER,
            delivered_data TEXT,
            price REAL,
            purchased_at TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(stock_id) REFERENCES stocks(id)
        )
    """)
    
    # Replace Requests Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS replace_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER,
            user_id INTEGER,
            reason TEXT,
            status TEXT DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED
            created_at TEXT,
            FOREIGN KEY(purchase_id) REFERENCES purchases(id)
        )
    """)
    
    # Settings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Default Settings Insert
    default_settings = [
        ("maintenance_mode", "0"),
        ("force_join_channel", ""),
        ("payment_number", "Not Set"),
        ("support_username", "Not Set"),
        ("community_link", "Not Set")
    ]
    for key, val in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
        
    conn.commit()
    conn.close()

init_db()

# ==========================================
# DATABASE HELPER FUNCTIONS
# ==========================================
def db_query(query, params=(), commit=False, fetchall=False, fetchone=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
        if fetchall:
            return cursor.fetchall()
        if fetchone:
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error on query '{query}': {e}")
        return None
    finally:
        conn.close()

def get_setting(key):
    res = db_query("SELECT value FROM settings WHERE key=?", (key,), fetchone=True)
    return res[0] if res else ""

def set_setting(key, value):
    db_query("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)), commit=True)

def is_user_banned(user_id):
    res = db_query("SELECT is_banned FROM users WHERE user_id=?", (user_id,), fetchone=True)
    return res and res[0] == 1

# ==========================================
# FORCE JOIN CHECK HELPER
# ==========================================
async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    channel = get_setting("force_join_channel")
    if not channel:
        return True
    
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        return True
        
    try:
        # Check membership status
        member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        logger.error(f"Force Join Check Error: {e}")
        
    # If not joined, show alert
    text = (
        "⚠️ **আপনাকে প্রথমে আমাদের অফিশিয়াল চ্যানেলে জয়েন করতে হবে!**\n\n"
        "নিচের লিংকে ক্লিক করে জয়েন করুন এবং তারপর আবার বটটি চালু করতে `/start` চাপুন।"
    )
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel.replace('@', '')}")],
        [InlineKeyboardButton("🔄 Checked & Start", callback_data="btn_start_check")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer("দয়া করে প্রথমে চ্যানেলে যুক্ত হোন!", show_alert=True)
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    return False

# ==========================================
# USER INTERFACE & FLOWS
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "No Username"
    
    # Maintenance check (except for Admin)
    if get_setting("maintenance_mode") == "1" and user_id != ADMIN_ID:
        await update.effective_message.reply_text("🚧 বটটি বর্তমানে রক্ষণাবেক্ষণের (Maintenance Mode) অধীনে রয়েছে। দয়া করে পরে চেষ্টা করুন।")
        return ConversationHandler.END

    # Auto registration
    db_query(
        "INSERT OR IGNORE INTO users (user_id, username, joined_date) VALUES (?, ?, ?)",
        (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        commit=True
    )
    
    # Update username if changed
    db_query("UPDATE users SET username=? WHERE user_id=?", (username, user_id), commit=True)
    
    if is_user_banned(user_id):
        await update.effective_message.reply_text("🚫 দুঃখিত, আপনাকে এই বট থেকে ব্যান করা হয়েছে।")
        return ConversationHandler.END

    if not await check_force_join(update, context):
        return ConversationHandler.END

    # Main Menu
    text = f"👋 হ্যালো {user.first_name}!\nআমাদের ডিজিটাল অ্যাকাউন্ট স্টোরে আপনাকে স্বাগতম। আপনি এখান থেকে যেকোনো প্রিমিয়াম অ্যাকাউন্ট স্বয়ংক্রিয়ভাবে কিনতে পারবেন।"
    
    keyboard = [
        [InlineKeyboardButton("🛍️ Buy Accounts", callback_data="buy_menu")],
        [InlineKeyboardButton("👤 My Profile", callback_data="user_profile"), InlineKeyboardButton("💼 My Orders", callback_data="my_orders")],
        [InlineKeyboardButton("➕ Deposit Balance", callback_data="deposit_menu")],
        [InlineKeyboardButton("💬 Support", callback_data="support_info"), InlineKeyboardButton("👥 Community", callback_data="community_info")]
    ]
    
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)
        
    return ConversationHandler.END

# Profile & Wallet
async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user_data = db_query("SELECT balance, joined_date FROM users WHERE user_id=?", (user_id,), fetchone=True)
    if not user_data:
        await query.message.edit_text("ব্যবহারকারীর তথ্য পাওয়া যায়নি।")
        return
        
    balance, joined = user_data
    text = (
        f"👤 **আপনার প্রোফাইল**\n\n"
        f"🆔 ইউজার আইডি: `{user_id}`\n"
        f"💰 ওয়ালেট ব্যালেন্স: `{balance:.2f} BDT`\n"
        f"📅 যুক্ত হয়েছেন: `{joined}`"
    )
    
    keyboard = [
        [InlineKeyboardButton("➕ Deposit Balance", callback_data="deposit_menu")],
        [InlineKeyboardButton("🔙 Back to Home", callback_data="go_home")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Deposit Section
async def deposit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    pay_num = get_setting("payment_number")
    text = (
        f"💳 **ব্যালেন্স অ্যাড বা ডিপোজিট করুন**\n\n"
        f"নিচে দেওয়া নাম্বারে পেমেন্ট (Send Money) সম্পন্ন করুন:\n"
        f"📞 **বিকাশ/নগদ/রকেট:** `{pay_num}`\n\n"
        f"⚠️ **টাকা পাঠানোর পর:** পেমেন্ট প্রুফ বা ট্রানজেকশনের স্ক্রিনশটটি এই চ্যাটে পাঠান।"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="go_home")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return STATE_DEPOSIT_PROOF

async def handle_deposit_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not update.message.photo:
        await update.message.reply_text("❌ অনুগ্রহ করে শুধুমাত্র স্ক্রিনশট বা ইমেজ (Photo) পাঠান!")
        return STATE_DEPOSIT_PROOF
        
    file_id = update.message.photo[-1].file_id
    
    # Save pending deposit to DB
    db_query(
        "INSERT INTO payments (user_id, amount, proof_file_id, created_at) VALUES (?, ?, ?, ?)",
        (user_id, 0.0, file_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        commit=True
    )
    
    # Notify Admin
    last_id = db_query("SELECT last_insert_rowid()", fetchone=True)[0]
    admin_text = (
        f"🔔 **নতুন ডিপোজিট রিকোয়েস্ট!**\n\n"
        f"👤 ইউজার আইডি: `{user_id}`\n"
        f"📊 ট্রানজেকশন আইডি: #{last_id}"
    )
    admin_keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"dep_app_{last_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"dep_rej_{last_id}")
        ]
    ]
    
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=admin_text,
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to notify admin on deposit: {e}")

    await update.message.reply_text("✅ আপনার পেমেন্ট প্রুফটি অ্যাডমিনের কাছে পাঠানো হয়েছে। যাচাই শেষে ব্যালেন্স যুক্ত করা হবে।")
    return ConversationHandler.END

# Product / Buying Menu
async def buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    categories = db_query("SELECT id, name FROM categories", fetchall=True)
    if not categories:
        await query.message.edit_text(
            "😔 দুঃখিত, এখন কোনো ক্যাটাগরি তৈরি করা নেই।",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="go_home")]])
        )
        return
        
    keyboard = []
    for cat_id, name in categories:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"cat_view_{cat_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Home", callback_data="go_home")])
    
    await query.message.edit_text("📁 **ক্যাটাগরি নির্বাচন করুন:**", reply_markup=InlineKeyboardMarkup(keyboard))

async def view_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = int(query.data.split("_")[2])
    
    products = db_query("SELECT id, name, price FROM products WHERE category_id=?", (cat_id,), fetchall=True)
    cat_name = db_query("SELECT name FROM categories WHERE id=?", (cat_id,), fetchone=True)[0]
    
    if not products:
        await query.message.edit_text(
            f"❌ **{cat_name}** ক্যাটাগরিতে কোনো প্রোডাক্ট পাওয়া যায়নি।",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="buy_menu")]])
        )
        return
        
    keyboard = []
    for prod_id, name, price in products:
        # Check stock count
        stock_count = db_query("SELECT COUNT(*) FROM stocks WHERE product_id=? AND is_sold=0", (prod_id,), fetchone=True)[0]
        keyboard.append([InlineKeyboardButton(f"{name} - {price} BDT (Stock: {stock_count})", callback_data=f"prod_view_{prod_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="buy_menu")])
    
    await query.message.edit_text(f"🛍️ **{cat_name} ক্যাটাগরির প্রোডাক্টস:**", reply_markup=InlineKeyboardMarkup(keyboard))

async def view_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prod_id = int(query.data.split("_")[2])
    
    product = db_query("SELECT name, description, price, warranty, image_file_id, category_id FROM products WHERE id=?", (prod_id,), fetchone=True)
    if not product:
        await query.message.edit_text("প্রোডাক্ট পাওয়া যায়নি।")
        return
        
    name, desc, price, warranty, img_id, cat_id = product
    stock_count = db_query("SELECT COUNT(*) FROM stocks WHERE product_id=? AND is_sold=0", (prod_id,), fetchone=True)[0]
    
    text = (
        f"📦 **{name}**\n\n"
        f"📝 বিবরণ: {desc}\n"
        f"💵 দাম: `{price:.2f} BDT`\n"
        f"🛡️ ওয়ারেন্টি: {warranty}\n"
        f"🟢 উপলব্ধ স্টক: `{stock_count}` টি"
    )
    
    keyboard = []
    if stock_count > 0:
        keyboard.append([InlineKeyboardButton("🛒 Buy Now", callback_data=f"prod_buy_{prod_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"cat_view_{cat_id}")])
    
    if img_id:
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=img_id,
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prod_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    # Check User
    user_bal = db_query("SELECT balance FROM users WHERE user_id=?", (user_id,), fetchone=True)[0]
    prod_data = db_query("SELECT name, price FROM products WHERE id=?", (prod_id,), fetchone=True)
    
    if not prod_data:
        await query.message.reply_text("দুঃখিত, প্রোডাক্টটি স্টোরে আর নেই।")
        return
        
    prod_name, price = prod_data
    
    if user_bal < price:
        await query.answer("❌ আপনার ওয়ালেটে পর্যাপ্ত ব্যালেন্স নেই!", show_alert=True)
        return
        
    # Get available stock
    stock = db_query("SELECT id, data FROM stocks WHERE product_id=? AND is_sold=0 LIMIT 1", (prod_id,), fetchone=True)
    if not stock:
        await query.answer("❌ দুঃখিত, এই প্রোডাক্টের পর্যাপ্ত স্টক নেই!", show_alert=True)
        return
        
    stock_id, stock_data = stock
    
    # Deduct balance & mark stock as sold
    new_bal = user_bal - price
    db_query("UPDATE users SET balance=? WHERE user_id=?", (new_bal, user_id), commit=True)
    db_query(
        "UPDATE stocks SET is_sold=1, sold_to=?, sold_at=? WHERE id=?", 
        (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), stock_id), 
        commit=True
    )
    
    # Save Purchase
    db_query(
        "INSERT INTO purchases (user_id, product_id, stock_id, delivered_data, price, purchased_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, prod_id, stock_id, stock_data, price, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        commit=True
    )
    
    # Deliver account
    delivery_text = (
        f"🎉 **ক্রয় সফল হয়েছে!**\n\n"
        f"📦 প্রোডাক্ট: **{prod_name}**\n"
        f"💵 পরিশোধিত মূল্য: `{price:.2f} BDT`\n"
        f"🔑 **আপনার ডিজিটাল অ্যাকাউন্ট ডেটা:**\n\n"
        f"`{stock_data}`\n\n"
        f"🛡️ যদি কোনো সমস্যা থাকে তবে ওয়ারেন্টির নিয়মানুযায়ী রিপ্লেস রিকোয়েস্ট করতে পারেন।"
    )
    
    # Delete previous inline menu (especially if with photo) to avoid confusion
    try:
        await query.message.delete()
    except Exception:
        pass
        
    await context.bot.send_message(chat_id=user_id, text=delivery_text, parse_mode="Markdown")

# My Orders / Purchases
async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    orders = db_query(
        "SELECT p.id, pr.name, p.delivered_data, p.purchased_at FROM purchases p JOIN products pr ON p.product_id = pr.id WHERE p.user_id=? ORDER BY p.id DESC LIMIT 10",
        (user_id,), fetchall=True
    )
    
    if not orders:
        await query.message.edit_text(
            "📦 আপনি এখনো কোনো প্রোডাক্ট কেনেননি।",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="go_home")]])
        )
        return
        
    text = "📦 **আপনার সাম্প্রতিক অর্ডারসমূহ (সর্বোচ্চ ১০টি):**\n\n"
    keyboard = []
    for p_id, prod_name, data, date in orders:
        text += f"🆔 অর্ডার আইডি: #{p_id}\n📦 প্রোডাক্ট: **{prod_name}**\n📅 তারিখ: {date}\n🔑 ডেটা: `{data}`\n\n"
        keyboard.append([InlineKeyboardButton(f"🔁 Replace Req #{p_id}", callback_data=f"req_rep_{p_id}")])
        
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="go_home")])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Replace System User-Side
async def init_replace_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p_id = int(query.data.split("_")[2])
    
    # Check if already has a pending replacement
    existing = db_query("SELECT status FROM replace_requests WHERE purchase_id=?", (p_id,), fetchone=True)
    if existing:
        await query.message.reply_text(f"⚠️ এই অর্ডারের জন্য ইতিমধ্যেই রিপ্লেস রিকোয়েস্ট সাবমিট করা হয়েছে। স্ট্যাটাস: {existing[0]}")
        return ConversationHandler.END
        
    context.user_data["replace_p_id"] = p_id
    await query.message.reply_text("📝 অনুগ্রহ করে অ্যাকাউন্টের সমস্যাটি বিস্তারিত লিখুন (রিপ্লেসের কারণ):")
    return STATE_REPLACE_REASON

async def handle_replace_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reason = update.message.text
    p_id = context.user_data.get("replace_p_id")
    
    if not p_id:
        await update.message.reply_text("⚠️ সমস্যা হয়েছে। অনুগ্রহ করে আবার ট্রাই করুন।")
        return ConversationHandler.END
        
    # Save replace request
    db_query(
        "INSERT INTO replace_requests (purchase_id, user_id, reason, created_at) VALUES (?, ?, ?, ?)",
        (p_id, user_id, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        commit=True
    )
    
    last_id = db_query("SELECT last_insert_rowid()", fetchone=True)[0]
    
    # Get purchase data
    purchase_data = db_query(
        "SELECT pr.name, pu.delivered_data FROM purchases pu JOIN products pr ON pu.product_id = pr.id WHERE pu.id=?",
        (p_id,), fetchone=True
    )
    prod_name, old_data = purchase_data if purchase_data else ("Unknown", "None")
    
    # Notify Admin
    admin_text = (
        f"🔁 **নতুন রিপ্লেস রিকোয়েস্ট!**\n\n"
        f"🆔 রিকোয়েস্ট আইডি: #{last_id}\n"
        f"👤 ইউজার আইডি: `{user_id}`\n"
        f"📦 প্রোডাক্ট: {prod_name}\n"
        f"🔑 পুরাতন ডেটা: `{old_data}`\n"
        f"📝 কারণ: {reason}"
    )
    admin_keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"rep_app_{last_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rep_rej_{last_id}")
        ]
    ]
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=admin_text, 
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to notify admin on replace request: {e}")

    await update.message.reply_text("✅ আপনার রিপ্লেস রিকোয়েস্টটি সফলভাবে অ্যাডমিনের কাছে পাঠানো হয়েছে।")
    return ConversationHandler.END

# Static Buttons
async def support_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sup = get_setting("support_username")
    await query.message.edit_text(
        f"💬 **আমাদের কাস্টমার সাপোর্ট টিম:**\n\nযেকোনো প্রয়োজনে যোগাযোগ করুন: @{sup.replace('@', '')}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="go_home")]])
    )

async def community_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    com = get_setting("community_link")
    await query.message.edit_text(
        f"👥 **আমাদের কমিউনিটি গ্রুপ:**\n\nনিচের লিংকে ক্লিক করে আমাদের গ্রুপে যুক্ত হোন:\n{com}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="go_home")]])
    )

# ==========================================
# ADMIN PANEL & STATISTICS
# ==========================================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("❌ আপনি অ্যাডমিন নন!")
        return
        
    text = "⚙️ **অ্যাডমিন কন্ট্রোল প্যানেল**\n\nবটের সেটিংস, প্রোডাক্ট, ক্যাটাগরি এবং স্টক পরিচালনা করতে নিচের অপশনগুলো ব্যবহার করুন।"
    keyboard = [
        [InlineKeyboardButton("📊 Stats & Dashboard", callback_data="admin_stats")],
        [InlineKeyboardButton("📁 Categories", callback_data="admin_cats"), InlineKeyboardButton("📦 Products", callback_data="admin_prods")],
        [InlineKeyboardButton("⚡ Stock Upload", callback_data="admin_stocks"), InlineKeyboardButton("👤 User Control", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_settings")],
        [InlineKeyboardButton("🔙 Exit Panel", callback_data="go_home")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Compute Statistics
    t_users = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
    t_cats = db_query("SELECT COUNT(*) FROM categories", fetchone=True)[0]
    t_prods = db_query("SELECT COUNT(*) FROM products", fetchone=True)[0]
    t_stocks = db_query("SELECT COUNT(*) FROM stocks", fetchone=True)[0]
    u_stocks = db_query("SELECT COUNT(*) FROM stocks WHERE is_sold=1", fetchone=True)[0]
    a_stocks = db_query("SELECT COUNT(*) FROM stocks WHERE is_sold=0", fetchone=True)[0]
    t_orders = db_query("SELECT COUNT(*) FROM purchases", fetchone=True)[0]
    t_deposits = db_query("SELECT COUNT(*) FROM payments WHERE status='APPROVED'", fetchone=True)[0]
    
    # Revenue
    rev = db_query("SELECT SUM(price) FROM purchases", fetchone=True)[0] or 0.0
    
    text = (
        f"📊 **স্টোর ড্যাশবোর্ড ও পরিসংখ্যান**\n\n"
        f"👥 মোট ইউজার: `{t_users}` জন\n"
        f"📁 মোট ক্যাটাগরি: `{t_cats}` টি\n"
        f"📦 মোট প্রোডাক্ট: `{t_prods}` টি\n\n"
        f"⚡ মোট স্টক: `{t_stocks}` টি\n"
        f"🟢 উপলব্ধ স্টক: `{a_stocks}` টি\n"
        f"🔴 ব্যবহৃত স্টক: `{u_stocks}` টি\n\n"
        f"🛒 মোট অর্ডার: `{t_orders}` টি\n"
        f"💵 মোট পেমেন্ট রিসিভ: `{t_deposits}` টি\n"
        f"💰 মোট রেভিনিউ: `{rev:.2f} BDT`"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ==========================================
# BROADCAST SYSTEM (ADMIN)
# ==========================================
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📢 ব্রডকাস্ট করার জন্য মেসেজ/ফটো/ফরওয়ার্ড মেসেজটি পাঠান:")
    return STATE_ADMIN_BROADCAST

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = db_query("SELECT user_id FROM users WHERE is_banned=0", fetchall=True)
    success = 0
    fail = 0
    
    await update.message.reply_text("⏳ ব্রডকাস্ট করা হচ্ছে...")
    
    for (u_id,) in users:
        try:
            if update.message.text:
                await context.bot.send_message(chat_id=u_id, text=update.message.text)
            elif update.message.photo:
                await context.bot.send_photo(
                    chat_id=u_id, 
                    photo=update.message.photo[-1].file_id, 
                    caption=update.message.caption
                )
            elif update.message.forward_origin:
                await context.bot.forward_message(
                    chat_id=u_id, 
                    from_chat_id=update.message.chat_id, 
                    message_id=update.message.message_id
                )
            success += 1
        except Exception:
            fail += 1
            
    await update.message.reply_text(f"📢 **ব্রডকাস্ট সম্পন্ন!**\n\n🟢 সফল: `{success}`\n🔴 ব্যর্থ: `{fail}`", parse_mode="Markdown")
    return ConversationHandler.END

# ==========================================
# CATEGORY MANAGEMENT
# ==========================================
async def admin_cats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    cats = db_query("SELECT id, name FROM categories", fetchall=True)
    text = "📁 **ক্যাটাগরি তালিকা:**\n\n"
    for cat_id, name in cats:
        text += f"ID: `{cat_id}` - Name: **{name}**\n"
        
    keyboard = [
        [InlineKeyboardButton("➕ Add Category", callback_data="cat_add"), InlineKeyboardButton("✏️ Edit Category", callback_data="cat_edit")],
        [InlineKeyboardButton("❌ Delete Category", callback_data="cat_del")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Category Add
async def cat_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📝 নতুন ক্যাটাগরির নাম দিন:")
    return STATE_ADD_CAT_NAME

async def cat_add_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    try:
        db_query("INSERT INTO categories (name) VALUES (?)", (name,), commit=True)
        await update.message.reply_text(f"✅ ক্যাটাগরি **'{name}'** সফলভাবে যুক্ত হয়েছে।", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("❌ এই নামের ক্যাটাগরি ইতিমধ্যে বিদ্যমান আছে।")
    return ConversationHandler.END

# Category Edit
async def cat_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✏️ যে ক্যাটাগরি এডিট করতে চান তার ID লিখুন:")
    return STATE_EDIT_CAT_ID

async def cat_edit_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat_id = update.message.text
    context.user_data["edit_cat_id"] = cat_id
    await update.message.reply_text("📝 ক্যাটাগরির নতুন নামটি টাইপ করে পাঠান:")
    return STATE_EDIT_CAT_NAME

async def cat_edit_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    cat_id = context.user_data.get("edit_cat_id")
    db_query("UPDATE categories SET name=? WHERE id=?", (name, cat_id), commit=True)
    await update.message.reply_text("✅ ক্যাটাগরির নাম সফলভাবে আপডেট করা হয়েছে।")
    return ConversationHandler.END

# Category Delete
async def cat_del_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("❌ যে ক্যাটাগরিটি ডিলিট করতে চান তার ID পাঠান:")
    return STATE_DEL_CAT_ID

async def cat_del_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat_id = update.message.text
    # Safely cascading products delete check
    prods = db_query("SELECT COUNT(*) FROM products WHERE category_id=?", (cat_id,), fetchone=True)[0]
    if prods > 0:
        await update.message.reply_text("❌ এই ক্যাটাগরি ডিলিট করা সম্ভব নয়। ক্যাটাগরি ডিলিট করার আগে এর মধ্যকার সমস্ত প্রোডাক্টগুলো ডিলিট করুন!")
        return ConversationHandler.END
        
    db_query("DELETE FROM categories WHERE id=?", (cat_id,), commit=True)
    await update.message.reply_text("✅ ক্যাটাগরিটি সফলভাবে ডিলিট করা হয়েছে।")
    return ConversationHandler.END

# ==========================================
# PRODUCT MANAGEMENT
# ==========================================
async def admin_prods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    prods = db_query("SELECT p.id, p.name, c.name, p.price FROM products p JOIN categories c ON p.category_id=c.id", fetchall=True)
    text = "📦 **প্রোডাক্ট তালিকা:**\n\n"
    for p_id, p_name, c_name, price in prods:
        text += f"ID: `{p_id}` | Name: **{p_name}** | Cat: {c_name} | Price: `{price} BDT`\n"
        
    keyboard = [
        [InlineKeyboardButton("➕ Add Product", callback_data="prod_add"), InlineKeyboardButton("✏️ Edit Product", callback_data="prod_edit")],
        [InlineKeyboardButton("❌ Delete Product", callback_data="prod_del")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Add Product Flow
async def prod_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📁 ক্যাটাগরি ID নির্বাচন করে পাঠান (প্রোডাক্টটি কোন ক্যাটাগরিতে থাকবে):")
    return STATE_ADD_PROD_CAT

async def prod_add_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat_id = update.message.text
    context.user_data["add_prod_cat"] = cat_id
    await update.message.reply_text("📝 প্রোডাক্টের নাম লিখুন:")
    return STATE_ADD_PROD_NAME

async def prod_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_prod_name"] = update.message.text
    await update.message.reply_text("📝 প্রোডাক্টের বিবরণ (Description) লিখুন:")
    return STATE_ADD_PROD_DESC

async def prod_add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_prod_desc"] = update.message.text
    await update.message.reply_text("💵 প্রোডাক্টের দাম (Price in BDT) সংখ্যায় লিখুন:")
    return STATE_ADD_PROD_PRICE

async def prod_add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text)
        context.user_data["add_prod_price"] = price
        await update.message.reply_text("🛡️ প্রোডাক্টের ওয়ারেন্টি সময়কাল লিখুন (যেমন: 24 Hours, No Warranty):")
        return STATE_ADD_PROD_WARRANTY
    except ValueError:
        await update.message.reply_text("❌ অবৈধ সংখ্যা। দয়া করে সঠিক দাম দিন:")
        return STATE_ADD_PROD_PRICE

async def prod_add_warranty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_prod_warranty"] = update.message.text
    await update.message.reply_text("🖼️ প্রোডাক্টের ছবি পাঠান (ঐচ্ছিক/Optional), না পাঠাতে চাইলে `/skip` টাইপ করুন:")
    return STATE_ADD_PROD_IMG

async def prod_add_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    img_id = None
    if update.message.photo:
        img_id = update.message.photo[-1].file_id
        
    cat_id = context.user_data.get("add_prod_cat")
    name = context.user_data.get("add_prod_name")
    desc = context.user_data.get("add_prod_desc")
    price = context.user_data.get("add_prod_price")
    warranty = context.user_data.get("add_prod_warranty")
    
    db_query(
        "INSERT INTO products (category_id, name, description, price, warranty, image_file_id) VALUES (?, ?, ?, ?, ?, ?)",
        (cat_id, name, desc, price, warranty, img_id),
        commit=True
    )
    
    await update.message.reply_text("✅ প্রোডাক্টটি সফলভাবে যুক্ত হয়েছে।")
    return ConversationHandler.END

async def prod_add_skip_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat_id = context.user_data.get("add_prod_cat")
    name = context.user_data.get("add_prod_name")
    desc = context.user_data.get("add_prod_desc")
    price = context.user_data.get("add_prod_price")
    warranty = context.user_data.get("add_prod_warranty")
    
    db_query(
        "INSERT INTO products (category_id, name, description, price, warranty, image_file_id) VALUES (?, ?, ?, ?, ?, NULL)",
        (cat_id, name, desc, price, warranty),
        commit=True
    )
    
    await update.message.reply_text("✅ প্রোডাক্টটি সফলভাবে যুক্ত হয়েছে (ছবি ছাড়া)।")
    return ConversationHandler.END

# Product Delete
async def prod_del_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("❌ যে প্রোডাক্টটি ডিলিট করতে চান তার ID পাঠান:")
    return STATE_DEL_PROD_ID

async def prod_del_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prod_id = update.message.text
    db_query("DELETE FROM products WHERE id=?", (prod_id,), commit=True)
    db_query("DELETE FROM stocks WHERE product_id=?", (prod_id,), commit=True) # delete related stocks
    await update.message.reply_text("✅ প্রোডাক্ট এবং তার সমস্ত স্টক ডিলিট করা হয়েছে।")
    return ConversationHandler.END

# Edit Product
async def prod_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✏️ যে প্রোডাক্টটি এডিট করবেন তার ID পাঠান:")
    return STATE_EDIT_PROD_ID

async def prod_edit_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["edit_prod_id"] = update.message.text
    await update.message.reply_text("কোন ফিল্ড পরিবর্তন করতে চান? (name, description, price, warranty) লিখুন:")
    return STATE_EDIT_PROD_FIELD

async def prod_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text.lower().strip()
    if field not in ["name", "description", "price", "warranty"]:
        await update.message.reply_text("❌ অবৈধ ফিল্ডের নাম। দয়া করে সঠিক ফিল্ড সিলেক্ট করুন:")
        return STATE_EDIT_PROD_FIELD
    context.user_data["edit_prod_field"] = field
    await update.message.reply_text(f"নতুন তথ্যটি লিখে পাঠান:")
    return STATE_EDIT_PROD_VAL

async def prod_edit_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    field = context.user_data.get("edit_prod_field")
    prod_id = context.user_data.get("edit_prod_id")
    
    if field == "price":
        try:
            val = float(val)
        except ValueError:
            await update.message.reply_text("❌ দাম শুধুমাত্র সংখ্যা হতে হবে! আবার সঠিক দাম দিন:")
            return STATE_EDIT_PROD_VAL
            
    db_query(f"UPDATE products SET {field}=? WHERE id=?", (val, prod_id), commit=True)
    await update.message.reply_text("✅ প্রোডাক্টটি সফলভাবে আপডেট করা হয়েছে।")
    return ConversationHandler.END

# ==========================================
# STOCK UPLOAD & IMPORT
# ==========================================
async def admin_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("⚡ যে প্রোডাক্ট আইডিতে স্টক যুক্ত করবেন সেই Product ID লিখে পাঠান:")
    return STATE_STOCK_PROD_ID

async def stock_prod_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stock_prod_id"] = update.message.text
    await update.message.reply_text(
        "📝 এবার প্রতিটি লাইনে একটি করে একাউন্ট ডেটা লিখে পাঠান (Bulk Import):\n\n"
        "যেমন:\n"
        "username:password\n"
        "example@mail.com:password123\n"
        "or write code/token here..."
    )
    return STATE_STOCK_TXT

async def stock_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prod_id = context.user_data.get("stock_prod_id")
    lines = update.message.text.split("\n")
    
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped:
            db_query("INSERT INTO stocks (product_id, data) VALUES (?, ?)", (prod_id, stripped), commit=True)
            count += 1
            
    await update.message.reply_text(f"✅ সফলভাবে `{count}` টি অ্যাকাউন্ট স্টক হিসেবে যুক্ত করা হয়েছে।", parse_mode="Markdown")
    return ConversationHandler.END

# ==========================================
# USER MANAGEMENT (ADMIN)
# ==========================================
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔍 Search User", callback_data="user_search"), InlineKeyboardButton("💵 Edit User Balance", callback_data="user_edit_bal")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
    ]
    await query.message.edit_text("👤 **ব্যবহারকারী পরিচালনা**", reply_markup=InlineKeyboardMarkup(keyboard))

# Search User
async def user_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔍 যে ইউজারের আইডি সার্চ করতে চান সেটি পাঠান:")
    return STATE_ADMIN_SEARCH_USER

async def user_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.message.text
    user = db_query("SELECT user_id, username, balance, is_banned FROM users WHERE user_id=?", (u_id,), fetchone=True)
    if not user:
        await update.message.reply_text("❌ এই ইউজার আইডিটি ডেটাবেসে পাওয়া যায়নি।")
        return ConversationHandler.END
        
    u_id, username, bal, is_banned = user
    ban_status = "BANNED" if is_banned == 1 else "ACTIVE"
    
    text = (
        f"👤 **ইউজার রেকর্ড:**\n\n"
        f"🆔 আইডি: `{u_id}`\n"
        f"👤 ইউজারনেম: @{username}\n"
        f"💰 ব্যালেন্স: `{bal:.2f} BDT`\n"
        f"🛡️ স্ট্যাটাস: `{ban_status}`"
    )
    
    keyboard = []
    if is_banned == 0:
        keyboard.append([InlineKeyboardButton("🚫 Ban User", callback_data=f"user_ban_{u_id}")])
    else:
        keyboard.append([InlineKeyboardButton("✅ Unban User", callback_data=f"user_unban_{u_id}")])
    keyboard.append([InlineKeyboardButton("❌ Delete User Records", callback_data=f"user_delrec_{u_id}")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END

async def handle_user_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[1]
    target_id = int(data[2])
    
    if action == "ban":
        db_query("UPDATE users SET is_banned=1 WHERE user_id=?", (target_id,), commit=True)
        await query.message.reply_text(f"🚫 ইউজার `{target_id}` কে সফলভাবে ব্যান করা হয়েছে।")
    elif action == "unban":
        db_query("UPDATE users SET is_banned=0 WHERE user_id=?", (target_id,), commit=True)
        await query.message.reply_text(f"✅ ইউজার `{target_id}` কে সফলভাবে আনব্যান করা হয়েছে।")
    elif action == "delrec":
        db_query("DELETE FROM users WHERE user_id=?", (target_id,), commit=True)
        db_query("DELETE FROM purchases WHERE user_id=?", (target_id,), commit=True)
        await query.message.reply_text(f"🗑️ ইউজার `{target_id}` এর সব ডাটা সম্পূর্ণ ডিলেট করা হয়েছে।")

# Edit Balance
async def edit_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("💵 যে ইউজারের ব্যালেন্স পরিবর্তন করবেন তার ID পাঠান:")
    return STATE_ADMIN_EDIT_BAL_ID

async def edit_balance_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["edit_bal_uid"] = update.message.text
    await update.message.reply_text("💰 কত ব্যালেন্স সেট করবেন তা টাইপ করুন (যেমন: 500.00):")
    return STATE_ADMIN_EDIT_BAL_AMT

async def edit_balance_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        u_id = context.user_data.get("edit_bal_uid")
        
        db_query("UPDATE users SET balance=? WHERE user_id=?", (amount, u_id), commit=True)
        await update.message.reply_text(f"✅ ইউজার `{u_id}` এর ব্যালেন্স আপডেট করে `{amount} BDT` করা হয়েছে।", parse_mode="Markdown")
        
        # Notify user
        try:
            await context.bot.send_message(chat_id=u_id, text=f"💰 অ্যাডমিন আপনার ব্যালেন্স পরিবর্তন করে `{amount} BDT` সেট করেছেন।")
        except Exception:
            pass
            
    except ValueError:
        await update.message.reply_text("❌ অবৈধ ব্যালেন্স এমাউন্ট।")
    return ConversationHandler.END

# ==========================================
# SETTINGS PANEL (ADMIN)
# ==========================================
async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    m_mode = "ENABLED" if get_setting("maintenance_mode") == "1" else "DISABLED"
    fj = get_setting("force_join_channel") or "Not Set"
    pn = get_setting("payment_number")
    sup = get_setting("support_username")
    com = get_setting("community_link")
    
    text = (
        f"⚙️ **বট সেটিংস কনফিগারেশন**\n\n"
        f"🚧 রক্ষণাবেক্ষণ মোড: `{m_mode}`\n"
        f"📢 ফোর্স জয়েন চ্যানেল: `{fj}`\n"
        f"📞 পেমেন্ট নাম্বার: `{pn}`\n"
        f"💬 সাপোর্ট ইউজারনেম: @{sup}\n"
        f"👥 কমিউনিটি লিংক: {com}"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚧 Toggle Maintenance", callback_data="set_toggle_m")],
        [InlineKeyboardButton("📢 Force Join Channel", callback_data="set_fj"), InlineKeyboardButton("📞 Payment Number", callback_data="set_pn")],
        [InlineKeyboardButton("💬 Support Username", callback_data="set_sup"), InlineKeyboardButton("👥 Community Link", callback_data="set_com")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_settings_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "set_toggle_m":
        curr = get_setting("maintenance_mode")
        nxt = "1" if curr == "0" else "0"
        set_setting("maintenance_mode", nxt)
        await query.message.reply_text(f"✅ রক্ষণাবেক্ষণ মোড পরিবর্তন করা হয়েছে।")
        return ConversationHandler.END
    elif data == "set_fj":
        await query.message.reply_text("📢 ফোর্স জয়েন চ্যানেলের ইউজারনেম পাঠান (যেমন: @YourChannel):")
        return STATE_ADMIN_SET_FORCE_JOIN
    elif data == "set_pn":
        await query.message.reply_text("📞 নতুন পেমেন্ট নাম্বার পাঠান (যেমন: 017XXXXXXXX):")
        return STATE_ADMIN_SET_PAYMENT_NO
    elif data == "set_sup":
        await query.message.reply_text("💬 সাপোর্ট টিমের ইউজারনেম পাঠান (ইউজারনেম ছাড়া):")
        return STATE_ADMIN_SET_SUPPORT
    elif data == "set_com":
        await query.message.reply_text("👥 আপনার টেলিগ্রাম কমিউনিটি গ্রুপের পুরো লিংক পাঠান:")
        return STATE_ADMIN_SET_COMMUNITY

# Settings Reciever Handlers
async def set_fj_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    set_setting("force_join_channel", val)
    await update.message.reply_text("✅ ফোর্স জয়েন চ্যানেল আপডেট করা হয়েছে।")
    return ConversationHandler.END

async def set_pn_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    set_setting("payment_number", val)
    await update.message.reply_text("✅ পেমেন্ট নাম্বার আপডেট করা হয়েছে।")
    return ConversationHandler.END

async def set_sup_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    set_setting("support_username", val)
    await update.message.reply_text("✅ সাপোর্ট ইউজারনেম আপডেট করা হয়েছে।")
    return ConversationHandler.END

async def set_com_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    set_setting("community_link", val)
    await update.message.reply_text("✅ কমিউনিটি লিংক আপডেট করা হয়েছে।")
    return ConversationHandler.END

# ==========================================
# ADMIN DEPOSIT / REPLACE ACTION CALLBACKS
# ==========================================
async def handle_deposit_verdict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    action = data[1] # app / rej
    p_id = int(data[2])
    
    payment = db_query("SELECT user_id, amount, status FROM payments WHERE id=?", (p_id,), fetchone=True)
    if not payment or payment[2] != "PENDING":
        await query.message.reply_text("⚠️ এই ট্রানজেকশনটি ইতিমধ্যেই প্রসেস বা নিষ্পত্তি হয়ে গেছে!")
        return
        
    u_id, amount, status = payment
    
    if action == "app":
        # Request Amount from admin
        context.user_data["dep_app_p_id"] = p_id
        context.user_data["dep_app_u_id"] = u_id
        await query.message.reply_text("💵 অ্যাড করার জন্য ব্যালেন্সের পরিমাণ সংখ্যায় লিখুন (যেমন: 150):")
        return STATE_ADMIN_EDIT_BAL_AMT
        
    elif action == "rej":
        db_query("UPDATE payments SET status='REJECTED' WHERE id=?", (p_id,), commit=True)
        await query.message.reply_text("❌ ডিপোজিটটি রিজেক্ট করা হয়েছে।")
        try:
            await context.bot.send_message(chat_id=u_id, text="❌ দুঃখিত, আপনার ডিপোজিট রিকোয়েস্টটি রিজেক্ট করা হয়েছে। পেমেন্ট বিবরণ ঠিক ছিল না।")
        except Exception:
            pass

async def handle_deposit_approve_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        p_id = context.user_data.get("dep_app_p_id")
        u_id = context.user_data.get("dep_app_u_id")
        
        # update payment status and user wallet balance
        db_query("UPDATE payments SET amount=?, status='APPROVED' WHERE id=?", (amount, p_id), commit=True)
        
        curr_bal = db_query("SELECT balance FROM users WHERE user_id=?", (u_id,), fetchone=True)[0]
        db_query("UPDATE users SET balance=? WHERE user_id=?", (curr_bal + amount, u_id), commit=True)
        
        await update.message.reply_text(f"✅ পেমেন্ট রিকোয়েস্ট সফলভাবে ভেরিফাই ও ইউজার `{u_id}` অ্যাকাউন্টে `{amount} BDT` অ্যাড করা হয়েছে।", parse_mode="Markdown")
        
        # Notification to User
        try:
            await context.bot.send_message(
                chat_id=u_id, 
                text=f"🎉 **ডিপোজিট সফল!**\n\nআপনার অ্যাকাউন্টে `{amount} BDT` যোগ করা হয়েছে। প্রধান মেন্যু থেকে প্রোফাইল চেক করুন।"
            )
        except Exception:
            pass
            
    except ValueError:
        await update.message.reply_text("❌ অংকটি সঠিক নয়। অনুগ্রহ করে পুনরায় সঠিক অংকটি সংখ্যায় দিন:")
        return STATE_ADMIN_EDIT_BAL_AMT
    return ConversationHandler.END

# Replace Action Approvals
async def handle_replace_verdict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    action = data[1] # app / rej
    r_id = int(data[2])
    
    replace_req = db_query("SELECT purchase_id, user_id, status FROM replace_requests WHERE id=?", (r_id,), fetchone=True)
    if not replace_req or replace_req[2] != "PENDING":
        await query.message.reply_text("⚠️ এই রিকোয়েস্টটি ইতিমধ্যে সমাধান করা হয়েছে!")
        return
        
    p_id, u_id, status = replace_req
    
    if action == "app":
        # Find product ID from original purchase
        prod_id = db_query("SELECT product_id FROM purchases WHERE id=?", (p_id,), fetchone=True)[0]
        
        # Get new available stock item
        new_stock = db_query("SELECT id, data FROM stocks WHERE product_id=? AND is_sold=0 LIMIT 1", (prod_id,), fetchone=True)
        if not new_stock:
            await query.message.reply_text("❌ স্টকে কোনো রিপ্লেসমেন্ট অ্যাকাউন্ট নেই! আগে স্টক আপলোড করুন।")
            return
            
        new_stock_id, new_data = new_stock
        
        # Complete substitution logic
        db_query("UPDATE replace_requests SET status='APPROVED' WHERE id=?", (r_id,), commit=True)
        db_query(
            "UPDATE stocks SET is_sold=1, sold_to=?, sold_at=? WHERE id=?", 
            (u_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), new_stock_id), 
            commit=True
        )
        db_query("UPDATE purchases SET stock_id=?, delivered_data=? WHERE id=?", (new_stock_id, new_data, p_id), commit=True)
        
        await query.message.reply_text("✅ রিপ্লেসমেন্ট রিকোয়েস্ট মঞ্জুর করা হয়েছে এবং নতুন অ্যাকাউন্টটি পাঠানো হয়েছে।")
        
        # Send new account delivery info to user
        user_msg = (
            f"🔄 **রিপ্লেসমেন্ট অনুমোদন করা হয়েছে!**\n\n"
            f"অর্ডার আইডি: #{p_id} এর জন্য নতুন অ্যাকাউন্ট ডেটা নিচে দেওয়া হলো:\n\n"
            f"`{new_data}`"
        )
        try:
            await context.bot.send_message(chat_id=u_id, text=user_msg, parse_mode="Markdown")
        except Exception:
            pass
            
    elif action == "rej":
        db_query("UPDATE replace_requests SET status='REJECTED' WHERE id=?", (r_id,), commit=True)
        await query.message.reply_text("❌ রিপ্লেসমেন্ট রিকোয়েস্ট প্রত্যাখ্যান করা হয়েছে।")
        try:
            await context.bot.send_message(chat_id=u_id, text=f"❌ অর্ডার #{p_id} এর জন্য আপনার সাবমিটকৃত রিপ্লেস রিকোয়েস্টটি অ্যাডমিন রিজেক্ট করেছেন।")
        except Exception:
            pass

# Cancel Handler for States
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ চলমান প্রক্রিয়া বাতিল করা হয়েছে।")
    return ConversationHandler.END

# ==========================================
# MAIN APPLICATION BUILDER
# ==========================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation Handlers Setup
    conv_handler = ConversationHandler(
        entry_points=[
            # User Trigger Channels
            CallbackQueryHandler(deposit_menu, pattern="^deposit_menu$"),
            CallbackQueryHandler(init_replace_request, pattern="^req_rep_\\d+$"),
            # Admin Settings & Panels Setup
            CallbackQueryHandler(start_broadcast, pattern="^admin_broadcast$"),
            CallbackQueryHandler(user_search_start, pattern="^user_search$"),
            CallbackQueryHandler(edit_balance_start, pattern="^user_edit_bal$"),
            CallbackQueryHandler(cat_add_start, pattern="^cat_add$"),
            CallbackQueryHandler(cat_edit_start, pattern="^cat_edit$"),
            CallbackQueryHandler(cat_del_start, pattern="^cat_del$"),
            CallbackQueryHandler(prod_add_start, pattern="^prod_add$"),
            CallbackQueryHandler(prod_del_start, pattern="^prod_del$"),
            CallbackQueryHandler(prod_edit_start, pattern="^prod_edit$"),
            CallbackQueryHandler(admin_stocks, pattern="^admin_stocks$"),
            CallbackQueryHandler(handle_settings_callbacks, pattern="^set_"),
            CallbackQueryHandler(handle_deposit_verdict, pattern="^dep_"),
        ],
        states={
            # User States
            STATE_DEPOSIT_PROOF: [MessageHandler(filters.PHOTO, handle_deposit_proof)],
            STATE_REPLACE_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_replace_reason)],
            
            # Admin States
            STATE_ADMIN_BROADCAST: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_broadcast)],
            STATE_ADMIN_SEARCH_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_search_result)],
            STATE_ADMIN_EDIT_BAL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_balance_id_received)],
            STATE_ADMIN_EDIT_BAL_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_balance_save)],
            
            # Category Config States
            STATE_ADD_CAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, cat_add_save)],
            STATE_EDIT_CAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, cat_edit_id_received)],
            STATE_EDIT_CAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, cat_edit_save)],
            STATE_DEL_CAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, cat_del_save)],
            
            # Product States
            STATE_ADD_PROD_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_add_cat)],
            STATE_ADD_PROD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_add_name)],
            STATE_ADD_PROD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_add_desc)],
            STATE_ADD_PROD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_add_price)],
            STATE_ADD_PROD_WARRANTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_add_warranty)],
            STATE_ADD_PROD_IMG: [
                MessageHandler(filters.PHOTO, prod_add_img),
                CommandHandler("skip", prod_add_skip_img),
            ],
            STATE_DEL_PROD_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_del_save)],
            STATE_EDIT_PROD_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_edit_id)],
            STATE_EDIT_PROD_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_edit_field)],
            STATE_EDIT_PROD_VAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_edit_save)],
            
            # Stock States
            STATE_STOCK_PROD_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, stock_prod_id_received)],
            STATE_STOCK_TXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, stock_save)],
            
            # Dynamic Settings States
            STATE_ADMIN_SET_FORCE_JOIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_fj_save)],
            STATE_ADMIN_SET_PAYMENT_NO: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_pn_save)],
            STATE_ADMIN_SET_SUPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_sup_save)],
            STATE_ADMIN_SET_COMMUNITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_com_save)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Basic Setup Command Register
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    
    # Callback Handlers (outside state engine)
    app.add_handler(CallbackQueryHandler(start, pattern="^go_home$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^btn_start_check$"))
    app.add_handler(CallbackQueryHandler(user_profile, pattern="^user_profile$"))
    app.add_handler(CallbackQueryHandler(my_orders, pattern="^my_orders$"))
    app.add_handler(CallbackQueryHandler(buy_menu, pattern="^buy_menu$"))
    app.add_handler(CallbackQueryHandler(view_category, pattern="^cat_view_\\d+$"))
    app.add_handler(CallbackQueryHandler(view_product, pattern="^prod_view_\\d+$"))
    app.add_handler(CallbackQueryHandler(buy_product, pattern="^prod_buy_\\d+$"))
    app.add_handler(CallbackQueryHandler(support_info, pattern="^support_info$"))
    app.add_handler(CallbackQueryHandler(community_info, pattern="^community_info$"))
    
    # Action callbacks
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin_cats, pattern="^admin_cats$"))
    app.add_handler(CallbackQueryHandler(admin_prods, pattern="^admin_prods$"))
    app.add_handler(CallbackQueryHandler(admin_users, pattern="^admin_users$"))
    app.add_handler(CallbackQueryHandler(admin_settings, pattern="^admin_settings$"))
    app.add_handler(CallbackQueryHandler(handle_user_actions, pattern="^user_(ban|unban|delrec)_\\d+$"))
    app.add_handler(CallbackQueryHandler(handle_replace_verdict, pattern="^rep_"))

    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
