"""
VesiKolay Pro - Configuration
Application configuration and constants
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Tuple
import logging
import sys

@dataclass
class Config:
    """Application configuration"""

    def __init__(self):
        # Base directories - exe için düzeltme
        if getattr(sys, 'frozen', False):
            # PyInstaller ile derlenmiş exe
            self.BASE_DIR = Path(sys._MEIPASS)
        else:
            # Normal Python çalışması
            self.BASE_DIR = Path.cwd()

        # Documents dizininde VesiKolayPro klasörü oluştur
        documents_dir = Path.home() / "Documents"
        documents_dir.mkdir(exist_ok=True)
        self.VESIKOLAY_DIR = documents_dir / "VesiKolayPro"
        self.VESIKOLAY_DIR.mkdir(exist_ok=True)

        # Temel dizinleri ayarla
        self.TEMPLATES_DIR = self.BASE_DIR / "templates"
        self.LANGUAGES_DIR = self.BASE_DIR / "languages"
        self.LOG_DIR = self.VESIKOLAY_DIR / "logs"

        # Gerekli alt dizinleri oluştur
        self._create_output_directories()

        # Database - VesiKolayPro dizininde tut
        self.DATABASE_PATH = self.VESIKOLAY_DIR / "schools.db"

        # UI Configuration
        self.WINDOW_TITLE = "VesiKolay Pro"
        self.WINDOW_SIZE = "1200x800"
        self.MIN_WINDOW_SIZE = (800, 600)

        # Photo processing
        self.SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        self.MAX_IMAGE_SIZE = 4000  # Maximum dimension in pixels
        self.DEFAULT_DPI = 300

        # Predefined photo sizes (in mm)
        self.PHOTO_SIZES = {
            'passport': (35, 45),
            'id_card': (50, 60),
            'visa': (35, 35),
            'us_passport': (51, 51),
            'digital_small': (300, 400),  # pixels
            'digital_large': (600, 800)   # pixels
        }

        # Naming patterns
        self.NAMING_PATTERNS = {
            'first_last': '{first_name}_{last_name}',
            'last_first': '{last_name}_{first_name}',
            'first_last_class': '{first_name}_{last_name}_{class_name}',
            'number_first_last': '{student_no}_{first_name}_{last_name}',
            'class_last_first': '{class_name}_{last_name}_{first_name}'
        }

        # Face detection parameters
        self.FACE_DETECTION = {
            'scale_factor': 1.1,
            'min_neighbors': 5,
            'min_size': (30, 30),
            'padding_factor': 0.3
        }

        # Watermark settings
        self.WATERMARK_SETTINGS = {
            'default_size': (30, 30),  # Default watermark size in pixels
            'max_size': (100, 100),    # Maximum allowed watermark size
            'default_opacity': 0.7,    # Default opacity (0.0 to 1.0)
            'default_position': 'bottom_right',  # Default position
            'supported_positions': ['bottom_right', 'bottom_left', 'top_right', 'top_left'],
            'margin': 10,  # Margin from edges in pixels
            'supported_formats': ['.png', '.jpg', '.jpeg', '.gif', '.bmp']  # Supported watermark formats
        }

        # PDF settings
        self.PDF_SETTINGS = {
            'page_format': 'A4',
            'margin': 10,
            'id_card_size': (85.6, 53.98),  # Credit card size in mm
            'quality': 85
        }

        # Language settings
        self.DEFAULT_LANGUAGE = 'en'
        self.SUPPORTED_LANGUAGES = ['en', 'tr']

        # Application colors (for customtkinter)
        self.COLORS = {
            'primary': '#1f538d',
            'secondary': '#14375e',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'info': '#17a2b8'
        }

        # File size limits (in MB)
        self.MAX_FILE_SIZE = 50
        self.MAX_EXCEL_SIZE = 10

        # Processing limits
        self.MAX_PHOTOS_PER_BATCH = 1000
        self.MAX_STUDENTS_PER_CLASS = 50

        # Logging settings
        self.LOG_LEVEL = logging.INFO
        self.LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    def _create_output_directories(self):
        """Gerekli temel dizinleri oluştur"""
        # Sadece log dizini oluştur, diğerleri ihtiyaç duyulduğunda oluşturulacak
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

    def get_log_file_path(self) -> Path:
        """Log dosyası yolunu döndür"""
        return self.LOG_DIR / 'vesikolay_pro.log'

    def get_vesikolay_school_dir(self, school_name: str) -> Path:
        """Get VesiKolayPro school directory"""
        clean_name = school_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        school_dir = self.VESIKOLAY_DIR / clean_name
        school_dir.mkdir(parents=True, exist_ok=True)
        return school_dir

    def get_photo_size_pixels(self, size_name: str, dpi: int = None) -> Tuple[int, int]:
        """Convert photo size to pixels"""
        if dpi is None:
            dpi = self.DEFAULT_DPI

        if size_name not in self.PHOTO_SIZES:
            return (300, 400)  # Default size

        width, height = self.PHOTO_SIZES[size_name]

        # If already in pixels (digital sizes)
        if size_name.startswith('digital'):
            return (width, height)

        # Convert mm to pixels
        width_px = int((width / 25.4) * dpi)
        height_px = int((height / 25.4) * dpi)

        return (width_px, height_px)

    def mm_to_pixels(self, mm: float, dpi: int = None) -> int:
        """Convert millimeters to pixels"""
        if dpi is None:
            dpi = self.DEFAULT_DPI
        return int((mm / 25.4) * dpi)

    def cm_to_pixels(self, cm: float, dpi: int = None) -> int:
        """Convert centimeters to pixels"""
        if dpi is None:
            dpi = self.DEFAULT_DPI
        return int((cm / 2.54) * dpi)

    def pixels_to_mm(self, pixels: int, dpi: int = None) -> float:
        """Convert pixels to millimeters"""
        if dpi is None:
            dpi = self.DEFAULT_DPI
        return (pixels * 25.4) / dpi

    def validate_image_file(self, file_path: Path) -> bool:
        """Validate if file is a supported image"""
        if not file_path.exists():
            return False

        if file_path.suffix.lower() not in self.SUPPORTED_IMAGE_FORMATS:
            return False

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE:
            return False

        return True

    def validate_excel_file(self, file_path: Path) -> bool:
        """Validate if file is a supported Excel file"""
        if not file_path.exists():
            return False

        if file_path.suffix.lower() not in ['.xlsx', '.xls']:
            return False

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_EXCEL_SIZE:
            return False

        return True