"""Updated class name extraction and PDF generation logic."""
"""
The code has been updated to include a function for organizing photos by class for PDF generation.
"""
"""
VesiKolay Pro - Photo Processing
Handles photo operations including face detection, cropping, and renaming
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageDraw
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union, Any
import re
import shutil
from dataclasses import dataclass


@dataclass
class CropDimensions:
    """Crop dimensions with unit conversion support"""
    width: int
    height: int
    unit: str = 'px'
    dpi: int = 300
    min_dpi: int = None  # Minimum DPI zorunluluğu için

    def to_pixels(self) -> Tuple[int, int]:
        """Convert dimensions to pixels based on unit"""
        if self.unit == 'px':
            return self.width, self.height
        elif self.unit == 'mm':
            return self._mm_to_px(self.width), self._mm_to_px(self.height)
        elif self.unit == 'cm':
            return self._cm_to_px(self.width), self._cm_to_px(self.height)
        else:
            return self.width, self.height

    def _mm_to_px(self, mm: float) -> int:
        """Convert millimeters to pixels"""
        return int((mm / 25.4) * self.dpi)

    def _cm_to_px(self, cm: float) -> int:
        """Convert centimeters to pixels"""
        return int((cm / 2.54) * self.dpi)

class PhotoProcessor:
    """Handles all photo processing operations"""

    def __init__(self):
        """PhotoProcessor sınıfını başlat"""
        self.logger = logging.getLogger(__name__)

        # Desteklenen dosya formatları
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}

        # Face detection cascade dosyasını yükle
        try:
            import cv2
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if self.face_cascade.empty():
                raise ValueError("Cascade classifier yüklenemedi")
            self.logger.info("OpenCV yüz tanıma başarıyla yüklendi")
        except ImportError:
            self.logger.warning("OpenCV bulunamadı, yüz tanıma devre dışı")
            self.face_cascade = None
        except Exception as e:
            self.logger.error(f"Face cascade yüklenirken hata: {e}")
            self.face_cascade = None

    def detect_faces(self, image_path: Path) -> List[Tuple[int, int, int, int]]:
        """Görüntüde yüzleri algıla ve koordinatlarını döndür"""
        if self.face_cascade is None:
            self.logger.warning("Face cascade yüklenmemiş, yüz algılama atlanıyor")
            return []

        try:
            import cv2
            # Görüntüyü oku
            img = cv2.imread(str(image_path))
            if img is None:
                self.logger.error(f"Görüntü okunamadı: {image_path}")
                return []

            # Gri tonlamaya çevir
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Yüzleri algıla
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            # Tuple listesi olarak döndür
            return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]

        except ImportError:
            self.logger.warning("OpenCV import edilemedi")
            return []
        except Exception as e:
            self.logger.error(f"Yüz algılama hatası {image_path}: {e}")
            return []

    def crop_face_biometric_acik_lise(self, image_path: Path, output_path: Path, 
                                     dimensions: CropDimensions, white_background: bool = True) -> bool:
        """
        Açık Lise için özel biyometrik kırpma - baş ve boyun tam görünür, beyaz arka plan
        """
        try:
            faces = self.detect_faces(image_path)

            if not faces:
                self.logger.warning(f"No faces detected in {image_path}")
                return False

            # En büyük yüzü seç
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face

            # Açık Lise için özel padding - baş ve boyun tam görünür olacak şekilde
            padding_w = int(w * 0.6)  # Yanlar için %60 daha fazla
            padding_h_top = int(h * 0.8)  # Saç için %80 daha fazla
            padding_h_bottom = int(h * 1.0)  # Boyun ve omuzlar için %100 daha fazla

            # Resim boyutlarını kontrol et
            with Image.open(image_path) as img:
                img_width, img_height = img.size

            # Kırpma koordinatlarını hesapla
            crop_x = max(0, x - padding_w)
            crop_y = max(0, y - padding_h_top)
            crop_w = min(w + 2 * padding_w, img_width - crop_x)
            crop_h = min(h + padding_h_top + padding_h_bottom, img_height - crop_y)

            # Resim sınırlarını aşmayacak şekilde ayarla
            if crop_x + crop_w > img_width:
                crop_w = img_width - crop_x
            if crop_y + crop_h > img_height:
                crop_h = img_height - crop_y

            # Kırp ve boyutlandır
            success = self.crop_image_with_white_background_optimized(image_path, output_path, dimensions,
                                                           crop_x, crop_y, crop_w, crop_h, white_background)

            if success:
                self.logger.debug(f"Successfully cropped for Açık Lise: {image_path}")

            return success

        except Exception as e:
            self.logger.error(f"Error in Açık Lise biometric cropping for {image_path}: {e}")
            return False

    def crop_face_biometric_mebbis(self, image_path: Path, output_path: Path, 
                                  dimensions: CropDimensions, white_background: bool = True) -> bool:
        """
        MEBBIS için özel biyometrik kırpma - baş ve boyun tam görünür, beyaz arka plan
        """
        try:
            faces = self.detect_faces(image_path)

            if not faces:
                self.logger.warning(f"No faces detected in {image_path}")
                return False

            # En büyük yüzü seç
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face

            # MEBBIS için özel padding - daha sıkı kırpma
            padding_w = int(w * 0.5)  # Yanlar için %50 daha fazla
            padding_h_top = int(h * 0.7)  # Saç için %70 daha fazla
            padding_h_bottom = int(h * 0.9)  # Boyun ve omuzlar için %90 daha fazla

            # Resim boyutlarını kontrol et
            with Image.open(image_path) as img:
                img_width, img_height = img.size

            # Kırpma koordinatlarını hesapla
            crop_x = max(0, x - padding_w)
            crop_y = max(0, y - padding_h_top)
            crop_w = min(w + 2 * padding_w, img_width - crop_x)
            crop_h = min(h + padding_h_top + padding_h_bottom, img_height - crop_y)

            # Resim sınırlarını aşmayacak şekilde ayarla
            if crop_x + crop_w > img_width:
                crop_w = img_width - crop_x
            if crop_y + crop_h > img_height:
                crop_h = img_height - crop_y

            # Kırp ve boyutlandır
            success = self.crop_image_with_white_background_optimized(image_path, output_path, dimensions,
                                                           crop_x, crop_y, crop_w, crop_h, white_background)

            if success:
                self.logger.debug(f"Successfully cropped for MEBBIS: {image_path}")

            return success

        except Exception as e:
            self.logger.error(f"Error in MEBBIS biometric cropping for {image_path}: {e}")
            return False

    def crop_face_auto(self, image_path: Path, output_path: Path, 
                      dimensions: CropDimensions, padding_factor: float = 0.5) -> bool:
        """
        Automatically crop face from image using face detection
        """
        try:
            faces = self.detect_faces(image_path)

            if not faces:
                self.logger.warning(f"No faces detected in {image_path}")
                return False

            # Use the largest face (assume it's the main subject)
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face

            # Vesikalık fotoğraf için daha uygun padding
            # Yüzün üst kısmında saç için daha fazla alan
            padding_w = int(w * padding_factor)
            padding_h_top = int(h * 0.8)  # Üst kısım için %80 daha fazla
            padding_h_bottom = int(h * 0.4)  # Alt kısım için %40 daha fazla

            # Resim boyutlarını kontrol et
            with Image.open(image_path) as img:
                img_width, img_height = img.size

            # Calculate crop coordinates with improved padding
            crop_x = max(0, x - padding_w)
            crop_y = max(0, y - padding_h_top)
            crop_w = min(w + 2 * padding_w, img_width - crop_x)
            crop_h = min(h + padding_h_top + padding_h_bottom, img_height - crop_y)

            # Ensure we don't exceed image boundaries
            if crop_x + crop_w > img_width:
                crop_w = img_width - crop_x
            if crop_y + crop_h > img_height:
                crop_h = img_height - crop_y

            # Crop and resize image
            return self.crop_image(image_path, output_path, dimensions,
                                 crop_x, crop_y, crop_w, crop_h)

        except Exception as e:
            self.logger.error(f"Error auto-cropping face from {image_path}: {e}")
            return False

    def crop_image_with_white_background_optimized(self, image_path: Path, output_path: Path, 
                                               dimensions: CropDimensions, x: int = None, y: int = None, 
                                               width: int = None, height: int = None, white_background: bool = True) -> bool:
        """
        Optimize edilmiş beyaz arka plan ile kırpma - beyaz şerit problemini çözer
        """
        try:
            # Target dimensions
            target_width, target_height = dimensions.to_pixels()

            # PNG desteği için format kontrolü
            original_format = image_path.suffix.lower()
            if original_format == '.png':
                # PNG dosyalar için format zorlaması yapma
                pass
            else:
                # Diğer formatlar için JPG'ye çevir
                output_path = output_path.with_suffix('.jpg')

            with Image.open(image_path) as img:
                # RGB'ye çevir
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                orig_width, orig_height = img.size

                # Kırpma koordinatları belirtilmemişse merkezi kırpma
                if x is None or y is None or width is None or height is None:
                    aspect_ratio = target_width / target_height

                    if orig_width / orig_height > aspect_ratio:
                        new_width = int(orig_height * aspect_ratio)
                        x = (orig_width - new_width) // 2
                        y = 0
                        width = new_width
                        height = orig_height
                    else:
                        new_height = int(orig_width / aspect_ratio)
                        x = 0
                        y = (orig_height - new_height) // 2
                        width = orig_width
                        height = new_height

                # Resim sınırları içinde kal
                x = max(0, min(x, orig_width))
                y = max(0, min(y, orig_height))
                width = min(width, orig_width - x)
                height = min(height, orig_height - y)

                # Kırp
                cropped = img.crop((x, y, x + width, y + height))

                # Hedef en-boy oranını hesapla
                target_ratio = target_width / target_height
                cropped_ratio = cropped.width / cropped.height

                if white_background:
                    # Beyaz arka plan oluştur
                    white_bg = Image.new('RGB', (target_width, target_height), (255, 255, 255))

                    # Kırpılan resmi hedef boyuta tam olarak sığdır
                    if abs(cropped_ratio - target_ratio) < 0.01:  # Oranlar neredeyse eşitse
                        # Direkt boyutlandır
                        resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
                        final_img = resized
                    else:
                        # En-boy oranını koruyarak boyutlandır
                        if cropped_ratio > target_ratio:
                            # Genişlik fazla, yüksekliği hedef yap
                            new_height = target_height
                            new_width = int(new_height * cropped_ratio)
                        else:
                            # Yükseklik fazla, genişliği hedef yap
                            new_width = target_width
                            new_height = int(new_width / cropped_ratio)

                        resized = cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)

                        # Ortaya yerleştir
                        paste_x = (target_width - new_width) // 2
                        paste_y = (target_height - new_height) // 2
                        white_bg.paste(resized, (paste_x, paste_y))
                        final_img = white_bg
                else:
                    # Normal boyutlandırma
                    final_img = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)

                # Kaliteyi artır
                enhancer = ImageEnhance.Sharpness(final_img)
                enhanced = enhancer.enhance(1.1)

                # Dizin oluştur
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Format ve DPI kontrolü
                dpi_value = getattr(dimensions, 'dpi', 300)
                min_dpi_required = getattr(dimensions, 'min_dpi', None)

                # Minimum DPI kontrolü
                if min_dpi_required and dpi_value < min_dpi_required:
                    final_dpi = min_dpi_required
                    self.logger.warning(f"DPI {dpi_value} yetersiz, {min_dpi_required} DPI'ya yükseltildi")
                else:
                    final_dpi = dpi_value

                # Format kontrolü ile kaydetme
                output_format = output_path.suffix.lower()
                if output_format == '.png':
                    # PNG formatı için
                    if enhanced.mode != 'RGBA':
                        enhanced = enhanced.convert('RGBA')
                    enhanced.save(output_path, format='PNG', optimize=True, dpi=(final_dpi, final_dpi))
                else:
                    # JPG formatı için
                    if enhanced.mode != 'RGB':
                        enhanced = enhanced.convert('RGB')
                    enhanced.save(output_path, format='JPEG', quality=90, optimize=True, dpi=(final_dpi, final_dpi))

                self.logger.debug(f"Successfully cropped with optimized white background: {image_path}")
                return True

        except Exception as e:
            self.logger.error(f"Error cropping with optimized white background {image_path}: {e}")
            return False

    def crop_image_with_white_background(self, image_path: Path, output_path: Path, 
                                               dimensions: CropDimensions, x: int = None, y: int = None, 
                                               width: int = None, height: int = None, white_background: bool = True) -> bool:
        """
        Beyaz arka plan ile kırpma - Açık Lise için özel
        """
        try:
            # Target dimensions
            target_width, target_height = dimensions.to_pixels()

            # Force JPG format for Açık Lise
            output_path = output_path.with_suffix('.jpg')

            with Image.open(image_path) as img:
                # RGB'ye çevir
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                orig_width, orig_height = img.size

                # Kırpma koordinatları belirtilmemişse merkezi kırpma
                if x is None or y is None or width is None or height is None:
                    aspect_ratio = target_width / target_height

                    if orig_width / orig_height > aspect_ratio:
                        new_width = int(orig_height * aspect_ratio)
                        x = (orig_width - new_width) // 2
                        y = 0
                        width = new_width
                        height = orig_height
                    else:
                        new_height = int(orig_width / aspect_ratio)
                        x = 0
                        y = (orig_height - new_height) // 2
                        width = orig_width
                        height = new_height

                # Resim sınırları içinde kal
                x = max(0, min(x, orig_width))
                y = max(0, min(y, orig_height))
                width = min(width, orig_width - x)
                height = min(height, orig_height - y)

                # Kırp
                cropped = img.crop((x, y, x + width, y + height))

                # Beyaz arka plan oluştur
                if white_background:
                    white_bg = Image.new('RGB', (target_width, target_height), (255, 255, 255))

                    # Kırpılan resmi hedef boyuta sığdır (en boy oranını koruyarak)
                    cropped.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)

                    # Beyaz arka planın ortasına yapıştır
                    paste_x = (target_width - cropped.width) // 2
                    paste_y = (target_height - cropped.height) // 2
                    white_bg.paste(cropped, (paste_x, paste_y))

                    final_img = white_bg
                else:
                    # Normal boyutlandırma
                    final_img = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)

                # Kaliteyi artır
                enhancer = ImageEnhance.Sharpness(final_img)
                enhanced = enhancer.enhance(1.1)

                # Dizin oluştur
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # JPG olarak kaydet (400 DPI ile)
                enhanced.save(output_path, format='JPEG', quality=90, optimize=True, dpi=(400, 400))

                self.logger.debug(f"Successfully cropped with white background: {image_path}")
                return True

        except Exception as e:
            self.logger.error(f"Error cropping with white background {image_path}: {e}")
            return False

    def crop_image(self, image_path: Path, output_path: Path, 
                  dimensions: CropDimensions, x: int = None, y: int = None, 
                  width: int = None, height: int = None) -> bool:
        """
        Crop image to specified dimensions
        If crop coordinates are not provided, center crop is used
        """
        try:
            # Orijinal dosya formatını al
            original_format = image_path.suffix.lower()
            output_format = output_path.suffix.lower()

            # "original" format seçilmişse orijinal formatı koru
            if output_format == '.original' or 'original' in str(output_path):
                output_format = original_format
                output_path = output_path.with_suffix(original_format)

            # Open image with better error handling
            try:
                with Image.open(image_path) as img:
                    # PNG dosyaları için RGBA modunu koru, diğerleri için RGB'ye çevir
                    if output_format == '.png':
                        if img.mode not in ['RGBA']:
                            img = img.convert('RGBA')
                    else:
                        if img.mode not in ['RGB']:
                            img = img.convert('RGB')

                    orig_width, orig_height = img.size

                    # Convert target dimensions to pixels
                    target_width, target_height = dimensions.to_pixels()

                    # If crop coordinates not provided, use center crop
                    if x is None or y is None or width is None or height is None:
                        # Calculate center crop
                        aspect_ratio = target_width / target_height

                        if orig_width / orig_height > aspect_ratio:
                            # Image is wider, crop width
                            new_width = int(orig_height * aspect_ratio)
                            x = (orig_width - new_width) // 2
                            y = 0
                            width = new_width
                            height = orig_height
                        else:
                            # Image is taller, crop height
                            new_height = int(orig_width / aspect_ratio)
                            x = 0
                            y = (orig_height - new_height) // 2
                            width = orig_width
                            height = new_height

                    # Ensure crop coordinates are within image bounds
                    x = max(0, min(x, orig_width))
                    y = max(0, min(y, orig_height))
                    width = min(width, orig_width - x)
                    height = min(height, orig_height - y)

                    # Crop image
                    cropped = img.crop((x, y, x + width, y + height))

                    # Resize to target dimensions with high quality
                    resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)

                    # Enhance image quality
                    enhancer = ImageEnhance.Sharpness(resized)
                    enhanced = enhancer.enhance(1.1)  # Daha hafif keskinleştirme

                    # Create output directory if it doesn't exist
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    # Orijinal görüntünün alfa kanalı olup olmadığını kontrol et
                    original_has_alpha = img.mode in ('RGBA', 'LA') or 'transparency' in img.info

                    if output_format == '.png':
                        # PNG için saydamlığı koru
                        if original_has_alpha:
                            # Saydamlık varsa RGBA modunda kal
                            if enhanced.mode != 'RGBA':
                                enhanced = enhanced.convert('RGBA')
                        else:
                            # Saydamlık yoksa RGB kullan
                            if enhanced.mode != 'RGB':
                                enhanced = enhanced.convert('RGB')
                        enhanced.save(output_path, format='PNG', optimize=True, dpi=(300, 300))

                    elif output_format in ['.jpg', '.jpeg']:
                        # JPEG için RGB moduna geç (saydamlık desteklenmez)
                        if enhanced.mode != 'RGB':
                            # Saydam arka planı beyaza çevir
                            if enhanced.mode == 'RGBA':
                                background = Image.new('RGB', enhanced.size, (255, 255, 255))
                                background.paste(enhanced, mask=enhanced.split()[-1])
                                enhanced = background
                            else:
                                enhanced = enhanced.convert('RGB')
                        enhanced.save(output_path, format='JPEG', quality=95, optimize=True, dpi=(300, 300))

                    else:
                        # Varsayılan olarak JPEG kaydet
                        if enhanced.mode != 'RGB':
                            if enhanced.mode == 'RGBA':
                                background = Image.new('RGB', enhanced.size, (255, 255, 255))
                                background.paste(enhanced, mask=enhanced.split()[-1])
                                enhanced = background
                            else:
                                enhanced = enhanced.convert('RGB')
                        output_path = output_path.with_suffix('.jpg')
                        enhanced.save(output_path, format='JPEG', quality=95, optimize=True, dpi=(300, 300))

                    self.logger.debug(f"Successfully cropped {image_path} to {output_path}")
                    return True

            except Exception as img_error:
                self.logger.error(f"PIL image processing error for {image_path}: {img_error}")
                return False

        except Exception as e:
            self.logger.error(f"Error cropping image {image_path}: {e}")
            return False

    def resize_image(self, image_path: Path, output_path: Path, 
                    dimensions: CropDimensions, maintain_aspect: bool = True) -> bool:
        """
        Resize image to specified dimensions
        """
        try:
            with Image.open(image_path) as img:
                target_width, target_height = dimensions.to_pixels()

                if maintain_aspect:
                    img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
                else:
                    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

                # Create output directory if it doesn't exist
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Save image
                img.save(output_path, quality=95, optimize=True)

                self.logger.debug(f"Successfully resized {image_path} to {output_path}")
                return True

        except Exception as e:
            self.logger.error(f"Error resizing image {image_path}: {e}")
            return False

    def get_image_files(self, directory: Path) -> List[Path]:
        """Get all supported image files from directory"""
        if not directory.exists() or not directory.is_dir():
            return []

        image_files = []
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                image_files.append(file_path)

        return sorted(image_files)

    def match_photos_to_people(self, photos: List[Path], people: List[Dict], 
                              match_method: str = 'sequential') -> Dict[str, Optional[Path]]:
        """
        Match photos to people based on specified method
        Returns dict with person identifier as key and photo path as value
        """
        matches = {}

        if match_method == 'sequential':
            # Sequential matching - match photos in order
            for i, person in enumerate(people):
                person_key = self._get_person_key(person)
                if i < len(photos):
                    matches[person_key] = photos[i]
                else:
                    matches[person_key] = None

        elif match_method == 'name_matching':
            # Try to match by filename
            matches = self._match_by_filename(photos, people)

        elif match_method == 'student_number':
            # Match by student number in filename
            matches = self._match_by_student_number(photos, people)

        return matches

    def _get_person_key(self, person: Dict) -> str:
        """Generate a unique key for a person"""
        if 'student_no' in person and person['student_no']:
            return f"{person['student_no']}_{person['first_name']}_{person['last_name']}"
        return f"{person['first_name']}_{person['last_name']}"

    def _match_by_filename(self, photos: List[Path], people: List[Dict]) -> Dict[str, Optional[Path]]:
        """Match photos by filename similarity to names"""
        matches = {}
        used_photos = set()

        for person in people:
            person_key = self._get_person_key(person)
            best_match = None
            best_score = 0

            # Create search terms
            search_terms = [
                person['first_name'].lower(),
                person['last_name'].lower(),
                f"{person['first_name']} {person['last_name']}".lower(),
                f"{person['last_name']} {person['first_name']}".lower()
            ]

            if 'student_no' in person and person['student_no']:
                search_terms.append(person['student_no'])

            # Find best matching photo
            for photo in photos:
                if photo in used_photos:
                    continue

                filename = photo.stem.lower()
                score = 0

                for term in search_terms:
                    if term in filename:
                        score += len(term)

                if score > best_score:
                    best_score = score
                    best_match = photo

            if best_match and best_score > 0:
                matches[person_key] = best_match
                used_photos.add(best_match)
            else:
                matches[person_key] = None

        return matches

    def _match_by_student_number(self, photos: List[Path], people: List[Dict]) -> Dict[str, Optional[Path]]:
        """Match photos by student number in filename"""
        matches = {}
        used_photos = set()

        for person in people:
            person_key = self._get_person_key(person)

            if 'student_no' not in person or not person['student_no']:
                matches[person_key] = None
                continue

            student_no = str(person['student_no'])
            best_match = None

            # Look for student number in filename
            for photo in photos:
                if photo in used_photos:
                    continue

                filename = photo.stem
                # Look for exact student number match
                if student_no in filename:
                    best_match = photo
                    break

            if best_match:
                matches[person_key] = best_match
                used_photos.add(best_match)
            else:
                matches[person_key] = None

        return matches

    def generate_filename(self, person: Dict[str, Any], pattern: str = 'first_last', 
                         selected_column: str = None, text_case: str = 'as_is', 
                         separator: str = '_') -> str:
        """Generate filename based on person data and pattern with flexible column selection"""

        if selected_column and selected_column in person.get('_original_data', {}):
            # Use user-selected column for naming
            base_name = person['_original_data'][selected_column]
            filename = str(base_name).strip()
        elif selected_column and selected_column in person:
            # Use mapped column data
            base_name = person[selected_column]
            filename = str(base_name).strip()
        else:
            # Use predefined patterns as fallback
            patterns = {
                'first_last': f"{person.get('first_name', '')}_{person.get('last_name', '')}",
                'last_first': f"{person.get('last_name', '')}_{person.get('first_name', '')}",
                'first_last_class': f"{person.get('first_name', '')}_{person.get('last_name', '')}_{person.get('class_name', '')}",
                'number_first_last': f"{person.get('student_no', '')}_{person.get('first_name', '')}_{person.get('last_name', '')}",
                'tc_first_last': f"{person.get('tc_no', '')}_{person.get('first_name', '')}_{person.get('last_name', '')}",
                'class_last_first': f"{person.get('class_name', '')}_{person.get('last_name', '')}_{person.get('first_name', '')}",
                'student_no': f"{person.get('student_no', 'no_number')}",
                'tc_no': f"{person.get('tc_no', 'no_tc')}"
            }

            filename = patterns.get(pattern, patterns['first_last'])

        try:
            # Apply text case transformation
            if filename:
                filename = self._apply_text_case(filename, text_case)

            # Apply separator replacement
            if filename:
                filename = self._apply_separator(filename, separator)

            # Clean the filename
            if filename:
                # Remove invalid characters for Windows filenames
                invalid_chars = '<>:"/\\|?*'
                for char in invalid_chars:
                    filename = filename.replace(char, '')

                # Remove multiple spaces with single space
                filename = ' '.join(filename.split())

                # Remove consecutive separators
                if separator:
                    while separator + separator in filename:
                        filename = filename.replace(separator + separator, separator)

                    # Remove leading/trailing separators
                    filename = filename.strip(separator)

                # Ensure filename is not empty
                if not filename:
                    filename = f"photo_{hash(str(person)) % 10000}"
            else:
                filename = f"photo_{hash(str(person)) % 10000}"

            return filename

        except Exception as e:
            self.logger.error(f"Error generating filename: {e}")
            return f"photo_{hash(str(person)) % 10000}"

    def _apply_text_case(self, text: str, case_type: str) -> str:
        """Apply text case transformation"""
        if not text or case_type == 'as_is':
            return text

        if case_type == 'uppercase':
            return text.upper()
        elif case_type == 'lowercase':
            return text.lower()
        elif case_type == 'title_case':
            # Turkish-aware title case
            return self._turkish_title_case(text)
        elif case_type == 'sentence_case':
            if text:
                return text[0].upper() + text[1:].lower()

        return text

    def _turkish_title_case(self, text: str) -> str:
        """Apply Turkish-aware title case"""
        # Handle Turkish specific characters for title case
        words = text.split()
        result = []

        for word in words:
            if word:
                # Handle Turkish i/I conversion properly
                if word[0].lower() == 'i':
                    # Turkish 'i' becomes 'İ' when capitalized
                    result.append('İ' + word[1:].lower())
                elif word[0].lower() == 'ı':
                    # Turkish 'ı' becomes 'I' when capitalized  
                    result.append('I' + word[1:].lower())
                else:
                    result.append(word[0].upper() + word[1:].lower())

        return ' '.join(result)

    def _apply_separator(self, text: str, separator: str) -> str:
        """Apply separator to text"""
        if not text:
            return text

        # Replace common separators with the chosen one
        common_separators = ['_', '-', ' ', '.']

        for sep in common_separators:
            if sep != separator:
                text = text.replace(sep, separator)

        return text
    def _get_class_name_from_record(self, record: Dict) -> str:
        """Extract class name from record for organization"""
        # Try different possible class field names
        class_fields = ['class_name', 'sınıf', 'sinif', 'class', 'sınıf_adı']

        for field in class_fields:
            if field in record and record[field]:
                return str(record[field]).strip()

        # Try from original data
        original_data = record.get('_original_data', {})
        for field in class_fields:
            if field in original_data and original_data[field]:
                return str(original_data[field]).strip()

        # Check all original data columns for class-like content
        for col_name, value in original_data.items():
            if value and any(class_word in col_name.lower() for class_word in ['sınıf', 'sinif', 'class']):
                return str(value).strip()

        return None

    def get_photos_by_class_for_pdf(self, photos: List[Path], excel_data: List[Dict], 
                                   primary_column: str) -> Dict[str, List[Dict]]:
        """
        Group photos by class for PDF generation
        Returns dict with class_name as key and list of photo info dicts as value
        """
        photos_by_class = {}

        for i, photo in enumerate(photos):
            if i < len(excel_data):
                record = excel_data[i]

                # Get class name
                class_name = self._get_class_name_from_record(record)
                if not class_name:
                    class_name = "Sınıf_Bilgisi_Yok"

                # Create display name from primary column
                display_name = photo.stem  # Use filename without extension as fallback
                if primary_column in record.get('_original_data', {}):
                    display_name = str(record['_original_data'][primary_column]).strip()

                if class_name not in photos_by_class:
                    photos_by_class[class_name] = []

                photos_by_class[class_name].append({
                    'filename': photo.name,
                    'display_name': display_name
                })

        return photos_by_class

    def copy_and_rename_photo(self, source_path: Path, dest_dir: Path, 
                             new_filename: str) -> Optional[Path]:
        """Copy photo to destination with new filename"""
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / new_filename

            shutil.copy2(source_path, dest_path)
            self.logger.debug(f"Copied {source_path} to {dest_path}")

            return dest_path

        except Exception as e:
            self.logger.error(f"Error copying photo {source_path}: {e}")
            return None

    def organize_photos_by_school(self, photos: List[Path], output_dir: Path, 
                                 school_name: str) -> Optional[Path]:
        """Organize photos by creating school folder and moving photos there"""
        try:
            # Clean school name for folder creation
            clean_school_name = re.sub(r'[^\w\s\-_]', '_', school_name)
            clean_school_name = re.sub(r'\s+', '_', clean_school_name.strip())

            # Create school folder
            school_folder = output_dir / clean_school_name
            school_folder.mkdir(parents=True, exist_ok=True)

            moved_photos = []
            for photo in photos:
                if photo.exists():
                    dest_path = school_folder / photo.name
                    shutil.move(str(photo), str(dest_path))
                    moved_photos.append(dest_path)
                    self.logger.debug(f"Moved {photo} to {dest_path}")

            self.logger.info(f"Organized {len(moved_photos)} photos into school folder: {school_folder}")
            return school_folder

        except Exception as e:
            self.logger.error(f"Error organizing photos by school: {e}")
            return None

    def organize_photos_by_class(self, photos_with_classes: Dict[str, List[Path]], 
                                output_dir: Path, school_name: str = None) -> Dict[str, Path]:
        """
        Organize photos by class folders

        Args:
            photos_with_classes: Dict mapping class names to photo paths
            output_dir: Base output directory
            school_name: Optional school name for nested organization

        Returns:
            Dict mapping class names to their folder paths
        """
        created_folders = {}

        try:
            for class_name, photos in photos_with_classes.items():
                if not photos:
                    continue

                # Clean class name for folder creation
                clean_class_name = re.sub(r'[^\w\s\-_]', '_', class_name)
                clean_class_name = re.sub(r'\s+', '_', clean_class_name.strip())

                # Create class folder structure
                if school_name:
                    clean_school_name = re.sub(r'[^\w\s\-_]', '_', school_name)
                    clean_school_name = re.sub(r'\s+', '_', clean_school_name.strip())
                    class_folder = output_dir / clean_school_name / clean_class_name
                else:
                    class_folder = output_dir / clean_class_name

                class_folder.mkdir(parents=True, exist_ok=True)
                created_folders[class_name] = class_folder

                # Move photos to class folder
                moved_count = 0
                for photo in photos:
                    if photo.exists():
                        dest_path = class_folder / photo.name
                        try:
                            shutil.move(str(photo), str(dest_path))
                            moved_count += 1
                            self.logger.debug(f"Moved {photo} to {dest_path}")
                        except Exception as e:
                            self.logger.error(f"Error moving {photo} to {dest_path}: {e}")

                self.logger.info(f"Organized {moved_count} photos into class folder: {class_folder}")

            return created_folders

        except Exception as e:
            self.logger.error(f"Error organizing photos by class: {e}")
            return {}

    def get_photos_by_class_from_data(self, photos: List[Path], excel_data: List[Dict],
                                     naming_pattern: str, selected_column: str = None) -> Dict[str, List[Path]]:
        """
        Group photos by class based on Excel data
        Assumes sequential matching between photos and data
        """
        photos_by_class = {}

        try:
            for i, record in enumerate(excel_data):
                if i >= len(photos):
                    break

                # Get class name from record
                class_name = self._get_class_name_from_record(record)
                if not class_name:
                    class_name = "Sınıf_Bilgisi_Yok"

                if class_name not in photos_by_class:
                    photos_by_class[class_name] = []

                photos_by_class[class_name].append(photos[i])

            return photos_by_class

        except Exception as e:
            self.logger.error(f"Error grouping photos by class: {e}")
            return {}

    def _get_class_name_from_record(self, record: Dict) -> Optional[str]:
        """Extract class name from record using multiple possible fields"""
        # Try different possible field names for class
        possible_class_fields = ['class_name', 'sınıf', 'sinif', 'class', 'sınıf_adı', 'sinif_adi']

        # First check mapped data
        for field in possible_class_fields:
            if field in record and record[field]:
                return str(record[field]).strip()

        # Then check original data
        original_data = record.get('_original_data', {})
        for field in possible_class_fields:
            if field in original_data and original_data[field]:
                return str(original_data[field]).strip()

        # Try to find any column that might contain class information
        for col_name, value in original_data.items():
            if value and any(keyword in col_name.lower() for keyword in ['sınıf', 'sinif', 'class']):
                return str(value).strip()

        return None

    def copy_photos_to_school_folder(self, photos: List[Path], output_dir: Path, 
                                   school_name: str) -> Optional[Path]:
        """Copy photos to school folder without moving originals"""
        try:
            # Clean school name for folder creation
            clean_school_name = re.sub(r'[^\w\s\-_]', '_', school_name)
            clean_school_name = re.sub(r'\s+', '_', clean_school_name.strip())

            # Create school folder
            school_folder = output_dir / clean_school_name
            school_folder.mkdir(parents=True, exist_ok=True)

            copied_photos = []
            for photo in photos:
                if photo.exists():
                    dest_path = school_folder / photo.name
                    shutil.copy2(str(photo), str(dest_path))
                    copied_photos.append(dest_path)
                    self.logger.debug(f"Copied {photo} to {dest_path}")

            self.logger.info(f"Copied {len(copied_photos)} photos to school folder: {school_folder}")
            return school_folder

        except Exception as e:
            self.logger.error(f"Error copying photos to school folder: {e}")
            return None

    def add_watermark(self, image_path: Path, watermark_path: Path, 
                     output_path: Path, watermark_size: Tuple[int, int] = (50, 50),
                     position: str = 'bottom_right', opacity: float = 0.7) -> bool:
        """
        Add watermark to image

        Args:
            image_path: Path to the main image
            watermark_path: Path to the watermark/logo image
            output_path: Path where the watermarked image will be saved
            watermark_size: Size of the watermark (width, height) in pixels
            position: Position of watermark ('bottom_right', 'bottom_left', 'top_right', 'top_left', 'center')
            opacity: Watermark opacity (0.0 to 1.0)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with Image.open(image_path) as base_img:
                with Image.open(watermark_path) as watermark_img:
                    # Resize watermark
                    watermark_resized = watermark_img.resize(watermark_size, Image.Resampling.LANCZOS)

                    # Convert to RGBA for transparency
                    if base_img.mode != 'RGBA':
                        base_img = base_img.convert('RGBA')
                    if watermark_resized.mode != 'RGBA':
                        watermark_resized = watermark_resized.convert('RGBA')

                    # Adjust opacity
                    alpha = watermark_resized.split()[-1]
                    alpha = alpha.point(lambda p: p * opacity)
                    watermark_resized.putalpha(alpha)

                    # Calculate position
                    base_width, base_height = base_img.size
                    wm_width, wm_height = watermark_resized.size

                    positions = {
                        'bottom_right': (base_width - wm_width - 10, base_height - wm_height - 10),
                        'bottom_left': (10, base_height - wm_height - 10),
                        'top_right': (base_width - wm_width - 10, 10),
                        'top_left': (10, 10),
                        'center': ((base_width - wm_width) // 2, (base_height - wm_height) // 2)
                    }

                    pos = positions.get(position, positions['bottom_right'])

                    # Paste watermark
                    base_img.paste(watermark_resized, pos, watermark_resized)

                    # Save image
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    base_img.save(output_path, quality=95, optimize=True)

                    self.logger.debug(f"Successfully added watermark to {image_path}")
                    return True

        except Exception as e:
            self.logger.error(f"Error adding watermark to {image_path}: {e}")
            return False