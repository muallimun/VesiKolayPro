"""
VesiKolay Pro - Update Checker
GitHub üzerinden program güncellemelerini kontrol eden modül
"""

import requests
import logging
import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser

class UpdateChecker:
    """GitHub üzerinden güncelleme kontrolü yapan sınıf"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_version = "1.0"
        self.version_url = "https://github.com/muallimun/VesiKolayPro/raw/main/VesiKolayPro_version.txt"
        self.releases_url = "https://github.com/muallimun/VesiKolayPro/releases/tag/1.0"
        self.homepage_url = "https://github.com/muallimun/VesiKolayPro"
        self.timeout = 5  # Kısa timeout

    def get_current_version(self) -> str:
        """Mevcut program versiyonunu döndür"""
        return self.current_version

    def check_for_updates(self) -> tuple:
        """
        GitHub'dan güncelleme kontrolü yap
        Returns: (güncelleme_var_mı, yeni_versiyon, hata_mesajı)
        """
        try:
            self.logger.info("Güncelleme kontrolü başlatılıyor...")

            # GitHub'dan versiyon bilgisini al
            response = requests.get(self.version_url, timeout=self.timeout)
            response.raise_for_status()

            # Versiyon bilgisini temizle
            latest_version = response.text.strip()

            self.logger.info(f"GitHub'dan alınan versiyon: '{latest_version}'")
            self.logger.info(f"Mevcut versiyon: '{self.current_version}'")

            # Basit string karşılaştırması
            if latest_version != self.current_version:
                self.logger.info(f"Yeni versiyon bulundu: {latest_version}")
                return True, latest_version, ""
            else:
                self.logger.info("Program güncel")
                return False, latest_version, ""

        except requests.exceptions.RequestException as e:
            error_msg = f"İnternet bağlantısı hatası: {str(e)}"
            self.logger.error(error_msg)
            return False, "", error_msg

        except Exception as e:
            error_msg = f"Güncelleme kontrolü hatası: {str(e)}"
            self.logger.error(error_msg)
            return False, "", error_msg

    def check_for_updates_async(self, callback):
        """Asenkron güncelleme kontrolü"""
        def check_updates():
            result = self.check_for_updates()
            if callback:
                callback(result)

        thread = threading.Thread(target=check_updates, daemon=True)
        thread.start()

    def show_update_dialog(self, parent, new_version: str) -> bool:
        """Güncelleme dialog'unu göster"""
        title = "🎉 Yeni Güncelleme Mevcut!"
        message = f"""VesiKolay Pro için yeni bir versiyon mevcut!

📌 Mevcut versiyon: {self.current_version}
🆕 Yeni versiyon: {new_version}

🔗 GitHub sayfasından yeni versiyonu indirebilirsiniz.

Şimdi indirmek ister misiniz?"""

        result = messagebox.askyesno(
            title, 
            message,
            icon='question',
            parent=parent
        )

        if result:
            self.open_releases_page()

        return result

    def show_no_update_dialog(self, parent):
        """Güncelleme yok dialog'unu göster"""
        title = "✅ Program Güncel"
        message = f"""VesiKolay Pro zaten en güncel versiyonda!

📌 Mevcut versiyon: {self.current_version}

🔗 GitHub sayfamızı ziyaret edebilirsiniz."""

        result = messagebox.askyesno(
            title,
            message + "\n\nGitHub sayfasını açmak ister misiniz?",
            icon='info',
            parent=parent
        )

        if result:
            self.open_homepage()

    def show_error_dialog(self, parent, error_message: str):
        """Hata dialog'unu göster"""
        title = "❌ Güncelleme Kontrolü Hatası"
        message = f"""Güncelleme kontrolü sırasında bir hata oluştu:

{error_message}

🔗 Manuel olarak GitHub sayfasını kontrol edebilirsiniz."""

        result = messagebox.askyesno(
            title,
            message + "\n\nGitHub sayfasını açmak ister misiniz?",
            icon='error',
            parent=parent
        )

        if result:
            self.open_homepage()

    def open_releases_page(self):
        """GitHub releases sayfasını aç"""
        try:
            webbrowser.open(self.releases_url)
            self.logger.info("GitHub releases sayfası açıldı")
        except Exception as e:
            self.logger.error(f"Tarayıcı açma hatası: {e}")

    def open_homepage(self):
        """GitHub ana sayfasını aç"""
        try:
            webbrowser.open(self.homepage_url)
            self.logger.info("GitHub ana sayfası açıldı")
        except Exception as e:
            self.logger.error(f"Tarayıcı açma hatası: {e}")

    def perform_startup_check(self, parent_window):
        """Program başlangıcında güncelleme kontrolü yap"""
        def update_callback(result):
            has_update, new_version, error_msg = result

            # Sadece güncelleme varsa göster, hata varsa sessizce geç
            if has_update:
                parent_window.after(0, lambda: self.show_update_dialog(parent_window, new_version))

        # Asenkron kontrol başlat
        self.check_for_updates_async(update_callback)

    def perform_manual_check(self, parent_window):
        """Manuel güncelleme kontrolü yap"""
        def update_callback(result):
            has_update, new_version, error_msg = result

            if error_msg:
                parent_window.after(0, lambda: self.show_error_dialog(parent_window, error_msg))
            elif has_update:
                parent_window.after(0, lambda: self.show_update_dialog(parent_window, new_version))
            else:
                parent_window.after(0, lambda: self.show_no_update_dialog(parent_window))

        # Manuel kontrolde tüm durumları göster
        self.check_for_updates_async(update_callback)


# Global instance
update_checker = UpdateChecker()