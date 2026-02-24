import sqlite3
import re
import database

async def handle_finance(text, chat_id, user_id, conn_id, context, now_str):
    u_text = text.upper()
    
    with sqlite3.connect(database.FINANCE_DB) as conn:
        row = conn.execute("SELECT currency, balance FROM customer_settings WHERE chat_id=?", (chat_id,)).fetchone()
        curr, bal = row if row else ('$', 0.0)

    # 1. 记账: +100 / -50
    if re.match(r'^[+-]\d+(\.\d+)?$', text):
        val = float(text[1:])
        op = "入金" if text.startswith('+') else "出金"
        new_bal = bal + (val if text.startswith('+') else -val)
        with sqlite3.connect(database.FINANCE_DB) as conn:
            conn.execute("INSERT INTO records (chat_id, type, amount, currency, time) VALUES (?, ?, ?, ?, ?)", (chat_id, op, val, curr, now_str))
            conn.execute("INSERT OR REPLACE INTO customer_settings (chat_id, currency, balance) VALUES (?, ?, ?)", (chat_id, curr, new_bal))
        await context.bot.send_message(chat_id=chat_id, text=f"✅ {op} {val} {curr}\n💰 余额: {new_bal:.2f}", business_connection_id=conn_id)
        return True

    # 2. 查询: / (余额)
    if text == '/':
        await context.bot.send_message(chat_id=chat_id, text=f"💰 当前余额: `{bal:.2f} {curr}`", parse_mode='Markdown', business_connection_id=conn_id)
        return True

    # 3. 流水: ..
    if text == '..':
        with sqlite3.connect(database.FINANCE_DB) as conn:
            rows = conn.execute("SELECT type, amount, time FROM records WHERE chat_id=? ORDER BY id DESC LIMIT 10", (chat_id,)).fetchall()
        txt = "📊 **最近流水:**\n" + "\n".join([f"• `{r[2][5:16]}` | {r[0]} {r[1]}" for r in rows]) if rows else "📜 暂无记录"
        await context.bot.send_message(chat_id=chat_id, text=txt, parse_mode='Markdown', business_connection_id=conn_id)
        return True

    # 4. 清账: //
    if text == '//':
        with sqlite3.connect(database.FINANCE_DB) as conn:
            conn.execute("UPDATE customer_settings SET balance=0 WHERE chat_id=?", (chat_id,))
            conn.execute("DELETE FROM records WHERE chat_id=?", (chat_id,))
        await context.bot.send_message(chat_id=chat_id, text="🧹 **账目已清空**", business_connection_id=conn_id)
        return True

    # 5. 切换币种
    if u_text in ['/U', '/R']:
        new_curr = '$' if u_text == '/U' else '¥'
        with sqlite3.connect(database.FINANCE_DB) as conn:
            conn.execute("INSERT OR REPLACE INTO customer_settings (chat_id, currency, balance) VALUES (?, ?, ?)", (chat_id, new_curr, bal))
        await context.bot.send_message(chat_id=chat_id, text=f"💱 币种已切换为: {new_curr}", business_connection_id=conn_id)
        return True

    return False