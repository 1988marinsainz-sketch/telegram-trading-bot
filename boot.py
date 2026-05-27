import os
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# DATOS BINANCE
# =========================

def get_klines(symbol="BTCUSDT", interval="1h", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        'time','open','high','low','close','volume',
        'close_time','qav','num_trades',
        'taker_base_vol','taker_quote_vol','ignore'
    ])

    df['close'] = df['close'].astype(float)

    return df

# =========================
# ANALISIS
# =========================

def analyze(symbol="BTCUSDT"):
    df = get_klines(symbol)

    rsi = RSIIndicator(df['close']).rsi().iloc[-1]

    macd = MACD(df['close'])

    macd_value = macd.macd().iloc[-1]
    signal_value = macd.macd_signal().iloc[-1]

    price = df['close'].iloc[-1]

    signal = "NEUTRAL"

    if rsi < 30 and macd_value > signal_value:
        signal = "COMPRA"

    elif rsi > 70 and macd_value < signal_value:
        signal = "VENTA"

    return {
        "price": round(price, 2),
        "rsi": round(rsi, 2),
        "signal": signal
    }

# =========================
# COMANDOS TELEGRAM
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Bot de Trading Activo\n\nComandos:\n/btc\n/eth\n/sol"
    )

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = analyze("BTCUSDT")

    msg = f"""
BTC/USDT

Precio: {data['price']}
RSI: {data['rsi']}
Señal: {data['signal']}
"""

    await update.message.reply_text(msg)

async def eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = analyze("ETHUSDT")

    msg = f"""
ETH/USDT

Precio: {data['price']}
RSI: {data['rsi']}
Señal: {data['signal']}
"""

    await update.message.reply_text(msg)

async def sol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = analyze("SOLUSDT")

    msg = f"""
SOL/USDT

Precio: {data['price']}
RSI: {data['rsi']}
Señal: {data['signal']}
"""

    await update.message.reply_text(msg)

# =========================
# ALERTAS AUTOMATICAS
# =========================

async def send_signal(app):
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    for symbol in symbols:
        data = analyze(symbol)

        if data['signal'] != "NEUTRAL":

            msg = f"""
🚨 ALERTA {symbol}

Precio: {data['price']}
RSI: {data['rsi']}
Señal: {data['signal']}

⚠️ Esto no es asesoramiento financiero.
"""

            await app.bot.send_message(
                chat_id=CHAT_ID,
                text=msg
            )

# =========================
# LOOP ALERTAS
# =========================

async def periodic_signals(app):

    while True:

        try:
            await send_signal(app)

        except Exception as e:
            print(e)

        await asyncio.sleep(3600)

# =========================
# MAIN
# =========================

async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("eth", eth))
    app.add_handler(CommandHandler("sol", sol))

    asyncio.create_task(periodic_signals(app))

    print("Bot funcionando...")

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
