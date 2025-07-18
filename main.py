#!/usr/bin/env python3
"""
VesiKolay Pro - School Photography Automation
Main entry point for the application
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Lazy import - sadece gerektiğinde import et
def setup_logging():
    import logging
    from config import Config
    config = Config()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.get_log_file_path()),
            logging.StreamHandler()
        ]
    )
    return logging

def main():
    """Main application entry point"""
    try:
        print("🚀 VesiKolay Pro başlatılıyor...")
        print("📊 Excel verilerini fotoğraflarla eşleştirme programı")
        print("=" * 60)

        # Setup logging lazily
        logging = setup_logging()

        # Replit GUI desteği için gerekli ayarlar
        # Display ayarları
        if not os.getenv('DISPLAY'):
            os.environ['DISPLAY'] = ':0'

        # X11 forwarding için gerekli ayarlar
        if os.getenv('REPL_ID'):
            os.environ['XDG_RUNTIME_DIR'] = '/tmp'
            os.environ['XAUTHORITY'] = '/tmp/.Xauthority'
            print("🖥️ Replit GUI ortamı hazırlanıyor...")

        # Import here to handle potential import errors gracefully
        from app import VesiKolayProApp

        # Create and run the application
        app = VesiKolayProApp()
        app.run()

    except ImportError as e:
        logging.error(f"Failed to import required modules: {e}")
        print("Hata: Gerekli modüller bulunamadı. Lütfen gerekli paketleri yükleyin.")
        print(f"Import hatası: {e}")
        print("\nKonsol modunda devam ediliyor...")

        # Basit konsol uygulaması çalıştır
        try:
            from app import VesiKolayProApp
            app = VesiKolayProApp()
            app.run_console_mode()
        except:
            print("Minimal mod çalıştırılıyor...")
            minimal_mode()

    except Exception as e:
        logging.error(f"Application failed to start: {e}")
        print(f"Hata: Uygulama başlatılamadı - {e}")
        import traceback
        traceback.print_exc()
        print("\nKonsol modunda devam ediliyor...")
        minimal_mode()

def minimal_mode():
    """Minimal konsol modu"""
    print("\n" + "=" * 40)
    print("VesiKolay Pro - Minimal Mod")
    print("=" * 40)
    print("Program sistem limitleri nedeniyle minimal modda çalışıyor.")
    print("Temel sistem kontrolü yapılıyor...")

    # VesiKolayPro dizin bilgileri
    from utils import VesiKolayUtils
    try:
        project_info = VesiKolayUtils.get_project_info()
        print(f"\n📁 VesiKolayPro Dizinleri:")
        print(f"   Ana Dizin: {project_info['vesikolay_directory']}")
        print(f"   Çıktı Dizini: {project_info['output_directory']}")
        print(f"   Log Dizini: {project_info['log_directory']}")
        print(f"   Yedek Dizini: {project_info['backup_directory']}")
        print(f"   Veritabanı: {project_info['database_file']}")
        print(f"   Log Dosyası: {project_info['log_file']}")
    except Exception as e:
        print(f"❌ VesiKolayPro dizin bilgileri alınamadı: {e}")

    # Kullanıcı veri kontrolü
    print(f"\n📋 Program artık kullanıcının seçeceği dosyalarla çalışır:")
    print(f"   📊 Excel dosyası: Kullanıcı seçecek")
    print(f"   📸 Fotoğraf klasörü: Kullanıcı seçecek")
    print(f"   📁 Çıktılar: Documents/VesiKolayPro dizininde")

    print("\n✅ VesiKolayPro dizinleri hazırlandı.")
    print("📝 Tüm çıktılar Documents/VesiKolayPro dizininde oluşturulacak.")
    print("🖥️  GUI destekli bir sistemde çalıştırın.")

if __name__ == "__main__":
    main()