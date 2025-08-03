import json
import random
import string
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN = "8454274411:AAHWKVlmxku60aTnkOFafjMYh9jLrJSgVEg"
ADMIN_ID = 7288118092
USERS_FILE = "users.json"
CHANNELS_FILE = "channels.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def load_channels():
    try:
        with open(CHANNELS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

def generate_uid():
    return "uid" + ''.join(random.choices(string.digits, k=9))

async def check_user_membership(bot: Bot, user_id: int) -> bool:
    channels = load_channels()
    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

async def send_join_channels_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = load_channels()
    buttons = []
    for ch in channels:
        if ch.startswith("@"):
            link = f"https://t.me/{ch[1:]}"
            buttons.append([InlineKeyboardButton(ch, url=link)])
        else:
            buttons.append([InlineKeyboardButton(str(ch), url=f"https://t.me/{ch}")])
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        "برای ادامه لطفاً عضو کانال‌های زیر شوید:",
        reply_markup=keyboard
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    allowed = await check_user_membership(context.bot, update.effective_user.id)
    if not allowed:
        await send_join_channels_message(update, context)
        return
    user = update.effective_user
    users = load_users()
    uid = None
    for k,v in users.items():
        if str(user.id) == k:
            uid = v["uid"]
            break
    if not uid:
        uid = generate_uid()
        users[str(user.id)] = {
            "username": f"@{user.username}" if user.username else "",
            "uid": uid
        }
        save_users(users)
    link = f"https://t.me/{context.bot.username}?start={uid}"
    await update.message.reply_text(
        f"سلام {user.first_name}!\n"
        f"این لینک شخصی شماست:\n{link}\n\n"
        f"وقتی این لینک رو به کسی بدی، می‌تونه به صورت ناشناس برات پیام بفرسته."
    )

async def start_with_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    allowed = await check_user_membership(context.bot, update.effective_user.id)
    if not allowed:
        await send_join_channels_message(update, context)
        return
    if not args:
        await start(update, context)
        return
    target_uid = args[0]
    context.user_data["chat_with_uid"] = target_uid
    await update.message.reply_text(
        f"شما الان به کاربری که uid‌ش {target_uid} هست پیام می‌فرستی. پیام‌هات ناشناس خواهد بود."
    )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    allowed = await check_user_membership(context.bot, update.effective_user.id)
    if not allowed:
        await send_join_channels_message(update, context)
        return
    sender = update.effective_user
    users = load_users()
    if "chat_with_uid" not in context.user_data:
        await update.message.reply_text(
            "ابتدا باید با لینک /start یا دستور /start <uid> وارد چت ناشناس بشی."
        )
        return
    target_uid = context.user_data["chat_with_uid"]
    target_id = None
    for uid, data in users.items():
        if data["uid"] == target_uid:
            target_id = int(uid)
            break
    if not target_id:
        await update.message.reply_text("کاربر مقصد پیدا نشد یا آیدی اشتباه است.")
        return
    try:
        await context.bot.send_message(chat_id=target_id, text=update.message.text)
    except:
        await update.message.reply_text("ارسال پیام به کاربر مقصد با مشکل مواجه شد.")
        return
    admin_msg = (
        f"🔎 پیام ناشناس جدید:\n"
        f"👤 فرستنده: {sender.id} (@{sender.username})\n"
        f"🎯 گیرنده: {target_id}\n"
        f"📝 پیام: {update.message.text}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)

async def msg_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    allowed = await check_user_membership(context.bot, sender.id)
    if not allowed:
        await send_join_channels_message(update, context)
        return
    args = context.args
    users = load_users()
    if not args or len(args) < 2:
        await update.message.reply_text("فرمت درست: /msg <uid|id|@username> پیام شما")
        return
    target = args[0]
    text = " ".join(args[1:])
    target_id = None
    if target.isdigit():
        target_id = int(target)
    else:
        for uid, data in users.items():
            if data["uid"] == target or data.get("username") == target:
                target_id = int(uid)
                break
    if not target_id:
        await update.message.reply_text("کاربر مقصد پیدا نشد.")
        return
    try:
        await context.bot.send_message(chat_id=target_id, text=text)
    except:
        await update.message.reply_text("ارسال پیام به کاربر مقصد با مشکل مواجه شد.")
        return
    admin_msg = (
        f"🔎 پیام ناشناس جدید:\n"
        f"👤 فرستنده: {sender.id} (@{sender.username})\n"
        f"🎯 گیرنده: {target_id}\n"
        f"📝 پیام: {text}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
    args = context.args
    if not args:
        await update.message.reply_text("آیدی یا یوزرنیم کانال را وارد کنید.")
        return
    channel = args[0]
    channels = load_channels()
    if channel in channels:
        await update.message.reply_text("این کانال قبلا اضافه شده.")
        return
    channels.append(channel)
    save_channels(channels)
    await update.message.reply_text(f"کانال {channel} اضافه شد.")

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
    args = context.args
    if not args:
        await update.message.reply_text("آیدی یا یوزرنیم کانال را وارد کنید.")
        return
    channel = args[0]
    channels = load_channels()
    if channel not in channels:
        await update.message.reply_text("این کانال در لیست نیست.")
        return
    channels.remove(channel)
    save_channels(channels)
    await update.message.reply_text(f"کانال {channel} حذف شد.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_with_uid))
    app.add_handler(CommandHandler("msg", msg_command))
    app.add_handler(CommandHandler("addchannel", add_channel))
    app.add_handler(CommandHandler("removechannel", remove_channel))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))
    app.run_polling()
