import logging
import sqlite3
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, TypeHandler
from telegram.request import HTTPXRequest

import database, fanzha, finance, calc

BOT_TOKEN = '8338681840:AAF0p3dyfVK7Msv5TqQnWm-u2-a7oM-Nhc0'
SUPER_ADMIN_ID = 6863213861 

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

def check_auth(user_id):
    if user_id == SUPER_ADMIN_ID: return True
    with sqlite3.connect(database.FINANCE_DB) as conn:
        row = conn.execute("SELECT is_authorized FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row and row[0] == 1

async def global_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # A. 处理撤回消息
    bus_del = getattr(update, 'deleted_business_messages', None)
    if bus_del:
        chat_id, chat_name = bus_del.chat.id, (bus_del.chat.first_name or "客户")
        for mid in bus_del.message_ids:
            with sqlite3.connect(database.CACHE_DB) as conn:
                row = conn.execute("SELECT text, time FROM cache WHERE msg_id = ?", (mid,)).fetchone()
            if row:
                # 后台
                await context.bot.send_message(chat_id=SUPER_ADMIN_ID, text=f"🗑️ **撤回审计**\n👤 窗口: [{chat_name}](tg://user?id={chat_id})\n📄 内容: `{row[0]}`", parse_mode='Markdown')
                # 窗口
                try: await context.bot.send_message(chat_id=chat_id, text=f"📝 提示：消息撤回\n撤回消息：\n{row[0]}")
                except: pass
        return

    # B. 处理消息（含反诈触发）
    msg = update.business_message or update.message or update.edited_business_message
    if msg and msg.text:
        text, chat_id, user_id = msg.text.strip(), msg.chat.id, msg.from_user.id
        name, conn_id = (msg.chat.first_name or "未知"), getattr(msg, 'business_connection_id', None)

        # 缓存
        with sqlite3.connect(database.CACHE_DB) as conn:
            conn.execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?, ?, ?, ?)", (msg.message_id, chat_id, name, user_id, text, now_str))

        # --- 无论谁发的，只要是新用户就查反诈 ---
        # 排除管理员自己发的消息去查自己
        target_id = user_id # 获取消息发送者的ID
        asyncio.create_task(fanzha.check_fanzha_logic(target_id, name, chat_id, context, SUPER_ADMIN_ID, conn_id))

        if not check_auth(user_id): return

        # 分发功能
        if await finance.handle_finance(text, chat_id, user_id, conn_id, context, now_str): return
        if await calc.handle_calc(text, chat_id, conn_id, context): return

if __name__ == '__main__':
    database.init_all_db()
    t_req = HTTPXRequest(connection_pool_size=50, read_timeout=30, connect_timeout=30)
    app = ApplicationBuilder().token(BOT_TOKEN).request(t_req).build()
    app.add_handler(TypeHandler(Update, global_monitor))
    print("🚀 机器人启动 ")
    app.run_polling(drop_pending_updates=True)