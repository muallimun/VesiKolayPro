"""
VesiKolay Pro - Ana Uygulama
Excel verileri ile fotoğrafları eşleştirip yeniden adlandıran ana program
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from pathlib import Path
from typing import List, Dict, Optional
import os
import threading
import webbrowser

class ToolTip:
    """Tooltip sınıfı - Widget'lara açıklama baloncukları ekler"""
    
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def on_enter(self, event=None):
        self.show_tip()

    def on_leave(self, event=None):
        self.hide_tip()

    def show_tip(self, event=None):
        "Display text in tooltip window"
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("tahoma", "8", "normal"),
                        wraplength=300,
                        padx=4, pady=4)
        label.pack(ipadx=1)

    def hide_tip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

    def update_text(self, new_text):
        self.text = new_text

from excel_reader import ExcelReader
from photo_processor import PhotoProcessor
from utils import FileUtils, ValidationUtils, ProgressTracker

class ModernUI:
    """Modern UI stil sınıfı"""

    # Renk paleti
    COLORS = {
        'primary': '#2C3E50',
        'secondary': '#3498DB',
        'success': '#27AE60',
        'warning': '#F39C12',
        'danger': '#E74C3C',
        'light': '#ECF0F1',
        'dark': '#34495E',
        'white': '#FFFFFF',
        'text': '#2C3E50',
        'text_light': '#7F8C8D',
        'bg_main': '#F8F9FA',
        'card_bg': '#FFFFFF',
        'border': '#E9ECEF'
    }

    # Font ayarları
    FONTS = {
        'title': ('Segoe UI', 16, 'bold'),
        'subtitle': ('Segoe UI', 12, 'bold'),
        'body': ('Segoe UI', 10),
        'small': ('Segoe UI', 9),
        'button': ('Segoe UI', 10, 'bold')
    }

class VesiKolayProApp:
    """VesiKolay Pro ana uygulama sınıfı"""

    def __init__(self):
        """Uygulamayı başlat"""
        self.logger = logging.getLogger(__name__)

        # Modülleri başlat
        self.excel_reader = ExcelReader()
        self.photo_processor = PhotoProcessor()

        # Update checker'ı başlat
        try:
            from update_checker import UpdateChecker
            self.update_checker = UpdateChecker()
        except ImportError as e:
            self.update_checker = None
            print(f"⚠️ Güncelleme kontrolü modülü yüklenemedi: {e}")
        except Exception as e:
            self.update_checker = None
            print(f"⚠️ Güncelleme kontrolü başlatma hatası: {e}")

        # Uygulama durumu
        self.excel_file_path = None
        self.photo_directory = None
        self.excel_data = []
        self.available_columns = []
        self.selected_naming_columns = []
        self.school_name = ""

        # Threading için
        self.current_operation = None
        self.cancel_requested = threading.Event()

        # GUI oluştur
        self.setup_gui()

    def setup_gui(self):
        """Modern GUI arayüzünü oluştur"""
        # Display ayarları - Replit için
        import os
        
        # Replit için gerekli environment değişkenleri
        if 'DISPLAY' not in os.environ:
            os.environ['DISPLAY'] = ':0'
        
        # X11 forwarding için gerekli ayarlar
        if os.getenv('REPL_ID'):
            os.environ['XDG_RUNTIME_DIR'] = '/tmp'
            os.environ['XAUTHORITY'] = '/tmp/.Xauthority'

        try:
            # Ana pencere
            self.root = tk.Tk()
            self.root.title("VesiKolay Pro - Fotoğraf Adlandırma Otomasyonu")
            self.root.geometry("1200x800")
            self.root.minsize(1000, 700)
            self.root.configure(bg=ModernUI.COLORS['bg_main'])
            
            # Program simgesi ayarla - görev çubuğu için optimize edilmiş
            try:
                import platform
                system_type = platform.system()
                
                # Windows için ICO dosyasını öncelikle dene
                if system_type == 'Windows':
                    ico_icon_path = Path(__file__).parent / "images" / "vesikolaypro.ico"
                    if ico_icon_path.exists():
                        # Hem pencere hem de görev çubuğu için
                        self.root.iconbitmap(str(ico_icon_path))
                        print("✅ ICO simgesi başarıyla yüklendi (Windows)")
                    else:
                        # ICO yoksa PNG'yi dene
                        png_icon_path = Path(__file__).parent / "images" / "vesikolaypro.png"
                        if png_icon_path.exists():
                            from PIL import Image, ImageTk
                            # Görev çubuğu için daha büyük boyut
                            icon_image = Image.open(png_icon_path)
                            icon_image = icon_image.resize((48, 48), Image.Resampling.LANCZOS)
                            self.icon_photo = ImageTk.PhotoImage(icon_image)
                            self.root.iconphoto(True, self.icon_photo)  # True = görev çubuğu için de geçerli
                            print("✅ PNG simgesi başarıyla yüklendi (Windows)")
                
                # Linux/Unix için PNG dosyasını dene
                else:
                    png_icon_path = Path(__file__).parent / "images" / "vesikolaypro.png"
                    if png_icon_path.exists():
                        from PIL import Image, ImageTk
                        # Linux için farklı boyutlarda ikonlar hazırla
                        icon_image = Image.open(png_icon_path)
                        
                        # Küçük ikon (16x16) - görev çubuğu için
                        small_icon = icon_image.resize((16, 16), Image.Resampling.LANCZOS)
                        self.small_icon_photo = ImageTk.PhotoImage(small_icon)
                        
                        # Büyük ikon (48x48) - pencere için
                        large_icon = icon_image.resize((48, 48), Image.Resampling.LANCZOS)
                        self.large_icon_photo = ImageTk.PhotoImage(large_icon)
                        
                        # Her ikisini de ayarla
                        self.root.iconphoto(True, self.large_icon_photo, self.small_icon_photo)
                        print("✅ PNG simgesi başarıyla yüklendi (Linux/Unix)")
                    
                    # Alternatif olarak ICO dosyasını da dene
                    else:
                        ico_icon_path = Path(__file__).parent / "images" / "vesikolaypro.ico"
                        if ico_icon_path.exists():
                            try:
                                # ICO dosyasını PNG'ye çevir
                                from PIL import Image, ImageTk
                                icon_image = Image.open(ico_icon_path)
                                icon_image = icon_image.resize((48, 48), Image.Resampling.LANCZOS)
                                self.icon_photo = ImageTk.PhotoImage(icon_image)
                                self.root.iconphoto(True, self.icon_photo)
                                print("✅ ICO simgesi PNG'ye çevrilerek yüklendi (Linux/Unix)")
                            except:
                                print("⚠️ ICO dosyası PNG'ye çevrilemedi")
                
                # Pencere başlığını da ayarla (görev çubuğu için)
                self.root.title("VesiKolay Pro - Fotoğraf Adlandırma Otomasyonu")
                
                # Windows için ek ayarlar
                if system_type == 'Windows':
                    try:
                        # Görev çubuğu gruplama için
                        import ctypes
                        myappid = 'muallimun.vesikolaypro.v1.0'  # Uygulama kimliği
                        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                    except:
                        pass  # Hata olursa görmezden gel
                        
            except Exception as icon_error:
                print(f"⚠️ Simge yüklenirken hata (normal): {icon_error}")
            
            # GUI test
            self.root.update()
            print("✅ GUI başarıyla başlatıldı")
            
        except Exception as e:
            print(f"❌ GUI başlatma hatası: {e}")
            print("🖥️ Konsol modunda çalışılıyor...")
            self.root = None
            return self.run_console_mode()

        # Stil ayarları
        self.setup_styles()

        # Ana container
        self.main_container = tk.Frame(self.root, bg=ModernUI.COLORS['bg_main'])
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        self.create_header()

        # Ana içerik alanı (sol-sağ split)
        self.create_main_layout()

        # Footer bölümü
        self.create_footer()

        # Grid yapılandırması
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Program açılışında güncelleme kontrolü başlat
        self.check_for_updates_startup()

    def setup_styles(self):
        """TTK stillerini ayarla - Modern hover efektleri ile"""
        style = ttk.Style()
        style.theme_use('clam')

        # Primary Button - hover efektli
        style.configure('Primary.TButton',
                       background=ModernUI.COLORS['secondary'],
                       foreground=ModernUI.COLORS['white'],
                       font=ModernUI.FONTS['button'],
                       padding=(20, 12),
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat')
        
        style.map('Primary.TButton',
                 background=[('active', '#2980B9'),  # Hover rengi (daha koyu mavi)
                           ('pressed', '#1F6391')],  # Basılma rengi
                 foreground=[('active', ModernUI.COLORS['white']),
                           ('pressed', ModernUI.COLORS['white'])])

        # Success Button - hover efektli
        style.configure('Success.TButton',
                       background=ModernUI.COLORS['success'],
                       foreground=ModernUI.COLORS['white'],
                       font=ModernUI.FONTS['button'],
                       padding=(20, 12),
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat')
        
        style.map('Success.TButton',
                 background=[('active', '#219A52'),  # Hover rengi (daha koyu yeşil)
                           ('pressed', '#1E7E34')],  # Basılma rengi
                 foreground=[('active', ModernUI.COLORS['white']),
                           ('pressed', ModernUI.COLORS['white'])])

        # Warning Button - hover efektli
        style.configure('Warning.TButton',
                       background=ModernUI.COLORS['warning'],
                       foreground=ModernUI.COLORS['white'],
                       font=ModernUI.FONTS['button'],
                       padding=(16, 8),
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat')
        
        style.map('Warning.TButton',
                 background=[('active', '#E0A800'),  # Hover rengi (daha koyu sarı)
                           ('pressed', '#C69500')],  # Basılma rengi
                 foreground=[('active', ModernUI.COLORS['white']),
                           ('pressed', ModernUI.COLORS['white'])])

        # Danger Button - hover efektli
        style.configure('Danger.TButton',
                       background=ModernUI.COLORS['danger'],
                       foreground=ModernUI.COLORS['white'],
                       font=ModernUI.FONTS['button'],
                       padding=(16, 8),
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat')
        
        style.map('Danger.TButton',
                 background=[('active', '#C82333'),  # Hover rengi (daha koyu kırmızı)
                           ('pressed', '#A71E2A')],  # Basılma rengi
                 foreground=[('active', ModernUI.COLORS['white']),
                           ('pressed', ModernUI.COLORS['white'])])

    def setup_progress_style(self):
        """Progress bar özel stilini ayarla"""
        style = ttk.Style()
        
        # Custom progress bar stili
        style.configure('Custom.Horizontal.TProgressbar',
                       background=ModernUI.COLORS['success'],
                       troughcolor=ModernUI.COLORS['light'],
                       borderwidth=0,
                       lightcolor=ModernUI.COLORS['success'],
                       darkcolor=ModernUI.COLORS['success'])

    def create_header(self):
        """Header bölümünü oluştur - Gradient ve modern efektlerle"""
        # Ana header frame
        header_frame = tk.Frame(self.main_container, height=55)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        header_frame.pack_propagate(False)

        # Gradient arka plan için Canvas
        self.header_canvas = tk.Canvas(header_frame, height=55, highlightthickness=0)
        self.header_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Gradient oluştur
        self.create_gradient_background()

        # İçerik container - Canvas üzerine
        content_frame = tk.Frame(self.header_canvas, bg=ModernUI.COLORS['secondary'])
        
        # Canvas penceresini oluştur
        canvas_window = self.header_canvas.create_window(0, 0, anchor='nw', window=content_frame)
        
        # Ana başlık bölümü
        title_section = tk.Frame(content_frame, bg=ModernUI.COLORS['secondary'])
        title_section.pack(expand=True, fill=tk.BOTH)

        # Başlık ve ikon container - tek satırda
        title_frame = tk.Frame(title_section, bg=ModernUI.COLORS['secondary'])
        title_frame.pack(pady=(10, 10), expand=True)

        # Program simgesi
        try:
            from PIL import Image, ImageTk
            icon_path = Path(__file__).parent / "images" / "vesikolaypro.png"
            if icon_path.exists():
                icon_image = Image.open(icon_path)
                icon_image = icon_image.resize((24, 24), Image.Resampling.LANCZOS)
                self.header_icon = ImageTk.PhotoImage(icon_image)
                icon_widget = tk.Label(title_frame,
                                     image=self.header_icon,
                                     bg=ModernUI.COLORS['secondary'])
                icon_widget.pack(side=tk.LEFT, padx=(0, 8))
        except:
            pass

        # Ana başlık
        title_label = tk.Label(title_frame,
                              text="VesiKolayPro",
                              font=('Segoe UI', 16, 'bold'),
                              fg='white',
                              bg=ModernUI.COLORS['secondary'])
        title_label.pack(side=tk.LEFT, padx=(0, 15))

        # Alt başlık - aynı satırda
        subtitle_label = tk.Label(title_frame,
                                 text="📋 Yeni Nesil Okul Fotoğrafçılığı Asistanı",
                                 font=('Segoe UI', 11),
                                 fg='#FFFFFF',
                                 bg=ModernUI.COLORS['secondary'])
        subtitle_label.pack(side=tk.LEFT)

        # Canvas boyutunu güncelle
        def update_canvas_size(event=None):
            self.header_canvas.configure(scrollregion=self.header_canvas.bbox("all"))
            canvas_width = self.header_canvas.winfo_width()
            self.header_canvas.itemconfig(canvas_window, width=canvas_width)
            
        self.header_canvas.bind('<Configure>', update_canvas_size)
        content_frame.bind('<Configure>', update_canvas_size)

    def create_gradient_background(self):
        """Header için gradient arka plan oluştur"""
        def draw_gradient():
            width = self.header_canvas.winfo_width()
            height = self.header_canvas.winfo_height()
            
            if width <= 1 or height <= 1:
                self.header_canvas.after(100, draw_gradient)
                return
                
            # Gradient renkler
            start_color = (44, 62, 80)    # #2C3E50 (koyu mavi)
            end_color = (52, 152, 219)    # #3498DB (açık mavi)
            
            # Canvas'ı temizle
            self.header_canvas.delete("gradient")
            
            # Gradient çiz
            for i in range(height):
                ratio = i / height
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
                
                color = f"#{r:02x}{g:02x}{b:02x}"
                self.header_canvas.create_line(0, i, width, i, fill=color, tags="gradient")
        
        # İlk çizimi geciktir
        self.header_canvas.after(10, draw_gradient)

    def create_main_layout(self):
        """Ana layout (sol-sağ split) oluştur"""
        # Ana paned window
        self.main_paned = tk.PanedWindow(self.main_container, 
                                        orient=tk.HORIZONTAL,
                                        sashwidth=8,
                                        bg=ModernUI.COLORS['border'])
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # Sol panel (işlem adımları)
        self.left_panel = tk.Frame(self.main_paned, bg=ModernUI.COLORS['bg_main'])
        self.main_paned.add(self.left_panel, minsize=350, width=440)

        # Sağ panel (sonuçlar ve durum)
        self.right_panel = tk.Frame(self.main_paned, bg=ModernUI.COLORS['bg_main'])
        self.main_paned.add(self.right_panel, minsize=280, width=380)

        # Sol panel içeriği
        self.create_left_panel_content()

        # Sağ panel içeriği
        self.create_right_panel_content()

    def create_left_panel_content(self):
        """Sol panel içeriğini oluştur"""
        # Başlık
        left_title = tk.Label(self.left_panel,
                             text="İşlem Adımları",
                             font=ModernUI.FONTS['title'],
                             fg=ModernUI.COLORS['text'],
                             bg=ModernUI.COLORS['bg_main'])
        left_title.pack(pady=(0, 10), anchor='w')

        # Scroll alanı
        canvas = tk.Canvas(self.left_panel, bg=ModernUI.COLORS['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.left_panel, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=ModernUI.COLORS['bg_main'])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # İçerik kartları
        self.create_step_cards()

        # Canvas pack
        canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel binding - güvenli versiyon
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except (tk.TclError, Exception):
                try:
                    canvas.unbind_all("<MouseWheel>")
                except:
                    pass
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def create_right_panel_content(self):
        """Sağ panel içeriğini oluştur"""
        # İlerleme kartı
        self.create_progress_card()

        # Sonuçlar kartı
        self.create_results_card()

        # Dosya erişim kartı
        self.create_file_access_card()

    def create_step_cards(self):
        """Adım kartlarını oluştur"""
        # Adım 1: Okul Bilgisi
        self.create_school_info_card()

        # Adım 2: Excel Dosyası
        self.create_excel_card()

        # Adım 3: Fotoğraf Dizini
        self.create_photo_card()

        # Adım 4: İşlem Ayarları
        self.create_advanced_naming_card()
        
        # Adım 5: Fotoğraf İşleme Ayarları
        self.create_photo_processing_card()

        # Adım 6: İşlem Butonları
        self.create_action_card()

    def create_school_info_card(self):
        """Okul bilgisi kartı"""
        card_frame = tk.Frame(self.scrollable_frame, 
                             bg=ModernUI.COLORS['card_bg'],
                             relief='solid',
                             bd=1)
        card_frame.pack(fill=tk.X, pady=(0, 8), padx=5, ipady=6, ipadx=8)

        # Başlık
        self.create_card_header(card_frame, "1", "Okul Bilgisi", 
                               "Okul adını girin (çıktı klasörü adı olarak kullanılacak)")

        # Okul adı giriş alanı
        school_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        school_frame.pack(fill=tk.X, pady=(8, 0))

        school_label = tk.Label(school_frame,
                               text="Okul Adı:",
                               font=ModernUI.FONTS['body'],
                               bg=ModernUI.COLORS['card_bg'])
        school_label.pack(side=tk.LEFT, padx=(0, 8))
        ToolTip(school_label, "Okulunuzun adını girin. Bu ad çıktı klasörlerinde kullanılacak.")

        self.school_name_var = tk.StringVar()
        school_entry = tk.Entry(school_frame,
                               textvariable=self.school_name_var,
                               font=ModernUI.FONTS['body'],
                               width=35)
        school_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        school_entry.bind('<KeyRelease>', self.on_school_name_change)
        ToolTip(school_entry, "Okul adınızı buraya yazın. Örnek: 'Ankara Merkez İmam Hatip Lisesi' veya 'Fatih Anadolu Lisesi'")

        # Eğitim-öğretim yılı girişi
        year_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        year_frame.pack(fill=tk.X, pady=(8, 0))

        year_label = tk.Label(year_frame,
                             text="Eğitim-Öğretim Yılı:",
                             font=ModernUI.FONTS['body'],
                             bg=ModernUI.COLORS['card_bg'])
        year_label.pack(side=tk.LEFT)
        ToolTip(year_label, "Kimlik kartlarında görünecek eğitim-öğretim yılı")

        self.school_year_var = tk.StringVar(value="2025-2026")
        year_entry = tk.Entry(year_frame,
                             textvariable=self.school_year_var,
                             font=ModernUI.FONTS['body'],
                             width=15)
        year_entry.pack(side=tk.LEFT, padx=(8, 0))
        ToolTip(year_entry, "Format: '2025-2026' şeklinde yazın. Bu bilgi kimlik kartlarında görünecek.")

    def on_school_name_change(self, event=None):
        """Okul adı değiştiğinde çağrılır"""
        self.school_name = self.school_name_var.get().strip()
        # Boyutlandırma buton durumunu güncelle
        self.update_crop_resize_button_state()
        # Watermark metnini güncelle
        if hasattr(self, 'watermark_text_var') and not self.watermark_text_var.get():
            self.watermark_text_var.set(self.school_name)

    def on_sizing_naming_change(self):
        """Boyutlandırma adlandırma seçeneği değiştiğinde çağrılır"""
        self.update_crop_resize_button_state()

    def update_crop_resize_button_state(self):
        """Boyutlandırma butonunun durumunu güncelle"""
        if not hasattr(self, 'crop_resize_button'):
            return

        # Boyutlandırma aktif değilse buton pasif
        if not self.sizing_enabled.get():
            self.crop_resize_button.config(state="disabled")
            return

        # Fotoğraf dizini seçilmeli
        if not self.photo_directory:
            self.crop_resize_button.config(state="disabled")
            return

        # Adlandırma seçeneği aktifse okul adı ve excel gerekli
        if self.sizing_with_naming.get():
            if not self.school_name or not self.excel_data:
                self.crop_resize_button.config(state="disabled")
                return

            # Sütun seçimi de gerekli
            selected_columns = self.get_selected_columns()
            if not selected_columns:
                self.crop_resize_button.config(state="disabled")
                return
        else:
            # Adlandırma yapılmayacaksa sadece okul adı yeterli
            if not self.school_name:
                self.crop_resize_button.config(state="disabled")
                return

        # Tüm koşullar sağlanmışsa aktif et
        self.crop_resize_button.config(state="normal")

    def update_all_button_states(self):
        """Tüm buton durumlarını güncelle"""
        # Adlandırma butonu - Kontrol Et çalıştırıldıktan sonra aktif olur
        rename_ready = (self.school_name and self.excel_data and self.photo_directory and 
                       self.get_selected_columns())
        
        # PDF ve kimlik kartı butonları - Adlandırma yapıldıktan sonra aktif olur
        # Bu kontrol check_counts fonksiyonunda yapılıyor
        
        # Boyutlandırma butonunu güncelle
        self.update_crop_resize_button_state()

    def on_size_selection_change(self, event=None):
        """Boyut seçimi değiştiğinde çağrılır"""
        selected_display = self.size_combo.get()
        selected_value = self.size_display_values.get(selected_display, "e_okul")

        if selected_value == "custom":
            self.custom_size_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.custom_size_frame.pack_forget()

    def create_excel_card(self):
        """Excel dosyası seçim kartı"""
        card_frame = tk.Frame(self.scrollable_frame, 
                             bg=ModernUI.COLORS['card_bg'],
                             relief='solid',
                             bd=1)
        card_frame.pack(fill=tk.X, pady=(0, 8), padx=5, ipady=6, ipadx=8)

        # Başlık
        self.create_card_header(card_frame, "2", "Excel Dosyası", 
                               "Öğrenci verilerini içeren Excel dosyasını seçin")

        # Dosya seçim alanı - tek satır
        file_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        file_frame.pack(fill=tk.X, pady=(8, 0))

        excel_button = ttk.Button(file_frame,
                                 text="📁 Seç",
                                 command=self.select_excel_file,
                                 style='Primary.TButton')
        excel_button.pack(side=tk.LEFT, padx=(0, 8))
        ToolTip(excel_button, "Öğrenci bilgilerini içeren Excel dosyasını seçin (.xlsx veya .xls)")

        self.excel_path_var = tk.StringVar()
        self.excel_entry = ttk.Entry(file_frame,
                               textvariable=self.excel_path_var,
                               font=ModernUI.FONTS['body'],
                               state="readonly",
                               width=30)
        self.excel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ToolTip(self.excel_entry, "Seçilen Excel dosyasının yolu burada görünecek")

    def create_photo_card(self):
        """Fotoğraf dizini seçim kartı"""
        card_frame = tk.Frame(self.scrollable_frame, 
                             bg=ModernUI.COLORS['card_bg'],
                             relief='solid',
                             bd=1)
        card_frame.pack(fill=tk.X, pady=(0, 8), padx=5, ipady=6, ipadx=8)

        # Başlık
        self.create_card_header(card_frame, "3", "Fotoğraf Klasörü", 
                               "Adlandırılacak fotoğrafların bulunduğu klasörü seçin")

        # Dizin seçim alanı - tek satır
        dir_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        dir_frame.pack(fill=tk.X, pady=(8, 0))

        photo_button = ttk.Button(dir_frame,
                                 text="📂 Seç",
                                 command=self.select_photo_directory,
                                 style='Primary.TButton')
        photo_button.pack(side=tk.LEFT, padx=(0, 8))
        ToolTip(photo_button, "Adlandırılacak fotoğrafların bulunduğu klasörü seçin")

        self.photo_dir_var = tk.StringVar()
        self.photo_entry = ttk.Entry(dir_frame,
                               textvariable=self.photo_dir_var,
                               font=ModernUI.FONTS['body'],
                               state="readonly",
                               width=30)
        self.photo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ToolTip(self.photo_entry, "Seçilen fotoğraf klasörünün yolu burada görünecek")

    def create_advanced_naming_card(self):
        """İşlem ayarları kartı"""
        card_frame = tk.Frame(self.scrollable_frame, 
                             bg=ModernUI.COLORS['card_bg'],
                             relief='solid',
                             bd=1)
        card_frame.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10, ipadx=10)

        # Başlık
        self.create_card_header(card_frame, "4", "Adlandırma Ayarları", 
                               "Fotoğraf adlandırma için kullanılacak sütunları seçin")

        # Adlandırma seçenekleri
        naming_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        naming_frame.pack(fill=tk.X, pady=(8, 0))

        # Tek sütun seçimi
        single_frame = tk.Frame(naming_frame, bg=ModernUI.COLORS['card_bg'])
        single_frame.pack(fill=tk.X, pady=(0, 8))

        self.naming_type = tk.StringVar(value="single")
        single_radio = tk.Radiobutton(single_frame,
                                     text="Tek sütun kullan:",
                                     variable=self.naming_type,
                                     value="single",
                                     bg=ModernUI.COLORS['card_bg'],
                                     font=ModernUI.FONTS['body'],
                                     command=self.update_naming_options)
        single_radio.pack(side=tk.LEFT)
        ToolTip(single_radio, "Fotoğraf adlandırma için tek bir Excel sütunu kullanın (Örnek: Sadece 'Ad_Soyad')")

        self.column_var = tk.StringVar()
        self.column_combo = ttk.Combobox(single_frame,
                                        textvariable=self.column_var,
                                        font=ModernUI.FONTS['body'],
                                        width=25,
                                        state="readonly")
        self.column_combo.pack(side=tk.LEFT, padx=(8, 0))
        ToolTip(self.column_combo, "Excel'den hangi sütunun dosya adı olarak kullanılacağını seçin")

        # Çoklu sütun seçimi
        multi_frame = tk.Frame(naming_frame, bg=ModernUI.COLORS['card_bg'])
        multi_frame.pack(fill=tk.X, pady=(0, 5))

        multi_radio = tk.Radiobutton(multi_frame,
                                    text="Çoklu sütun kullan (birleştirilmiş):",
                                    variable=self.naming_type,
                                    value="multiple",
                                    bg=ModernUI.COLORS['card_bg'],
                                    font=ModernUI.FONTS['body'],
                                    command=self.update_naming_options)
        multi_radio.pack(side=tk.LEFT)
        ToolTip(multi_radio, "Birden fazla Excel sütununu birleştirerek dosya adı oluşturun (Örnek: 'Ad'+'Soyad'+'Sınıf')")

        # Çoklu sütun seçim alanı (hemen altta, kompakt tasarım)
        self.multi_columns_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        self.multi_columns_frame.pack(fill=tk.X, pady=(0, 8))
        self.multi_columns_frame.pack_forget()  # Başlangıçta gizli

        # Ayraç seçimi
        separator_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        separator_frame.pack(fill=tk.X, pady=(0, 8))

        separator_label = tk.Label(separator_frame,
                                  text="Sütunlar arası ayraç:",
                                  font=ModernUI.FONTS['body'],
                                  bg=ModernUI.COLORS['card_bg'])
        separator_label.pack(side=tk.LEFT)
        ToolTip(separator_label, "Çoklu sütun kullanırken sütunlar arasında hangi karakter kullanılacak")

        self.separator_var = tk.StringVar(value="_")
        separator_combo = ttk.Combobox(separator_frame,
                                      textvariable=self.separator_var,
                                      values=["_", "-", " ", "."],
                                      font=ModernUI.FONTS['body'],
                                      width=5,
                                      state="readonly")
        separator_combo.pack(side=tk.LEFT, padx=(8, 0))
        ToolTip(separator_combo, "Seçim: '_' = alt çizgi, '-' = tire, ' ' = boşluk, '.' = nokta")

        # Sınıf bazında organizasyon
        org_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        org_frame.pack(fill=tk.X, pady=(5, 0))

        self.organize_by_class = tk.BooleanVar()
        class_checkbox = tk.Checkbutton(org_frame,
                                       text="Fotoğrafları sınıflara göre ayrı klasörlere kopyala",
                                       variable=self.organize_by_class,
                                       bg=ModernUI.COLORS['card_bg'],
                                       font=ModernUI.FONTS['body'])
        class_checkbox.pack(side=tk.LEFT)
        ToolTip(class_checkbox, "İşaretlenirse: Adlandırılmış fotoğraflar ayrıca sınıf bazında ayrı klasörlere de kopyalanır")

    def create_photo_processing_card(self):
        """Fotoğraf işleme ayarları kartı"""
        card_frame = tk.Frame(self.scrollable_frame, 
                             bg=ModernUI.COLORS['card_bg'],
                             relief='solid',
                             bd=1)
        card_frame.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=8, ipadx=10)

        # Başlık
        self.create_card_header(card_frame, "5", "Fotoğraf İşleme Ayarları", 
                               "Boyutlandırma, kırpma ve watermark ayarları")

        # İçerik container
        content_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        content_frame.pack(fill=tk.X, pady=(10, 5))

        # Boyutlandırma ayarları
        sizing_frame = tk.LabelFrame(content_frame, 
                                   text="✂️ Fotoğraf Boyutlandırma",
                                   bg=ModernUI.COLORS['card_bg'],
                                   font=ModernUI.FONTS['body'])
        sizing_frame.pack(fill=tk.X, pady=(0, 8))

        # Boyutlandırma aktif/pasif
        sizing_enable_row = tk.Frame(sizing_frame, bg=ModernUI.COLORS['card_bg'])
        sizing_enable_row.pack(fill=tk.X, padx=8, pady=5)

        self.sizing_enabled = tk.BooleanVar()
        sizing_checkbox = tk.Checkbutton(sizing_enable_row,
                                       text="🔧 Fotoğrafları boyutlandır ve kırp",
                                       variable=self.sizing_enabled,
                                       command=self.toggle_sizing_options,
                                       bg=ModernUI.COLORS['card_bg'],
                                       font=ModernUI.FONTS['body'])
        sizing_checkbox.pack(side=tk.LEFT)
        ToolTip(sizing_checkbox, "Fotoğrafları belirli boyutlara kırpıp yeniden boyutlandırır (E-Okul, vesikalık vb.)")

        # Boyutlandırma seçenekleri frame
        self.sizing_options_frame = tk.Frame(sizing_frame, bg=ModernUI.COLORS['card_bg'])
        self.sizing_options_frame.pack(fill=tk.X, padx=8, pady=5)

        # Boyut seçimi
        size_selection_row = tk.Frame(self.sizing_options_frame, bg=ModernUI.COLORS['card_bg'])
        size_selection_row.pack(fill=tk.X, pady=(0, 8))

        tk.Label(size_selection_row, text="📏 Fotoğraf Boyutu:", 
                bg=ModernUI.COLORS['card_bg'], font=ModernUI.FONTS['body'],
                width=18, anchor='w').pack(side=tk.LEFT)

        self.size_type = tk.StringVar(value="e_okul")
        size_options = [
            ("35mm x 45mm (E-Okul) - 20-150 KB", "e_okul"),
            ("394px x 512px (Açık Lise) - Max 150 KB", "acik_lise"),
            ("394px x 512px (MEBBIS) - Max 150 KB", "mebbis"),
            ("50mm x 60mm (Biyometrik)", "biometric"),
            ("45mm x 60mm (Vesikalık)", "vesikalik"),
            ("35mm x 35mm (Pasaport/Vize)", "passport"),
            ("25mm x 35mm (Ehliyet)", "license"),
            ("Özel boyut", "custom")
        ]

        self.size_combo = ttk.Combobox(size_selection_row,
                                      textvariable=self.size_type,
                                      values=[option[0] for option in size_options],
                                      font=ModernUI.FONTS['body'],
                                      width=30,
                                      state="readonly")

        # Combobox değerlerini görünen metinlerle eşle
        self.size_display_values = {option[0]: option[1] for option in size_options}
        self.size_value_to_display = {option[1]: option[0] for option in size_options}
        self.size_combo.bind('<<ComboboxSelected>>', self.on_size_selection_change)

        # İlk değeri ayarla
        self.size_combo.set("35mm x 45mm (E-Okul) - 20-150 KB")
        self.size_combo.pack(side=tk.LEFT, padx=(5, 0))
        ToolTip(self.size_combo, "Fotoğrafların kırpılacağı boyutu seçin:\n• E-Okul: 35x45mm, max 150KB\n• Açık Lise: 394x512px, 400DPI\n• Vesikalık: 45x60mm\n• Özel boyut: Kendi boyutunuzu belirleyin")

        # Özel boyut girişi (başlangıçta gizli)
        self.custom_size_frame = tk.Frame(self.sizing_options_frame, bg=ModernUI.COLORS['card_bg'])
        self.custom_size_frame.pack(fill=tk.X, pady=(5, 0))

        # Boyut girişi bölümü
        size_input_row = tk.Frame(self.custom_size_frame, bg=ModernUI.COLORS['card_bg'])
        size_input_row.pack(fill=tk.X, pady=(0, 5))

        tk.Label(size_input_row, text="📐 Özel boyut:", bg=ModernUI.COLORS['card_bg'], 
                font=ModernUI.FONTS['body'], width=18, anchor='w').pack(side=tk.LEFT)

        size_inputs_frame = tk.Frame(size_input_row, bg=ModernUI.COLORS['card_bg'])
        size_inputs_frame.pack(side=tk.LEFT, padx=(5, 0))

        tk.Label(size_inputs_frame, text="Genişlik:", bg=ModernUI.COLORS['card_bg'], 
                font=ModernUI.FONTS['body']).pack(side=tk.LEFT)
        self.custom_width_var = tk.StringVar(value="35")
        tk.Entry(size_inputs_frame, textvariable=self.custom_width_var, 
                font=ModernUI.FONTS['body'], width=6).pack(side=tk.LEFT, padx=(5, 8))

        tk.Label(size_inputs_frame, text="Yükseklik:", bg=ModernUI.COLORS['card_bg'], 
                font=ModernUI.FONTS['body']).pack(side=tk.LEFT)
        self.custom_height_var = tk.StringVar(value="45")
        tk.Entry(size_inputs_frame, textvariable=self.custom_height_var, 
                font=ModernUI.FONTS['body'], width=6).pack(side=tk.LEFT, padx=(5, 8))

        # Ölçü birimi seçimi
        self.custom_unit_var = tk.StringVar(value="mm")
        unit_combo = ttk.Combobox(size_inputs_frame,
                                 textvariable=self.custom_unit_var,
                                 values=["mm", "cm", "px"],
                                 font=ModernUI.FONTS['body'],
                                 width=5,
                                 state="readonly")
        unit_combo.pack(side=tk.LEFT, padx=(5, 0))

        # DPI ve dosya boyutu
        advanced_row = tk.Frame(self.custom_size_frame, bg=ModernUI.COLORS['card_bg'])
        advanced_row.pack(fill=tk.X, pady=(5, 0))

        tk.Label(advanced_row, text="⚙️ Gelişmiş:", bg=ModernUI.COLORS['card_bg'], 
                font=ModernUI.FONTS['body'], width=18, anchor='w').pack(side=tk.LEFT)

        advanced_inputs_frame = tk.Frame(advanced_row, bg=ModernUI.COLORS['card_bg'])
        advanced_inputs_frame.pack(side=tk.LEFT, padx=(5, 0))

        tk.Label(advanced_inputs_frame, text="DPI:", bg=ModernUI.COLORS['card_bg'], 
                font=ModernUI.FONTS['body']).pack(side=tk.LEFT)
        self.custom_dpi_var = tk.StringVar(value="300")
        tk.Entry(advanced_inputs_frame, textvariable=self.custom_dpi_var, 
                font=ModernUI.FONTS['body'], width=6).pack(side=tk.LEFT, padx=(5, 15))

        tk.Label(advanced_inputs_frame, text="Max KB:", bg=ModernUI.COLORS['card_bg'], 
                font=ModernUI.FONTS['body']).pack(side=tk.LEFT)
        self.custom_max_size_var = tk.StringVar(value="")
        tk.Entry(advanced_inputs_frame, textvariable=self.custom_max_size_var, 
                font=ModernUI.FONTS['body'], width=6).pack(side=tk.LEFT, padx=(5, 5))
        tk.Label(advanced_inputs_frame, text="(boş=sınırsız)", bg=ModernUI.COLORS['card_bg'], 
                font=ModernUI.FONTS['small']).pack(side=tk.LEFT)

        # Başlangıçta özel boyut frame'ini gizle
        self.custom_size_frame.pack_forget()

        # Adlandırma seçeneği (boyutlandırma için)
        naming_row = tk.Frame(self.sizing_options_frame, bg=ModernUI.COLORS['card_bg'])
        naming_row.pack(fill=tk.X, pady=(8, 5))

        self.sizing_with_naming = tk.BooleanVar(value=False)
        naming_checkbox = tk.Checkbutton(naming_row,
                                       text="📝 Boyutlandırma sırasında fotoğrafları yeniden adlandır",
                                       variable=self.sizing_with_naming,
                                       command=self.on_sizing_naming_change,
                                       bg=ModernUI.COLORS['card_bg'],
                                       font=ModernUI.FONTS['body'])
        naming_checkbox.pack(side=tk.LEFT)

        # Boyutlandırma seçeneklerini varsayılan olarak gizle
        self.sizing_enabled.set(False)  # Başlangıçta pasif olsun
        self.sizing_options_frame.pack_forget()  # Başlangıçta gizli

        # Watermark ayarları
        watermark_frame = tk.LabelFrame(content_frame, 
                                       text="🏷️ Watermark Ayarları",
                                       bg=ModernUI.COLORS['card_bg'],
                                       font=ModernUI.FONTS['body'])
        watermark_frame.pack(fill=tk.X, pady=(0, 0))

        # Watermark aktif/pasif
        watermark_enable_row = tk.Frame(watermark_frame, bg=ModernUI.COLORS['card_bg'])
        watermark_enable_row.pack(fill=tk.X, padx=8, pady=5)

        self.watermark_enabled = tk.BooleanVar()
        watermark_checkbox = tk.Checkbutton(watermark_enable_row,
                                          text="✨ Fotoğraflara watermark ekle",
                                          variable=self.watermark_enabled,
                                          command=self.toggle_watermark_options,
                                          bg=ModernUI.COLORS['card_bg'],
                                          font=ModernUI.FONTS['body'])
        watermark_checkbox.pack(side=tk.LEFT)
        ToolTip(watermark_checkbox, "Fotoğrafların sağ alt köşesine okul adı veya özel metin ekler")
        
        # PNG uyarı etiketi - ayrı satırda
        png_watermark_row = tk.Frame(watermark_frame, bg=ModernUI.COLORS['card_bg'])
        png_watermark_row.pack(fill=tk.X, padx=8, pady=(5, 0))
        
        png_watermark_label = tk.Label(png_watermark_row,
                                     text="💡 JPG formatında daha iyi sonuç alırsınız",
                                     font=ModernUI.FONTS['small'],
                                     fg=ModernUI.COLORS['text_light'],
                                     bg=ModernUI.COLORS['card_bg'])
        png_watermark_label.pack(anchor='w')

        # Watermark seçenekleri frame
        self.watermark_options_frame = tk.Frame(watermark_frame, bg=ModernUI.COLORS['card_bg'])
        self.watermark_options_frame.pack(fill=tk.X, padx=8, pady=5)

        self.watermark_type = tk.StringVar(value="text")

        # Metin girişi
        self.text_frame = tk.Frame(self.watermark_options_frame, bg=ModernUI.COLORS['card_bg'])
        self.text_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(self.text_frame, text="💬 Watermark Metni:", bg=ModernUI.COLORS['card_bg'], 
                font=ModernUI.FONTS['body'], width=18, anchor='w').pack(side=tk.LEFT)
        self.watermark_text_var = tk.StringVar(value=self.school_name if hasattr(self, 'school_name') else "")
        self.watermark_text_entry = tk.Entry(self.text_frame, textvariable=self.watermark_text_var, 
                                            font=ModernUI.FONTS['body'])
        self.watermark_text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        ToolTip(self.watermark_text_entry, "Fotoğraflara eklenecek yazıyı girin. Genellikle okul adı kullanılır.")

        # Logo seçimi (kimlik kartları için)
        self.logo_frame = tk.Frame(self.watermark_options_frame, bg=ModernUI.COLORS['card_bg'])
        self.logo_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(self.logo_frame, text="🖼️ Okul Logosu:", bg=ModernUI.COLORS['card_bg'], 
                font=ModernUI.FONTS['body'], width=18, anchor='w').pack(side=tk.LEFT)

        self.logo_path_var = tk.StringVar()
        self.logo_entry = tk.Entry(self.logo_frame,
                               textvariable=self.logo_path_var, font=ModernUI.FONTS['body'], 
                               state="readonly")
        self.logo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 8))

        logo_button = ttk.Button(self.logo_frame, text="Logo Seç", 
                               command=self.select_school_logo, style='Primary.TButton')
        logo_button.pack(side=tk.LEFT)

        # Watermark seçeneklerini varsayılan olarak gizle
        self.watermark_enabled.set(False)  # Başlangıçta pasif olsun
        self.watermark_options_frame.pack_forget()  # Başlangıçta gizli

        self.column_checkboxes = {}
        self.column_order = []  # Sütun sırası için

    def create_action_card(self):
        """İşlem butonları kartı"""
        card_frame = tk.Frame(self.scrollable_frame, 
                             bg=ModernUI.COLORS['card_bg'],
                             relief='solid',
                             bd=1)
        card_frame.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10, ipadx=10)

        # Başlık
        self.create_card_header(card_frame, "6", "İşlemler", 
                               "Fotoğraf adlandırma ve PDF oluşturma işlemlerini başlatın")

        # PNG bilgi metni (başlık altında)
        info_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        info_frame.pack(fill=tk.X, pady=(8, 0))

        png_info_label = tk.Label(info_frame,
                                 text="💡 En iyi sonuç için JPG formatındaki dosyaları kullanın",
                                 font=ModernUI.FONTS['small'],
                                 fg=ModernUI.COLORS['text_light'],
                                 bg=ModernUI.COLORS['card_bg'])
        png_info_label.pack(anchor='w')

        # İptal butonu container (en üstte, merkezi)
        self.cancel_container = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        self.cancel_container.pack(fill=tk.X, pady=(8, 0))

        # İptal butonu (başlangıçta gizli)
        self.cancel_button = ttk.Button(self.cancel_container,
                                       text="⏹️ İşlemi Durdur",
                                       command=self.cancel_operation,
                                       style='Danger.TButton')
        self.cancel_button.pack(pady=(0, 8))
        self.cancel_container.pack_forget()

        # Buton listesi (tek sütun düzen)
        button_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        button_frame.pack(fill=tk.X, pady=(8, 0))

        # Kontrol butonu
        check_button = ttk.Button(button_frame,
                                 text="🔍 Kontrol Et",
                                 command=self.handle_check_button_click,
                                 style='Primary.TButton')
        check_button.pack(fill=tk.X, pady=(0, 4))
        ToolTip(check_button, "Excel ve fotoğraf sayılarını kontrol eder. İşlem öncesi mutlaka çalıştırın!")

        # Adlandırma butonu
        self.rename_button = ttk.Button(button_frame,
                                       text="✨ Fotoğrafları Adlandır",
                                       command=self.handle_rename_button_click,
                                       state="disabled",
                                       style='Success.TButton')
        self.rename_button.pack(fill=tk.X, pady=(0, 4))
        ToolTip(self.rename_button, "Fotoğrafları Excel verilerine göre yeniden adlandırır. Önce 'Kontrol Et' çalıştırın.")

        # Boyutlandırma butonu
        self.crop_resize_button = ttk.Button(button_frame,
                                           text="✂️ Fotoğrafları Kırp ve Boyutlandır",
                                           command=self.handle_crop_resize_button_click,
                                           state="disabled",
                                           style='Success.TButton')
        self.crop_resize_button.pack(fill=tk.X, pady=(0, 4))
        ToolTip(self.crop_resize_button, "Fotoğrafları seçilen boyutlara kırpar ve yeniden boyutlandırır (E-Okul, vesikalık vb.)")

        # PDF butonu
        self.pdf_button = ttk.Button(button_frame,
                                    text="📄 Sınıf PDF'lerini Oluştur",
                                    command=self.handle_pdf_button_click,
                                    state="disabled",
                                    style='Warning.TButton')
        self.pdf_button.pack(fill=tk.X, pady=(0, 4))
        ToolTip(self.pdf_button, "Her sınıf için fotoğraf listesi PDF'i oluşturur. Önce fotoğrafları adlandırın.")

        # Kimlik kartı butonu
        self.id_card_button = ttk.Button(button_frame,
                                        text="🆔 Kimlik Kartları Oluştur",
                                        command=self.handle_id_card_button_click,
                                        state="disabled",
                                        style='Warning.TButton')
        self.id_card_button.pack(fill=tk.X, pady=(0, 0))
        ToolTip(self.id_card_button, "Öğrenci kimlik kartları oluşturur. Önce fotoğrafları adlandırın.")

    def create_progress_card(self):
        """İlerleme kartı - Renkli durum göstergeleri ile"""
        card_frame = tk.Frame(self.right_panel, 
                             bg=ModernUI.COLORS['card_bg'],
                             relief='solid',
                             bd=1)
        card_frame.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=8, ipadx=10)

        # Başlık bölümü
        title_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        title_frame.pack(fill=tk.X, pady=(0, 10))

        # Başlık ikonu ve metin
        title_icon = tk.Label(title_frame,
                             text="📊",
                             font=('Segoe UI', 14),
                             bg=ModernUI.COLORS['card_bg'])
        title_icon.pack(side=tk.LEFT, padx=(0, 8))

        progress_title = tk.Label(title_frame,
                                 text="İlerleme Durumu",
                                 font=ModernUI.FONTS['subtitle'],
                                 fg=ModernUI.COLORS['text'],
                                 bg=ModernUI.COLORS['card_bg'])
        progress_title.pack(side=tk.LEFT)

        # Durum ikonu (dinamik)
        self.progress_status_icon = tk.Label(title_frame,
                                           text="🟢",
                                           font=('Segoe UI', 12),
                                           bg=ModernUI.COLORS['card_bg'])
        self.progress_status_icon.pack(side=tk.RIGHT)

        # İlerleme çubuğu bölümü
        progress_section = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        progress_section.pack(fill=tk.X, pady=(0, 3))

        # İlerleme çubuğu
        self.progress = ttk.Progressbar(progress_section,
                                       mode='determinate',
                                       length=300,
                                       style='Custom.Horizontal.TProgressbar')
        self.progress.pack(fill=tk.X)

        # Yüzde göstergesi - daha belirgin
        self.progress_percent = tk.Label(progress_section,
                                        text="0%",
                                        font=('Segoe UI', 10, 'bold'),
                                        fg=ModernUI.COLORS['success'],
                                        bg=ModernUI.COLORS['card_bg'])
        self.progress_percent.pack(pady=(2, 0))

        # Durum detay bölümü - kompakt
        status_section = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        status_section.pack(fill=tk.X, pady=(1, 0))

        # Ana durum label
        self.status_label = tk.Label(status_section,
                                    text="🚀 Hazır - İşlem bekliyor",
                                    font=('Segoe UI', 11, 'bold'),
                                    fg=ModernUI.COLORS['secondary'],
                                    bg=ModernUI.COLORS['card_bg'])
        self.status_label.pack(anchor='w', pady=(0, 0))

        # Detay durum label (opsiyonel) - daha kompakt
        self.status_detail = tk.Label(status_section,
                                     text="",
                                     font=('Segoe UI', 9, 'bold'),
                                     fg=ModernUI.COLORS['text_light'],
                                     bg=ModernUI.COLORS['card_bg'])
        self.status_detail.pack(anchor='w', pady=(0, 0))

        # Progress bar stilini özelleştir
        self.setup_progress_style()

    def create_results_card(self):
        """Sonuçlar kartı"""
        card_frame = tk.Frame(self.right_panel, 
                             bg=ModernUI.COLORS['card_bg'],
                             relief='solid',
                             bd=1)
        card_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5, ipady=10, ipadx=10)

        # Başlık
        results_title = tk.Label(card_frame,
                                text="📋 İşlem Geçmişi",
                                font=ModernUI.FONTS['subtitle'],
                                fg=ModernUI.COLORS['text'],
                                bg=ModernUI.COLORS['card_bg'])
        results_title.pack(anchor='w', pady=(0, 8))

        # Log alanı
        text_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        text_frame.pack(fill=tk.BOTH, expand=True)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.status_text = tk.Text(text_frame,
                                  wrap=tk.WORD,
                                  font=('Consolas', 9),
                                  bg=ModernUI.COLORS['light'],
                                  fg=ModernUI.COLORS['text'],
                                  relief='sunken',
                                  bd=1,
                                  padx=8,
                                  pady=8)

        status_scrollbar = ttk.Scrollbar(text_frame,
                                        orient="vertical",
                                        command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)

        self.status_text.grid(row=0, column=0, sticky="nsew")
        status_scrollbar.grid(row=0, column=1, sticky="ns")

        # İlk mesaj
        self.log_message("🚀 VesiKolay Pro başlatıldı.")
        self.log_message("📋 Adımları takip ederek Excel dosyası ve fotoğraf dizini seçin.")

    def create_file_access_card(self):
        """Dosya erişim kartı"""
        card_frame = tk.Frame(self.right_panel, 
                             bg=ModernUI.COLORS['card_bg'],
                             relief='solid',
                             bd=1)
        card_frame.pack(fill=tk.X, pady=(0, 0), padx=5, ipady=10, ipadx=10)

        # Başlık
        access_title = tk.Label(card_frame,
                               text="🗂️ Dosya Erişimi",
                               font=ModernUI.FONTS['subtitle'],
                               fg=ModernUI.COLORS['text'],
                               bg=ModernUI.COLORS['card_bg'])
        access_title.pack(anchor='w', pady=(0, 8))

        # Butonlar
        access_frame = tk.Frame(card_frame, bg=ModernUI.COLORS['card_bg'])
        access_frame.pack(fill=tk.X)

        self.output_access_button = ttk.Button(access_frame,
                                              text="📁 Çıktı Klasörü",
                                              command=self.open_output_directory,
                                              state="disabled",
                                              style='Warning.TButton')
        self.output_access_button.pack(side=tk.LEFT, padx=(0, 8))
        ToolTip(self.output_access_button, "Ana çıktı klasörünü açar. İşlem sonrası adlandırılmış fotoğrafları görebilirsiniz.")

        self.pdf_access_button = ttk.Button(access_frame,
                                           text="📄 PDF Klasörü",
                                           command=self.open_pdf_directory,
                                           state="disabled",
                                           style='Warning.TButton')
        self.pdf_access_button.pack(side=tk.LEFT, padx=(0, 8))
        ToolTip(self.pdf_access_button, "Oluşturulan sınıf PDF'lerinin bulunduğu klasörü açar.")

        # Kimlik kartları erişim butonu
        self.id_cards_access_button = ttk.Button(access_frame,
                                                text="🆔 Kimlik Kartları",
                                                command=self.open_id_cards_directory,
                                                state="disabled",
                                                style='Warning.TButton')
        self.id_cards_access_button.pack(side=tk.LEFT)
        ToolTip(self.id_cards_access_button, "Oluşturulan kimlik kartı PDF'lerinin bulunduğu klasörü açar.")

    def create_card_header(self, parent, step_num, title, description):
        """Kart başlığı oluştur - Dinamik durum ikonları ile"""
        header_frame = tk.Frame(parent, bg=ModernUI.COLORS['card_bg'])
        header_frame.pack(fill=tk.X, pady=(0, 8))

        # Sol taraf - Adım numarası ve durum
        left_section = tk.Frame(header_frame, bg=ModernUI.COLORS['card_bg'])
        left_section.pack(side=tk.LEFT, padx=(0, 12))

        # Adım numarası - daha modern circular tasarım
        step_label = tk.Label(left_section,
                             text=step_num,
                             font=('Segoe UI', 12, 'bold'),
                             fg=ModernUI.COLORS['white'],
                             bg=ModernUI.COLORS['secondary'],
                             width=3, height=1,
                             relief='flat')
        step_label.pack()

        # Durum ikonu - dinamik
        status_icon = self.get_step_status_icon(step_num)
        self.step_status_icons = getattr(self, 'step_status_icons', {})
        
        status_label = tk.Label(left_section,
                               text=status_icon,
                               font=('Segoe UI', 14),
                               bg=ModernUI.COLORS['card_bg'])
        status_label.pack(pady=(2, 0))
        
        # İkonu kaydet (daha sonra güncellemek için)
        self.step_status_icons[step_num] = status_label

        # Sağ taraf - Başlık ve açıklama
        text_frame = tk.Frame(header_frame, bg=ModernUI.COLORS['card_bg'])
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Başlık - ikon ile birlikte
        title_container = tk.Frame(text_frame, bg=ModernUI.COLORS['card_bg'])
        title_container.pack(anchor='w', fill=tk.X)

        # Küçük dekoratif ikon
        deco_icon = tk.Label(title_container,
                            text="🔹",
                            font=('Segoe UI', 10),
                            fg=ModernUI.COLORS['secondary'],
                            bg=ModernUI.COLORS['card_bg'])
        deco_icon.pack(side=tk.LEFT, padx=(0, 5))

        title_label = tk.Label(title_container,
                              text=title,
                              font=ModernUI.FONTS['subtitle'],
                              fg=ModernUI.COLORS['text'],
                              bg=ModernUI.COLORS['card_bg'])
        title_label.pack(side=tk.LEFT)

        # Açıklama
        desc_label = tk.Label(text_frame,
                             text=description,
                             font=ModernUI.FONTS['small'],
                             fg=ModernUI.COLORS['text_light'],
                             bg=ModernUI.COLORS['card_bg'])
        desc_label.pack(anchor='w', padx=(15, 0))

    def get_step_status_icon(self, step_num):
        """Adım durumuna göre ikon döndür"""
        # Başlangıçta tüm adımlar beklemede
        status_icons = {
            "pending": "⏳",      # Beklemede
            "active": "🟢",      # Aktif/Hazır
            "warning": "🟡",     # Uyarı
            "error": "🔴",       # Hata
            "completed": "✅"    # Tamamlandı
        }
        return status_icons["pending"]

    def update_step_status(self, step_num, status):
        """Adım durumunu güncelle"""
        if not hasattr(self, 'step_status_icons'):
            return
            
        if step_num in self.step_status_icons:
            status_icons = {
                "pending": "⏳",
                "active": "🟢", 
                "warning": "🟡",
                "error": "🔴",
                "completed": "✅"
            }
            
            if status in status_icons:
                self.step_status_icons[step_num].config(text=status_icons[status])

    def update_naming_options(self):
        """Adlandırma seçeneklerine göre UI'ı güncelle"""
        if self.naming_type.get() == "multiple":
            # Çoklu sütun frame'ini hemen seçenekten sonra göster
            self.multi_columns_frame.pack(fill=tk.X, pady=(5, 8), after=self.multi_columns_frame.master.children[list(self.multi_columns_frame.master.children.keys())[1]])
            self.update_column_ordering_interface()
        else:
            self.multi_columns_frame.pack_forget()
        # Boyutlandırma buton durumunu güncelle
        self.update_crop_resize_button_state()

    def update_column_ordering_interface(self):
        """Sütun sıralama arayüzünü güncelle - Kompakt ve modern tasarım"""
        # Önce tüm widget'ları temizle
        for widget in self.multi_columns_frame.winfo_children():
            widget.destroy()

        if not self.available_columns:
            no_data_label = tk.Label(self.multi_columns_frame,
                                    text="📋 Excel dosyası yüklendiğinde sütunlar burada görünecek",
                                    font=ModernUI.FONTS['small'],
                                    fg=ModernUI.COLORS['text_light'],
                                    bg=ModernUI.COLORS['card_bg'])
            no_data_label.pack(pady=8)
            return

        # Başlık
        title_label = tk.Label(self.multi_columns_frame,
                              text="📊 Kullanılacak Sütunları Seçin ve Sıralayın:",
                              font=ModernUI.FONTS['subtitle'],
                              fg=ModernUI.COLORS['text'],
                              bg=ModernUI.COLORS['card_bg'])
        title_label.pack(pady=(5, 8))

        # Ana container - daha kompakt
        main_container = tk.Frame(self.multi_columns_frame, bg=ModernUI.COLORS['card_bg'])
        main_container.pack(fill=tk.X, padx=8, pady=(0, 8))

        # Sol taraf - Mevcut sütunlar
        left_section = tk.Frame(main_container, bg=ModernUI.COLORS['card_bg'])
        left_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        tk.Label(left_section, text="Mevcut Sütunlar:", 
                font=ModernUI.FONTS['body'], fg=ModernUI.COLORS['text'], 
                bg=ModernUI.COLORS['card_bg']).pack(anchor='w')

        self.available_listbox = tk.Listbox(left_section, height=5, font=ModernUI.FONTS['small'],
                                           relief='solid', bd=1)
        for column in self.available_columns:
            self.available_listbox.insert(tk.END, column)
        self.available_listbox.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

        # Orta - Butonlar (dikey)
        button_section = tk.Frame(main_container, bg=ModernUI.COLORS['card_bg'])
        button_section.pack(side=tk.LEFT, padx=5)

        # Boşluk için
        tk.Label(button_section, text="", bg=ModernUI.COLORS['card_bg']).pack(pady=10)

        add_button = ttk.Button(button_section, text="→", width=3,
                               command=self.add_column_to_selection,
                               style='Primary.TButton')
        add_button.pack(pady=1)

        remove_button = ttk.Button(button_section, text="←", width=3,
                                  command=self.remove_column_from_selection,
                                  style='Warning.TButton')
        remove_button.pack(pady=1)

        tk.Frame(button_section, height=5, bg=ModernUI.COLORS['card_bg']).pack()

        up_button = ttk.Button(button_section, text="↑", width=3,
                              command=self.move_column_up,
                              style='Primary.TButton')
        up_button.pack(pady=1)

        down_button = ttk.Button(button_section, text="↓", width=3,
                                command=self.move_column_down,
                                style='Primary.TButton')
        down_button.pack(pady=1)

        # Sağ taraf - Seçili sütunlar
        right_section = tk.Frame(main_container, bg=ModernUI.COLORS['card_bg'])
        right_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        tk.Label(right_section, text="Seçili Sütunlar (Sıralı):", 
                font=ModernUI.FONTS['body'], fg=ModernUI.COLORS['text'], 
                bg=ModernUI.COLORS['card_bg']).pack(anchor='w')

        self.selected_listbox = tk.Listbox(right_section, height=5, font=ModernUI.FONTS['small'],
                                          relief='solid', bd=1)
        self.selected_listbox.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

    def get_selected_columns(self):
        """Seçili sütunları döndür"""
        if self.naming_type.get() == "single":
            selected_col = self.column_var.get()
            return [selected_col] if selected_col else []
        else:
            # Çoklu sütun seçiminde sıralı listeyi kullan
            if hasattr(self, 'column_order'):
                return self.column_order
            return []

    def log_message(self, message: str):
        """Durum metnine mesaj ekle"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, message: str, status_type: str = "info"):
        """Durum labelını güncelle - Renkli ikonlarla"""
        # Status ikonları
        status_icons = {
            "info": "ℹ️",
            "success": "✅", 
            "warning": "⚠️",
            "error": "❌",
            "processing": "⚙️",
            "waiting": "⏳"
        }
        
        # Status renkleri
        status_colors = {
            "info": ModernUI.COLORS['text'],
            "success": ModernUI.COLORS['success'],
            "warning": ModernUI.COLORS['warning'], 
            "error": ModernUI.COLORS['danger'],
            "processing": ModernUI.COLORS['secondary'],
            "waiting": ModernUI.COLORS['text_light']
        }
        
        icon = status_icons.get(status_type, "ℹ️")
        color = status_colors.get(status_type, ModernUI.COLORS['text'])
        
        self.status_label.config(text=f"{icon} {message}", fg=color)
        
        # Progress status ikonu güncelle
        if hasattr(self, 'progress_status_icon'):
            if status_type == "success":
                self.progress_status_icon.config(text="🟢")
            elif status_type == "warning":
                self.progress_status_icon.config(text="🟡")
            elif status_type == "error":
                self.progress_status_icon.config(text="🔴")
            elif status_type == "processing":
                self.progress_status_icon.config(text="🔄")
            else:
                self.progress_status_icon.config(text="🟢")
        
        self.root.update_idletasks()

    def update_progress_with_percentage(self, current, total):
        """İlerleme çubuğunu yüzde ile güncelle"""
        if total > 0:
            percentage = (current / total) * 100
            self.progress['value'] = current
            self.progress['maximum'] = total
            
            if hasattr(self, 'progress_percent'):
                # Yüzde gösterimi daha belirgin
                self.progress_percent.config(text=f"{percentage:.0f}%")
                
                # Renk değişimi - %100'de yeşil
                if percentage >= 100:
                    self.progress_percent.config(fg=ModernUI.COLORS['success'])
                elif percentage >= 50:
                    self.progress_percent.config(fg=ModernUI.COLORS['warning'])
                else:
                    self.progress_percent.config(fg=ModernUI.COLORS['secondary'])
                
            # Durum detayı güncelle
            if hasattr(self, 'status_detail'):
                self.status_detail.config(text=f"İşlenen: {current}/{total}")
        
        self.root.update_idletasks()

    def select_excel_file(self):
        """Excel dosyası seç"""
        file_path = filedialog.askopenfilename(
            title="Excel Dosyası Seçin",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )

        if file_path:
            self.excel_file_path = Path(file_path)
            self.excel_path_var.set(f"✅ {self.excel_file_path.name}")
            self.load_excel_data()

    def select_photo_directory(self):
        """Fotoğraf dizini seç"""
        directory = filedialog.askdirectory(title="Fotoğraf Dizini Seçin")

        if directory:
            self.photo_directory = Path(directory)
            self.photo_dir_var.set(f"✅ {self.photo_directory.name}")
            self.log_message(f"📂 Fotoğraf dizini seçildi: {self.photo_directory.name}")
            
            # PNG dosyalarının varlığını kontrol et
            png_files = list(self.photo_directory.glob("*.png"))
            if png_files:
                self.log_message(f"⚠️ PNG dosyaları tespit edildi: {len(png_files)} adet")
                self.log_message("📋 NOT: En iyi sonuç için JPG formatındaki dosyaları kullanın")
                messagebox.showinfo("PNG Dosyaları Tespit Edildi", 
                                   f"Dizinde {len(png_files)} adet PNG dosyası bulundu.\n\n"
                                   "⚠️ PNG dosyaları desteklenmektedir ancak en iyi sonuç için JPG formatındaki dosyaları kullanmanız önerilir.\n\n"
                                   "Boyutlandırma ve watermark işlemlerinde JPG formatı daha kararlı sonuçlar verir.")
            
            # Boyutlandırma buton durumunu güncelle
            self.update_crop_resize_button_state()

    def load_excel_data(self):
        """Excel verilerini yükle"""
        try:
            self.update_status("Excel dosyası okunuyor...")
            self.log_message(f"📊 Excel dosyası okunuyor: {self.excel_file_path.name}")

            # Excel dosyasını oku
            data_list, errors, available_columns = self.excel_reader.read_excel_flexible(self.excel_file_path)

            if data_list:
                self.excel_data = data_list
                self.available_columns = available_columns

                # Sütun seçeneklerini güncelle
                self.column_combo['values'] = available_columns
                if available_columns:
                    self.column_combo.set(available_columns[0])

                # Çoklu sütun seçeneklerini güncelle
                if self.naming_type.get() == "multiple":
                    self.update_column_ordering_interface()

                self.log_message(f"✅ Excel verisi başarıyla yüklendi: {len(data_list)} satır, {len(available_columns)} sütun")
                self.log_message(f"📋 Kullanılabilir sütunlar: {', '.join(available_columns[:5])}{'...' if len(available_columns) > 5 else ''}")
                self.update_status(f"Excel yüklendi: {len(data_list)} kayıt")
                # Tüm buton durumlarını güncelle
                self.update_crop_resize_button_state()
                self.update_all_button_states()
            else:
                self.log_message("❌ Excel dosyasından veri okunamadı.")
                self.update_status("Excel yükleme başarısız")

        except Exception as e:
            self.log_message(f"❌ Excel dosyası okuma hatası: {e}")
            self.update_status("Excel okuma hatası")

    def add_column_to_selection(self):
        """Seçili sütunu ekle"""
        selection = self.available_listbox.curselection()
        if selection:
            column = self.available_listbox.get(selection[0])
            if column not in [self.selected_listbox.get(i) for i in range(self.selected_listbox.size())]:
                self.selected_listbox.insert(tk.END, column)
                self.update_column_order()

    def remove_column_from_selection(self):
        """Seçili sütunu çıkar"""
        selection = self.selected_listbox.curselection()
        if selection:
            self.selected_listbox.delete(selection[0])
            self.update_column_order()

    def move_column_up(self):
        """Sütunu yukarı taşı"""
        selection = self.selected_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            column = self.selected_listbox.get(index)
            self.selected_listbox.delete(index)
            self.selected_listbox.insert(index - 1, column)
            self.selected_listbox.selection_set(index - 1)
            self.update_column_order()

    def move_column_down(self):
        """Sütunu aşağı taşı"""
        selection = self.selected_listbox.curselection()
        if selection and selection[0] < self.selected_listbox.size() - 1:
            index = selection[0]
            column = self.selected_listbox.get(index)
            self.selected_listbox.delete(index)
            self.selected_listbox.insert(index + 1, column)
            self.selected_listbox.selection_set(index + 1)
            self.update_column_order()

    def update_column_order(self):
        """Sütun sırasını güncelle"""
        self.column_order = [self.selected_listbox.get(i) for i in range(self.selected_listbox.size())]
        # Boyutlandırma buton durumunu güncelle
        self.update_crop_resize_button_state()

    def toggle_sizing_options(self):
        """Boyutlandırma seçeneklerini göster/gizle"""
        if self.sizing_enabled.get():
            self.sizing_options_frame.pack(fill=tk.X, padx=8, pady=5)
        else:
            self.sizing_options_frame.pack_forget()
        # Boyutlandırma buton durumunu güncelle
        self.update_crop_resize_button_state()

    def toggle_watermark_options(self):
        """Watermark seçeneklerini göster/gizle"""
        if self.watermark_enabled.get():
            self.watermark_options_frame.pack(fill=tk.X, padx=8, pady=5)
            self.update_watermark_type()
        else:
            self.watermark_options_frame.pack_forget()

    def update_watermark_type(self):
        """Watermark tipine göre arayüzü güncelle - sadece metin desteklenir"""
        # Watermark sadece metin olacak, logo seçeneğini kaldır
        self.text_frame.pack(fill=tk.X, pady=(0, 5))
        self.logo_frame.pack_forget()
        # Okul adı varsa metin olarak ayarla
        if hasattr(self, 'school_name') and self.school_name:
            self.watermark_text_var.set(self.school_name)

    def select_school_logo(self):
        """Okul logosu seç (kimlik kartları ve PDF'ler için) - PNG desteği ile"""
        file_path = filedialog.askopenfilename(
            title="Okul Logosu Seçin",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self.logo_path_var.set(str(Path(file_path).name))
            self.school_logo_path = Path(file_path)
            self.log_message(f"🖼️ Okul logosu seçildi: {Path(file_path).name}")

    def check_counts(self):
        """Fotoğraf ve Excel veri sayılarını kontrol et"""
        if not self.school_name:
            messagebox.showerror("Hata", "Önce okul adını girin.")
            return

        if not self.excel_data:
            messagebox.showerror("Hata", "Önce Excel dosyası seçin ve yükleyin.")
            return

        if not self.photo_directory:
            messagebox.showerror("Hata", "Önce fotoğraf dizini seçin.")
            return

        selected_columns = self.get_selected_columns()
        if not selected_columns:
            messagebox.showerror("Hata", "Adlandırma için en az bir sütun seçin.")
            return

        try:
            self.update_status("Dosyalar kontrol ediliyor...")

            # Fotoğraf dosyalarını al
            photos = self.photo_processor.get_image_files(self.photo_directory)
            photo_count = len(photos)
            data_count = len(self.excel_data)

            self.log_message(f"\n📊 === SAYIM KONTROLÜ ===")
            self.log_message(f"📄 Excel verisi satır sayısı: {data_count}")
            self.log_message(f"🖼️ Fotoğraf dosyası sayısı: {photo_count}")

            # Detaylı bilgi ver
            if data_count > photo_count:
                self.log_message(f"⚠️ Excel'de {data_count - photo_count} adet fazla kayıt var")
            elif photo_count > data_count:
                self.log_message(f"⚠️ Fotoğraf klasöründe {photo_count - data_count} adet fazla dosya var")
            else:
                self.log_message(f"✅ Excel verisi ve fotoğraf sayısı eşit")

            # Eşleştirme önerisi
            self.log_message(f"📋 Adlandırma için seçilen sütunlar: {selected_columns}")

            # Sonucu göster
            result_text = f"Excel: {data_count} kayıt | Fotoğraf: {photo_count} dosya"
            messagebox.showinfo("Sayım Kontrolü", result_text)
            self.log_message(f"📋 Seçilen sütunlar: {', '.join(selected_columns)}")

            # Kontrolün başarılı olup olmadığını belirle
            success_count = min(data_count, photo_count)
            
            if success_count > 0:
                self.log_message("✅ BAŞARILI: Fotoğraf ve veri kontrol edildi!")
                self.log_message("🚀 Fotoğrafları adlandırma işlemi için hazır.")

                # Butonları aktif et - sadece Excel verisi varsa
                if self.excel_data:
                    self.rename_button.config(state="normal")
                    self.pdf_button.config(state="normal")
                    self.id_card_button.config(state="normal")
                self.update_status("Hazır - İşlem başlatılabilir")

                # İlk 5 fotoğrafı listele
                self.log_message(f"\n📋 Bulunan fotoğraflar (ilk 5):")
                for i, photo in enumerate(photos[:5], 1):
                    self.log_message(f"   {i}. {photo.name}")
                if photo_count > 5:
                    self.log_message(f"   ... ve {photo_count - 5} tane daha.")
                    
                # Eşleşmeyen sayılar için uyarı ver ama devam et
                if data_count != photo_count:
                    if photo_count > data_count:
                        self.log_message(f"⚠️ Fazla fotoğraf var: {photo_count - data_count} adet")
                    else:
                        self.log_message(f"⚠️ Yetersiz fotoğraf var: {data_count - photo_count} adet eksik")

            else:
                self.log_message("❌ HATA: Hiç fotoğraf veya veri bulunamadı!")
                self.rename_button.config(state="disabled")
                self.pdf_button.config(state="disabled")
                self.id_card_button.config(state="disabled")
                self.update_status("Hata - Veri bulunamadı")

            # Boyutlandırma butonunu her durumda kontrol et
            self.update_crop_resize_button_state()

        except Exception as e:
            self.log_message(f"❌ Kontrol hatası: {e}")
            self.update_status("Kontrol hatası")

    def disable_all_buttons(self):
        """Tüm işlem butonlarını devre dışı bırak"""
        self.rename_button.config(state="disabled")
        self.crop_resize_button.config(state="disabled")
        self.pdf_button.config(state="disabled")
        self.id_card_button.config(state="disabled")

    def enable_all_buttons(self):
        """Tüm işlem butonlarını aktif et"""
        self.rename_button.config(state="normal")
        self.crop_resize_button.config(state="normal")
        self.pdf_button.config(state="normal")
        self.id_card_button.config(state="normal")

    def show_cancel_button(self):
        """İptal butonunu göster"""
        self.cancel_container.pack(fill=tk.X, pady=(8, 0))

    def hide_cancel_button(self):
        """İptal butonunu gizle"""
        self.cancel_container.pack_forget()

    def cancel_operation(self):
        """Devam eden işlemi iptal et"""
        self.cancel_requested.set()
        self.log_message("⏹️ İşlem iptali istendi, lütfen bekleyin...")
        self.update_status("İptal ediliyor...")

    def start_rename_photos(self):
        """Fotoğraf adlandırma işlemini thread'de başlat"""
        self.cancel_requested.clear()
        self.disable_all_buttons()
        self.show_cancel_button()

        self.current_operation = threading.Thread(target=self.rename_photos, daemon=True)
        self.current_operation.start()

    def start_crop_and_resize_photos(self):
        """Fotoğraf kırpma işlemini thread'de başlat"""
        self.cancel_requested.clear()
        self.disable_all_buttons()
        self.show_cancel_button()

        self.current_operation = threading.Thread(target=self.crop_and_resize_photos, daemon=True)
        self.current_operation.start()

    def start_generate_class_pdfs(self):
        """PDF oluşturma işlemini thread'de başlat"""
        self.cancel_requested.clear()
        self.disable_all_buttons()
        self.show_cancel_button()

        self.current_operation = threading.Thread(target=self.generate_class_pdfs, daemon=True)
        self.current_operation.start()

    def start_generate_id_cards(self):
        """Kimlik kartı oluşturma işlemini thread'de başlat"""
        # Önce sütun seçimi yap
        if not self.excel_data:
            messagebox.showerror("Hata", "Önce Excel dosyası yükleyin.")
            return
            
        selected_columns = self.show_id_card_column_selection()
        if not selected_columns:
            return  # Kullanıcı iptal etti
            
        self.id_card_selected_columns = selected_columns
        
        self.cancel_requested.clear()
        self.disable_all_buttons()
        self.show_cancel_button()

        self.current_operation = threading.Thread(target=self.generate_id_cards, daemon=True)
        self.current_operation.start()

    def show_id_card_column_selection(self):
        """Kimlik kartı için gelişmiş sütun seçim penceresi göster"""
        if not self.available_columns:
            messagebox.showerror("Hata", "Excel sütunları bulunamadı.")
            return None
        
        # Önce kapsam seçimi yap
        scope_result = self.show_id_card_scope_selection()
        if not scope_result:
            return None
        
        scope_type, selected_items = scope_result
        
        # Yeni pencere oluştur - boyutu artırıldı
        dialog = tk.Toplevel(self.root)
        dialog.title("Kimlik Kartı Oluşturma - Detaylı Ayarlar")
        dialog.geometry("1200x950")
        dialog.configure(bg=ModernUI.COLORS['bg_main'])
        dialog.grab_set()  # Modal yap
        
        # Pencereyi merkeze al
        dialog.transient(self.root)
        
        # Ana frame - scroll için
        main_frame = tk.Frame(dialog, bg=ModernUI.COLORS['bg_main'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scroll canvas ve scrollbar
        canvas = tk.Canvas(main_frame, bg=ModernUI.COLORS['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=ModernUI.COLORS['bg_main'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Değişkenler
        selected_columns = []
        selected_logo_path = None
        selected_logo2_path = None
        
        # Başlık
        title_label = tk.Label(scrollable_frame, 
                              text="🆔 Kimlik Kartı Oluşturma - Detaylı Ayarlar",
                              font=('Segoe UI', 16, 'bold'),
                              fg=ModernUI.COLORS['text'],
                              bg=ModernUI.COLORS['bg_main'])
        title_label.pack(pady=(10, 5))
        
        # Açıklama
        desc_label = tk.Label(scrollable_frame,
                             text="Kimlik kartlarınızı özelleştirin: Sütunlar, logolar, renkler, QR kod ve daha fazlası",
                             font=ModernUI.FONTS['body'],
                             fg=ModernUI.COLORS['text_light'],
                             bg=ModernUI.COLORS['bg_main'])
        desc_label.pack(pady=(0, 10))
        
        # Ana container - 2 sütunlu layout
        main_container = tk.Frame(scrollable_frame, bg=ModernUI.COLORS['bg_main'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Sol sütun
        left_column = tk.Frame(main_container, bg=ModernUI.COLORS['bg_main'])
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Sağ sütun
        right_column = tk.Frame(main_container, bg=ModernUI.COLORS['bg_main'])
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 1. SÜTUN SEÇİMİ (Sol sütun) - yükseklik azaltıldı
        column_frame = tk.LabelFrame(left_column, text="📊 Sütun Seçimi", 
                                    font=ModernUI.FONTS['subtitle'], 
                                    bg=ModernUI.COLORS['card_bg'], relief='solid', bd=1)
        column_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Sütun seçim alt container
        column_container = tk.Frame(column_frame, bg=ModernUI.COLORS['card_bg'])
        column_container.pack(fill=tk.X, padx=10, pady=10)
        
        # Sol taraf - Mevcut sütunlar
        avail_frame = tk.Frame(column_container, bg=ModernUI.COLORS['card_bg'])
        avail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(avail_frame, text="Mevcut Sütunlar:", 
                font=ModernUI.FONTS['body'], fg=ModernUI.COLORS['text'], 
                bg=ModernUI.COLORS['card_bg']).pack(anchor='w')
        
        available_listbox = tk.Listbox(avail_frame, font=ModernUI.FONTS['small'],
                                      relief='solid', bd=1, height=6)
        for column in self.available_columns:
            available_listbox.insert(tk.END, column)
        available_listbox.pack(fill=tk.X, pady=(5, 0))
        
        # Orta - Butonlar
        button_frame = tk.Frame(column_container, bg=ModernUI.COLORS['card_bg'])
        button_frame.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        tk.Label(button_frame, text="", bg=ModernUI.COLORS['card_bg']).pack(pady=20)
        
        def add_column():
            selection = available_listbox.curselection()
            if selection:
                column = available_listbox.get(selection[0])
                if column not in [selected_listbox.get(i) for i in range(selected_listbox.size())]:
                    selected_listbox.insert(tk.END, column)
        
        def remove_column():
            selection = selected_listbox.curselection()
            if selection:
                selected_listbox.delete(selection[0])
        
        def move_up():
            selection = selected_listbox.curselection()
            if selection and selection[0] > 0:
                index = selection[0]
                column = selected_listbox.get(index)
                selected_listbox.delete(index)
                selected_listbox.insert(index - 1, column)
                selected_listbox.selection_set(index - 1)
        
        def move_down():
            selection = selected_listbox.curselection()
            if selection and selection[0] < selected_listbox.size() - 1:
                index = selection[0]
                column = selected_listbox.get(index)
                selected_listbox.delete(index)
                selected_listbox.insert(index + 1, column)
                selected_listbox.selection_set(index + 1)
        
        ttk.Button(button_frame, text="→", command=add_column, width=5).pack(pady=2)
        ttk.Button(button_frame, text="←", command=remove_column, width=5).pack(pady=2)
        tk.Frame(button_frame, height=10, bg=ModernUI.COLORS['card_bg']).pack()
        ttk.Button(button_frame, text="↑", command=move_up, width=5).pack(pady=2)
        ttk.Button(button_frame, text="↓", command=move_down, width=5).pack(pady=2)
        
        # Sağ taraf - Seçili sütunlar
        selected_frame = tk.Frame(column_container, bg=ModernUI.COLORS['card_bg'])
        selected_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(selected_frame, text="Seçili Sütunlar:", 
                font=ModernUI.FONTS['body'], fg=ModernUI.COLORS['text'], 
                bg=ModernUI.COLORS['card_bg']).pack(anchor='w')
        
        selected_listbox = tk.Listbox(selected_frame, font=ModernUI.FONTS['small'],
                                     relief='solid', bd=1, height=6)
        selected_listbox.pack(fill=tk.X, pady=(5, 0))
        
        # 2. LOGO SEÇİMLERİ (Sol sütun)
        logo_frame = tk.LabelFrame(left_column, text="🖼️ Logo Ayarları", 
                                  font=ModernUI.FONTS['subtitle'], 
                                  bg=ModernUI.COLORS['card_bg'], relief='solid', bd=1)
        logo_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Ana logo
        logo1_container = tk.Frame(logo_frame, bg=ModernUI.COLORS['card_bg'])
        logo1_container.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(logo1_container, text="📋 Ana Logo (Header):", 
                font=ModernUI.FONTS['body'], bg=ModernUI.COLORS['card_bg']).pack(anchor='w')
        
        logo1_select_frame = tk.Frame(logo1_container, bg=ModernUI.COLORS['card_bg'])
        logo1_select_frame.pack(fill=tk.X, pady=(5, 0))
        
        logo_path_var = tk.StringVar()
        logo_entry = tk.Entry(logo1_select_frame, textvariable=logo_path_var, 
                             font=ModernUI.FONTS['small'], state="readonly")
        logo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        def select_logo():
            nonlocal selected_logo_path
            file_path = filedialog.askopenfilename(
                title="Ana Logo Seçin",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg *.jpeg"),
                    ("All image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                selected_logo_path = file_path
                logo_path_var.set(Path(file_path).name)
        
        ttk.Button(logo1_select_frame, text="Logo Seç", 
                  command=select_logo, style='Primary.TButton').pack(side=tk.RIGHT)
        
        # İkinci logo
        logo2_container = tk.Frame(logo_frame, bg=ModernUI.COLORS['card_bg'])
        logo2_container.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(logo2_container, text="🏢 İkinci Logo (Header Sağ):", 
                font=ModernUI.FONTS['body'], bg=ModernUI.COLORS['card_bg']).pack(anchor='w')
        
        logo2_select_frame = tk.Frame(logo2_container, bg=ModernUI.COLORS['card_bg'])
        logo2_select_frame.pack(fill=tk.X, pady=(5, 10))
        
        logo2_path_var = tk.StringVar()
        logo2_entry = tk.Entry(logo2_select_frame, textvariable=logo2_path_var, 
                              font=ModernUI.FONTS['small'], state="readonly")
        logo2_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        def select_logo2():
            nonlocal selected_logo2_path
            file_path = filedialog.askopenfilename(
                title="İkinci Logo Seçin",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg *.jpeg"),
                    ("All image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                selected_logo2_path = file_path
                logo2_path_var.set(Path(file_path).name)
        
        ttk.Button(logo2_select_frame, text="Logo Seç", 
                  command=select_logo2, style='Primary.TButton').pack(side=tk.RIGHT)
        
        # 3. RENK AYARLARI (Sol sütun - alt tarafta)
        color_frame = tk.LabelFrame(left_column, text="🎨 Renk Ayarları", 
                                   font=ModernUI.FONTS['subtitle'], 
                                   bg=ModernUI.COLORS['card_bg'], relief='solid', bd=1)
        color_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Renk seçici fonksiyonu
        def choose_color(color_var, button_widget):
            from tkinter import colorchooser
            color = colorchooser.askcolor(title="Renk Seçin")[1]
            if color:
                color_var.set(color)
                button_widget.configure(bg=color)
        
        # Header renk ayarları
        header_color_container = tk.Frame(color_frame, bg=ModernUI.COLORS['card_bg'])
        header_color_container.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(header_color_container, text="📋 Üst Başlık Renkleri:", 
                font=ModernUI.FONTS['body'], bg=ModernUI.COLORS['card_bg']).pack(anchor='w')
        
        header_row = tk.Frame(header_color_container, bg=ModernUI.COLORS['card_bg'])
        header_row.pack(fill=tk.X, pady=(5, 0))
        
        header_color_var = tk.StringVar(value="#2D55A5")
        header_color_button = tk.Button(header_row, text="Renk 1", width=8, bg="#2D55A5", fg="white",
                                       command=lambda: choose_color(header_color_var, header_color_button))
        header_color_button.pack(side=tk.LEFT, padx=(0, 5))
        
        header_color_entry = tk.Entry(header_row, textvariable=header_color_var, width=10)
        header_color_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        header_gradient_var = tk.BooleanVar()
        header_gradient_cb = tk.Checkbutton(header_row, text="Gradient", 
                                           variable=header_gradient_var, 
                                           bg=ModernUI.COLORS['card_bg'])
        header_gradient_cb.pack(side=tk.LEFT, padx=(0, 10))
        
        header_color2_var = tk.StringVar(value="#1B3F73")
        header_color2_button = tk.Button(header_row, text="Renk 2", width=8, bg="#1B3F73", fg="white",
                                        command=lambda: choose_color(header_color2_var, header_color2_button))
        header_color2_button.pack(side=tk.LEFT, padx=(0, 5))
        
        header_color2_entry = tk.Entry(header_row, textvariable=header_color2_var, width=10)
        header_color2_entry.pack(side=tk.LEFT)
        
        # Footer renk ayarları
        footer_color_container = tk.Frame(color_frame, bg=ModernUI.COLORS['card_bg'])
        footer_color_container.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        tk.Label(footer_color_container, text="📊 Alt Bilgi Renkleri:", 
                font=ModernUI.FONTS['body'], bg=ModernUI.COLORS['card_bg']).pack(anchor='w')
        
        footer_row = tk.Frame(footer_color_container, bg=ModernUI.COLORS['card_bg'])
        footer_row.pack(fill=tk.X, pady=(5, 0))
        
        footer_color_var = tk.StringVar(value="#2D55A5")
        footer_color_button = tk.Button(footer_row, text="Renk 1", width=8, bg="#2D55A5", fg="white",
                                       command=lambda: choose_color(footer_color_var, footer_color_button))
        footer_color_button.pack(side=tk.LEFT, padx=(0, 5))
        
        footer_color_entry = tk.Entry(footer_row, textvariable=footer_color_var, width=10)
        footer_color_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        footer_gradient_var = tk.BooleanVar()
        footer_gradient_cb = tk.Checkbutton(footer_row, text="Gradient", 
                                           variable=footer_gradient_var, 
                                           bg=ModernUI.COLORS['card_bg'])
        footer_gradient_cb.pack(side=tk.LEFT, padx=(0, 10))
        
        footer_color2_var = tk.StringVar(value="#1B3F73")
        footer_color2_button = tk.Button(footer_row, text="Renk 2", width=8, bg="#1B3F73", fg="white",
                                        command=lambda: choose_color(footer_color2_var, footer_color2_button))
        footer_color2_button.pack(side=tk.LEFT, padx=(0, 5))
        
        footer_color2_entry = tk.Entry(footer_row, textvariable=footer_color2_var, width=10)
        footer_color2_entry.pack(side=tk.LEFT)
        
        # 4. QR KOD AYARLARI (Sağ sütun - üst tarafta)
        qr_frame = tk.LabelFrame(right_column, text="📱 QR Kod Ayarları", 
                                font=ModernUI.FONTS['subtitle'], 
                                bg=ModernUI.COLORS['card_bg'], relief='solid', bd=1)
        qr_frame.pack(fill=tk.X, pady=(0, 10))
        
        qr_enable_var = tk.BooleanVar(value=True)  # Varsayılan olarak seçili
        qr_enable_cb = tk.Checkbutton(qr_frame, text="QR Kod Ekle", 
                                     variable=qr_enable_var, font=ModernUI.FONTS['body'],
                                     bg=ModernUI.COLORS['card_bg'])
        qr_enable_cb.pack(anchor='w', padx=10, pady=(5, 0))
        
        # QR kod seçenekleri
        qr_options_frame = tk.Frame(qr_frame, bg=ModernUI.COLORS['card_bg'])
        qr_options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(qr_options_frame, text="QR Kod Verisi:", 
                font=ModernUI.FONTS['body'], bg=ModernUI.COLORS['card_bg']).pack(anchor='w')
        
        qr_data_var = tk.StringVar(value="student")  # Varsayılan olarak "Öğrenci Bilgileri" seçili
        
        qr_custom_rb = tk.Radiobutton(qr_options_frame, text="Özel Metin", variable=qr_data_var, 
                                     value="custom", bg=ModernUI.COLORS['card_bg'])
        qr_custom_rb.pack(anchor='w', pady=2)
        
        qr_custom_text_var = tk.StringVar(value="VesiKolay Pro")
        qr_custom_entry = tk.Entry(qr_options_frame, textvariable=qr_custom_text_var, 
                                  font=ModernUI.FONTS['small'])
        qr_custom_entry.pack(fill=tk.X, padx=(20, 0), pady=(0, 5))
        
        qr_student_rb = tk.Radiobutton(qr_options_frame, text="Öğrenci Bilgileri", variable=qr_data_var, 
                                      value="student", bg=ModernUI.COLORS['card_bg'])
        qr_student_rb.pack(anchor='w', pady=2)
        
        # QR kod pozisyon
        tk.Label(qr_options_frame, text="QR Kod Pozisyonu:", 
                font=ModernUI.FONTS['body'], bg=ModernUI.COLORS['card_bg']).pack(anchor='w', pady=(10, 0))
        
        qr_position_var = tk.StringVar(value="bottom_right")
        
        position_frame = tk.Frame(qr_options_frame, bg=ModernUI.COLORS['card_bg'])
        position_frame.pack(fill=tk.X)
        
        tk.Radiobutton(position_frame, text="Sağ Alt", variable=qr_position_var, 
                      value="bottom_right", bg=ModernUI.COLORS['card_bg']).pack(side=tk.LEFT)
        tk.Radiobutton(position_frame, text="Sol Alt", variable=qr_position_var, 
                      value="bottom_left", bg=ModernUI.COLORS['card_bg']).pack(side=tk.LEFT)
        
        # 5. BAŞLIK AYARLARI (Sağ sütun)
        header_frame = tk.LabelFrame(right_column, text="📝 Başlık Ayarları", 
                                    font=ModernUI.FONTS['subtitle'], 
                                    bg=ModernUI.COLORS['card_bg'], relief='solid', bd=1)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="1. Satır (Örnek: T.C.):", 
                font=ModernUI.FONTS['body'], bg=ModernUI.COLORS['card_bg']).pack(anchor='w', padx=10, pady=(5, 0))
        
        header_line1_var = tk.StringVar(value="T.C.")
        header_line1_entry = tk.Entry(header_frame, textvariable=header_line1_var, 
                                     font=ModernUI.FONTS['body'])
        header_line1_entry.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        tk.Label(header_frame, text="2. Satır (Kaymakamlık/Müdürlük):", 
                font=ModernUI.FONTS['body'], bg=ModernUI.COLORS['card_bg']).pack(anchor='w', padx=10, pady=(5, 0))
        
        header_line2_var = tk.StringVar(value="...... KAYMAKAMLIGI")
        header_line2_entry = tk.Entry(header_frame, textvariable=header_line2_var, 
                                     font=ModernUI.FONTS['body'])
        header_line2_entry.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        tk.Label(header_frame, text="3. Satır (Okul Adı):", 
                font=ModernUI.FONTS['body'], bg=ModernUI.COLORS['card_bg']).pack(anchor='w', padx=10, pady=(5, 0))
        
        header_line3_var = tk.StringVar(value=self.school_name if hasattr(self, 'school_name') else "KONYA LİSESİ")
        header_line3_entry = tk.Entry(header_frame, textvariable=header_line3_var, 
                                     font=ModernUI.FONTS['body'])
        header_line3_entry.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        tk.Label(header_frame, text="4. Satır (Kart Başlığı - Renkli alan dışı):", 
                font=ModernUI.FONTS['body'], bg=ModernUI.COLORS['card_bg']).pack(anchor='w', padx=10, pady=(5, 0))
        
        header_line4_var = tk.StringVar(value="Öğrenci Kimlik Kartı")
        header_line4_entry = tk.Entry(header_frame, textvariable=header_line4_var, 
                                     font=ModernUI.FONTS['body'])
        header_line4_entry.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        tk.Label(header_frame, text="5. Satır (Eğitim-Öğretim Yılı - Footer):", 
                font=ModernUI.FONTS['body'], bg=ModernUI.COLORS['card_bg']).pack(anchor='w', padx=10, pady=(5, 0))
        
        header_line5_var = tk.StringVar(value="2025-2026 EĞİTİM-ÖĞRETİM YILI")
        header_line5_entry = tk.Entry(header_frame, textvariable=header_line5_var, 
                                     font=ModernUI.FONTS['body'])
        header_line5_entry.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # Alt butonlar - scrollable_frame içinde
        bottom_frame = tk.Frame(scrollable_frame, bg=ModernUI.COLORS['bg_main'])
        bottom_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Önizleme butonu
        def show_preview():
            messagebox.showinfo("Önizleme", 
                               f"📋 Seçilen Sütunlar: {len([selected_listbox.get(i) for i in range(selected_listbox.size())])}\n"
                               f"🖼️ Ana Logo: {'✅' if selected_logo_path else '❌'}\n"
                               f"🏢 İkinci Logo: {'✅' if selected_logo2_path else '❌'}\n"
                               f"🎨 Header Gradient: {'✅' if header_gradient_var.get() else '❌'}\n"
                               f"📱 QR Kod: {'✅' if qr_enable_var.get() else '❌'}\n"
                               f"📝 Başlık Satırları:\n"
                               f"   1. {header_line1_var.get()[:30]}\n"
                               f"   2. {header_line2_var.get()[:30]}\n"
                               f"   3. {header_line3_var.get()[:30]}")
        
        preview_button = ttk.Button(bottom_frame, text="🔍 Önizleme", 
                                   command=show_preview, style='Primary.TButton')
        preview_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Boşluk
        tk.Frame(bottom_frame, bg=ModernUI.COLORS['bg_main']).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # İptal butonu
        cancel_button = ttk.Button(bottom_frame, text="❌ İptal", 
                                  style='Warning.TButton')
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Oluştur butonu
        create_button = ttk.Button(bottom_frame, text="🆔 Kimlik Kartlarını Oluştur", 
                                  style='Success.TButton')
        create_button.pack(side=tk.RIGHT, padx=(10, 5))
        
        # Canvas ve scrollbar'ı pack et
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scroll desteği - güvenli versiyon
        def _on_mousewheel(event):
            try:
                # Canvas'ın hala mevcut olup olmadığını kontrol et
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                # Canvas silinmişse event binding'i kaldır
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                # Diğer hatalar için de binding'i kaldır
                canvas.unbind_all("<MouseWheel>")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Dialog kapatılırken event binding'leri temizle
        def cleanup_events():
            try:
                canvas.unbind_all("<MouseWheel>")
            except:
                pass
        
        dialog.protocol("WM_DELETE_WINDOW", lambda: (cleanup_events(), dialog.destroy()))
        
        def on_create():
            nonlocal selected_columns
            selected_columns = [selected_listbox.get(i) for i in range(selected_listbox.size())]
            if not selected_columns:
                messagebox.showwarning("Uyarı", "En az bir sütun seçmelisiniz.")
                return
                
            # Tüm ayarları kaydet
            self.id_card_settings = {
                'header_color': header_color_var.get(),
                'header_gradient': header_gradient_var.get(),
                'header_gradient_color2': header_color2_var.get(),
                'footer_color': footer_color_var.get(),
                'footer_gradient': footer_gradient_var.get(),
                'footer_gradient_color2': footer_color2_var.get(),
                'qr_enabled': qr_enable_var.get(),
                'qr_data_type': qr_data_var.get(),
                'qr_custom_text': qr_custom_text_var.get(),
                'qr_position': qr_position_var.get(),
                'header_line1': header_line1_var.get(),
                'header_line2': header_line2_var.get(),
                'header_line3': header_line3_var.get(),
                'header_line4': header_line4_var.get(),
                'header_line5': header_line5_var.get(),
                'main_logo_path': selected_logo_path,
                'second_logo_path': selected_logo2_path
            }
            
            dialog.destroy()
        
        def on_cancel():
            nonlocal selected_columns, selected_logo_path, selected_logo2_path
            selected_columns = []
            selected_logo_path = None
            selected_logo2_path = None
            dialog.destroy()
        
        # Buton komutlarını bağla
        cancel_button.configure(command=on_cancel)
        create_button.configure(command=on_create)
        
        
        
        # Pencereyi bekle
        dialog.wait_window()
        
        # Sonuçları döndür
        if selected_columns:
            if selected_logo_path:
                self.id_card_logo_path = selected_logo_path
            if selected_logo2_path:
                self.id_card_logo2_path = selected_logo2_path
            
            # Kapsam bilgisini de kaydet
            self.id_card_scope_type = scope_type
            self.id_card_selected_items = selected_items
            
            return selected_columns
        return None

    def show_id_card_scope_selection(self):
        """Kimlik kartı kapsamı seçim penceresi"""
        # Kapsam seçim penceresi
        scope_dialog = tk.Toplevel(self.root)
        scope_dialog.title("Kimlik Kartı Oluşturma Kapsamı")
        scope_dialog.geometry("800x650")
        scope_dialog.configure(bg=ModernUI.COLORS['bg_main'])
        scope_dialog.grab_set()
        scope_dialog.transient(self.root)
        
        result = None
        
        # Başlık
        title_label = tk.Label(scope_dialog, 
                              text="🆔 Kimlik Kartı Oluşturma Kapsamı",
                              font=('Segoe UI', 16, 'bold'),
                              fg=ModernUI.COLORS['text'],
                              bg=ModernUI.COLORS['bg_main'])
        title_label.pack(pady=(20, 10))
        
        # Açıklama
        desc_label = tk.Label(scope_dialog,
                             text="Kimlik kartlarını hangi kapsamda oluşturmak istiyorsunuz?",
                             font=ModernUI.FONTS['body'],
                             fg=ModernUI.COLORS['text_light'],
                             bg=ModernUI.COLORS['bg_main'])
        desc_label.pack(pady=(0, 20))
        
        # Seçenekler frame
        options_frame = tk.Frame(scope_dialog, bg=ModernUI.COLORS['bg_main'])
        options_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)
        
        scope_var = tk.StringVar(value="all")
        
        # Tüm öğrenciler seçeneği
        all_frame = tk.LabelFrame(options_frame, text="📋 Tüm Öğrenciler", 
                                 font=ModernUI.FONTS['subtitle'], 
                                 bg=ModernUI.COLORS['card_bg'], relief='solid', bd=1)
        all_frame.pack(fill=tk.X, pady=(0, 15))
        
        all_radio = tk.Radiobutton(all_frame, text="Tüm öğrenci listesi için kimlik kartı oluştur",
                                  variable=scope_var, value="all",
                                  bg=ModernUI.COLORS['card_bg'], font=ModernUI.FONTS['body'])
        all_radio.pack(anchor='w', padx=15, pady=10)
        
        all_info = tk.Label(all_frame, text=f"📊 Toplam: {len(self.excel_data)} öğrenci",
                           font=ModernUI.FONTS['small'], fg=ModernUI.COLORS['text_light'],
                           bg=ModernUI.COLORS['card_bg'])
        all_info.pack(anchor='w', padx=30, pady=(0, 10))
        
        # Sınıf bazlı seçenek
        class_frame = tk.LabelFrame(options_frame, text="🏫 Sınıf Bazında", 
                                   font=ModernUI.FONTS['subtitle'], 
                                   bg=ModernUI.COLORS['card_bg'], relief='solid', bd=1)
        class_frame.pack(fill=tk.X, pady=(0, 15))
        
        class_radio = tk.Radiobutton(class_frame, text="Belirli sınıflar için kimlik kartı oluştur",
                                    variable=scope_var, value="class",
                                    bg=ModernUI.COLORS['card_bg'], font=ModernUI.FONTS['body'])
        class_radio.pack(anchor='w', padx=15, pady=(10, 5))
        
        # Sınıf listesi
        class_list_frame = tk.Frame(class_frame, bg=ModernUI.COLORS['card_bg'])
        class_list_frame.pack(fill=tk.X, padx=30, pady=(0, 10))
        
        # Excel'den sınıfları çıkar
        classes = set()
        for record in self.excel_data:
            class_name = record.get('class_name', record.get('sınıf', 'Bilinmiyor'))
            if class_name and str(class_name).lower() not in ['nan', 'none', '']:
                classes.add(str(class_name))
        
        classes = sorted(list(classes))
        
        if classes:
            class_info = tk.Label(class_list_frame, 
                                 text=f"📚 Mevcut sınıflar: {', '.join(classes[:5])}{'...' if len(classes) > 5 else ''}",
                                 font=ModernUI.FONTS['small'], fg=ModernUI.COLORS['text_light'],
                                 bg=ModernUI.COLORS['card_bg'])
            class_info.pack(anchor='w')
        else:
            class_info = tk.Label(class_list_frame, text="⚠️ Sınıf bilgisi bulunamadı",
                                 font=ModernUI.FONTS['small'], fg=ModernUI.COLORS['warning'],
                                 bg=ModernUI.COLORS['card_bg'])
            class_info.pack(anchor='w')
        
        # Bireysel seçenek
        individual_frame = tk.LabelFrame(options_frame, text="👤 Bireysel Seçim", 
                                        font=ModernUI.FONTS['subtitle'], 
                                        bg=ModernUI.COLORS['card_bg'], relief='solid', bd=1)
        individual_frame.pack(fill=tk.X, pady=(0, 20))
        
        individual_radio = tk.Radiobutton(individual_frame, text="Belirli öğrenciler için kimlik kartı oluştur",
                                         variable=scope_var, value="individual",
                                         bg=ModernUI.COLORS['card_bg'], font=ModernUI.FONTS['body'])
        individual_radio.pack(anchor='w', padx=15, pady=(10, 5))
        
        individual_info = tk.Label(individual_frame, text="🔍 Liste üzerinden tek tek öğrenci seçimi yapabilirsiniz",
                                  font=ModernUI.FONTS['small'], fg=ModernUI.COLORS['text_light'],
                                  bg=ModernUI.COLORS['card_bg'])
        individual_info.pack(anchor='w', padx=30, pady=(0, 10))
        
        # Butonlar - yukarı taşındı
        button_frame = tk.Frame(scope_dialog, bg=ModernUI.COLORS['bg_main'])
        button_frame.pack(fill=tk.X, padx=40, pady=(10, 20))
        
        def on_continue():
            nonlocal result
            scope_type = scope_var.get()
            
            if scope_type == "all":
                result = ("all", None)
                scope_dialog.destroy()
            elif scope_type == "class":
                if not classes:
                    messagebox.showwarning("Uyarı", "Sınıf bilgisi bulunamadı.")
                    return
                selected_classes = self.show_class_selection(classes)
                if selected_classes:
                    result = ("class", selected_classes)
                    scope_dialog.destroy()
            elif scope_type == "individual":
                selected_students = self.show_individual_selection()
                if selected_students:
                    result = ("individual", selected_students)
                    scope_dialog.destroy()
        
        def on_cancel():
            nonlocal result
            result = None
            scope_dialog.destroy()
        
        ttk.Button(button_frame, text="❌ İptal", command=on_cancel, 
                  style='Warning.TButton').pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="➡️ Devam Et", command=on_continue, 
                  style='Success.TButton').pack(side=tk.RIGHT)
        
        # Pencereyi bekle
        scope_dialog.wait_window()
        
        return result

    def show_class_selection(self, available_classes):
        """Sınıf seçim penceresi"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Sınıf Seçimi")
        dialog.geometry("650x500")
        dialog.configure(bg=ModernUI.COLORS['bg_main'])
        dialog.grab_set()
        dialog.transient(self.root)
        
        selected_classes = []
        
        # Başlık
        title_label = tk.Label(dialog, text="🏫 Sınıf Seçimi",
                              font=('Segoe UI', 14, 'bold'),
                              fg=ModernUI.COLORS['text'],
                              bg=ModernUI.COLORS['bg_main'])
        title_label.pack(pady=(15, 10))
        
        # Açıklama
        desc_label = tk.Label(dialog, text="Kimlik kartı oluşturulacak sınıfları seçin:",
                             font=ModernUI.FONTS['body'],
                             fg=ModernUI.COLORS['text_light'],
                             bg=ModernUI.COLORS['bg_main'])
        desc_label.pack(pady=(0, 15))
        
        # Sınıf listesi frame
        list_frame = tk.Frame(dialog, bg=ModernUI.COLORS['bg_main'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Scroll listbox
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        class_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE,
                                  font=ModernUI.FONTS['body'],
                                  yscrollcommand=scrollbar.set)
        
        # Sınıfları ekle ve öğrenci sayılarını göster
        for class_name in available_classes:
            student_count = sum(1 for record in self.excel_data 
                              if record.get('class_name', record.get('sınıf', '')) == class_name)
            class_listbox.insert(tk.END, f"{class_name} ({student_count} öğrenci)")
        
        class_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=class_listbox.yview)
        
        # Butonlar
        button_frame = tk.Frame(dialog, bg=ModernUI.COLORS['bg_main'])
        button_frame.pack(fill=tk.X, padx=30, pady=15)
        
        def on_select():
            nonlocal selected_classes
            indices = class_listbox.curselection()
            if not indices:
                messagebox.showwarning("Uyarı", "En az bir sınıf seçmelisiniz.")
                return
            
            selected_classes = [available_classes[i] for i in indices]
            dialog.destroy()
        
        def on_cancel():
            nonlocal selected_classes
            selected_classes = []
            dialog.destroy()
        
        ttk.Button(button_frame, text="❌ İptal", command=on_cancel,
                  style='Warning.TButton').pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="✅ Seç", command=on_select,
                  style='Success.TButton').pack(side=tk.RIGHT)
        
        dialog.wait_window()
        return selected_classes

    def show_individual_selection(self):
        """Bireysel öğrenci seçim penceresi"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Öğrenci Seçimi")
        dialog.geometry("900x600")
        dialog.configure(bg=ModernUI.COLORS['bg_main'])
        dialog.grab_set()
        dialog.transient(self.root)
        
        selected_students = []
        
        # Başlık
        title_label = tk.Label(dialog, text="👤 Öğrenci Seçimi",
                              font=('Segoe UI', 14, 'bold'),
                              fg=ModernUI.COLORS['text'],
                              bg=ModernUI.COLORS['bg_main'])
        title_label.pack(pady=(15, 10))
        
        # Arama frame
        search_frame = tk.Frame(dialog, bg=ModernUI.COLORS['bg_main'])
        search_frame.pack(fill=tk.X, padx=30, pady=(0, 10))
        
        tk.Label(search_frame, text="🔍 Arama:", font=ModernUI.FONTS['body'],
                bg=ModernUI.COLORS['bg_main']).pack(side=tk.LEFT)
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var,
                               font=ModernUI.FONTS['body'])
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Öğrenci listesi frame
        list_frame = tk.Frame(dialog, bg=ModernUI.COLORS['bg_main'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Scroll listbox
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        student_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE,
                                    font=ModernUI.FONTS['body'],
                                    yscrollcommand=scrollbar.set)
        student_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=student_listbox.yview)
        
        # Öğrenci verilerini hazırla
        student_list = []
        for i, record in enumerate(self.excel_data):
            # Ad bilgisini oluştur - daha kapsamlı sütun arama
            name_parts = []
            
            # Tüm mevcut sütunları kontrol et
            original_data = record.get('_original_data', {})
            
            # İlk ad için geniş sütun arama
            first_name = ""
            first_name_cols = [
                'ad', 'Ad', 'AD', 'ADI', 'Adı', 'adi',
                'name', 'first_name', 'firstName', 'First_Name',
                'isim', 'İsim', 'ISIM', 'İSİM', 'Isim',
                'adı', 'ismi'
            ]
            
            for col in first_name_cols:
                if col in original_data:
                    value = str(original_data[col]).strip()
                    if value and value.lower() not in ['nan', 'none', '', 'null']:
                        first_name = value
                        break
            
            # Soyad için geniş sütun arama
            last_name = ""
            last_name_cols = [
                'soyad', 'Soyad', 'SOYAD', 'SOYADI', 'Soyadı', 'soyadi',
                'surname', 'last_name', 'lastName', 'Last_Name',
                'family_name', 'familyName', 'soyadı'
            ]
            
            for col in last_name_cols:
                if col in original_data:
                    value = str(original_data[col]).strip()
                    if value and value.lower() not in ['nan', 'none', '', 'null']:
                        last_name = value
                        break
            
            # Tam ad kombinasyonu sütunları da kontrol et
            full_name_cols = [
                'ad_soyad', 'Ad_Soyad', 'AD_SOYAD', 'AdSoyad',
                'full_name', 'fullName', 'Full_Name',
                'tam_ad', 'Tam_Ad', 'TAM_AD', 'TamAd',
                'adsoyad', 'AdıSoyadı', 'isim_soyisim'
            ]
            
            full_name_found = ""
            for col in full_name_cols:
                if col in original_data:
                    value = str(original_data[col]).strip()
                    if value and value.lower() not in ['nan', 'none', '', 'null']:
                        full_name_found = value
                        break
            
            # İsim oluşturma mantığı
            if full_name_found:
                # Tam ad bulunduysa onu kullan
                name_parts = [full_name_found]
            elif first_name and last_name:
                # Ad ve soyad ayrı ayrı bulunduysa birleştir
                name_parts = [first_name, last_name]
            elif first_name:
                # Sadece ad bulunduysa
                name_parts = [first_name]
            elif last_name:
                # Sadece soyad bulunduysa
                name_parts = [last_name]
            else:
                # Hiçbir ad bilgisi bulunamadıysa, diğer sütunları kontrol et
                for col_name, col_value in original_data.items():
                    value = str(col_value).strip()
                    if (value and value.lower() not in ['nan', 'none', '', 'null'] and
                        len(value) > 2 and not value.isdigit()):
                        # İsim gibi görünen ilk değeri al
                        name_parts = [value]
                        break
                
                # Hala bulunamadıysa varsayılan isim ver
                if not name_parts:
                    name_parts = [f"Öğrenci_{i+1}"]
            
            student_name = " ".join(name_parts)
            
            # Sınıf bilgisini al
            class_name = "Bilinmiyor"
            class_cols = ['sınıf', 'Sınıf', 'SINIF', 'class', 'Class', 'class_name', 'sinif']
            for col in class_cols:
                if col in original_data:
                    value = str(original_data[col]).strip()
                    if value and value.lower() not in ['nan', 'none', '', 'null']:
                        class_name = value
                        break
            
            # Öğrenci numarasını al (varsa)
            student_no = ""
            no_cols = ['no', 'No', 'NO', 'numara', 'Numara', 'NUMARA', 'student_no', 'ogrenci_no']
            for col in no_cols:
                if col in original_data:
                    value = str(original_data[col]).strip()
                    if value and value.lower() not in ['nan', 'none', '', 'null']:
                        student_no = value
                        break
            
            # Görüntü metni oluştur
            if student_no:
                student_display = f"{student_name} ({student_no} - {class_name})"
            else:
                student_display = f"{student_name} ({class_name})"
            
            student_list.append((student_display, i))
        
        def update_student_list(filter_text=""):
            student_listbox.delete(0, tk.END)
            for display_name, index in student_list:
                if filter_text.lower() in display_name.lower():
                    student_listbox.insert(tk.END, display_name)
        
        # İlk doldurma
        update_student_list()
        
        # Arama fonksiyonu
        def on_search_change(*args):
            update_student_list(search_var.get())
        
        search_var.trace('w', on_search_change)
        
        # Butonlar
        button_frame = tk.Frame(dialog, bg=ModernUI.COLORS['bg_main'])
        button_frame.pack(fill=tk.X, padx=30, pady=15)
        
        def on_select():
            nonlocal selected_students
            indices = student_listbox.curselection()
            if not indices:
                messagebox.showwarning("Uyarı", "En az bir öğrenci seçmelisiniz.")
                return
            
            selected_students = []
            current_filter = search_var.get().lower()
            filtered_list = [(display, idx) for display, idx in student_list 
                           if current_filter in display.lower()]
            
            for listbox_index in indices:
                if listbox_index < len(filtered_list):
                    _, original_index = filtered_list[listbox_index]
                    selected_students.append(original_index)
            
            dialog.destroy()
        
        def on_cancel():
            nonlocal selected_students
            selected_students = []
            dialog.destroy()
        
        ttk.Button(button_frame, text="❌ İptal", command=on_cancel,
                  style='Warning.TButton').pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="✅ Seç", command=on_select,
                  style='Success.TButton').pack(side=tk.RIGHT)
        
        dialog.wait_window()
        return selected_students

    def operation_finished(self):
        """İşlem bittiğinde UI'ı sıfırla"""
        self.hide_cancel_button()
        self.enable_all_buttons()
        self.progress['value'] = 0
        self.current_operation = None

    def rename_photos(self):
        """Fotoğrafları Excel verilerine göre yeniden adlandır"""
        try:
            if not self.school_name:
                self.log_message("❌ Önce okul adını girin.")
                return

            if not self.excel_data or not self.photo_directory:
                self.log_message("❌ Excel verisi ve fotoğraf dizini gerekli.")
                return

            selected_columns = self.get_selected_columns()
            if not selected_columns:
                self.log_message("❌ Adlandırma için en az bir sütun seçin.")
                return

            self.update_status("Fotoğraflar adlandırılıyor...")

            # Fotoğrafları al ve sırala
            photos = self.photo_processor.get_image_files(self.photo_directory)
            photos.sort()

            # Ana çıktı dizini oluştur - VesiKolayPro konumunda
            from datetime import datetime
            from utils import VesiKolayUtils
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_school_name = self.clean_filename(self.school_name)

            # VesiKolayPro ana dizininde okul klasörü oluştur
            school_main_dir = VesiKolayUtils.get_school_directory(self.school_name)

            # Tarih-saat alt klasörü
            base_output_dir = school_main_dir / timestamp

            # Dizin var mı kontrol et
            if base_output_dir.exists():
                import time
                time.sleep(1)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_output_dir = school_main_dir / timestamp

            base_output_dir.mkdir(exist_ok=True)

            # Ana okul klasörünü sınıf değişkeninde sakla
            self.current_school_output_dir = school_main_dir

            # Adlandırılmış fotoğraflar için dizin
            renamed_dir = base_output_dir / "renamed"
            renamed_dir.mkdir(exist_ok=True)

            self.log_message(f"\n🚀 === ADLANDIRMA İŞLEMİ BAŞLIYOR ===")
            self.log_message(f"📋 Seçilen sütunlar: {', '.join(selected_columns)}")
            self.log_message(f"📁 Çıktı dizini: {base_output_dir.name}")

            # İlerleme başlat
            total_count = min(len(photos), len(self.excel_data))
            self.progress['maximum'] = total_count

            success_count = 0
            error_count = 0
            renamed_photos = []
            photos_by_class = {}

            for i in range(total_count):
                # İptal kontrolü
                if self.cancel_requested.is_set():
                    self.log_message("⏹️ İşlem kullanıcı tarafından iptal edildi.")
                    break

                try:
                    photo = photos[i]
                    data_record = self.excel_data[i]

                    # Yeni dosya adı oluştur (çoklu sütun desteği)
                    name_parts = []
                    for col in selected_columns:
                        if col in data_record.get('_original_data', {}):
                            value = str(data_record['_original_data'][col]).strip()
                            if value and value != 'nan':
                                name_parts.append(value)

                    if not name_parts:
                        name_parts = [f"photo_{i+1}"]

                    # Dosya adını temizle ve oluştur (seçilen ayraçla)
                    separator = self.separator_var.get() if hasattr(self, 'separator_var') else "_"
                    if separator == " ":
                        # Boşluk seçildiğinde gerçekten boşluk kullan
                        base_name = " ".join(name_parts)
                    else:
                        base_name = separator.join(name_parts)
                    clean_name = self.clean_filename(base_name, preserve_spaces=(separator == " "))
                    new_filename = f"{clean_name}{photo.suffix}"

                    # Dosyayı kopyala ve yeniden adlandır
                    new_path = renamed_dir / new_filename

                    # Aynı isimde dosya varsa numara ekle
                    counter = 1
                    original_new_path = new_path
                    while new_path.exists():
                        stem = original_new_path.stem
                        suffix = original_new_path.suffix
                        new_path = renamed_dir / f"{stem}_{counter}{suffix}"
                        counter += 1

                    # Dosyayı kopyala
                    FileUtils.copy_file_safe(photo, new_path, overwrite=True)

                    # Watermark ekle (eğer aktifse)
                    if self.watermark_enabled.get():
                        self.apply_watermark_to_photo(new_path)

                    renamed_photos.append(new_path)

                    # Sınıf bilgisini al (sınıf organizasyonu için)
                    if self.organize_by_class.get():
                        class_name = self.photo_processor._get_class_name_from_record(data_record)
                        if not class_name:
                            class_name = "Sınıf_Bilgisi_Yok"

                        if class_name not in photos_by_class:
                            photos_by_class[class_name] = []
                        photos_by_class[class_name].append(new_path)

                    success_count += 1
                    # Tüm işlemleri göster
                    self.log_message(f"✅ {i+1:3d}. {photo.name} → {new_path.name}")

                except Exception as e:
                    error_count += 1
                    self.log_message(f"❌ Hata {i+1}: {photo.name} - {e}")

                # İlerlemeyi güncelle
                self.progress['value'] = i + 1
                self.update_status(f"İşleniyor: {i+1}/{total_count}")

            # Sınıf bazında organizasyon
            if self.organize_by_class.get() and photos_by_class:
                class_dir = base_output_dir / "by_class"
                class_dir.mkdir(exist_ok=True)

                self.log_message(f"\n📂 === SINIF BAZINDA ORGANİZASYON ===")
                for class_name, class_photos in photos_by_class.items():
                    if self.cancel_requested.is_set():
                        break

                    class_folder = class_dir / self.clean_filename(class_name)
                    class_folder.mkdir(exist_ok=True)

                    for photo_path in class_photos:
                        if self.cancel_requested.is_set():
                            break
                        class_photo_path = class_folder / photo_path.name
                        FileUtils.copy_file_safe(photo_path, class_photo_path, overwrite=True)

                    self.log_message(f"📁 {class_name}: {len(class_photos)} fotoğraf")

            # Sonuçları göster
            if not self.cancel_requested.is_set():
                self.log_message(f"\n🎉 === İŞLEM TAMAMLANDI ===")
                self.log_message(f"✅ Başarılı: {success_count}")
                self.log_message(f"❌ Hatalı: {error_count}")
                self.log_message(f"📊 Toplam: {total_count}")
                self.log_message(f"📁 Çıktı dizini: {base_output_dir.name}")

                self.update_status(f"Tamamlandı: {success_count}/{total_count} başarılı")

                if success_count > 0:
                    result_msg = f"🎉 Adlandırma tamamlandı!\n\n✅ Başarılı: {success_count}\n❌ Hatalı: {error_count}\n📁 Çıktı: {base_output_dir.name}"
                    if self.organize_by_class.get():
                        result_msg += f"\n📂 Sınıf organizasyonu: {len(photos_by_class)} sınıf"

                    # Çıktı klasörü erişim butonunu aktif et
                    self.root.after(0, lambda: self.output_access_button.config(state="normal"))

                    # UI thread'de messagebox göster
                    self.root.after(0, lambda: messagebox.showinfo("Başarılı", result_msg))
            else:
                self.update_status("İşlem iptal edildi")

        except Exception as e:
            self.log_message(f"❌ Genel hata: {e}")
            self.update_status("Hata oluştu")

        finally:
            # UI thread'de cleanup
            self.root.after(0, self.operation_finished)

    def crop_and_resize_photos(self):
        """Fotoğrafları boyutlandır ve kırp"""
        try:
            if not self.sizing_enabled.get():
                self.log_message("⚠️ Önce boyutlandırma seçeneğini aktifleştirin.")
                return

            if not self.school_name:
                self.log_message("❌ Önce okul adını girin.")
                return

            if not self.photo_directory:
                self.log_message("❌ Fotoğraf dizini gerekli.")
                return

            # PNG dosyaları için uyarı göster
            png_files = list(self.photo_directory.glob("*.png"))
            if png_files:
                result = messagebox.askyesno("PNG Dosyaları Tespit Edildi", 
                                           f"Dizinde {len(png_files)} adet PNG dosyası bulundu.\n\n"
                                           "⚠️ PNG dosyaları desteklenmektedir ancak en iyi sonuç için JPG formatındaki dosyaları kullanmanız önerilir.\n\n"
                                           "Boyutlandırma ve watermark işlemlerinde JPG formatı daha kararlı sonuçlar verir.\n\n"
                                           "Devam etmek istiyor musunuz?")
                if not result:
                    self.log_message("💭 Kullanıcı PNG dosyaları nedeniyle işlemi iptal etti.")
                    return
                    
                self.log_message(f"⚠️ PNG dosyalarıyla işlem devam ediyor: {len(png_files)} adet")

            # Adlandırma yapılacaksa Excel verisi ve sütun seçimi kontrol et
            use_naming = self.sizing_with_naming.get()
            selected_columns = []

            if use_naming:
                if not self.excel_data:
                    self.log_message("❌ Adlandırma için Excel verisi gerekli.")
                    return

                selected_columns = self.get_selected_columns()
                if not selected_columns:
                    self.log_message("❌ Adlandırma için en az bir sütun seçin.")
                    return

            self.update_status("Fotoğraflar kırpılıyor ve boyutlandırılıyor...")

            # Boyut ayarlarını al
            size_config = self.get_size_configuration()
            if not size_config:
                self.log_message("❌ Boyut yapılandırması alınamadı.")
                return

            # Fotoğrafları al ve sırala
            photos = self.photo_processor.get_image_files(self.photo_directory)
            photos.sort()

            # Ana çıktı dizini oluştur - VesiKolayPro konumunda
            from datetime import datetime
            from utils import VesiKolayUtils
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_school_name = self.clean_filename(self.school_name)

            # VesiKolayPro ana dizininde okul klasörü oluştur
            school_main_dir = VesiKolayUtils.get_school_directory(self.school_name)

            # Tarih-saat alt klasörü
            base_output_dir = school_main_dir / timestamp

            if base_output_dir.exists():
                import time
                time.sleep(1)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_output_dir = school_main_dir / timestamp

            base_output_dir.mkdir(exist_ok=True)

            # Boyutlandırılmış fotoğraflar için dizin
            folder_suffix = "_named" if use_naming else "_original_names"
            sized_dir = base_output_dir / (size_config['folder_name'] + folder_suffix)
            sized_dir.mkdir(exist_ok=True)

            self.log_message(f"\n✂️ === FOTOĞRAF BOYUTLANDIRMA İŞLEMİ BAŞLIYOR ===")
            if use_naming:
                self.log_message(f"📋 Seçilen sütunlar: {', '.join(selected_columns)}")
            else:
                self.log_message(f"📋 Adlandırma: Orijinal dosya adları korunacak")
            self.log_message(f"📏 Boyut: {size_config['display_name']}")
            self.log_message(f"📁 Çıktı dizini: {sized_dir.name}")

            # İlerleme başlat
            if use_naming and self.excel_data:
                total_count = min(len(photos), len(self.excel_data))
            else:
                total_count = len(photos)
            self.progress['maximum'] = total_count

            success_count = 0
            error_count = 0
            processed_photos = []

            for i in range(total_count):
                # İptal kontrolü
                if self.cancel_requested.is_set():
                    self.log_message("⏹️ İşlem kullanıcı tarafından iptal edildi.")
                    break

                try:
                    photo = photos[i]

                    if use_naming and self.excel_data and i < len(self.excel_data):
                        # Adlandırma yapılacak
                        data_record = self.excel_data[i]

                        # Yeni dosya adı oluştur
                        name_parts = []
                        for col in selected_columns:
                            if col in data_record.get('_original_data', {}):
                                value = str(data_record['_original_data'][col]).strip()
                                if value and value != 'nan':
                                    name_parts.append(value)

                        if not name_parts:
                            name_parts = [f"photo_{i+1}"]

                        # Dosya adını temizle ve oluştur
                        separator = self.separator_var.get() if hasattr(self, 'separator_var') else "_"
                        if separator == " ":
                            base_name = " ".join(name_parts)
                        else:
                            base_name = separator.join(name_parts)
                        clean_name = self.clean_filename(base_name, preserve_spaces=(separator == " "))
                    else:
                        # Orijinal dosya adını kullan
                        clean_name = photo.stem

                    # Seçilen formata göre dosya uzantısını belirle
                    # output_format = size_config.get('format', 'jpg') # Çıktı formatı seçimi kaldırıldı
                    file_extension = ".jpg" # Sabit JPG

                    # Çıktı dosya yolu
                    output_path = sized_dir / f"{clean_name}{file_extension}"

                    # Aynı isimde dosya varsa numara ekle
                    counter = 1
                    original_output_path = output_path
                    while output_path.exists():
                        stem = original_output_path.stem
                        suffix = original_output_path.suffix
                        output_path = sized_dir / f"{stem}_{counter}{suffix}"
                        counter += 1

                    # Fotoğrafı kırp ve boyutlandır
                    success = self.process_single_photo(photo, output_path, size_config)

                    if success:
                        processed_photos.append(output_path)
                        success_count += 1
                        self.log_message(f"✅ {i+1:3d}. {photo.name} → {output_path.name}")
                    else:
                        error_count += 1
                        self.log_message(f"❌ {i+1:3d}. {photo.name} - Boyutlandırma başarısız")

                except Exception as e:
                    error_count += 1
                    self.log_message(f"❌ Hata {i+1}: {photo.name} - {e}")

                # İlerlemeyi güncelle
                self.progress['value'] = i + 1
                self.update_status(f"İşleniyor: {i+1}/{total_count}")

            # Sonuçları göster
            if not self.cancel_requested.is_set():
                self.log_message(f"\n🎉 === BOYUTLANDIRMA İŞLEMİ TAMAMLANDI ===")
                self.log_message(f"✅ Başarılı: {success_count}")
                self.log_message(f"❌ Hatalı: {error_count}")
                self.log_message(f"📊 Toplam: {total_count}")
                self.log_message(f"📁 Çıktı dizini: {sized_dir.name}")

                self.update_status(f"Tamamlandı: {success_count}/{total_count} başarılı")

                if success_count > 0:
                    naming_info = " (Yeniden adlandırıldı)" if use_naming else " (Orijinal adlar)"
                    result_msg = f"✂️ Boyutlandırma tamamlandı!{naming_info}\n\n✅ Başarılı: {success_count}\n❌ Hatalı: {error_count}\n📁 Çıktı: {sized_dir.name}"
                    
                    # Çıktı klasörü erişim butonunu aktif et
                    self.root.after(0, lambda: self.output_access_button.config(state="normal"))
                    
                    self.root.after(0, lambda: messagebox.showinfo("Başarılı", result_msg))
            else:
                self.update_status("İşlem iptal edildi")

        except Exception as e:
            self.log_message(f"❌ Genel hata: {e}")
            self.update_status("Hata oluştu")

        finally:
            self.root.after(0, self.operation_finished)

    def generate_class_pdfs(self):
        """Sınıf bazında PDF'leri oluştur"""
        try:
            if not self.school_name:
                self.log_message("❌ Önce okul adını girin.")
                return

            if not self.excel_data or not self.photo_directory:
                self.log_message("❌ Excel verisi ve fotoğraf dizini gerekli.")
                return

            selected_columns = self.get_selected_columns()
            if not selected_columns:
                self.log_message("❌ PDF oluşturmak için sütun seçimi gerekli.")
                return

            self.update_status("PDF dosyaları oluşturuluyor...")

            from pdf_generator import PDFGenerator
            from utils import VesiKolayUtils

            # VesiKolayPro ana dizinindeki okul klasörünü bul
            school_main_dir = VesiKolayUtils.get_school_directory(self.school_name)

            # En son oluşturulan tarih-saat klasörünü bul
            timestamp_dirs = [d for d in school_main_dir.iterdir() 
                             if d.is_dir() and d.name.replace('_', '').replace('-', '').isdigit()]

            if not timestamp_dirs:
                self.log_message("❌ Önce fotoğrafları adlandırın.")
                return

            # En son oluşturulan dizini seç
            base_output_dir = max(timestamp_dirs, key=lambda x: x.stat().st_mtime)
            renamed_dir = base_output_dir / "renamed"

            if not renamed_dir.exists():
                self.log_message("❌ Adlandırılmış fotoğraflar bulunamadı. Önce fotoğrafları adlandırın.")
                return

            # PDF çıktı dizini
            pdf_dir = base_output_dir / "pdfs"
            pdf_dir.mkdir(parents=True, exist_ok=True)

            # Adlandırılmış fotoğrafları al
            renamed_photos = self.photo_processor.get_image_files(renamed_dir)
            renamed_photos.sort()

            # Sınıf bazında fotoğrafları grupla - manuel olarak yapıyoruz
            photos_by_class = {}

            for i, photo_path in enumerate(renamed_photos):
                if self.cancel_requested.is_set():
                    break

                if i < len(self.excel_data):
                    record = self.excel_data[i]

                    # Sınıf adını al
                    class_name = record.get('class_name', record.get('sınıf', 'Sınıf_Bilgisi_Yok'))
                    if not class_name or str(class_name).lower() in ['nan', 'none', '']:
                        class_name = 'Sınıf_Bilgisi_Yok'

                    # Öğrenci adını oluştur
                    name_parts = []
                    for col in selected_columns:
                        if col in record.get('_original_data', {}):
                            value = str(record['_original_data'][col]).strip()
                            if value and value != 'nan':
                                name_parts.append(value)

                    if not name_parts:
                        name_parts = [f"Öğrenci_{i+1}"]

                    student_name = " ".join(name_parts)

                    # Sınıf listesine ekle
                    if class_name not in photos_by_class:
                        photos_by_class[class_name] = []

                    photos_by_class[class_name].append({
                        'filename': photo_path.name,
                        'name': student_name,
                        'display_name': student_name
                    })

            if not photos_by_class:
                self.log_message("❌ Sınıf bilgisi bulunamadı veya fotoğraflar henüz adlandırılmamış.")
                self.update_status("PDF oluşturulamadı - Sınıf bilgisi yok")
                return

            # PDF generator
            pdf_generator = PDFGenerator()

            self.log_message(f"\n📄 === PDF OLUŞTURMA BAŞLIYOR ===")
            self.log_message(f"📂 {len(photos_by_class)} sınıf için PDF oluşturulacak")

            success_count = 0
            total_classes = len(photos_by_class)

            for i, (class_name, photos_info) in enumerate(photos_by_class.items()):
                if self.cancel_requested.is_set():
                    break

                try:
                    self.update_status(f"PDF oluşturuluyor: {i+1}/{total_classes}")

                    # Güvenli dosya adı oluştur
                    safe_class_name = self.clean_filename(class_name)
                    pdf_path = pdf_dir / f"{safe_class_name}_fotoğraf_listesi.pdf"

                    # Okul adını al
                    school_name = self.school_name if self.school_name else "VesiKolay Pro"

                    # PDF oluştur - fotoğraf grid formatında
                    success = pdf_generator.generate_class_photo_grid(
                        photos_with_names=photos_info,
                        class_name=class_name,
                        school_name=school_name,
                        output_path=pdf_path,
                        photos_dir=renamed_dir
                    )
                    
                    # İlerleme güncelleme
                    self.update_progress_with_percentage(i + 1, total_classes)

                    if success:
                        success_count += 1
                        self.log_message(f"✅ {class_name}: {pdf_path.name} ({len(photos_info)} fotoğraf)")
                    else:
                        self.log_message(f"❌ {class_name}: PDF oluşturulamadı")

                except Exception as e:
                    self.log_message(f"❌ {class_name}: {e}")

            if not self.cancel_requested.is_set():
                self.log_message(f"\n🎉 PDF oluşturma tamamlandı!")
                self.log_message(f"✅ Başarılı: {success_count}/{total_classes} sınıf")
                self.log_message(f"📁 PDF dizini: {pdf_dir.name}")

                self.update_status(f"PDF tamamlandı: {success_count}/{total_classes}")

                if success_count > 0:
                    result_msg = f"📄 PDF oluşturma tamamlandı!\n\n✅ {success_count}/{total_classes} sınıf\n📁 Konum: {pdf_dir.name}"
                    
                    # PDF erişim butonunu aktif et
                    self.root.after(0, lambda: self.pdf_access_button.config(state="normal"))
                    
                    self.root.after(0, lambda: messagebox.showinfo("Başarılı", result_msg))
            else:
                self.update_status("İşlem iptal edildi")

        except Exception as e:
            self.log_message(f"❌ PDF oluşturma hatası: {e}")
            self.update_status("PDF oluşturma hatası")

        finally:
            self.root.after(0, self.operation_finished)

    def generate_id_cards(self):
        """Öğrenci kimlik kartlarını oluştur"""
        try:
            if not self.school_name:
                self.log_message("❌ Önce okul adını girin.")
                return

            if not self.excel_data or not self.photo_directory:
                self.log_message("❌ Excel verisi ve fotoğraf dizini gerekli.")
                return

            self.update_status("Kimlik kartları oluşturuluyor...")

            from pdf_generator import PDFGenerator
            from utils import VesiKolayUtils

            # VesiKolayPro ana dizinindeki okul klasörünü bul
            school_main_dir = VesiKolayUtils.get_school_directory(self.school_name)

            # En son oluşturulan tarih-saat klasörünü bul
            timestamp_dirs = [d for d in school_main_dir.iterdir() 
                             if d.is_dir() and d.name.replace('_', '').replace('-', '').isdigit()]

            if not timestamp_dirs:
                self.log_message("❌ Önce fotoğrafları adlandırın.")
                return

            # En son oluşturulan dizini seç
            base_output_dir = max(timestamp_dirs, key=lambda x: x.stat().st_mtime)
            renamed_dir = base_output_dir / "renamed"

            if not renamed_dir.exists():
                self.log_message("❌ Adlandırılmış fotoğraflar bulunamadı.")
                return

            # Kimlik kartı çıktı dizini
            id_card_dir = base_output_dir / "id_cards"
            id_card_dir.mkdir(parents=True, exist_ok=True)

            # PDF generator
            pdf_generator = PDFGenerator()

            # Set school logo path if available
            if hasattr(self, 'school_logo_path'):
                pdf_generator.school_logo_path = self.school_logo_path

            # Kapsam tipine göre filtreleme yap
            scope_type = getattr(self, 'id_card_scope_type', 'all')
            selected_items = getattr(self, 'id_card_selected_items', None)
            
            # İşlenecek kayıtları belirle
            if scope_type == "class" and selected_items:
                # Sınıf bazlı filtreleme
                filtered_data = []
                for i, record in enumerate(self.excel_data):
                    class_name = record.get('class_name', record.get('sınıf', ''))
                    if str(class_name) in selected_items:
                        filtered_data.append((i, record))
                self.log_message(f"📚 Seçili sınıflar: {', '.join(selected_items)}")
                self.log_message(f"👥 Filtrelenmiş öğrenci sayısı: {len(filtered_data)}")
            elif scope_type == "individual" and selected_items:
                # Bireysel filtreleme
                filtered_data = []
                for index in selected_items:
                    if index < len(self.excel_data):
                        filtered_data.append((index, self.excel_data[index]))
                self.log_message(f"👤 Seçili öğrenci sayısı: {len(filtered_data)}")
            else:
                # Tüm liste
                filtered_data = [(i, record) for i, record in enumerate(self.excel_data)]
                self.log_message(f"📋 Tüm öğrenci listesi: {len(filtered_data)} öğrenci")

            # Öğrenci verilerini hazırla ve fotoğraf dosya adlarını eşleştir
            students_for_cards = []
            renamed_photos = self.photo_processor.get_image_files(renamed_dir)

            for original_index, record in filtered_data:
                if self.cancel_requested.is_set():
                    break

                # Fotoğraf dosya adını belirle
                photo_filename = ""
                if original_index < len(renamed_photos):
                    photo_filename = renamed_photos[original_index].name

                # Kullanıcının seçtiği sütunlardan veri oluştur
                student_data = {
                    'school_name': self.school_name,
                    'photo_filename': photo_filename,
                    'school_year': self.school_year_var.get() if hasattr(self, 'school_year_var') else "2025-2026",
                    'selected_columns': getattr(self, 'id_card_selected_columns', []),
                    'column_data': {}
                }
                
                # Seçili sütunlar için verileri ekle
                if hasattr(self, 'id_card_selected_columns'):
                    for column in self.id_card_selected_columns:
                        if column in record.get('_original_data', {}):
                            value = str(record['_original_data'][column]).strip()
                            if value and value != 'nan':
                                student_data['column_data'][column] = value
                            else:
                                student_data['column_data'][column] = ""
                        else:
                            student_data['column_data'][column] = ""
                
                # Gradient renk ayarlarını ekle
                if hasattr(self, 'id_card_color_settings'):
                    student_data.update(self.id_card_color_settings)
                
                students_for_cards.append(student_data)

            # Logo yollarını kimlik kartı verilerine ekle
            main_logo_path = None
            second_logo_path = None
            
            if hasattr(self, 'id_card_settings'):
                main_logo_path = self.id_card_settings.get('main_logo_path')
                second_logo_path = self.id_card_settings.get('second_logo_path')
            
            # Fallback to old logo path
            if not main_logo_path:
                if hasattr(self, 'id_card_logo_path') and self.id_card_logo_path:
                    main_logo_path = self.id_card_logo_path
                elif hasattr(self, 'school_logo_path') and self.school_logo_path:
                    main_logo_path = self.school_logo_path
            
            for student in students_for_cards:
                if main_logo_path:
                    student['main_logo_path'] = str(main_logo_path)
                    student['logo_path'] = str(main_logo_path)  # Backward compatibility
                if second_logo_path:
                    student['second_logo_path'] = str(second_logo_path)
                
                # Add all ID card settings
                if hasattr(self, 'id_card_settings'):
                    student.update(self.id_card_settings)

            if self.cancel_requested.is_set():
                self.update_status("İşlem iptal edildi")
                return

            # Okul adını temizle
            clean_school_name = self.clean_filename(self.school_name)
            
            # Kapsama göre dosya adı oluştur
            if scope_type == "class" and selected_items:
                class_suffix = "_".join([self.clean_filename(c) for c in selected_items[:3]])
                if len(selected_items) > 3:
                    class_suffix += "_ve_diger"
                pdf_path = id_card_dir / f"{clean_school_name}_kimlik_kartlari_{class_suffix}.pdf"
            elif scope_type == "individual":
                pdf_path = id_card_dir / f"{clean_school_name}_secili_ogrenci_kimlik_kartlari.pdf"
            else:
                pdf_path = id_card_dir / f"{clean_school_name}_ogrenci_kimlik_kartlari.pdf"

            # İlerleme callback fonksiyonu tanımla
            def progress_callback(progress_percent, message):
                # Ana thread'e güvenli şekilde ilerleme güncellemesi gönder
                self.root.after(0, lambda: self.update_progress_with_percentage(
                    int(progress_percent), 100))
                self.root.after(0, lambda: self.update_status(message, "processing"))

            success = pdf_generator.generate_id_cards(
                people=students_for_cards,
                template_type="student", 
                output_path=pdf_path,
                photos_dir=renamed_dir,
                progress_callback=progress_callback
            )

            if success and not self.cancel_requested.is_set():
                self.log_message(f"\n🆔 === KİMLİK KARTLARI OLUŞTURULDU ===")
                self.log_message(f"✅ {len(students_for_cards)} öğrenci kimlik kartı")
                self.log_message(f"📁 Çıktı: {pdf_path.name}")

                self.update_status(f"Kimlik kartları tamamlandı: {len(students_for_cards)} öğrenci")

                # Kimlik kartları erişim butonunu aktif et
                self.root.after(0, lambda: self.id_cards_access_button.config(state="normal"))

                result_msg = f"🆔 Kimlik kartları oluşturuldu!\n\n✅ {len(students_for_cards)} öğrenci\n📁 Konum: {id_card_dir.name}"
                self.root.after(0, lambda: messagebox.showinfo("Başarılı", result_msg))
            elif self.cancel_requested.is_set():
                self.update_status("İşlem iptal edildi")
            else:
                self.log_message("❌ Kimlik kartları oluşturulamadı.")

        except Exception as e:
            self.log_message(f"❌ Kimlik kartı oluşturma hatası: {e}")
            self.update_status("Kimlik kartı hatası")

        finally:
            self.root.after(0, self.operation_finished)

    def _get_custom_file_size_limit(self):
        """Özel boyut için dosya boyutu sınırını hesapla"""
        if not hasattr(self, 'custom_max_size_var') or not self.custom_max_size_var.get().strip():
            return None  # Sınır yok

        try:
            max_size_kb = int(self.custom_max_size_var.get())
            if max_size_kb > 0:
                return (1, max_size_kb)  # Min 1 KB, Max kullanıcı tanımlı
            else:
                return None
        except ValueError:
            return None

    def get_size_configuration(self):
        """Seçilen boyut yapılandırmasını döndür"""
        selected_display = self.size_combo.get()
        size_type = self.size_display_values.get(selected_display, "e_okul")
        # output_format = self.output_format.get() # Çıktı formatı seçimi kaldırıldı
        output_format = 'jpg' # Sabit JPG

        configurations = {
            'e_okul': {
                'width_mm': 35,
                'height_mm': 45,
                'display_name': '35mm x 45mm (E-Okul)',
                'folder_name': 'E-Okul',
                'file_size_limit': (20, 150),  # KB cinsinden min-max
                'quality': 85,
                'dpi': 300,  # Minimum 300 DPI
                'format': output_format
            },
            'acik_lise': {
                'width_px': 394,
                'height_px': 512,
                'display_name': '394px x 512px (Açık Lise)',
                'folder_name': 'Acik_Lise',
                'file_size_limit': (1, 150),  # KB cinsinden min-max
                'quality': 90,
                'dpi': 400,  # Açık Lise için zorunlu 400 DPI
                'min_dpi': 400,  # Minimum DPI kontrolü
                'format': 'jpg',
                'force_biometric': True,  # Biyometrik kırpma zorla
                'white_background': True  # Beyaz arka plan zorla
            },
            'mebbis': {
                'width_px': 394,
                'height_px': 512,
                'display_name': '394px x 512px (MEBBIS)',
                'folder_name': 'MEBBIS',
                'file_size_limit': (1, 150),  # KB cinsinden min-max
                'quality': 90,
                'dpi': 300,  # 300 DPI
                'format': 'jpg',
                'force_biometric': True,  # Biyometrik kırpma zorla
                'white_background': True  # Beyaz arka plan zorla
            },
            'biometric': {
                'width_mm': 50,
                'height_mm': 60,
                'display_name': '50mm x 60mm (Biyometrik)',
                'folder_name': 'Biyometrik',
                'file_size_limit': None,  # Dosya boyutu sınırı yok
                'quality': 95,
                'dpi': 300,  # Minimum 300 DPI
                'format': output_format
            },
            'vesikalik': {
                'width_mm': 45,
                'height_mm': 60,
                'display_name': '45mm x 60mm (Vesikalık)',
                'folder_name': 'Vesikalik',
                'file_size_limit': None,  # Dosya boyutu sınırı yok
                'quality': 95,
                'dpi': 300,  # Minimum 300 DPI
                'format': output_format
            },
            'passport': {
                'width_mm': 35,
                'height_mm': 35,
                'display_name': '35mm x 35mm (Pasaport/Vize)',
                'folder_name': 'Pasaport',
                'file_size_limit': None,  # Dosya boyutu sınırı yok
                'quality': 95,
                'dpi': 300,  # Minimum 300 DPI
                'format': output_format
            },
            'license': {
                'width_mm': 25,
                'height_mm': 35,
                'display_name': '25mm x 35mm (Ehliyet)',
                'folder_name': 'Ehliyet',
                'file_size_limit': None,  # Dosya boyutu sınırı yok
                'quality': 95,
                'dpi': 300,  # Minimum 300 DPI
                'format': output_format
            },
            'custom': {
                'width': float(self.custom_width_var.get()) if self.custom_width_var.get().replace('.', '').replace(',', '').isdigit() else 35,
                'height': float(self.custom_height_var.get()) if self.custom_height_var.get().replace('.', '').replace(',', '').isdigit() else 45,
                'width_mm': float(self.custom_width_var.get()) if self.custom_width_var.get().replace('.', '').replace(',', '').isdigit() else 35,
                'height_mm': float(self.custom_height_var.get()) if self.custom_height_var.get().replace('.', '').replace(',', '').isdigit() else 45,
                'unit': self.custom_unit_var.get() if hasattr(self, 'custom_unit_var') else 'mm',
                'display_name': f'{self.custom_width_var.get()}{self.custom_unit_var.get() if hasattr(self, "custom_unit_var") else "mm"} x {self.custom_height_var.get()}{self.custom_unit_var.get() if hasattr(self, "custom_unit_var") else "mm"} (Özel)',
                'folder_name': 'Ozel_Boyut',
                'file_size_limit': self._get_custom_file_size_limit(),
                'quality': 95,
                'dpi': int(self.custom_dpi_var.get()) if hasattr(self, 'custom_dpi_var') and self.custom_dpi_var.get().isdigit() else 300,
                'format': output_format
            },
            'original': {
                'width_mm': 0,
                'height_mm': 0,
                'display_name': 'Orijinal Boyut',
                'folder_name': 'Orijinal',
                'file_size_limit': None,
                'quality': 95,
                'dpi': 300,
                'format': 'original'
            }
        }

        return configurations.get(size_type)

    def process_single_photo(self, input_path, output_path, size_config):
        """Tek bir fotoğrafı işle (kırp ve boyutlandır)"""
        try:
            # Dosya varlığını kontrol et
            if not input_path.exists():
                self.log_message(f"❌ Dosya bulunamadı: {input_path}")
                return False

            # Dosya boyutunu kontrol et
            if input_path.stat().st_size == 0:
                self.log_message(f"❌ Boş dosya: {input_path}")
                return False

            from photo_processor import CropDimensions

            # Orijinal format korunacaksa dosya uzantısını al
            # if size_config.get('format') == 'original': # Çıktı formatı seçimi kaldırıldı
            #     original_extension = input_path.suffix.lower()
            #     output_path = output_path.with_suffix(original_extension)

            # Boyutları belirle (pixel veya mm)
            dpi = size_config.get('dpi', 300)
            min_dpi = size_config.get('min_dpi', None)

            if 'width_px' in size_config and 'height_px' in size_config:
                # Pixel boyutları (Açık Lise gibi)
                dimensions = CropDimensions(
                    width=size_config['width_px'],
                    height=size_config['height_px'],
                    unit='px',
                    dpi=dpi,
                    min_dpi=min_dpi
                )
            elif size_config.get('unit') == 'px' or 'width_px' in size_config:
                # Pixel boyutları
                width = size_config.get('width_px', size_config.get('width', 300))
                height = size_config.get('height_px', size_config.get('height', 400))
                dimensions = CropDimensions(
                    width=int(width),
                    height=int(height),
                    unit='px',
                    dpi=dpi,
                    min_dpi=min_dpi
                )
            elif size_config.get('unit') == 'cm':
                # cm boyutları
                width = size_config.get('width_cm', size_config.get('width', 3.5))
                height = size_config.get('height_cm', size_config.get('height', 4.5))
                dimensions = CropDimensions(
                    width=float(width),
                    height=float(height),
                    unit='cm',
                    dpi=dpi,
                    min_dpi=min_dpi
                )
            else:
                # mm boyutları (varsayılan)
                width = size_config.get('width_mm', size_config.get('width', 35))
                height = size_config.get('height_mm', size_config.get('height', 45))
                dimensions = CropDimensions(
                    width=float(width),
                    height=float(height),
                    unit='mm',
                    dpi=dpi,
                    min_dpi=min_dpi
                )

            # Çıktı dosya formatını ayarla
            # output_format = size_config.get('format', 'jpg') # Çıktı formatı seçimi kaldırıldı
            output_format = 'jpg' # Sabit JPG
            if output_format == 'original':
                # Orijinal formatı koru
                pass  # output_path zaten yukarıda ayarlandı
            elif output_format == 'png':
                output_path = output_path.with_suffix('.png')
            else:
                output_path = output_path.with_suffix('.jpg')

            success = False

            # Açık Lise/MEBBIS için özel işleme
            if size_config.get('force_biometric'):
                try:
                    # Boyut tipine göre farklı fonksiyon çağır
                    selected_display = self.size_combo.get()
                    size_type = self.size_display_values.get(selected_display, "e_okul")

                    if size_type == 'mebbis':
                        success = self.photo_processor.crop_face_biometric_mebbis(
                            input_path, 
                            output_path, 
                            dimensions,
                            white_background=size_config.get('white_background', False)
                        )
                        if success:
                            self.log_message(f"   🎯 MEBBIS biyometrik kırpma kullanıldı")
                    else:
                        success = self.photo_processor.crop_face_biometric_acik_lise(
                            input_path, 
                            output_path, 
                            dimensions,
                            white_background=size_config.get('white_background', False)
                        )
                        if success:
                            self.log_message(f"   🎯 Açık Lise biyometrik kırpma kullanıldı")
                except Exception as bio_error:
                    self.log_message(f"   ⚠️ Biyometrik kırpma hatası: {bio_error}")
                    success = False
            else:
                # Diğer formatlar için normal yüz algılama
                try:
                    success = self.photo_processor.crop_face_auto(
                        input_path, 
                        output_path, 
                        dimensions,
                        padding_factor=0.15  # Daha az padding
                    )
                except Exception as face_error:
                    self.log_message(f"   ⚠️ Yüz algılama hatası: {face_error}")
                    success = False

            # Yüz algılanamadığında merkezi kırpma
            if not success:
                try:
                    success = self.photo_processor.crop_image(
                        input_path,
                        output_path,
                        dimensions
                    )
                    if success:
                        self.log_message(f"   📐 Merkezi kırpma kullanıldı")
                except Exception as crop_error:
                    self.log_message(f"   ❌ Kırpma hatası: {crop_error}")
                    return False

            # Watermark ekle (eğer aktifse)
            if success and self.watermark_enabled.get():
                try:
                    self.apply_watermark_to_photo(output_path)
                except Exception as watermark_error:
                    self.log_message(f"   ⚠️ Watermark ekleme hatası: {watermark_error}")

            # E-Okul için dosya boyutu kontrolü
            if success and size_config.get('file_size_limit'):
                try:
                    success = self.optimize_file_size(output_path, size_config)
                    if success:
                        final_size = output_path.stat().st_size / 1024
                        self.log_message(f"   📏 Dosya boyutu optimize edildi: {final_size:.1f} KB")
                except Exception as size_error:
                    self.log_message(f"   ⚠️ Dosya boyutu optimizasyonu hatası: {size_error}")

            return success

        except Exception as e:
            self.log_message(f"❌ Fotoğraf işleme genel hatası: {e}")
            return False

    def optimize_file_size(self, file_path, size_config):
        """Dosya boyutunu optimize et (sadece E-Okul için)"""
        try:
            min_kb, max_kb = size_config['file_size_limit']
            min_bytes = min_kb * 1024
            max_bytes = max_kb * 1024

            from PIL import Image
            import os

            # Mevcut dosya boyutunu kontrol et
            current_size = os.path.getsize(file_path)

            if min_bytes <= current_size <= max_bytes:
                return True

            # Dosya formatını al
            # output_format = size_config.get('format', 'jpg') # Çıktı formatı seçimi kaldırıldı
            output_format = 'jpg' # Sabit JPG

            # Dosya boyutu uygun değilse kaliteyi ayarla
            quality = size_config['quality']
            original_quality = quality

            # Dosya çok büyükse kaliteyi düşür
            while current_size > max_bytes and quality > 20:
                quality -= 5

                with Image.open(file_path) as img:
                    # DPI bilgisini koru
                    dpi_info = img.info.get('dpi', (300, 300))

                    if output_format.lower() == 'png':
                        img.save(file_path, format='PNG', optimize=True, dpi=dpi_info)
                    else:
                        img.save(file_path, format='JPEG', quality=quality, optimize=True, dpi=dpi_info)

                current_size = os.path.getsize(file_path)

            # Dosya çok küçükse kaliteyi artır (sadece JPEG için)
            if current_size < min_bytes and quality < original_quality and output_format.lower() == 'jpg':
                quality = min(95, quality + 20)
                with Image.open(file_path) as img:
                    # DPI bilgisini koru
                    dpi_info = img.info.get('dpi', (300, 300))
                    img.save(file_path, format='JPEG', quality=quality, optimize=True, dpi=dpi_info)

            final_size = os.path.getsize(file_path)
            final_kb = final_size / 1024

            # Hedef aralıkta mı kontrol et
            if min_kb <= final_kb <= max_kb:
                return True
            else:
                self.log_message(f"   ⚠️ Dosya boyutu hedef aralığa getirilemedi: {final_kb:.1f} KB (Format: {output_format.upper()})")
                return True  # Yine de devam et

        except Exception as e:
            self.log_message(f"❌ Dosya boyutu optimizasyonu hatası: {e}")
            return False

    def apply_watermark_to_photo(self, photo_path: Path):
        """Fotoğrafa sadece metin watermark ekle"""
        try:
            # Dosya var mı kontrol et
            if not photo_path.exists():
                self.log_message(f"❌ Watermark eklenecek dosya bulunamadı: {photo_path}")
                return

            watermark_text = self.watermark_text_var.get().strip()
            if not watermark_text:
                return

            # PNG dosyası için uyarı
            if photo_path.suffix.lower() == '.png':
                self.log_message(f"⚠️ PNG dosyasına watermark ekleniyor: {photo_path.name}")

            from PIL import Image, ImageDraw, ImageFont

            with Image.open(photo_path) as img:
                # Format kontrolü
                is_png = photo_path.suffix.lower() == '.png'

                if is_png and img.mode != 'RGBA':
                    img = img.convert('RGBA')
                elif not is_png and img.mode != 'RGB':
                    img = img.convert('RGB')

                if is_png:
                    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                else:
                    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))

                draw = ImageDraw.Draw(overlay)

                font_size = max(20, min(img.width, img.height) // 30)
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()

                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                margin = 20
                x = img.width - text_width - margin
                y = img.height - text_height - margin

                bg_padding = 10
                draw.rectangle(
                    [x - bg_padding, y - bg_padding, 
                     x + text_width + bg_padding, y + text_height + bg_padding],
                    fill=(0, 0, 0, 128)
                )

                draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 200))

                if is_png:
                    watermarked = Image.alpha_composite(img, overlay)
                    watermarked.save(photo_path, format='PNG', optimize=True)
                else:
                    watermarked = Image.alpha_composite(img.convert('RGBA'), overlay)
                    watermarked = watermarked.convert('RGB')
                    watermarked.save(photo_path, format='JPEG', quality=95, optimize=True)

        except Exception as e:
            self.log_message(f"❌ Watermark ekleme hatası: {e}")

    def clean_filename(self, filename: str, preserve_spaces: bool = False) -> str:
        """Dosya adını temizle"""
        # Geçersiz karakterleri kaldır
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        if not preserve_spaces:
            # Boşlukları alt çizgi ile değiştir (sadece preserve_spaces False ise)
            filename = filename.replace(' ', '_')

            # Çoklu alt çizgileri tekle
            while '__' in filename:
                filename = filename.replace('__', '_')

            # Baştan ve sondan alt çizgi kaldır
            filename = filename.strip('_')
        else:
            # Boşlukları koru ama çoklu boşlukları tekle
            filename = ' '.join(filename.split())

        # Boş ise varsayılan ad ver
        if not filename:
            filename = 'unnamed'

        return filename

    def open_output_directory(self):
        """Çıktı dizinini aç"""
        if not self.school_name:
            messagebox.showwarning("Uyarı", "Önce okul adını girin.")
            return

        if not self.photo_directory:
            messagebox.showwarning("Uyarı", "Önce fotoğraf dizini seçin.")
            return

        # VesiKolayPro ana dizinindeki okul klasörünü aç
        from utils import VesiKolayUtils
        school_output_dir = VesiKolayUtils.get_school_directory(self.school_name)

        if school_output_dir.exists():
            # İşletim sistemine göre dizin açma
            import subprocess
            import sys
            try:
                if sys.platform == "win32":
                    subprocess.run(["explorer", str(school_output_dir)])
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(school_output_dir)])
                else:
                    subprocess.run(["xdg-open", str(school_output_dir)])
                self.log_message(f"📁 Okul çıktı dizini açıldı: {school_output_dir.name}")
            except Exception as e:
                self.log_message(f"📁 Okul çıktı dizini yolu: {school_output_dir}")
                self.log_message(f"❌ Dizin açma hatası: {e}")
        else:
            self.log_message("❌ Henüz bu okul için çıktı dizini oluşturulmamış.")

    def open_pdf_directory(self):
        """PDF dizinini aç"""
        if not self.school_name:
            messagebox.showwarning("Uyarı", "Önce okul adını girin.")
            return

        # VesiKolayPro ana dizinindeki okul klasörünü bul
        from utils import VesiKolayUtils
        school_main_dir = VesiKolayUtils.get_school_directory(self.school_name)

        if not school_main_dir.exists():
            self.log_message("❌ Henüz bu okul için çıktı dizini oluşturulmamış.")
            return

        # En son oluşturulan tarih-saat klasörünü bul
        timestamp_dirs = [d for d in school_main_dir.iterdir() 
                         if d.is_dir() and d.name.replace('_', '').replace('-', '').isdigit()]

        if not timestamp_dirs:
            self.log_message("❌ Henüz PDF dosyası oluşturulmamış.")
            return

        # En son oluşturulan dizindeki PDF klasörünü aç
        latest_dir = max(timestamp_dirs, key=lambda x: x.stat().st_mtime)
        pdf_dir = latest_dir / "pdfs"

        if pdf_dir.exists():
            import subprocess
            import sys
            try:
                if sys.platform == "win32":
                    subprocess.run(["explorer", str(pdf_dir)])
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(pdf_dir)])
                else:
                    subprocess.run(["xdg-open", str(pdf_dir)])
                self.log_message(f"📄 PDF dizini açıldı: {pdf_dir.name}")
            except Exception as e:
                self.log_message(f"📄 PDF dizini yolu: {pdf_dir}")
                self.log_message(f"❌ Dizin açma hatası: {e}")
        else:
            self.log_message("❌ Henüz PDF dosyası oluşturulmamış.")

    def open_id_cards_directory(self):
        """Kimlik kartları dizinini aç"""
        if not self.school_name:
            messagebox.showwarning("Uyarı", "Önce okul adını girin.")
            return

        # VesiKolayPro ana dizinindeki okul klasörünü bul
        from utils import VesiKolayUtils
        school_main_dir = VesiKolayUtils.get_school_directory(self.school_name)

        if not school_main_dir.exists():
            self.log_message("❌ Henüz bu okul için çıktı dizini oluşturulmamış.")
            return

        # En son oluşturulan tarih-saat klasörünü bul
        timestamp_dirs = [d for d in school_main_dir.iterdir() 
                         if d.is_dir() and d.name.replace('_', '').replace('-', '').isdigit()]

        if not timestamp_dirs:
            self.log_message("❌ Henüz kimlik kartı oluşturulmamış.")
            return

        # En son oluşturulan dizindeki kimlik kartları klasörünü aç
        latest_dir = max(timestamp_dirs, key=lambda x: x.stat().st_mtime)
        id_cards_dir = latest_dir / "id_cards"

        if id_cards_dir.exists():
            import subprocess
            import sys
            try:
                if sys.platform == "win32":
                    subprocess.run(["explorer", str(id_cards_dir)])
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(id_cards_dir)])
                else:
                    subprocess.run(["xdg-open", str(id_cards_dir)])
                self.log_message(f"🆔 Kimlik kartları dizini açıldı: {id_cards_dir.name}")
            except Exception as e:
                self.log_message(f"🆔 Kimlik kartları dizini yolu: {id_cards_dir}")
                self.log_message(f"❌ Dizin açma hatası: {e}")
        else:
            self.log_message("❌ Henüz kimlik kartı oluşturulmamış.")

    def create_footer(self):
        """Footer bölümünü oluştur"""
        footer_frame = tk.Frame(self.main_container, bg=ModernUI.COLORS['dark'], height=35)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)

        program_info = "VesiKolay Pro v1.0"
        link_text = "https://github.com/muallimun/VesiKolayPro"

        # Program bilgisi container
        program_info_container = tk.Frame(footer_frame, bg=ModernUI.COLORS['dark'])
        program_info_container.pack(side=tk.LEFT, padx=8, pady=8)
        
        # Program ismi ve versiyon
        info_label = tk.Label(program_info_container, text=program_info, 
                             fg=ModernUI.COLORS['light'], 
                             bg=ModernUI.COLORS['dark'],
                             font=('Segoe UI', 8),
                             cursor="hand2")
        info_label.pack(side=tk.LEFT)
        info_label.bind("<Button-1>", lambda e: self.open_link("https://www.muallimun.com/VesiKolayPro/"))
        ToolTip(info_label, "Muallimun.Net'e ulaşmak için TIKLAYINIZ.")
        
        # Güncelleme ikonu
        update_icon_label = tk.Label(program_info_container, 
                                   text="🔄", 
                                   fg='lightgreen', 
                                   bg=ModernUI.COLORS['dark'],
                                   font=('Segoe UI', 10),
                                   cursor="hand2")
        update_icon_label.pack(side=tk.LEFT, padx=(5, 0))
        update_icon_label.bind("<Button-1>", lambda e: self.check_for_updates_manual())
        ToolTip(update_icon_label, "Güncellemeleri kontrol et - VesiKolay Pro'nun yeni versiyonu var mı?")

        # Merkez container - logo ve link için
        center_frame = tk.Frame(footer_frame, bg=ModernUI.COLORS['dark'])
        center_frame.pack(expand=True)

        # Muallimun logo ve link container
        muallimun_container = tk.Frame(center_frame, bg=ModernUI.COLORS['dark'])
        muallimun_container.pack(pady=3)

        # Muallimun logosu
        try:
            from PIL import Image, ImageTk
            muallimun_logo_path = Path(__file__).parent / "images" / "muallimun.png"
            if muallimun_logo_path.exists():
                muallimun_image = Image.open(muallimun_logo_path)
                # Logo boyutunu footer'a uygun şekilde ayarla (yükseklik: 25px)
                logo_height = 25
                img_width, img_height = muallimun_image.size
                logo_width = int((img_width * logo_height) / img_height)
                muallimun_resized = muallimun_image.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                self.muallimun_logo = ImageTk.PhotoImage(muallimun_resized)
                
                muallimun_logo_label = tk.Label(muallimun_container,
                                              image=self.muallimun_logo,
                                              bg=ModernUI.COLORS['dark'],
                                              cursor="hand2")
                muallimun_logo_label.pack(side=tk.LEFT, padx=(0, 5))
                muallimun_logo_label.bind("<Button-1>", lambda e: self.open_link("https://www.muallimun.com/"))
                ToolTip(muallimun_logo_label, "Muallimun.Net'e ulaşmak için TIKLAYINIZ.")
            else:
                print("⚠️ Muallimun logosu bulunamadı")
        except Exception as e:
            print(f"⚠️ Muallimun logosu yüklenirken hata: {e}")

        

        # Sağ taraf container
        right_frame = tk.Frame(footer_frame, bg=ModernUI.COLORS['dark'])
        right_frame.pack(side=tk.RIGHT, padx=8, pady=8)

        # Güncelleme kontrol butonu
        update_button = tk.Label(right_frame, text="🔄 Güncelleme Kontrol Et", 
                                fg='lightblue', 
                                bg=ModernUI.COLORS['dark'], 
                                cursor="hand2",
                                font=('Segoe UI', 8))
        update_button.pack(side=tk.RIGHT, padx=(0, 8))
        update_button.bind("<Button-1>", lambda e: self.check_for_updates_manual())
        ToolTip(update_button, "Manuel güncelleme kontrolü yapar. Yeni sürüm varsa GitHub'dan indirme linkini açar.")

        link_label = tk.Label(right_frame, text=link_text, 
                             fg='white', 
                             bg=ModernUI.COLORS['dark'], 
                             cursor="hand2",
                             font=('Segoe UI', 8))
        link_label.pack(side=tk.RIGHT)
        link_label.bind("<Button-1>", lambda e: self.open_link(link_text))
        ToolTip(link_label, "VesiKolay Pro'nun GitHub sayfasını açar. Kaynak kod ve güncellemeler için tıklayın.")

    def open_link(self, url):
        """Belirtilen URL'yi aç"""
        webbrowser.open_new(url)

    def check_for_updates_manual(self):
        """Manuel güncelleme kontrolü"""
        try:
            if self.update_checker:
                self.update_checker.perform_manual_check(self.root)
            else:
                # Update checker yoksa direkt GitHub'ı aç
                result = messagebox.askyesno("Güncelleme Kontrolü", 
                                           "⚠️ Güncelleme kontrolü otomatik yapılamıyor.\n\n"
                                           "GitHub sayfasını açarak manuel kontrol yapmak ister misiniz?")
                if result:
                    webbrowser.open("https://github.com/muallimun/VesiKolayPro/releases")
        except Exception as e:
            self.log_message(f"❌ Güncelleme kontrolü hatası: {e}")
            # Hata durumunda GitHub sayfasını aç
            result = messagebox.askyesno("Hata", 
                                       f"Güncelleme kontrolü sırasında hata oluştu:\n{e}\n\n"
                                       "GitHub sayfasını açmak ister misiniz?")
            if result:
                webbrowser.open("https://github.com/muallimun/VesiKolayPro")

    def check_for_updates_startup(self):
        """Program açılışında güncelleme kontrolü"""
        try:
            if self.update_checker:
                # 2 saniye bekle (GUI tamamen yüklendikten sonra)
                self.root.after(2000, lambda: self.update_checker.perform_startup_check(self.root))
        except Exception as e:
            # Sessizce geç, startup'ta hata vermemeli
            pass

    def handle_check_button_click(self):
        """Kontrol butonuna tıklandığında çalışır"""
        # Kontrol butonu her zaman aktif olabilir, sadece temel kontrolleri yapar
        if not self.school_name:
            messagebox.showwarning("Eksik Bilgi", "⚠️ Önce okul adını girin.\n\n📝 Adım 1'de okul adını belirtmeniz gerekir.")
            return
            
        if not self.excel_data:
            messagebox.showwarning("Eksik Bilgi", "⚠️ Önce Excel dosyası seçin ve yükleyin.\n\n📊 Adım 2'de Excel dosyasını seçmeniz gerekir.")
            return
            
        if not self.photo_directory:
            messagebox.showwarning("Eksik Bilgi", "⚠️ Önce fotoğraf dizini seçin.\n\n📂 Adım 3'te fotoğraf klasörünü seçmeniz gerekir.")
            return
            
        selected_columns = self.get_selected_columns()
        if not selected_columns:
            messagebox.showwarning("Eksik Bilgi", "⚠️ Adlandırma için en az bir sütun seçin.\n\n🔧 Adım 4'te sütun seçimi yapmanız gerekir.")
            return
            
        # Tüm koşullar sağlanmışsa kontrolü çalıştır
        self.check_counts()

    def handle_rename_button_click(self):
        """Adlandırma butonuna tıklandığında çalışır"""
        if self.rename_button['state'] == 'disabled':
            missing_items = self.get_missing_requirements_for_rename()
            if missing_items:
                messagebox.showinfo("Gereksinimler", f"✨ Fotoğraf Adlandırma İçin Gereksinimler:\n\n{missing_items}\n\n💡 Bu gereksinimleri tamamladıktan sonra '🔍 Kontrol Et' butonuna tıklayın.")
            return
        
        # Buton aktifse işlemi başlat
        self.start_rename_photos()

    def handle_crop_resize_button_click(self):
        """Boyutlandırma butonuna tıklandığında çalışır"""
        if self.crop_resize_button['state'] == 'disabled':
            missing_items = self.get_missing_requirements_for_crop_resize()
            if missing_items:
                messagebox.showinfo("Gereksinimler", f"✂️ Fotoğraf Boyutlandırma İçin Gereksinimler:\n\n{missing_items}")
            return
        
        # Buton aktifse işlemi başlat
        self.start_crop_and_resize_photos()

    def handle_pdf_button_click(self):
        """PDF butonuna tıklandığında çalışır"""
        if self.pdf_button['state'] == 'disabled':
            missing_items = self.get_missing_requirements_for_pdf()
            if missing_items:
                messagebox.showinfo("Gereksinimler", f"📄 PDF Oluşturma İçin Gereksinimler:\n\n{missing_items}")
            return
        
        # Buton aktifse işlemi başlat
        self.start_generate_class_pdfs()

    def handle_id_card_button_click(self):
        """Kimlik kartı butonuna tıklandığında çalışır"""
        if self.id_card_button['state'] == 'disabled':
            missing_items = self.get_missing_requirements_for_id_cards()
            if missing_items:
                messagebox.showinfo("Gereksinimler", f"🆔 Kimlik Kartı Oluşturma İçin Gereksinimler:\n\n{missing_items}")
            return
        
        # Buton aktifse işlemi başlat
        self.start_generate_id_cards()

    def get_missing_requirements_for_rename(self):
        """Adlandırma için eksik gereksinimleri döndürür"""
        missing = []
        
        if not self.school_name:
            missing.append("📝 Okul adı (Adım 1)")
        
        if not self.excel_data:
            missing.append("📊 Excel dosyası (Adım 2)")
        
        if not self.photo_directory:
            missing.append("📂 Fotoğraf klasörü (Adım 3)")
        
        selected_columns = self.get_selected_columns()
        if not selected_columns:
            missing.append("🔧 Sütun seçimi (Adım 4)")
        
        if missing:
            missing.append("\n💡 Tüm gereksinimleri tamamladıktan sonra '🔍 Kontrol Et' butonuna tıklayın.")
        
        return "\n".join(missing) if missing else ""

    def get_missing_requirements_for_crop_resize(self):
        """Boyutlandırma için eksik gereksinimleri döndürür"""
        missing = []
        
        if not self.sizing_enabled.get():
            missing.append("🔧 Boyutlandırma seçeneğini aktifleştirin (Adım 5)")
        
        if not self.school_name:
            missing.append("📝 Okul adı (Adım 1)")
        
        if not self.photo_directory:
            missing.append("📂 Fotoğraf klasörü (Adım 3)")
        
        # Adlandırma ile birlikte boyutlandırma yapılacaksa
        if self.sizing_with_naming.get():
            if not self.excel_data:
                missing.append("📊 Excel dosyası (Adım 2 - Adlandırma için)")
            
            selected_columns = self.get_selected_columns()
            if not selected_columns:
                missing.append("🔧 Sütun seçimi (Adım 4 - Adlandırma için)")
        
        return "\n".join(missing) if missing else ""

    def get_missing_requirements_for_pdf(self):
        """PDF oluşturma için eksik gereksinimleri döndürür"""
        missing = []
        
        if not self.school_name:
            missing.append("📝 Okul adı (Adım 1)")
        
        if not self.excel_data:
            missing.append("📊 Excel dosyası (Adım 2)")
        
        if not self.photo_directory:
            missing.append("📂 Fotoğraf klasörü (Adım 3)")
        
        selected_columns = self.get_selected_columns()
        if not selected_columns:
            missing.append("🔧 Sütun seçimi (Adım 4)")
        
        missing.append("\n💡 PDF oluşturmadan önce fotoğrafları adlandırmanız gerekir.")
        missing.append("   '🔍 Kontrol Et' ardından '✨ Fotoğrafları Adlandır' işlemini yapın.")
        
        return "\n".join(missing) if missing else ""

    def get_missing_requirements_for_id_cards(self):
        """Kimlik kartı oluşturma için eksik gereksinimleri döndürür"""
        missing = []
        
        if not self.school_name:
            missing.append("📝 Okul adı (Adım 1)")
        
        if not self.excel_data:
            missing.append("📊 Excel dosyası (Adım 2)")
        
        if not self.photo_directory:
            missing.append("📂 Fotoğraf klasörü (Adım 3)")
        
        missing.append("\n💡 Kimlik kartı oluşturmadan önce fotoğrafları adlandırmanız gerekir.")
        missing.append("   '🔍 Kontrol Et' ardından '✨ Fotoğrafları Adlandır' işlemini yapın.")
        
        return "\n".join(missing) if missing else ""

    def run_console_mode(self):
        """Konsol modunda çalıştır"""
        print("=" * 50)
        print("VesiKolay Pro - Konsol Modu")
        print("=" * 50)
        print("Bu sistem grafik arayüzü desteklemiyor.")
        print("Lütfen aşağıdaki işlemlerden birini seçin:")
        print("1. Test verileriyle demo çalıştır")
        print("2. Sistem bilgilerini görüntüle")
        print("3. Çıkış")

        while True:
            try:
                secim = input("\nSeçiminizi yapın (1-3): ").strip()
                if secim == "1":
                    self.demo_run()
                elif secim == "2":
                    self.system_info()
                elif secim == "3":
                    print("Program sonlandırılıyor...")
                    break
                else:
                    print("Geçersiz seçim. Lütfen 1-3 arası bir sayı girin.")
            except KeyboardInterrupt:
                print("\nProgram sonlandırılıyor...")
                break
            except Exception as e:
                print(f"Hata: {e}")

    def demo_run(self):
        """Demo çalıştır"""
        print("\n" + "=" * 30)
        print("DEMO ÇALIŞTIRILIYOR")
        print("=" * 30)

        # Test Excel dosyasını kontrol et
        from pathlib import Path
        test_excel = Path("data/test_students.xlsx")
        test_photos = Path("data/test_photos")

        if test_excel.exists():
            print(f"✅ Test Excel dosyası bulundu: {test_excel}")
        else:
            print(f"❌ Test Excel dosyası bulunamadı: {test_excel}")

        if test_photos.exists():
            photos = list(test_photos.glob("*.jpg"))
            print(f"✅ Test fotoğraf klasörü bulundu: {len(photos)} fotoğraf")
        else:
            print(f"❌ Test fotoğraf klasörü bulunamadı: {test_photos}")

        print("\nDemo tamamlandı.")

    def system_info(self):
        """Sistem bilgilerini göster"""
        import platform
        import sys

        print("\n" + "=" * 30)
        print("SİSTEM BİLGİLERİ")
        print("=" * 30)
        print(f"Python Sürümü: {sys.version}")
        print(f"Platform: {platform.platform()}")
        print(f"İşlemci: {platform.processor()}")
        print(f"Sistem: {platform.system()}")

        # Modül kontrolü
        modules = ['tkinter', 'pandas', 'PIL', 'cv2', 'fpdf']
        print(f"\nModül Durumu:")
        for module in modules:
            try:
                if module == 'cv2':
                    import cv2
                    print(f"✅ OpenCV: {cv2.__version__}")
                elif module == 'PIL':
                    import PIL
                    print(f"✅ Pillow: {PIL.__version__}")
                elif module == 'tkinter':
                    import tkinter
                    print(f"✅ Tkinter: Mevcut")
                elif module == 'pandas':
                    import pandas
                    print(f"✅ Pandas: {pandas.__version__}")
                elif module == 'fpdf':
                    import fpdf
                    print(f"✅ FPDF: Mevcut")
            except ImportError:
                print(f"❌ {module}: Yüklenemedi")

    def run(self):
        """Uygulamayı çalıştır"""
        try:
            if hasattr(self, 'root') and self.root:
                self.root.mainloop()
            else:
                self.run_console_mode()
        except Exception as e:
            print(f"Uygulama çalıştırma hatası: {e}")
            self.run_console_mode()