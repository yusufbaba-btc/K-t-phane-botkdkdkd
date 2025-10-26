# shared_database.py
import sqlite3
import os
import json
from datetime import datetime

class SharedDatabase:
    def __init__(self):
        self.db_path = 'library.db'
        self.init_database()
    
    def init_database(self):
        """Database ve tabloları oluştur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Kitaplar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                description TEXT,
                category TEXT,
                file_path TEXT NOT NULL,
                cover_path TEXT,
                page_count INTEGER DEFAULT 0,
                file_size INTEGER,
                is_active BOOLEAN DEFAULT 1,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_by INTEGER
            )
        ''')
        
        # Kategoriler tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                book_count INTEGER DEFAULT 0
            )
        ''')
        
        # İstatistikler tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                total_books INTEGER DEFAULT 0,
                total_categories INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_book(self, book_data):
        """Yeni kitap ekle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO books 
            (title, author, description, category, file_path, cover_path, page_count, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            book_data['title'],
            book_data['author'],
            book_data.get('description', ''),
            book_data['category'],
            book_data['file_path'],
            book_data.get('cover_path', ''),
            book_data.get('page_count', 0),
            book_data.get('file_size', 0)
        ))
        
        # Kategori istatistiğini güncelle
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name, book_count) 
            VALUES (?, 0)
        ''', (book_data['category'],))
        
        cursor.execute('''
            UPDATE categories SET book_count = book_count + 1 
            WHERE name = ?
        ''', (book_data['category'],))
        
        # Genel istatistikleri güncelle
        cursor.execute('''
            INSERT OR REPLACE INTO stats (total_books, last_update)
            VALUES (
                (SELECT COUNT(*) FROM books WHERE is_active = 1),
                CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        book_id = cursor.lastrowid
        conn.close()
        
        return book_id
    
    def get_active_books(self, limit=50, offset=0):
        """Aktif kitapları getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM books 
            WHERE is_active = 1 
            ORDER BY uploaded_at DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        books = cursor.fetchall()
        conn.close()
        return books
    
    def search_books(self, query):
        """Kitaplarda arama yap"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM books 
            WHERE is_active = 1 
            AND (title LIKE ? OR author LIKE ? OR category LIKE ?)
            ORDER BY 
                CASE 
                    WHEN title LIKE ? THEN 1
                    WHEN author LIKE ? THEN 2
                    ELSE 3
                END
            LIMIT 20
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        
        books = cursor.fetchall()
        conn.close()
        return books
    
    def get_categories(self):
        """Kategorileri getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, book_count FROM categories 
            ORDER BY book_count DESC
        ''')
        
        categories = cursor.fetchall()
        conn.close()
        return categories