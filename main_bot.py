# main_bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import os
from config import MAIN_BOT_TOKEN
from shared_database import SharedDatabase

db = SharedDatabase()

# Modern ve Zarif Arayüz Tasarımı
async def start(update: Update, context: CallbackContext):
    stats = db.get_stats()
    
    welcome_text = f"""
📚 **Digital Kütüphaneye Hoş Geldiniz** 🌟

*"Binlerce kitap, tek tık uzağınızda"*

📊 **Kütüphane İstatistikleri:**
• 📖 {stats['total_books']}+ Kitap
• 📂 {stats['total_categories']}+ Kategori
• 🆕 Anlık Güncelleme

✨ **Özellikler:**
• 📖 Online PDF Okuyucu
• 💾 Hızlı İndirme
• 🔍 Akıllı Arama
• ⭐ Kişisel Koleksiyon
• 📱 Mobil Uyumlu

🎯 **Hemen keşfetmeye başlayın:**
    """
    
    keyboard = [
        [InlineKeyboardButton("🔍 Kitap Ara", callback_data="search_books"),
         InlineKeyboardButton("📚 Kategoriler", callback_data="show_categories")],
        [InlineKeyboardButton("⭐ Popüler Kitaplar", callback_data="popular_books"),
         InlineKeyboardButton("🆕 Yeni Eklenenler", callback_data="new_books")],
        [InlineKeyboardButton("ℹ️ Yardım", callback_data="show_help"),
         InlineKeyboardButton("🌟 Premium", callback_data="premium_info")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

# Anlık Kitap Listesi - Admin'den gelen kitaplar
async def show_new_books(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    books = db.get_active_books(limit=10)
    
    if not books:
        await query.edit_message_text(
            "📭 **Henüz kitap bulunmuyor**\n\n"
            "Kütüphane şu anda boş. Lütfen daha sonra tekrar kontrol edin.",
            parse_mode='Markdown'
        )
        return
    
    books_text = "🆕 **Son Eklenen Kitaplar**\n\n"
    keyboard = []
    
    for book in books:
        book_id, title, author, category = book[0], book[1], book[2], book[4]
        books_text += f"📚 **{title}**\n✍️ {author}\n📂 {category}\n\n"
        
        keyboard.append([InlineKeyboardButton(
            f"📖 {title[:20]}...", 
            callback_data=f"view_book_{book_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(books_text, reply_markup=reply_markup, parse_mode='Markdown')

def main():
    """Ana kütüphane botunu başlat"""
    application = Application.builder().token(MAIN_BOT_TOKEN).build()
    
    # Handler'lar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_new_books, pattern="^new_books$"))
    application.add_handler(CallbackQueryHandler(start, pattern="^main_menu$"))
    
    print("🟢 Ana Kütüphane Botu çalışıyor...")
    application.run_polling()

if __name__ == '__main__':
    main()