import aiohttp
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def check_fanzha_logic(user_id, chat_name, chat_id, context, admin_id, conn_id):
    import database
    if database.is_fanzha_checked(user_id):
        return
    
    url = f"https://qingfeng.qzz.io/api/fanzha?text={user_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                raw_text = await resp.text()
        
        database.mark_fanzha_checked(user_id)

        if "⚠️本用户为诈骗犯⚠️" in raw_text:
            count_match = re.search(r"有 (\d+) 条反诈记录", raw_text)
            count_str = count_match.group(1) if count_match else "多"
            
            # 提取时间和链接
            matches = re.findall(r"时间：(.*?)\n链接：(https://t\.me/\S+)", raw_text)
            
            # 1. 窗口端提醒
            client_msg = f"⚠️ **提示：检测到该用户可能存在风险。**"
            try: await context.bot.send_message(chat_id=chat_id, text=client_msg, business_connection_id=conn_id)
            except: pass
            
            # 2. 后台管理提醒
            buttons = [[InlineKeyboardButton(text=f"🕒 {m[0]}", url=m[1])] for m in matches]
            admin_warn = (
                f"🚨 **反诈预警！**\n"
                f"你当前可能正在与诈骗犯交谈\n"
                f"窗口: [{chat_name}](tg://user?id={chat_id})\n"
                f"该用户有 {count_str} 条反诈记录"
            )
            await context.bot.send_message(
                chat_id=admin_id, 
                text=admin_warn, 
                parse_mode='Markdown', 
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    except:
        pass