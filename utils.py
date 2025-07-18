"""
VesiKolay Pro - Utility Functions
Common utility functions used throughout the application
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import re
from datetime import datetime

class FileUtils:
    """File operation utilities"""

    @staticmethod
    def ensure_directory(path: Path) -> bool:
        """Ensure directory exists, create if necessary"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"Failed to create directory {path}: {e}")
            return False

    @staticmethod
    def safe_filename(filename: str) -> str:
        """Create a safe filename by removing invalid characters"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[^\w\s\-_\.]', '_', filename)
        filename = re.sub(r'_+', '_', filename)  # Replace multiple underscores
        filename = filename.strip('_. ')

        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext

        return filename

    @staticmethod
    def copy_file_safe(source: Path, destination: Path, overwrite: bool = False) -> bool:
        """Safely copy a file with error handling"""
        try:
            if destination.exists() and not overwrite:
                logging.warning(f"Destination file exists: {destination}")
                return False
            
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            return True
        except Exception as e:
            logging.error(f"Failed to copy {source} to {destination}: {e}")
            return False

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"

    


class VesiKolayUtils:
    """VesiKolay Pro specific utilities"""
    
    @staticmethod
    def get_vesikolay_directory() -> Path:
        """VesiKolayPro ana dizinini döndür"""
        documents_dir = Path.home() / "Documents"
        vesikolay_dir = documents_dir / "VesiKolayPro"
        vesikolay_dir.mkdir(parents=True, exist_ok=True)
        return vesikolay_dir
    
    @staticmethod
    def ensure_vesikolay_subdirectory(subdir_name: str) -> Path:
        """VesiKolayPro altında alt dizin oluştur"""
        vesikolay_dir = VesiKolayUtils.get_vesikolay_directory()
        subdir = vesikolay_dir / subdir_name
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir
    
    @staticmethod
    def get_output_path(output_type: str = "output") -> Path:
        """Belirli bir çıktı türü için yol döndür"""
        return VesiKolayUtils.ensure_vesikolay_subdirectory(output_type)
    
    @staticmethod
    def create_timestamped_backup_dir() -> Path:
        """Zaman damgalı yedek dizini oluştur"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        backup_dir = VesiKolayUtils.ensure_vesikolay_subdirectory("backups")
        timestamped_dir = backup_dir / f"backup_{timestamp}"
        timestamped_dir.mkdir(parents=True, exist_ok=True)
        return timestamped_dir
    
    @staticmethod
    def get_school_directory(school_name: str) -> Path:
        """Okul için özel dizin oluştur ve döndür"""
        vesikolay_dir = VesiKolayUtils.get_vesikolay_directory()
        # Okul adını temizle
        clean_name = school_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c in ('_', '-'))
        
        school_dir = vesikolay_dir / clean_name
        school_dir.mkdir(parents=True, exist_ok=True)
        return school_dir
    
    @staticmethod
    def get_project_info() -> Dict[str, str]:
        """Proje bilgilerini döndür"""
        vesikolay_dir = VesiKolayUtils.get_vesikolay_directory()
        return {
            'vesikolay_directory': str(vesikolay_dir),
            'output_directory': str(vesikolay_dir / "output"),
            'log_directory': str(vesikolay_dir / "logs"),
            'backup_directory': str(vesikolay_dir / "backups"),
            'database_file': str(vesikolay_dir / "schools.db"),
            'log_file': str(vesikolay_dir / "logs" / "vesikolay_pro.log")
        }

    

class StringUtils:
    """String manipulation utilities"""

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize person name (title case, clean spaces)"""
        if not name:
            return ""

        # Clean and normalize
        name = re.sub(r'\s+', ' ', name.strip())
        name = name.title()

        # Handle Turkish characters properly
        turkish_chars = {
            'İ': 'İ', 'ı': 'ı', 'Ğ': 'Ğ', 'ğ': 'ğ',
            'Ü': 'Ü', 'ü': 'ü', 'Ş': 'Ş', 'ş': 'ş',
            'Ö': 'Ö', 'ö': 'ö', 'Ç': 'Ç', 'ç': 'ç'
        }

        for char, replacement in turkish_chars.items():
            name = name.replace(char.lower(), replacement)
            name = name.replace(char.upper(), replacement.upper())

        return name

    @staticmethod
    def similarity_score(str1: str, str2: str) -> float:
        """Calculate similarity score between two strings"""
        if not str1 or not str2:
            return 0.0

        str1 = str1.lower().strip()
        str2 = str2.lower().strip()

        if str1 == str2:
            return 1.0

        # Simple similarity based on common characters
        common_chars = set(str1) & set(str2)
        total_chars = set(str1) | set(str2)

        if not total_chars:
            return 0.0

        return len(common_chars) / len(total_chars)

    

class ValidationUtils:
    """Data validation utilities"""

    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """Validate person name"""
        if not name or not name.strip():
            return False, "Name cannot be empty"

        name = name.strip()

        if len(name) < 2:
            return False, "Name must be at least 2 characters long"

        if len(name) > 50:
            return False, "Name cannot be longer than 50 characters"

        # Check for valid characters (letters, spaces, apostrophes, hyphens)
        if not re.match(r"^[a-zA-ZçÇğĞıİöÖşŞüÜ\s'\-]+$", name):
            return False, "Name contains invalid characters"

        return True, ""

    @staticmethod
    def validate_student_number(student_no: str) -> Tuple[bool, str]:
        """Validate student number"""
        if not student_no or not student_no.strip():
            return True, ""  # Student number is optional

        student_no = student_no.strip()

        if len(student_no) > 20:
            return False, "Student number cannot be longer than 20 characters"

        # Allow alphanumeric characters
        if not re.match(r"^[a-zA-Z0-9]+$", student_no):
            return False, "Student number can only contain letters and numbers"

        return True, ""

    @staticmethod
    def validate_class_name(class_name: str) -> Tuple[bool, str]:
        """Validate class name"""
        if not class_name or not class_name.strip():
            return True, ""  # Class name is optional

        class_name = class_name.strip()

        if len(class_name) > 20:
            return False, "Class name cannot be longer than 20 characters"

        # Allow alphanumeric characters, spaces, and common separators
        if not re.match(r"^[a-zA-Z0-9çÇğĞıİöÖşŞüÜ\s\-/]+$", class_name):
            return False, "Class name contains invalid characters"

        return True, ""

    @staticmethod
    def validate_tc_number(tc_str: str) -> Tuple[bool, str]:
        """Validate Turkish TC identity number"""
        if not tc_str or not tc_str.strip():
            return True, ""  # TC number is optional

        tc_str = str(tc_str).strip()

        # Must be exactly 11 digits
        if len(tc_str) != 11 or not tc_str.isdigit():
            return False, "TC number must be exactly 11 digits"

        # First digit cannot be 0
        if tc_str[0] == '0':
            return False, "TC number cannot start with 0"

        try:
            # TC number algorithm validation
            digits = [int(d) for d in tc_str]

            # Sum of odd positioned digits (1,3,5,7,9)
            odd_sum = sum(digits[i] for i in range(0, 9, 2))

            # Sum of even positioned digits (2,4,6,8)
            even_sum = sum(digits[i] for i in range(1, 8, 2))

            # 10th digit check
            tenth_digit = (odd_sum * 7 - even_sum) % 10
            if tenth_digit != digits[9]:
                return False, "Invalid TC number (10th digit check failed)"

            # 11th digit check
            eleventh_digit = (sum(digits[:10])) % 10
            if eleventh_digit != digits[10]:
                return False, "Invalid TC number (11th digit check failed)"

            return True, ""

        except Exception:
            return False, "Invalid TC number format"

class PhotoUtils:
    """Photo processing utilities"""

    @staticmethod
    def get_supported_formats() -> set:
        """Get supported image formats"""
        return {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'}

    @staticmethod
    def is_image_file(file_path: Path) -> bool:
        """Check if file is a supported image"""
        return file_path.suffix.lower() in PhotoUtils.get_supported_formats()

    @staticmethod
    def get_image_info(file_path: Path) -> Dict[str, Any]:
        """Get basic image information"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': file_path.stat().st_size,
                    'size_readable': FileUtils.format_file_size(file_path.stat().st_size)
                }
        except Exception:
            return {'error': 'Could not read image info'}

    

class ExcelUtils:
    """Excel processing utilities"""

    @staticmethod
    def get_column_types(df) -> Dict[str, str]:
        """Analyze column data types in DataFrame"""
        import pandas as pd

        column_types = {}
        for col in df.columns:
            # Check for numeric data
            if pd.api.types.is_numeric_dtype(df[col]):
                column_types[col] = 'numeric'
            # Check for date data
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                column_types[col] = 'date'
            # Check if column contains mostly digits (like student numbers)
            elif df[col].astype(str).str.isdigit().sum() / len(df) > 0.8:
                column_types[col] = 'identifier'
            else:
                column_types[col] = 'text'

        return column_types

    @staticmethod
    def suggest_column_mapping(columns: List[str]) -> Dict[str, str]:
        """Suggest mapping of columns to standard fields"""
        import re

        suggestions = {}

        # Define patterns for different field types
        patterns = {
            'first_name': [r'.*ad.*', r'.*first.*', r'.*isim.*', r'.*name.*'],
            'last_name': [r'.*soyad.*', r'.*last.*', r'.*surname.*', r'.*family.*'],
            'student_no': [r'.*numara.*', r'.*no.*', r'.*student.*', r'.*öğrenci.*'],
            'tc_no': [r'.*tc.*', r'.*kimlik.*', r'.*identity.*'],
            'class_name': [r'.*sınıf.*', r'.*sinif.*', r'.*class.*'],
            'school_name': [r'.*okul.*', r'.*school.*'],
            'branch': [r'.*branş.*', r'.*brans.*', r'.*branch.*', r'.*dal.*']
        }

        for col in columns:
            col_lower = col.lower().strip()
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    if re.search(pattern, col_lower):
                        suggestions[col] = field
                        break
                if col in suggestions:
                    break

        return suggestions

    @staticmethod
    def clean_excel_data(df) -> 'pd.DataFrame':
        """Clean and standardize Excel data"""
        import pandas as pd

        # Remove completely empty rows
        df = df.dropna(how='all')

        # Strip whitespace from string columns
        string_columns = df.select_dtypes(include=['object']).columns
        df[string_columns] = df[string_columns].astype(str).apply(lambda x: x.str.strip())

        # Replace empty strings with NaN
        df = df.replace('', pd.NA)

        # Remove duplicate rows
        df = df.drop_duplicates()

        return df



class ProgressTracker:
    """Progress tracking utility for long operations"""

    def __init__(self, total_items: int, callback=None):
        """Initialize progress tracker"""
        self.total_items = total_items
        self.current_item = 0
        self.callback = callback
        self.start_time = datetime.now()
        self.errors = []
        self.warnings = []

    def update(self, increment: int = 1, message: str = ""):
        """Update progress"""
        self.current_item = min(self.current_item + increment, self.total_items)

        progress = self.current_item / self.total_items if self.total_items > 0 else 0

        if self.callback:
            self.callback(progress, message, self.current_item, self.total_items)

    def add_error(self, error: str):
        """Add error message"""
        self.errors.append(error)
        logging.error(error)

    def add_warning(self, warning: str):
        """Add warning message"""
        self.warnings.append(warning)
        logging.warning(warning)

    def get_elapsed_time(self) -> str:
        """Get elapsed time as formatted string"""
        elapsed = datetime.now() - self.start_time
        total_seconds = int(elapsed.total_seconds())

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def is_complete(self) -> bool:
        """Check if processing is complete"""
        return self.current_item >= self.total_items

    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary"""
        return {
            'total_items': self.total_items,
            'processed_items': self.current_item,
            'success_rate': (self.current_item - len(self.errors)) / self.total_items if self.total_items > 0 else 0,
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'elapsed_time': self.get_elapsed_time(),
            'is_complete': self.is_complete()
        }

