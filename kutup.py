import logging
import json
import os
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

# --- AYARLAR ---
# @BotFather'dan aldığınız token'ı buraya yapıştırın
TOKEN = "8496932919:AAFqeNp--WdPpmx6VDFLQQbN_Ki_FozKuQU" 

# Kendi Telegram kullanıcı ID'nizi buraya girin.
# ID'nizi öğrenmek için Telegram'da @userinfobot'a /start yazabilirsiniz.
ADMIN_CHAT_ID = 5954623673 

# Kitap veritabanının saklanacağı dosya adı
DB_FILE = "book_library.json"
# --- AYARLAR SONU ---


# Logging (Hata ayıklama için)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Veritabanı Fonksiyonları ---

def load_library():
    """JSON dosyasından kütüphaneyi yükler."""
    if not os.path.exists(DB_FILE):
        return {}  # Dosya yoksa boş kütüphane
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.warning(f"{DB_FILE} dosyası bozuk veya boş. Sıfırdan başlanıyor.")
        return {}
    except Exception as e:
        logger.error(f"Kütüphane yüklenirken hata: {e}")
        return {}

def save_library(library_data):
    """Kütüphaneyi JSON dosyasına kaydeder."""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(library_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Kütüphane kaydedilirken hata: {e}")

# Kütüphaneyi global bir değişkene yükle
BOOK_LIBRARY = load_library()

# --- Admin Filtresi ---
admin_filter = filters.User(user_id=ADMIN_CHAT_ID)


# --- Kullanıcı Komutları ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komutu. Kullanıcıyı karşılar."""
    user_name = update.message.from_user.first_name
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Merhaba {user_name}! 📚\n\n"
             "Bu bot kişisel bir kitap kütüphanesidir.\n"
             "Mevcut kitapları görmek için /kitaplar komutunu kullanabilirsiniz."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help komutu. Kullanılabilir komutları listeler."""
    help_text = (
        "📖 *Kullanıcı Komutları:*\n"
        "/start - Botu başlatır\n"
        "/kitaplar - Kütüphanedeki tüm kitapları listeler\n"
        "/help - Bu yardım mesajını gösterir\n\n"
    )
    
    # Eğer mesajı gönderen admin ise, admin komutlarını da göster
    if update.message.from_user.id == ADMIN_CHAT_ID:
        help_text += (
            "🔑 *Admin Komutları:*\n"
            "Kitap eklemek için bota özelden bir dosya (PDF, EPUB vb.) gönderin.\n"
            "/sil - Kütüphaneden bir kitabı silmek için liste açar."
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text,
        parse_mode='Markdown'
    )

async def list_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/kitaplar komutu. Kitapları butonlar halinde listeler."""
    if not BOOK_LIBRARY:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Kütüphanede henüz hiç kitap yok. 😔"
        )
        return

    keyboard = []
    # Kütüphanedeki her kitap için bir buton oluştur
    # --- DÜZELTME ---
    # callback_data olarak file_id yerine 'kitap başlığını' kullanıyoruz.
    # Çünkü file_id, 64 byte callback_data limitini aşıyor.
    for book_title in BOOK_LIBRARY.keys():
        keyboard.append([
            InlineKeyboardButton(f"📖 {book_title}", callback_data=book_title)
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Lütfen indirmek istediğiniz kitabı seçin:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buton tıklamalarını yönetir (Kitap indirme ve silme)."""
    query = update.callback_query
    await query.answer()  # Butona basıldığını Telegram'a bildirir

    callback_data = query.data

    if callback_data.startswith("delete_"):
        # --- KİTAP SİLME İŞLEMİ (SADECE ADMİN) ---
        if query.from_user.id != ADMIN_CHAT_ID:
            await query.edit_message_text(text="❌ Bu işlemi yapma yetkiniz yok.")
            return

        book_title_to_delete = callback_data[len("delete_"):] # "delete_" önekini kaldır
        
        if book_title_to_delete in BOOK_LIBRARY:
            del BOOK_LIBRARY[book_title_to_delete]  # Kütüphaneden sil
            save_library(BOOK_LIBRARY)              # Değişiklikleri kaydet
            await query.edit_message_text(text=f"✅ '{book_title_to_delete}' başarıyla silindi.")
            logger.info(f"Admin '{book_title_to_delete}' kitabını sildi.")
        else:
            await query.edit_message_text(text="Kitap bulunamadı (belki çoktan silinmiştir).")
    
    else:
        # --- KİTAP İNDİRME İŞLEMİ (KULLANICI) ---
        
        # --- DÜZELTME ---
        # callback_data artık 'kitap başlığı'nı içeriyor.
        book_title = callback_data

        if book_title in BOOK_LIBRARY:
            # Kitap başlığını kullanarak kütüphaneden file_id'yi al
            file_id = BOOK_LIBRARY[book_title]
            
            try:
                # Kullanıcıya "Gönderiliyor..." mesajı gösterelim
                await context.bot.send_message(
                    chat_id=query.effective_chat.id,
                    text=f"📖 '{book_title}' hazırlanıyor ve gönderiliyor..."
                )
                # Kitabı (dosyayı) gönder
                await context.bot.send_document(
                    chat_id=query.effective_chat.id,
                    document=file_id
                )
                # Orijinal "Lütfen seçin" mesajını kaldırarak ekranı temizle
                await query.delete_message()
            except Exception as e:
                logger.error(f"Dosya gönderilemedi (file_id: {file_id}): {e}")
                await query.edit_message_text(
                    text="Hata: Dosya gönderilemedi. Dosya Telegram sunucularından silinmiş olabilir."
                )
        else:
            await query.edit_message_text(text="Hata: Kitap kütüphanede bulunamadı (belki silinmiştir).")


# --- Admin Komutları ---

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin bota bir dosya gönderdiğinde tetiklenir."""
    # Sadece adminin gönderdiği dosyaları işle
    if update.message.from_user.id != ADMIN_CHAT_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Üzgünüm, kütüphaneye kitap ekleme yetkiniz yok."
        )
        return

    document = update.message.document
    file_id = document.file_id
    file_name = document.file_name

    # Dosya adından uzantıyı kaldıralım (örn: "Kitap Adı.pdf" -> "Kitap Adı")
    book_title = os.path.splitext(file_name)[0]

    # Kitap zaten varsa uyar
    if book_title in BOOK_LIBRARY:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ Uyarı: '{book_title}' adlı kitap zaten kütüphanede mevcut. "
                 "Yeni dosya ile güncellendi."
        )

    # Kütüphaneye ekle
    BOOK_LIBRARY[book_title] = file_id
    save_library(BOOK_LIBRARY)  # Değişiklikleri JSON dosyasına kaydet

    logger.info(f"Admin '{book_title}' adlı kitabı ekledi/güncelledi. File ID: {file_id}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ Başarılı! '{book_title}' kütüphaneye eklendi.\n"
             f"Toplam kitap sayısı: {len(BOOK_LIBRARY)}"
    )

async def delete_book_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/sil komutu (Admin). Silinecek kitapları listeler."""
    if not BOOK_LIBRARY:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Silinecek kitap yok."
        )
        return

    keyboard = []
    # Silme işlemi için callback_data'yı "delete_Kitap Adı" olarak ayarlıyoruz
    for book_title in BOOK_LIBRARY.keys():
        keyboard.append([
            InlineKeyboardButton(f"❌ {book_title}", callback_data=f"delete_{book_title}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Silmek istediğiniz kitabı seçin:",
        reply_markup=reply_markup
    )


# --- Ana Bot Çalıştırma Fonksiyonu ---

async def post_init(application: Application):
    """Bot başlatıldıktan sonra komut menüsünü ayarlar."""
    # --- YENİ ÖZELLİK: Komut Menüsü ---
    
    # Tüm kullanıcılar için varsayılan komutlar
    user_commands = [
        BotCommand("start", "Botu başlatır"),
        BotCommand("kitaplar", "Tüm kitapları listeler"),
        BotCommand("help", "Yardım menüsünü gösterir"),
    ]
    await application.bot.set_my_commands(
        commands=user_commands,
        scope=BotCommandScopeDefault()
    )

    # Admin için özel komutlar (varsayılanlara /sil komutunu ekler)
    admin_commands = user_commands + [
        BotCommand("sil", "Kitap silme menüsünü açar (Admin)"),
    ]
    await application.bot.set_my_commands(
        commands=admin_commands,
        scope=BotCommandScopeChat(chat_id=ADMIN_CHAT_ID)
    )
    logger.info(f"Kullanıcı ve Admin (ID: {ADMIN_CHAT_ID}) için komut menüleri ayarlandı.")


def main():
    """Botu başlatır ve çalıştırır."""
    
    # Token'ı kontrol et
    if TOKEN == "BURAYA_BOT_TOKENINIZI_GIRIN" or ADMIN_CHAT_ID == 123456789:
        print("--- HATA ---")
        print("Lütfen kodun başındaki TOKEN ve ADMIN_CHAT_ID değişkenlerini güncelleyin.")
        print("TOKEN için @BotFather ile konuşun.")
        print("ADMIN_CHAT_ID için @userinfobot'a /start yazın.")
        print("------------")
        return

    # Uygulamayı kur
    application = ApplicationBuilder().token(TOKEN).build()

    # --- YENİ ÖZELLİK: Bot başlatıldığında komut menüsünü ayarlaması için ---
    application.post_init = post_init

    # --- Handler (Komut Yöneticileri) Ekleme ---

    # Kullanıcı komutları
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('kitaplar', list_books))

    # Buton tıklamalarını yakalayan handler
    application.add_handler(CallbackQueryHandler(button_callback))

    # Admin komutları (admin_filter ile korunuyor)
    application.add_handler(CommandHandler('sil', delete_book_list, filters=admin_filter))
    
    # Admin'den gelen dosyaları (kitapları) yakalayan handler
    application.add_handler(MessageHandler(filters.Document.ALL & admin_filter, handle_document))

    # Bilinmeyen dosya gönderimlerine (admin olmayan) yanıt
    application.add_handler(MessageHandler(filters.Document.ALL & ~admin_filter, handle_document))


    print("Bot çalışıyor... (Durdurmak için CTRL+C)")
    # Botu çalıştırmaya başla
    application.run_polling()

if __name__ == '__main__':
    main()
