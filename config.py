# config.py
import os

# Bot Token'ları - BUNLARI BOTFATHER'DAN ALACAKSINIZ
MAIN_BOT_TOKEN = "8496932919:AAFqeNp--WdPpmx6VDFLQQbN_Ki_FozKuQU"
ADMIN_BOT_TOKEN = "8333123080:AAFvEKuygrExzkhZNjnKUEhzS_Igx3zlr38"

# Admin şifresi - BUNU KENDİN BELİRLE
ADMIN_PASSWORD = "31kdf20"

# Dosya yolları
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKS_DIR = os.path.join(BASE_DIR, "books")
COVERS_DIR = os.path.join(BASE_DIR, "covers")

# Dosya limitleri
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png']

# Klasörleri oluştur
os.makedirs(BOOKS_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)