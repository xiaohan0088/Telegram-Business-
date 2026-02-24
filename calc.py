import re

async def handle_calc(text, chat_id, conn_id, context):
    if any(s in text for s in ['+', '-', '*', '/', 'x', '÷']) and re.match(r'^[0-9+\-*/().x÷\s]{3,}$', text):
        try:
            res = eval(text.replace('x', '*').replace('÷', '/'), {"__builtins__": None}, {})
            await context.bot.send_message(chat_id=chat_id, text=f"🔢 {text} = `{res}`", parse_mode='Markdown', business_connection_id=conn_id)
            return True
        except: pass
    return False