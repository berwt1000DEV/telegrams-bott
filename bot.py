import logging
import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Loglama
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YASAKLI_KELIMELER = ["küfür1", "küfür2", "dolandırıcı", "hacklink"]

# --- RENDER'IN İSTEDİĞİ MİNİ WEB SUNUCUSU ---
app_web = Flask(__name__)


@app_web.route("/")
def home():
  return "Bot aktif ve çalışıyor!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app_web.run(host="0.0.0.0", port=port)

# ---------------------------------------------


async def yaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return

  message_text = " ".join(context.args)
  if not message_text:
    await update.message.reply_text("Lütfen gönderilecek metni yazın: /yaz <metin>")
    return

  try:
    await context.bot.send_message(chat_id=CHANNEL_ID, text=message_text)
    await update.message.reply_text("✅ Mesaj kanala gönderildi.")
  except Exception as e:
    await update.message.reply_text(f"❌ Hata: {e}")


async def kanal_guvenlik_filtresi(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  if not update.effective_message or not update.effective_chat:
    return
  if str(update.effective_chat.id) != str(CHANNEL_ID):
    return

  message = update.effective_message
  user = update.effective_user
  text = (message.text or message.caption or "").lower()

  try:
    chat_member = await context.bot.get_chat_member(
        chat_id=CHANNEL_ID, user_id=user.id
    )
    if chat_member.status in ["administrator", "creator"]:
      return
  except Exception:
    pass

  for yasakli in YASAKLI_KELIMELER:
    if yasakli in text:
      try:
        await message.delete()
        return
      except Exception as e:
        print(f"Silme hatası: {e}")


def main():
  if not TOKEN:
    print("HATA: BOT_TOKEN bulunamadı!")
    return

  t = threading.Thread(target=run_web)
  t.start()

  app = ApplicationBuilder().token(TOKEN).build()
  app.add_handler(CommandHandler("yaz", yaz))
  app.add_handler(
      MessageHandler(
          filters.TEXT & ~filters.COMMAND, kanal_guvenlik_filtresi
      )
  )

  print("Bot başlatılıyor...")
  app.run_polling()


if __name__ == "__main__":
  main()
