# admin_bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
import os
import logging
from config import ADMIN_BOT_TOKEN, ADMIN_PASSWORD, BOOKS_DIR, COVERS_DIR, MAX_FILE_SIZE
from shared_database import SharedDatabase

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SharedDatabase()

# Konuşma durumları
PASSWORD, MENU, BOOK_TITLE, BOOK_AUTHOR, BOOK_CATEGORY, BOOK_DESCRIPTION, BOOK_PDF, BOOK_COVER = range(8)

# Zarif Admin Menü Tasarımı
async def start_admin(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🔐 **Admin Giriş Paneli**\n\n"
        "🏛️ *Digital Kütüphane Yönetim Sistemi*\n\n"
        "Lütfen admin şifresini girin:",
        parse_mode='Markdown'
    )
    return PASSWORD

async def check_password(update: Update, context: CallbackContext):
    user_input = update.message.text.strip()
    
    if user_input == ADMIN_PASSWORD:
        context.user_data['authenticated'] = True
        await show_admin_dashboard(update, context)
        return MENU
    else:
        await update.message.reply_text(
            "❌ *Hatalı şifre!*\n\n"
            "Lütfen tekrar deneyin:",
            parse_mode='Markdown'
        )
        return PASSWORD

async def show_admin_dashboard(update: Update, context: CallbackContext):
    stats = db.get_stats()
    
    dashboard_text = f"""
🏛️ **Admin Dashboard** ✨

📊 **Sistem İstatistikleri:**
• 📚 Toplam Kitaplar: {stats['total_books']}
• 📂 Toplam Kategoriler: {stats['total_categories']}
• ⏰ Son Güncelleme: {stats['last_update']}

🎯 **Yapılabilir İşlemler:**
    """
    
    keyboard = [
        [InlineKeyboardButton("📖 Yeni Kitap Ekle", callback_data="add_book")],
        [InlineKeyboardButton("📊 Kitap İstatistikleri", callback_data="book_stats")],
        [InlineKeyboardButton("📂 Kategori Yönetimi", callback_data="manage_categories")],
        [InlineKeyboardButton("🔄 Sistemi Yenile", callback_data="refresh_system")],
        [InlineKeyboardButton("🚪 Çıkış", callback_data="logout_admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(dashboard_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(dashboard_text, reply_markup=reply_markup, parse_mode='Markdown')

# Kitap Ekleme Akışı - Modern Tasarım
async def start_add_book_flow(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    # Kullanıcı verilerini temizle
    context.user_data.clear()
    context.user_data['book_data'] = {}
    
    welcome_text = """
📖 **Yeni Kitap Ekleme Sihirbazı** ✨

Kitapları sisteme kolayca ekleyebilirsiniz. 
Lütfen aşağıdaki bilgileri sırayla girin:

🎯 **Gerekli Bilgiler:**
1. 📝 Kitap Başlığı
2. ✍️ Yazar Adı  
3. 📂 Kategori
4. 📄 PDF Dosyası

💫 **Opsiyonel Bilgiler:**
5. 📝 Açıklama
6. 🖼️ Kapak Görseli

**İlk adım olarak kitap başlığını girin:**
    """
    
    await query.edit_message_text(welcome_text, parse_mode='Markdown')
    return BOOK_TITLE

async def get_book_title(update: Update, context: CallbackContext):
    context.user_data['book_data']['title'] = update.message.text
    await update.message.reply_text(
        "✍️ **Yazar bilgisini girin:**\n\n"
        "Örnek: *Ahmet Ümit*",
        parse_mode='Markdown'
    )
    return BOOK_AUTHOR

async def get_book_author(update: Update, context: CallbackContext):
    context.user_data['book_data']['author'] = update.message.text
    await update.message.reply_text(
        "📂 **Kategori seçin veya yeni kategori girin:**\n\n"
        "Mevcut kategoriler:\n"
        "• Roman\n• Şiir\n• Bilim Kurgu\n• Tarih\n• Kişisel Gelişim\n\n"
        "Yeni kategori için direkt yazın:",
        parse_mode='Markdown'
    )
    return BOOK_CATEGORY

async def get_book_category(update: Update, context: CallbackContext):
    context.user_data['book_data']['category'] = update.message.text
    await update.message.reply_text(
        "📝 **Kitap açıklamasını girin:**\n\n"
        "*(Opsiyonel - Atlamak için 'geç' yazın)*",
        parse_mode='Markdown'
    )
    return BOOK_DESCRIPTION

async def get_book_description(update: Update, context: CallbackContext):
    if update.message.text.lower() != 'geç':
        context.user_data['book_data']['description'] = update.message.text
    
    await update.message.reply_text(
        "📄 **PDF dosyasını gönderin:**\n\n"
        "⚠️ *Teknik Bilgiler:*\n"
        "• Maksimum dosya: 50MB\n"
        "• Format: PDF\n"
        "• Otomatik işleme: Aktif\n\n"
        "Lütfen PDF dosyasını yükleyin:",
        parse_mode='Markdown'
    )
    return BOOK_PDF

async def handle_pdf_upload(update: Update, context: CallbackContext):
    if not update.message.document:
        await update.message.reply_text("❌ Lütfen bir PDF dosyası gönderin!")
        return BOOK_PDF
    
    document = update.message.document
    
    # Dosya kontrolü
    if document.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("❌ Dosya boyutu çok büyük! Maksimum 50MB")
        return BOOK_PDF
    
    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ Sadece PDF dosyaları kabul edilir!")
        return BOOK_PDF
    
    # Dosyayı indir
    file = await document.get_file()
    safe_filename = f"{db.get_next_book_id()}_{document.file_name}"
    file_path = os.path.join(BOOKS_DIR, safe_filename)
    
    await file.download_to_drive(file_path)
    
    # Kitap verilerini kaydet
    context.user_data['book_data']['file_path'] = file_path
    context.user_data['book_data']['file_size'] = document.file_size
    
    # Database'e ekle
    book_id = db.add_book(context.user_data['book_data'])
    
    # Başarı mesajı
    book_title = context.user_data['book_data']['title']
    
    success_text = f"""
✅ **Kitap Başarıyla Eklendi!** 🎉

📚 **Kitap:** {book_title}
🆔 **Sistem ID:** #{book_id}
📂 **Kategori:** {context.user_data['book_data']['category']}
💾 **Dosya Boyutu:** {document.file_size // 1024 // 1024}MB

🌟 *Kitap anında kütüphane botunda görünür oldu!*

Yeni kitap eklemek için /menu yazın.
    """
    
    await update.message.reply_text(success_text, parse_mode='Markdown')
    
    # Temizlik
    context.user_data.clear()
    return ConversationHandler.END

def main():
    """Admin botunu başlat"""
    application = Application.builder().token(ADMIN_BOT_TOKEN).build()
    
    # Konuşma handler'ı
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_admin)],
        states={
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)],
            MENU: [CallbackQueryHandler(show_admin_dashboard, pattern='^refresh_system$')],
            BOOK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_book_title)],
            BOOK_AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_book_author)],
            BOOK_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_book_category)],
            BOOK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_book_description)],
            BOOK_PDF: [MessageHandler(filters.Document.ALL, handle_pdf_upload)],
        },
        fallbacks=[CommandHandler('menu', show_admin_dashboard)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(start_add_book_flow, pattern='^add_book$'))
    
    print("🟢 Admin Botu çalışıyor...")
    application.run_polling()

if __name__ == '__main__':
    main()