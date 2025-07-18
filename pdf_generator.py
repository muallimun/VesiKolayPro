"""This commit expands the text area for visual file names in PDFs to accommodate up to 5 lines."""
"""
VesiKolay Pro - PDF Generator
Handles PDF generation for ID cards and student/teacher lists
"""

from fpdf import FPDF
import logging
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image
import io
import urllib.request
import tempfile
import os

class PDFGenerator:
    """PDF generation handler for class lists and ID cards"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_fonts()

    def setup_fonts(self):
        """Setup fonts for Turkish character support"""
        try:
            # DejaVu Sans font'u Türkçe karakter desteği için ekle
            from pathlib import Path
            
            # Font dosyası yolu (proje klasörünüze koyun)
            font_path = Path(__file__).parent / "fonts" / "DejaVuSans.ttf"
            
            if font_path.exists():
                # Türkçe karakter destekli font ekle
                self.default_font = 'DejaVu'
                self.logger.info("Using DejaVu font for Turkish character support")
            else:
                # Fallback olarak Arial kullan
                self.default_font = 'Arial'
                self.logger.warning("DejaVu font not found, using Arial as fallback")
                
        except Exception as e:
            self.logger.warning(f"Font setup failed, using default: {e}")
            self.default_font = 'Arial'
    def _add_photo_to_pdf(self, pdf: FPDF, photo_path: Path, x: float, y: float, 
                         width: float, height: float) -> None:
        """Add photo to PDF at specified position with proper aspect ratio"""
        try:
            # Open image
            with Image.open(photo_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Calculate proper dimensions to maintain aspect ratio
                img_width, img_height = img.size
                img_aspect = img_width / img_height
                target_aspect = width / height

                # Calculate new dimensions that fit within the target area
                if img_aspect > target_aspect:
                    # Image is wider than target, fit by width
                    new_width = width
                    new_height = width / img_aspect
                    # Center vertically
                    y_offset = (height - new_height) / 2
                    final_x = x
                    final_y = y + y_offset
                else:
                    # Image is taller than target, fit by height
                    new_height = height
                    new_width = height * img_aspect
                    # Center horizontally
                    x_offset = (width - new_width) / 2
                    final_x = x + x_offset
                    final_y = y

                # Resize image with much higher resolution for better quality
                scale_factor = 8  # Increased from 4 to 8 for much better quality
                target_pixel_width = int(new_width * scale_factor)
                target_pixel_height = int(new_height * scale_factor)

                img_resized = img.resize((target_pixel_width, target_pixel_height), Image.Resampling.LANCZOS)

                # Save to temporary bytes with maximum quality
                img_bytes = io.BytesIO()
                img_resized.save(img_bytes, format='JPEG', quality=98, optimize=False, dpi=(300, 300))
                img_bytes.seek(0)

                # Add to PDF with calculated dimensions
                pdf.image(img_bytes, final_x, final_y, new_width, new_height)

        except Exception as e:
            self.logger.error(f"Error adding photo to PDF: {e}")
            raise

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            else:
                return (45, 85, 165)  # Default blue if invalid hex
        except Exception:
            return (45, 85, 165)  # Default blue if conversion fails

       
    def generate_class_list(self, students: List[Dict], class_name: str, 
                        output_path: Path, include_photos: bool = False,
                        photos_dir: Optional[Path] = None) -> bool:
        """Generate class list PDF"""
        try:
            pdf = FPDF('P', 'mm', 'A4')

            # Yazı tipi yüklemesini tek noktadan yap
            self._register_fonts(pdf)

            pdf.add_page()
            
            # Başlık - Türkçe karakterlerle
            pdf.set_font(self.default_font, 'B', 16)
            pdf.cell(0, 10, f'Sınıf Listesi - {class_name}', 0, 1, 'C')
            pdf.ln(5)

            # Headers
            pdf.set_font(self.default_font, 'B', 12)
            if include_photos:
                pdf.cell(20, 8, 'Fotoğraf', 1, 0, 'C')
                pdf.cell(15, 8, 'No.', 1, 0, 'C')
                pdf.cell(40, 8, 'Adı', 1, 0, 'C')
                pdf.cell(40, 8, 'Soyadı', 1, 0, 'C')
                pdf.cell(25, 8, 'Öğrenci No', 1, 1, 'C')
                row_height = 20
            else:
                pdf.cell(15, 8, self._convert_turkish_chars('No.'), 1, 0, 'C')
                pdf.cell(50, 8, self._convert_turkish_chars('Adi'), 1, 0, 'C')
                pdf.cell(50, 8, self._convert_turkish_chars('Soyadi'), 1, 0, 'C')
                pdf.cell(30, 8, self._convert_turkish_chars('Ogrenci No'), 1, 1, 'C')
                row_height = 8

            # Student data with Turkish character support
            pdf.set_font(self.default_font, '', 10)
            for i, student in enumerate(students, 1):
                # Check if new page needed
                if pdf.get_y() + row_height > 280:
                    pdf.add_page()
                    # Re-add headers
                    pdf.set_font(self.default_font, 'B', 12)
                    if include_photos:
                        pdf.cell(20, 8, 'Fotograf', 1, 0, 'C')
                        pdf.cell(15, 8, 'No.', 1, 0, 'C')
                        pdf.cell(40, 8, 'Adi', 1, 0, 'C')
                        pdf.cell(40, 8, 'Soyadi', 1, 0, 'C')
                        pdf.cell(25, 8, 'Ogrenci No', 1, 1, 'C')
                    else:
                        pdf.cell(15, 8, 'No.', 1, 0, 'C')
                        pdf.cell(50, 8, 'Adi', 1, 0, 'C')
                        pdf.cell(50, 8, 'Soyadi', 1, 0, 'C')
                        pdf.cell(30, 8, 'Ogrenci No', 1, 1, 'C')
                    pdf.set_font(self.default_font, '', 10)

                y_start = pdf.get_y()

                # Convert student names to safe characters
                safe_first_name = self._convert_turkish_chars(student.get('first_name', ''))
                safe_last_name = self._convert_turkish_chars(student.get('last_name', ''))

                if include_photos:
                    # Photo cell
                    pdf.cell(20, row_height, '', 1, 0, 'C')

                    # Add photo if available
                    if photos_dir and student.get('photo_filename'):
                        photo_path = photos_dir / student['photo_filename']
                        if photo_path.exists():
                            try:
                                self._add_photo_to_pdf(pdf, photo_path, 
                                                     pdf.get_x() - 18, y_start + 2, 16, 16)
                            except Exception as e:
                                self.logger.warning(f"Could not add photo for student {i}: {e}")

                    pdf.cell(15, row_height, str(i), 1, 0, 'C')
                    pdf.cell(40, row_height, safe_first_name[:18], 1, 0, 'L')
                    pdf.cell(40, row_height, safe_last_name[:18], 1, 0, 'L')
                    pdf.cell(25, row_height, str(student.get('student_no', ''))[:12], 1, 1, 'C')
                else:
                    pdf.cell(15, row_height, str(i), 1, 0, 'C')
                    pdf.cell(50, row_height, safe_first_name[:23], 1, 0, 'L')
                    pdf.cell(50, row_height, safe_last_name[:23], 1, 0, 'L')
                    pdf.cell(30, row_height, str(student.get('student_no', ''))[:15], 1, 1, 'C')

            # Footer with Turkish character support
            pdf.ln(10)
            pdf.set_font(self.default_font, 'I', 8)
            from datetime import datetime
            footer_text = self._convert_turkish_chars(f'Olusturma Tarihi: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
            pdf.cell(0, 5, footer_text, 0, 1, 'R')

            # Save PDF
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pdf.output(str(output_path))

            self.logger.info(f"Generated class list PDF: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error generating class list PDF: {e}")
            return False

    def generate_class_photo_grid(self, photos_with_names: List[Dict], 
                                 class_name: str, school_name: str, 
                                 output_path: Path, photos_dir: Path) -> bool:
        """Generate a photo grid PDF for a class"""
        try:
            pdf = FPDF('P', 'mm', 'A4')
            
            # Add DejaVu fonts if available
            self._register_fonts(pdf)
            
            pdf.add_page()

            # Title with Turkish character support
            pdf.set_font(self.default_font, 'B', 16)

            # Convert Turkish characters for FPDF compatibility
            safe_school_name = self._convert_turkish_chars(school_name)
            safe_class_name = self._convert_turkish_chars(class_name)
            safe_title = f'{safe_school_name} - {safe_class_name}'

            pdf.cell(0, 10, safe_title, 0, 1, 'C')

            # Page dimensions
            page_width = 210  # A4 width in mm
            page_height = 297  # A4 height in mm
            margin = 10

            # Grid configuration for minimum 40 photos per page
            grid_cols = 8  # 8 columns for more photos
            grid_rows = 5  # 5 rows = 40 photos minimum
            photos_per_page = grid_cols * grid_rows

            # Calculate photo dimensions to fit 40+ photos
            usable_width = page_width - (2 * margin)
            usable_height = page_height - (2 * margin) - 20  # Reserve space for title

            # Optimized spacing for more photos with better text space
            text_space = 15  # Space for up to 5 lines of text under photos (increased)
            spacing = 2  # Reduced spacing between photos

            photo_width = (usable_width - (grid_cols - 1) * spacing) / grid_cols
            photo_height = (usable_height - (grid_rows - 1) * spacing - grid_rows * text_space) / grid_rows

            # Adjust photo dimensions to ensure text area is adequate
            if photo_height < 15:  # Minimum photo height
                photo_height = 15
                # Recalculate available space
                total_photo_area = grid_rows * photo_height + (grid_rows - 1) * spacing + grid_rows * text_space
                if total_photo_area > usable_height:
                    # Reduce photo height proportionally
                    available_for_photos = usable_height - (grid_rows - 1) * spacing - grid_rows * text_space
                    photo_height = available_for_photos / grid_rows

            # Ensure photos maintain proper aspect ratio (portrait)
            if photo_width / photo_height > 0.8:  # If too wide
                photo_width = photo_height * 0.75  # Make it more portrait-like

            pdf.ln(5)
            current_y = pdf.get_y()

            for page_start in range(0, len(photos_with_names), photos_per_page):
                if page_start > 0:
                    pdf.add_page()
                    pdf.set_font(self.default_font, 'B', 16)
                    safe_title_cont = self._convert_turkish_chars(safe_title + " (devami)")
                    pdf.cell(0, 10, safe_title_cont, 0, 1, 'C')
                    pdf.ln(5)
                    current_y = pdf.get_y()

                page_photos = photos_with_names[page_start:page_start + photos_per_page]

                for i, photo_info in enumerate(page_photos):
                    row = i // grid_cols
                    col = i % grid_cols

                    # Calculate position with proper spacing
                    x = margin + col * (photo_width + spacing)
                    y = current_y + row * (photo_height + text_space + spacing)

                    # Photo frame with proper proportions
                    pdf.set_line_width(0.2)
                    pdf.set_draw_color(128, 128, 128)
                    pdf.rect(x, y, photo_width, photo_height)

                    # Add photo if exists with high quality
                    photo_path = photos_dir / photo_info['filename']
                    if photo_path.exists():
                        try:
                            self._add_high_quality_photo_to_pdf(pdf, photo_path, x + 1, y + 1, 
                                                 photo_width - 2, photo_height - 2)
                        except Exception as e:
                            self.logger.warning(f"Could not add photo {photo_info['filename']}: {e}")
                            # Photo placeholder on error
                            pdf.set_fill_color(240, 240, 240)
                            pdf.rect(x + 1, y + 1, photo_width - 2, photo_height - 2, 'F')
                            pdf.set_xy(x, y + photo_height/2)
                            pdf.set_font(self.default_font, 'I', 7)
                            pdf.set_text_color(128, 128, 128)
                            pdf.cell(photo_width, 3, self._convert_turkish_chars('Fotograf Yok'), 0, 0, 'C')
                    else:
                        # Photo placeholder
                        pdf.set_fill_color(240, 240, 240)
                        pdf.rect(x + 1, y + 1, photo_width - 2, photo_height - 2, 'F')
                        pdf.set_xy(x, y + photo_height/2)
                        pdf.set_font(self.default_font, 'I', 7)
                        pdf.set_text_color(128, 128, 128)
                        pdf.cell(photo_width, 3, self._convert_turkish_chars('Fotograf Yok'), 0, 0, 'C')

                    # Multi-line filename below photo with proper text wrapping
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font(self.default_font, '', 6)  # 6 punto font as requested

                    # Get filename and convert Turkish characters
                    display_name = photo_info.get('display_name', photo_info.get('filename', 'Unknown'))
                    
                    # If display_name is empty or just the filename, try to extract meaningful name
                    if not display_name or display_name == 'Unknown' or display_name == photo_info.get('filename', ''):
                        # Use filename without extension as fallback
                        display_name = Path(photo_info.get('filename', 'Unknown')).stem
                    
                    # Convert Turkish characters for font compatibility
                    safe_display_name = self._convert_turkish_chars(str(display_name))

                    # Smart line breaking based on separators in filename
                    # Split by common separators used in Excel data
                    separators = [' ', '-', '_', '.']
                    parts = []

                    # Split the filename by separators while keeping track of what was split
                    temp_parts = [safe_display_name]
                    for sep in separators:
                        new_temp_parts = []
                        for part in temp_parts:
                            if sep in part:
                                split_parts = part.split(sep)
                                # Filter out empty parts
                                split_parts = [p.strip() for p in split_parts if p.strip()]
                                new_temp_parts.extend(split_parts)
                            else:
                                new_temp_parts.append(part)
                        temp_parts = new_temp_parts

                    parts = temp_parts

                    # Create lines from parts - each part on separate line for clarity
                    lines = []
                    for part in parts:  # Use all parts, no limit
                        if part and part.strip():
                            # Ensure part fits in available width
                            char_width = 0.7  # Character width for 6pt font
                            available_width = photo_width - 4  # Leave 2mm margin on each side
                            max_chars_per_line = max(8, int(available_width / char_width))

                            if len(part) > max_chars_per_line:
                                # Truncate long parts with ellipsis
                                part = part[:max_chars_per_line-3] + "..."

                            lines.append(part.strip())

                    # If we have very short parts (4-5 chars), we can combine some on same line
                    if len(lines) > 1:
                        combined_lines = []
                        current_combined = ""

                        for line in lines:
                            # If both current and new line are short, combine them
                            if len(line) <= 5 and len(current_combined) <= 5 and current_combined:
                                test_combined = current_combined + " " + line
                                char_width = 0.7
                                available_width = photo_width - 4
                                max_chars_per_line = max(8, int(available_width / char_width))

                                if len(test_combined) <= max_chars_per_line:
                                    current_combined = test_combined
                                else:
                                    combined_lines.append(current_combined)
                                    current_combined = line
                            else:
                                if current_combined:
                                    combined_lines.append(current_combined)
                                current_combined = line

                        if current_combined:
                            combined_lines.append(current_combined)

                        # Use combined lines if they result in better layout
                        lines = combined_lines

                    # Write each line with proper spacing - text area width equals photo width
                    text_start_y = y + photo_height + spacing  # Use same spacing as between photos
                    line_height = 2.8  # Optimized line height for 5 lines

                    # Display all lines without arbitrary limits
                    for line_idx, line in enumerate(lines):
                        line_y = text_start_y + (line_idx * line_height)

                        # Ensure text doesn't exceed allocated space
                        if line_y + line_height <= y + photo_height + text_space:
                            # Text area width exactly matches photo width
                            text_x = x  # Start at same x as photo
                            text_width = photo_width  # Exact same width as photo

                            pdf.set_xy(text_x, line_y)
                            pdf.cell(text_width, line_height, line, 0, 0, 'C')
                        else:
                            # If we run out of space, stop adding more lines
                            break

            # Footer
            pdf.ln(10)
            pdf.set_font(self.default_font, 'I', 8)
            from datetime import datetime
            footer_text = self._convert_turkish_chars(f'Olusturma Tarihi: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
            pdf.cell(0, 5, footer_text, 0, 1, 'R')

            # Save PDF
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pdf.output(str(output_path))

            self.logger.info(f"Generated class photo grid PDF: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error generating class photo grid PDF: {e}")
            return False

    def generate_teacher_list(self, teachers: List[Dict], school_name: str,
                             output_path: Path, include_photos: bool = False,
                             photos_dir: Optional[Path] = None) -> bool:
        """Generate teacher list PDF"""
        try:
            pdf = FPDF('P', 'mm', 'A4')
            
            # Add DejaVu fonts if available
            self._register_fonts(pdf)
            
            pdf.add_page()

            # Title with Turkish character support
            pdf.set_font(self.default_font, 'B', 16)
            safe_school_name = self._convert_turkish_chars(school_name)
            safe_title = self._convert_turkish_chars(f'Ogretmen Listesi - {safe_school_name}')
            pdf.cell(0, 10, safe_title, 0, 1, 'C')
            pdf.ln(5)

            # Headers with Turkish character support
            pdf.set_font(self.default_font, 'B', 12)
            if include_photos:
                pdf.cell(20, 8, self._convert_turkish_chars('Fotograf'), 1, 0, 'C')
                pdf.cell(15, 8, self._convert_turkish_chars('No.'), 1, 0, 'C')
                pdf.cell(40, 8, self._convert_turkish_chars('Adi'), 1, 0, 'C')
                pdf.cell(40, 8, self._convert_turkish_chars('Soyadi'), 1, 0, 'C')
                pdf.cell(35, 8, self._convert_turkish_chars('Bransi'), 1, 1, 'C')
                row_height = 20
            else:
                pdf.cell(15, 8, self._convert_turkish_chars('No.'), 1, 0, 'C')
                pdf.cell(50, 8, self._convert_turkish_chars('Adi'), 1, 0, 'C')
                pdf.cell(50, 8, self._convert_turkish_chars('Soyadi'), 1, 0, 'C')
                pdf.cell(40, 8, self._convert_turkish_chars('Bransi'), 1, 1, 'C')
                row_height = 8

            # Teacher data with Turkish character support
            pdf.set_font(self.default_font, '', 10)
            for i, teacher in enumerate(teachers, 1):
                # Check if new page needed
                if pdf.get_y() + row_height > 280:
                    pdf.add_page()
                    # Re-add headers
                    pdf.set_font(self.default_font, 'B', 12)
                    if include_photos:
                        pdf.cell(20, 8, 'Fotograf', 1, 0, 'C')
                        pdf.cell(15, 8, 'No.', 1, 0, 'C')
                        pdf.cell(40, 8, 'Adi', 1, 0, 'C')
                        pdf.cell(40, 8, 'Soyadi', 1, 0, 'C')
                        pdf.cell(35, 8, 'Bransi', 1, 1, 'C')
                    else:
                        pdf.cell(15, 8, 'No.', 1, 0, 'C')
                        pdf.cell(50, 8, 'Adi', 1, 0, 'C')
                        pdf.cell(50, 8, 'Soyadi', 1, 0, 'C')
                        pdf.cell(40, 8, 'Bransi', 1, 1, 'C')
                    pdf.set_font(self.default_font, '', 10)

                y_start = pdf.get_y()

                # Convert teacher names and branch to safe characters
                safe_first_name = self._convert_turkish_chars(teacher.get('first_name', ''))
                safe_last_name = self._convert_turkish_chars(teacher.get('last_name', ''))
                safe_branch = self._convert_turkish_chars(teacher.get('branch', ''))

                if include_photos:
                    # Photo cell
                    pdf.cell(20, row_height, '', 1, 0, 'C')

                    # Add photo if available
                    if photos_dir and teacher.get('photo_filename'):
                        photo_path = photos_dir / teacher['photo_filename']
                        if photo_path.exists():
                            try:
                                self._add_photo_to_pdf(pdf, photo_path, 
                                                     pdf.get_x() - 18, y_start + 2, 16, 16)
                            except Exception as e:
                                self.logger.warning(f"Could not add photo for teacher {i}: {e}")

                    pdf.cell(15, row_height, str(i), 1, 0, 'C')
                    pdf.cell(40, row_height, safe_first_name[:18], 1, 0, 'L')
                    pdf.cell(40, row_height, safe_last_name[:18], 1, 0, 'L')
                    pdf.cell(35, row_height, safe_branch[:15], 1, 1, 'L')
                else:
                    pdf.cell(15, row_height, str(i), 1, 0, 'C')
                    pdf.cell(50, row_height, safe_first_name[:23], 1, 0, 'L')
                    pdf.cell(50, row_height, safe_last_name[:23], 1, 0, 'L')
                    pdf.cell(40, row_height, safe_branch[:18], 1, 1, 'L')

            # Footer with Turkish character support
            pdf.ln(10)
            pdf.set_font(self.default_font, 'I', 8)
            from datetime import datetime
            footer_text = self._convert_turkish_chars(f'Olusturma Tarihi: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
            pdf.cell(0, 5, footer_text, 0, 1, 'R')

            # Save PDF
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pdf.output(str(output_path))

            self.logger.info(f"Generated teacher list PDF: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error generating teacher list PDF: {e}")
            return False

    def generate_id_cards(self, people: List[Dict], template_type: str, 
                          output_path: Path, photos_dir: Optional[Path] = None, 
                          progress_callback: Optional[callable] = None) -> bool:
        """
        Generate professional ID cards PDF with cutting guides - 10 cards per A4 page
        """
        try:
            pdf = FPDF('P', 'mm', 'A4')
            pdf.set_auto_page_break(auto=False)

            # Yazı tipi tanımlamalarını yap
            self._register_fonts(pdf)

            # Başlangıç font ayarı (Türkçe destekli font ile)
            pdf.set_font(self.default_font, 'B', 10)

            # ID card dimensions - optimized for 10 cards per page
            card_width = 80
            card_height = 50

            # A4 layout for 2x5 = 10 cards per page
            cards_per_row = 2
            cards_per_col = 5
            cards_per_page = 10

            # Calculate spacing to center cards on A4
            page_width = 210  # A4 width
            page_height = 297  # A4 height

            # Calculate margins to center the cards
            total_cards_width = cards_per_row * card_width
            total_cards_height = cards_per_col * card_height

            # Spacing between cards
            card_spacing_x = (page_width - total_cards_width) / (cards_per_row + 1)
            card_spacing_y = (page_height - total_cards_height) / (cards_per_col + 1)

            # Starting positions
            start_x = card_spacing_x
            start_y = card_spacing_y

            card_count = 0
            total_people = len(people)

            for person in people:
                # Add new page if needed
                if card_count % cards_per_page == 0:
                    pdf.add_page()

                    # Draw cutting guides for 2x5 layout
                    self._draw_cutting_guides_2x5(pdf, start_x, start_y, card_width, card_height,
                                                  card_spacing_x, card_spacing_y)

                # Calculate position for this card
                row = (card_count % cards_per_page) // cards_per_row
                col = (card_count % cards_per_page) % cards_per_row

                x = start_x + col * (card_width + card_spacing_x)
                y = start_y + row * (card_height + card_spacing_y)

                # Draw card
                self._draw_professional_id_card(pdf, person, x, y, card_width, card_height, 
                                                template_type, photos_dir)

                card_count += 1
                
                # İlerleme callback'ini çağır
                if progress_callback:
                    progress_percent = (card_count / total_people) * 100
                    person_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
                    progress_callback(progress_percent, f"Kimlik kartı: {person_name} ({card_count}/{total_people})")

            # Save PDF
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pdf.output(str(output_path))

            self.logger.info(f"Generated {card_count} ID cards PDF: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error generating ID cards PDF: {e}")
            return False


    def _draw_cutting_guides_2x4(self, pdf: FPDF, start_x: float, start_y: float, 
                                card_width: float, card_height: float,
                                spacing_x: float, spacing_y: float):
        """Draw cutting guides for 2x4 card layout"""
        pdf.set_line_width(0.2)
        pdf.set_draw_color(128, 128, 128)
        pdf.set_dash_pattern(dash=2, gap=2)

        guide_length = 5

        # Vertical cutting lines (between columns)
        center_x = start_x + card_width + spacing_x/2
        for row in range(4):
            y_pos = start_y + row * (card_height + spacing_y)
            # Top guide
            pdf.line(center_x, y_pos - guide_length, center_x, y_pos)
            # Bottom guide
            pdf.line(center_x, y_pos + card_height, center_x, y_pos + card_height + guide_length)

        # Horizontal cutting lines (between rows)
        for row in range(1, 4):
            y_pos = start_y + row * (card_height + spacing_y) - spacing_y/2
            for col in range(2):
                x_pos = start_x + col * (card_width + spacing_x)
                # Left guide
                pdf.line(x_pos - guide_length, y_pos, x_pos, y_pos)
                # Right guide
                pdf.line(x_pos + card_width, y_pos, x_pos + card_width + guide_length, y_pos)

        # Reset line style
        pdf.set_dash_pattern()

    def _draw_cutting_guides_2x5(self, pdf: FPDF, start_x: float, start_y: float, 
                                card_width: float, card_height: float,
                                spacing_x: float, spacing_y: float):
        """Draw cutting guides for 2x5 card layout"""
        pdf.set_line_width(0.2)
        pdf.set_draw_color(128, 128, 128)
        pdf.set_dash_pattern(dash=2, gap=2)

        guide_length = 5

        # Vertical cutting lines (between columns)
        center_x = start_x + card_width + spacing_x/2
        for row in range(5):
            y_pos = start_y + row * (card_height + spacing_y)
            # Top guide
            pdf.line(center_x, y_pos - guide_length, center_x, y_pos)
            # Bottom guide
            pdf.line(center_x, y_pos + card_height, center_x, y_pos + card_height + guide_length)

        # Horizontal cutting lines (between rows)
        for row in range(1, 5):
            y_pos = start_y + row * (card_height + spacing_y) - spacing_y/2
            for col in range(2):
                x_pos = start_x + col * (card_width + spacing_x)
                # Left guide
                pdf.line(x_pos - guide_length, y_pos, x_pos, y_pos)
                # Right guide
                pdf.line(x_pos + card_width, y_pos, x_pos + card_width + guide_length, y_pos)

        # Reset line style
        pdf.set_dash_pattern()

    def _draw_professional_id_card(self, pdf: FPDF, person: Dict, x: float, y: float, 
                                   width: float, height: float, template_type: str, 
                                   photos_dir: Optional[Path]):
        """Draw modern, professional ID card with clean design"""

        # Debug: Log kişi bilgilerini
        self.logger.debug(f"Drawing ID card for person: {person.get('first_name', 'N/A')} {person.get('last_name', 'N/A')}")

        # Card border - thin and elegant
        pdf.set_line_width(0.3)
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(x, y, width, height)

        # Modern header with gradient support - compact height for 3 lines
        header_height = 12  # Reduced from 15 to 12
        header_color = person.get('header_color', '#2D55A5')
        header_gradient = person.get('header_gradient', False)
        header_gradient_color2 = person.get('header_gradient_color2', '#1B3F73')
        
        if header_gradient:
            self._draw_gradient_rectangle(pdf, x, y, width, header_height, 
                                         header_color, header_gradient_color2, 'horizontal')
        else:
            # Solid color header
            header_rgb = self._hex_to_rgb(header_color)
            pdf.set_fill_color(header_rgb[0], header_rgb[1], header_rgb[2])
            pdf.rect(x, y, width, header_height, 'F')

        # Main logo area - left side - boyutlar renkli alan yüksekliğine uygun artırıldı
        logo_width = 12  # 10'dan 12'ye artırıldı (2mm artış)
        logo_height = 10  # 8'den 10'a artırıldı (2mm artış)
        logo_x = x + 2
        logo_y = y + 1  # Y pozisyonu 1mm yukarı alındı (dikey ortalama için)

        # Try to add main school logo if available
        main_logo_added = False
        main_logo_path = person.get('main_logo_path') or person.get('logo_path')
        if main_logo_path and Path(main_logo_path).exists():
            try:
                self._add_logo_with_transparency(pdf, Path(main_logo_path), logo_x, logo_y, logo_width, logo_height, 
                                               header_color, header_gradient, header_gradient_color2, 'left')
                main_logo_added = True
            except Exception as e:
                self.logger.warning(f"Could not add main logo: {e}")

        # Second logo area - right side - exact same dimensions and properties as left logo
        second_logo_width = logo_width  # Exactly same as main logo (12)
        second_logo_height = logo_height  # Exactly same as main logo (10)
        second_logo_x = x + width - second_logo_width - 2
        second_logo_y = logo_y  # Exactly same Y position as main logo

        # Try to add second logo if available - same treatment as main logo
        second_logo_added = False
        second_logo_path = person.get('second_logo_path')
        if second_logo_path and Path(second_logo_path).exists():
            try:
                self._add_logo_with_transparency(pdf, Path(second_logo_path), second_logo_x, second_logo_y, second_logo_width, second_logo_height, 
                                               header_color, header_gradient, header_gradient_color2, 'right')
                second_logo_added = True
            except Exception as e:
                self.logger.warning(f"Could not add second logo: {e}")

        # Header text - 3 lines with proper spacing (renkli alan içinde) - dikey ortalanmış
        # Calculate text area between logos - yeni logo boyutlarına göre güncellenmiş
        if main_logo_added and second_logo_added:
            text_start_x = x + logo_width + 2
            text_width = width - logo_width - second_logo_width - 6
        elif main_logo_added:
            text_start_x = x + logo_width + 2
            text_width = width - logo_width - second_logo_width - 4
        elif second_logo_added:
            text_start_x = x + 2
            text_width = width - second_logo_width - 4
        else:
            text_start_x = x + 2
            text_width = width - 4

        pdf.set_text_color(255, 255, 255)
        
        # Get header lines from settings or use defaults
        header_line1 = person.get('header_line1', 'T.C.')
        header_line2 = person.get('header_line2', 'KONYA VALİLİĞİ')
        header_line3 = person.get('header_line3', person.get('school_name', 'KONYA LİSESİ'))
        
        # 3 satır için toplam yükseklik hesaplama - satır arası boşluk genişletildi
        line_height = 3.2  # 2.5'ten 3.2'ye artırıldı (satır arası boşluk genişletildi)
        total_text_height = 3 * line_height  # 3 satır
        
        # Başlangıç Y pozisyonunu hesapla (header alanında dikey ortalanmış)
        text_start_y = y + (header_height - total_text_height) / 2
        
        # Line 1 - T.C. (en üst) - dikey ortalanmış
        pdf.set_font(self.default_font, 'B', 6)
        pdf.set_xy(text_start_x, text_start_y)
        safe_line1 = self._convert_turkish_chars(str(header_line1)[:35])
        pdf.cell(text_width, line_height, safe_line1, 0, 0, 'C')
        
        # Line 2 - Valilik/Müdürlük - dikey ortalanmış
        pdf.set_font(self.default_font, 'B', 6)
        pdf.set_xy(text_start_x, text_start_y + line_height)
        safe_line2 = self._convert_turkish_chars(str(header_line2)[:35])
        pdf.cell(text_width, line_height, safe_line2, 0, 0, 'C')
        
        # Line 3 - Okul adı - dikey ortalanmış
        pdf.set_font(self.default_font, 'B', 6)
        pdf.set_xy(text_start_x, text_start_y + (2 * line_height))
        safe_line3 = self._convert_turkish_chars(str(header_line3)[:35])
        pdf.cell(text_width, line_height, safe_line3, 0, 0, 'C')

        # 4. Satır - Kart başlığı (renkli alan dışında) - immediately after header
        header_line4 = person.get('header_line4', 'Öğrenci Kimlik Kartı')
        pdf.set_text_color(0, 0, 0)  # Siyah metin
        pdf.set_font(self.default_font, 'B', 6.5)
        pdf.set_xy(x + 2, y + header_height + 0.5)  # Reduced gap
        safe_line4 = self._convert_turkish_chars(str(header_line4)[:35])
        pdf.cell(width - 4, 3, safe_line4, 0, 0, 'C')
        
        # İçerik başlangıç pozisyonunu yukarı çek - reduced spacing
        content_start_y = y + header_height + 4  # Reduced from 8 to 4

        # Photo area - thin border, positioned higher
        photo_width = 16
        photo_height = 20
        photo_x = x + 3

        # QR kod kontrolü - eğer QR kod varsa fotoğrafı ortalı konuma al
        qr_enabled = person.get('qr_enabled', False)
        qr_position = person.get('qr_position', 'bottom_right') if qr_enabled else None
        
        # Position photo in card content area - renkli header ile footer arasında tam ortalı
        footer_height = 5  # Footer yüksekliği
        available_content_height = height - header_height - footer_height  # Header + footer arası alan
        
        # Fotoğrafı header ile footer arasında tam ortalı pozisyona yerleştir
        photo_y = y + header_height + (available_content_height - photo_height) / 2

        # Thin modern border
        pdf.set_line_width(0.2)  # İnce çerçeve
        pdf.set_draw_color(100, 100, 100)  # Koyu renk
        pdf.rect(photo_x - 1, photo_y - 1, photo_width + 2, photo_height + 2)

        # Add photo or placeholder with high quality
        if photos_dir and person.get('photo_filename'):
            photo_path = photos_dir / person['photo_filename']
            if photo_path.exists():
                try:
                    self._add_high_quality_photo_to_pdf(pdf, photo_path, photo_x, photo_y, photo_width, photo_height)
                except Exception as e:
                    self.logger.warning(f"Could not add photo to ID card: {e}")
                    self._draw_modern_photo_placeholder(pdf, photo_x, photo_y, photo_width, photo_height)
            else:
                self._draw_modern_photo_placeholder(pdf, photo_x, photo_y, photo_width, photo_height)
        else:
            self._draw_modern_photo_placeholder(pdf, photo_x, photo_y, photo_width, photo_height)

        # Information area - properly spaced
        info_x = x + photo_width + 8
        info_width = width - photo_width - 11

        pdf.set_text_color(0, 0, 0)
        line_height = 3.8  # 6 satır için azaltılmış satır yüksekliği
        current_y = content_start_y

        # Kullanıcının seçtiği sütunları kullan
        selected_columns = person.get('selected_columns', [])
        column_data = person.get('column_data', {})

        if selected_columns and column_data:
            # Kullanılabilir toplam genişlik
            total_info_width = info_width - 1  # 1mm margin (azaltıldı)
            
            # Etiket genişliği: toplam genişliğin %45'i, maksimum 25mm (genişletildi)
            label_width = min(total_info_width * 0.45, 25)
            # Değer genişliği: kalan alan
            value_width = total_info_width - label_width - 0.5  # 0.5mm ara boşluk (azaltıldı)
            
            # 6 punto font için gerçek karakter genişlikleri (mm cinsinden)
            char_width_6pt_bold = 0.9  # Bold etiketler için (azaltıldı)
            char_width_6pt_normal = 0.8  # Normal değerler için (azaltıldı)
            
            # Güvenli maksimum karakter sayıları (azaltılmış padding)
            max_label_chars = max(1, int((label_width - 1.5) / char_width_6pt_bold))  # 1.5mm padding (azaltıldı)
            max_value_chars = max(1, int((value_width - 1) / char_width_6pt_normal))  # 1mm padding (azaltıldı)
            
            valid_data = []
            for column in selected_columns:
                value = column_data.get(column, '')
                if value and str(value).strip():  # Boş değilse
                    valid_data.append((column, value))

            # 6 satır için alan hesaplaması
            max_rows = 6  # Tam 6 satır
            available_height = photo_height + 10  # Daha geniş alan

            # Kullanıcının seçtiği sütunları sırasıyla göster - 6 satıra kadar
            for i, (column, value) in enumerate(valid_data):
                if i >= max_rows:
                    break  # 6 satır limitine ulaşıldı

                # Alan kontrolü - 6 satır sığacak şekilde hesaplanmış
                if current_y + line_height > content_start_y + available_height:
                    break  # Alan doldu

                # Etiket çerçeveli kutu
                pdf.set_xy(info_x, current_y)
                pdf.set_font(self.default_font, 'B', 6)
                pdf.set_text_color(60, 60, 60)

                # Etiket çerçevesi
                pdf.set_line_width(0.2)
                pdf.set_draw_color(150, 150, 150)
                pdf.rect(info_x, current_y, label_width, line_height)

                # Etiket metni - otomatik boyutlandırma ile
                safe_label = self._convert_turkish_chars(str(column))
                
                # Otomatik font boyutlandırma - etiket için
                font_size = 6
                while font_size > 4:  # Minimum 4pt
                    pdf.set_font(self.default_font, 'B', font_size)
                    test_width = pdf.get_string_width(safe_label + ":")
                    if test_width <= (label_width - 1):  # 1mm padding
                        break
                    font_size -= 0.5
                
                # Eğer hala sığmıyorsa kırp
                if pdf.get_string_width(safe_label + ":") > (label_width - 1):
                    while pdf.get_string_width(safe_label + ":") > (label_width - 1) and len(safe_label) > 3:
                        safe_label = safe_label[:-1]
                
                # Etiket metnini yazdır - azaltılmış padding ile
                pdf.set_xy(info_x + 0.5, current_y + 0.3)  # Padding azaltıldı
                pdf.cell(label_width - 1, line_height - 0.6, safe_label + ":", 0, 0, 'L')

                # Değer çerçeveli kutu
                value_x = info_x + label_width + 0.5  # Ara boşluk azaltıldı

                # Değer çerçevesi
                pdf.rect(value_x, current_y, value_width, line_height)

                # Değer metni - otomatik boyutlandırma ile
                pdf.set_font(self.default_font, '', 6)
                pdf.set_text_color(0, 0, 0)
                
                safe_value = self._convert_turkish_chars(str(value))
                
                # Otomatik font boyutlandırma - değer için
                font_size = 6
                while font_size > 4:  # Minimum 4pt
                    pdf.set_font(self.default_font, '', font_size)
                    test_width = pdf.get_string_width(safe_value)
                    if test_width <= (value_width - 0.8):  # 0.8mm padding
                        break
                    font_size -= 0.5
                
                # Eğer hala sığmıyorsa kırp
                if pdf.get_string_width(safe_value) > (value_width - 0.8):
                    while pdf.get_string_width(safe_value) > (value_width - 0.8) and len(safe_value) > 1:
                        safe_value = safe_value[:-1]
                
                # Değer metnini yazdır - azaltılmış padding ile
                pdf.set_xy(value_x + 0.4, current_y + 0.3)  # Padding azaltıldı
                pdf.cell(value_width - 0.8, line_height - 0.6, safe_value, 0, 0, 'L')

                current_y += line_height + 1
        else:
            # Fallback: Eski sistem (geriye uyumluluk için)
            extracted_data = self._extract_person_data(person)

            # T.C. Kimlik No
            if extracted_data['tc_no']:
                pdf.set_xy(info_x, current_y)
                pdf.set_font(self.default_font, 'B', 5)
                pdf.cell(15, line_height, "T.C. Kimlik:", 0, 0, 'L')
                pdf.set_font(self.default_font, '', 5)
                pdf.cell(info_width - 15, line_height, extracted_data['tc_no'][:11], 0, 1, 'L')
                current_y += line_height + 0.5

            # Okul/Öğrenci No
            if extracted_data['student_no']:
                pdf.set_xy(info_x, current_y)
                pdf.set_font(self.default_font, 'B', 5)
                label = "Okul No:" if template_type == 'student' else "Sicil No:"
                pdf.cell(15, line_height, label, 0, 0, 'L')
                pdf.set_font(self.default_font, '', 5)
                pdf.cell(info_width - 15, line_height, extracted_data['student_no'][:15], 0, 1, 'L')
                current_y += line_height + 0.5

            # Sınıf/Branş
            if extracted_data['class_info']:
                pdf.set_xy(info_x, current_y)
                pdf.set_font(self.default_font, 'B', 5)
                label = "Sınıfı:" if template_type == 'student' else "Branşı:"
                pdf.cell(15, line_height, label, 0, 0, 'L')
                pdf.set_font(self.default_font, '', 5)
                # Convert Turkish characters for font compatibility
                safe_class_info = self._convert_turkish_chars(str(extracted_data['class_info'][:15]))
                pdf.cell(info_width - 15, line_height, safe_class_info, 0, 1, 'L')
                current_y += line_height + 0.5

            # Adı
            if extracted_data['first_name']:
                pdf.set_xy(info_x, current_y)
                pdf.set_font(self.default_font, 'B', 5)
                pdf.cell(15, line_height, "Adı:", 0, 0, 'L')
                pdf.set_font(self.default_font, '', 5)
                # Convert Turkish characters for font compatibility
                safe_first_name = self._convert_turkish_chars(str(extracted_data['first_name'][:20]))
                pdf.cell(info_width - 15, line_height, safe_first_name, 0, 1, 'L')
                current_y += line_height + 0.5

            # Soyadı
            if extracted_data['last_name']:
                pdf.set_xy(info_x, current_y)
                pdf.set_font(self.default_font, 'B', 5)
                pdf.cell(15, line_height, "Soyadı:", 0, 0, 'L')
                pdf.set_font(self.default_font, '', 5)
                # Convert Turkish characters for font compatibility
                safe_last_name = self._convert_turkish_chars(str(extracted_data['last_name'][:20]))
                pdf.cell(info_width - 15, line_height, safe_last_name, 0, 1, 'L')

        # QR Code - Add before footer if enabled
        if qr_enabled:
            qr_position = person.get('qr_position', 'bottom_right')
            qr_size = 12  # QR code size increased to 12mm
            
            # Calculate QR code position - just above footer
            footer_height = 5
            if qr_position == 'bottom_right':
                qr_x = x + width - qr_size - 2
                qr_y = y + height - footer_height - qr_size - 1  # 1mm gap from footer
            elif qr_position == 'bottom_left':
                qr_x = x + 2
                qr_y = y + height - footer_height - qr_size - 1  # 1mm gap from footer
            else:  # Default to bottom_right
                qr_x = x + width - qr_size - 2
                qr_y = y + height - footer_height - qr_size - 1
                
            # Generate QR code content
            qr_data_type = person.get('qr_data_type', 'custom')
            if qr_data_type == 'student':
                # Create student info QR data using actual column data
                qr_content = ""
                column_data = person.get('column_data', {})
                selected_columns = person.get('selected_columns', [])
                
                # Add school information first
                qr_content += f"OKUL: {person.get('school_name', 'N/A')}\n"
                
                # Add all selected column data
                for column in selected_columns:
                    if column in column_data and column_data[column]:
                        value = str(column_data[column]).strip()
                        if value and value != 'nan':
                            qr_content += f"{column.upper()}: {value}\n"
                
                # Add education year if available
                header_line5 = person.get('header_line5', '2025-2026 EĞİTİM-ÖĞRETİM YILI')
                if header_line5:
                    qr_content += f"EĞİTİM YILI: {header_line5}"
                
                # Remove trailing newline
                qr_content = qr_content.rstrip('\n')
                
                # If no data found, use fallback
                if not qr_content or qr_content == f"OKUL: {person.get('school_name', 'N/A')}":
                    qr_content = f"OKUL: {person.get('school_name', 'N/A')}\nVESİKOLAY PRO"
            else:
                # Use custom text
                qr_content = person.get('qr_custom_text', 'VesiKolay Pro')
            
            try:
                self._add_qr_code_to_pdf(pdf, qr_content, qr_x, qr_y, qr_size)
            except Exception as e:
                self.logger.warning(f"Could not add QR code: {e}")

        # Renkli alt şerit with gradient support
        footer_height = 5  # Yükseklik artırıldı
        footer_color = person.get('footer_color', '#2D55A5')
        footer_gradient = person.get('footer_gradient', False)
        footer_gradient_color2 = person.get('footer_gradient_color2', '#1B3F73')
        
        if footer_gradient:
            self._draw_gradient_rectangle(pdf, x, y + height - footer_height, width, footer_height,
                                         footer_color, footer_gradient_color2, 'horizontal')
        else:
            # Solid color footer
            footer_rgb = self._hex_to_rgb(footer_color)
            pdf.set_fill_color(footer_rgb[0], footer_rgb[1], footer_rgb[2])
            pdf.rect(x, y + height - footer_height, width, footer_height, 'F')

        # Education year - alt şeritte (5. satır)
        header_line5 = person.get('header_line5', '2025-2026 EĞİTİM-ÖĞRETİM YILI')
        pdf.set_xy(x + 2, y + height - footer_height + 1)
        pdf.set_font(self.default_font, 'B', 5)
        pdf.set_text_color(255, 255, 255)  # Beyaz metin
        safe_line5 = self._convert_turkish_chars(str(header_line5)[:50])
        pdf.cell(width - 4, 3, safe_line5, 0, 0, 'C')

    def _extract_person_data(self, person: Dict) -> Dict[str, str]:
        """Extract person data using smart field matching from Excel columns"""
        extracted = {
            'tc_no': '',
            'student_no': '',
            'class_info': '',
            'first_name': '',
            'last_name': ''
        }

        # Debug: Log mevcut person data
        self.logger.debug(f"Extracting data from person: {person.keys()}")

        # Önce doğrudan person dict'inden al
        extracted['first_name'] = str(person.get('first_name', '')).strip()
        extracted['last_name'] = str(person.get('last_name', '')).strip()
        extracted['class_info'] = str(person.get('class_name', '')).strip()
        extracted['student_no'] = str(person.get('student_no', '')).strip()
        extracted['tc_no'] = str(person.get('tc_kimlik', '')).strip()

        # Branch bilgisini de kontrol et (öğretmenler için)
        if not extracted['class_info']:
            extracted['class_info'] = str(person.get('branch', '')).strip()

        # Eğer boşsa, _original_data'dan al veya person'ın kendisinden
        original_data = person.get('_original_data', person)

        # İlk olarak doğrudan person dict'inden tüm alanları kontrol et
        for key, value in person.items():
            if value and str(value).strip() and str(value).strip() != 'nan':
                value_str = str(value).strip()

                # Ad için
                if not extracted['first_name'] and any(pattern in key.lower() for pattern in ['ad', 'name', 'first', 'isim']) and 'soyad' not in key.lower():
                    extracted['first_name'] = value_str

                # Soyad için
                if not extracted['last_name'] and any(pattern in key.lower() for pattern in ['soyad', 'last', 'surname']):
                    extracted['last_name'] = value_str

                # Sınıf/Branş için
                if not extracted['class_info'] and any(pattern in key.lower() for pattern in ['sınıf', 'sinif', 'class', 'branş', 'brans', 'branch']):
                    extracted['class_info'] = value_str

                # Numara için
                if not extracted['student_no'] and any(pattern in key.lower() for pattern in ['no', 'numara', 'student_no', 'sicil']):
                    extracted['student_no'] = value_str

                # TC için
                if not extracted['tc_no'] and any(pattern in key.lower() for pattern in ['tc', 'kimlik']) and len(value_str) >= 10:
                    extracted['tc_no'] = value_str

        if not extracted['first_name']:
            first_name_fields = ['ad', 'adi', 'first_name', 'name', 'isim', 'adı', 'Ad', 'ADI', 'ISIM']
            for field in first_name_fields:
                if field in original_data and original_data[field]:
                    value = str(original_data[field]).strip()
                    if value and value != 'nan':
                        extracted['first_name'] = value
                        break

            # Sütun adına göre arama
            if not extracted['first_name']:
                for col_name, col_value in original_data.items():
                    if col_value and 'ad' in col_name.lower() and 'soyad' not in col_name.lower():
                        value = str(col_value).strip()
                        if value and value != 'nan':
                            extracted['first_name'] = value
                            break

        if not extracted['last_name']:
            last_name_fields = ['soyad', 'soyadi', 'last_name', 'surname', 'soyadı', 'Soyad', 'SOYAD']
            for field in last_name_fields:
                if field in original_data and original_data[field]:
                    value = str(original_data[field]).strip()
                    if value and value != 'nan':
                        extracted['last_name'] = value
                        break

            # Sütun adına göre arama
            if not extracted['last_name']:
                for col_name, col_value in original_data.items():
                    if col_value and 'soyad' in col_name.lower():
                        value = str(col_value).strip()
                        if value and value != 'nan':
                            extracted['last_name'] = value
                            break

        if not extracted['class_info']:
            class_fields = ['sınıf', 'sinif', 'class', 'class_name', 'branş', 'brans', 'branch', 'Sınıf', 'SINIF']
            for field in class_fields:
                if field in original_data and original_data[field]:
                    value = str(original_data[field]).strip()
                    if value and value != 'nan':
                        extracted['class_info'] = value
                        break

            # Sütun adına göre arama
            if not extracted['class_info']:
                for col_name, col_value in original_data.items():
                    if col_value and ('sınıf' in col_name.lower() or 'sinif' in col_name.lower() or 'class' in col_name.lower()):
                        value = str(col_value).strip()
                        if value and value != 'nan':
                            extracted['class_info'] = value
                            break

        if not extracted['student_no']:
            student_fields = ['numara', 'no', 'student_no', 'öğrenci_no', 'ogrenci_no', 'okul_no', 'sicil_no', 'sicil', 'Numara', 'NO']
            for field in student_fields:
                if field in original_data and original_data[field]:
                    value = str(original_data[field]).strip()
                    if value and value != 'nan':
                        extracted['student_no'] = value
                        break

            # Sütun adına göre arama
            if not extracted['student_no']:
                for col_name, col_value in original_data.items():
                    if col_value and ('numara' in col_name.lower() or 'no' in col_name.lower()):
                        value = str(col_value).strip()
                        if value and value != 'nan':
                            extracted['student_no'] = value
                            break

        if not extracted['tc_no']:
            tc_fields = ['tc_kimlik', 'tc_no', 'tc', 'kimlik', 'kimlik_no', 'tcno', 'tc kimlik', 'TC', 'KIMLIK']
            for field in tc_fields:
                if field in original_data and original_data[field]:
                    value = str(original_data[field]).strip()
                    if value and value != 'nan' and len(value) >= 10:
                        extracted['tc_no'] = value
                        break

            # Sütun adına göre arama
            if not extracted['tc_no']:
                for col_name, col_value in original_data.items():
                    if col_value and ('tc' in col_name.lower() or 'kimlik' in col_name.lower()):
                        value = str(col_value).strip()
                        if value and value != 'nan' and len(value) >= 10:
                            extracted['tc_no'] = value
                            break

        return extracted
    
    def _register_fonts(self, pdf: FPDF):
        """Register DejaVu fonts (with bold/italic) or fallback to Arial"""
        try:
            from pathlib import Path
            font_dir = Path(__file__).parent / "fonts"

            regular = font_dir / "DejaVuSans.ttf"
            bold = font_dir / "DejaVuSans-Bold.ttf"
            italic = font_dir / "DejaVuSans-Oblique.ttf"

            if regular.exists():
                pdf.add_font("DejaVu", '', str(regular), uni=True)
                self.default_font = "DejaVu"
                self.logger.info("Using DejaVu font for Turkish character support")

                if bold.exists():
                    pdf.add_font("DejaVu", 'B', str(bold), uni=True)
                if italic.exists():
                    pdf.add_font("DejaVu", 'I', str(italic), uni=True)
            else:
                self.default_font = "Arial"
                self.logger.warning("DejaVu fonts not found, using Arial as fallback")

        except Exception as e:
            self.default_font = "Arial"
            self.logger.error(f"Font registration failed, using Arial: {e}")



    def _draw_photo_placeholder(self, pdf: FPDF, x: float, y: float, width: float, height: float = None):
        """Draw photo placeholder when no photo is available"""
        if height is None:
            height = width

        # Light gray background
        pdf.set_fill_color(240, 240, 240)
        pdf.rect(x, y, width, height, 'F')

        # Placeholder text
        pdf.set_xy(x, y + height/2 - 2)
        pdf.set_font(self.default_font, 'I', 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(width, 4, 'Foto', 0, 0, 'C')

    def _add_high_quality_photo_to_pdf(self, pdf: FPDF, photo_path: Path, x: float, y: float, 
                         width: float, height: float) -> None:
        """Add high quality photo to PDF at specified position with proper aspect ratio"""
        try:
            # Open image
            with Image.open(photo_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Calculate proper dimensions to maintain aspect ratio
                img_width, img_height = img.size
                img_aspect = img_width / img_height
                target_aspect = width / height

                # Calculate new dimensions that fit within the target area
                if img_aspect > target_aspect:
                    # Image is wider than target, fit by width
                    new_width = width
                    new_height = width / img_aspect
                    # Center vertically
                    y_offset = (height - new_height) / 2
                    final_x = x
                    final_y = y + y_offset
                else:
                    # Image is taller than target, fit by height
                    new_height = height
                    new_width = height * img_aspect
                    # Center horizontally
                    x_offset = (width - new_width) / 2
                    final_x = x + x_offset
                    final_y = y

                # Use much higher resolution for crisp images
                scale_factor = 12  # Very high scale for ID cards
                target_pixel_width = int(new_width * scale_factor)
                target_pixel_height = int(new_height * scale_factor)

                # Ensure minimum resolution
                if target_pixel_width < 300:
                    target_pixel_width = 300
                if target_pixel_height < 400:
                    target_pixel_height = 400

                img_resized = img.resize((target_pixel_width, target_pixel_height), Image.Resampling.LANCZOS)

                # Apply sharpening for better quality
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Sharpness(img_resized)
                img_resized = enhancer.enhance(1.3)

                # Save to temporary bytes with maximum quality
                img_bytes = io.BytesIO()
                img_resized.save(img_bytes, format='JPEG', quality=100, optimize=False, dpi=(600, 600))
                img_bytes.seek(0)

                # Add to PDF with calculated dimensions
                pdf.image(img_bytes, final_x, final_y, new_width, new_height)

        except Exception as e:
            self.logger.error(f"Error adding high quality photo to PDF: {e}")
            # Fallback to placeholder
            self._draw_modern_photo_placeholder(pdf, x, y, width, height)

    def _add_logo_with_transparency(self, pdf: FPDF, logo_path: Path, x: float, y: float, 
                                   width: float, height: float, header_color: str = '#2D55A5', 
                                   header_gradient: bool = False, header_color2: str = '#1B3F73',
                                   logo_position: str = 'left') -> None:
        """Add logo to PDF with proper PNG transparency support and gradient background"""
        try:
            # Open image
            with Image.open(logo_path) as img:
                # PNG transparency desteği - gradient arka plana göre renk hesapla
                if img.mode in ('RGBA', 'LA'):
                    # Gradient varsa logo pozisyonuna göre arka plan rengini hesapla
                    if header_gradient:
                        if logo_position == 'left':
                            # Sol logo: %100 başlangıç rengi
                            background_color = header_color
                        else:  # right
                            # Sağ logo: %100 bitiş rengi
                            background_color = header_color2
                    else:
                        background_color = header_color
                    
                    # Arka plan rengini RGB'ye çevir
                    bg_rgb = self._hex_to_rgb(background_color)
                    
                    if img.mode == 'RGBA':
                        # RGBA için gelişmiş alpha composite - kenar yumuşatma ile
                        # Yüksek çözünürlükte işle
                        high_res_factor = 4
                        high_res_size = (img.size[0] * high_res_factor, img.size[1] * high_res_factor)
                        
                        # Resmi büyüt
                        img_high_res = img.resize(high_res_size, Image.Resampling.LANCZOS)
                        
                        # Yüksek çözünürlükte arka plan oluştur
                        rgba_background = Image.new('RGBA', high_res_size, bg_rgb + (255,))
                        
                        # Alpha composite ile birleştir
                        composite = Image.alpha_composite(rgba_background, img_high_res)
                        
                        # Orijinal boyuta küçült - antialiasing ile
                        img = composite.resize(img.size, Image.Resampling.LANCZOS)
                        
                        # RGB'ye çevir
                        img = img.convert('RGB')
                    else:  # LA mode
                        # LA modunda alpha kanalını mask olarak kullan - yumuşatma ile
                        background = Image.new('RGB', img.size, bg_rgb)
                        # Mask'ı yumuşat
                        alpha_mask = img.split()[-1]
                        # Gaussian blur uygula
                        from PIL import ImageFilter
                        alpha_mask = alpha_mask.filter(ImageFilter.GaussianBlur(radius=0.5))
                        background.paste(img, mask=alpha_mask)
                        img = background
                        
                elif img.mode == 'P' and 'transparency' in img.info:
                    # Palette mode'da transparency varsa - gelişmiş işleme
                    if header_gradient:
                        if logo_position == 'left':
                            # Sol logo: %100 başlangıç rengi  
                            background_color = header_color
                        else:
                            # Sağ logo: %100 bitiş rengi
                            background_color = header_color2
                    else:
                        background_color = header_color
                    
                    bg_rgb = self._hex_to_rgb(background_color)
                    
                    # Palette mode'u RGBA'ya çevir - transparency korunarak
                    img = img.convert('RGBA')
                    
                    # Yüksek kaliteli arka plan karışımı
                    high_res_factor = 3
                    high_res_size = (img.size[0] * high_res_factor, img.size[1] * high_res_factor)
                    
                    img_high_res = img.resize(high_res_size, Image.Resampling.LANCZOS)
                    background = Image.new('RGBA', high_res_size, bg_rgb + (255,))
                    composite = Image.alpha_composite(background, img_high_res)
                    img = composite.resize(img.size, Image.Resampling.LANCZOS)
                    img = img.convert('RGB')
                    
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Calculate proper dimensions to maintain aspect ratio
                img_width, img_height = img.size
                img_aspect = img_width / img_height
                target_aspect = width / height

                # Calculate new dimensions that fit within the target area
                if img_aspect > target_aspect:
                    # Image is wider than target, fit by width
                    new_width = width
                    new_height = width / img_aspect
                    # Center vertically
                    y_offset = (height - new_height) / 2
                    final_x = x
                    final_y = y + y_offset
                else:
                    # Image is taller than target, fit by height
                    new_height = height
                    new_width = height * img_aspect
                    # Center horizontally
                    x_offset = (width - new_width) / 2
                    final_x = x + x_offset
                    final_y = y

                # Resize image with much higher resolution for crisp logos
                scale_factor = 10  # Çok daha yüksek çözünürlük için artırıldı
                target_pixel_width = int(new_width * scale_factor)
                target_pixel_height = int(new_height * scale_factor)

                # Minimum çözünürlük garantisi
                if target_pixel_width < 200:
                    target_pixel_width = 200
                if target_pixel_height < 200:
                    target_pixel_height = 200

                img_resized = img.resize((target_pixel_width, target_pixel_height), Image.Resampling.LANCZOS)

                # Apply sharpening for even better quality
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Sharpness(img_resized)
                img_resized = enhancer.enhance(1.2)  # Keskinlik artırma

                # Save to temporary bytes with maximum quality
                img_bytes = io.BytesIO()
                img_resized.save(img_bytes, format='JPEG', quality=100, optimize=False, dpi=(600, 600))
                img_bytes.seek(0)

                # Add to PDF with calculated dimensions
                pdf.image(img_bytes, final_x, final_y, new_width, new_height)

        except Exception as e:
            self.logger.error(f"Error adding logo with transparency to PDF: {e}")
            raise

    def _draw_gradient_rectangle(self, pdf: FPDF, x: float, y: float, width: float, height: float,
                                color1: str, color2: str, direction: str = 'horizontal'):
        """Draw a gradient rectangle using thin strips"""
        try:
            rgb1 = self._hex_to_rgb(color1)
            rgb2 = self._hex_to_rgb(color2)
            
            # Number of strips for smooth gradient
            strips = max(20, int(width if direction == 'horizontal' else height))
            
            if direction == 'horizontal':
                strip_width = width / strips
                for i in range(strips):
                    # Calculate intermediate color
                    ratio = i / (strips - 1) if strips > 1 else 0
                    r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * ratio)
                    g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * ratio)
                    b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * ratio)
                    
                    pdf.set_fill_color(r, g, b)
                    strip_x = x + i * strip_width
                    pdf.rect(strip_x, y, strip_width + 0.1, height, 'F')  # +0.1 to avoid gaps
            else:  # vertical
                strip_height = height / strips
                for i in range(strips):
                    # Calculate intermediate color
                    ratio = i / (strips - 1) if strips > 1 else 0
                    r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * ratio)
                    g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * ratio)
                    b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * ratio)
                    
                    pdf.set_fill_color(r, g, b)
                    strip_y = y + i * strip_height
                    pdf.rect(x, strip_y, width, strip_height + 0.1, 'F')  # +0.1 to avoid gaps
                    
        except Exception as e:
            self.logger.warning(f"Gradient drawing failed, falling back to solid color: {e}")
            # Fallback to solid color
            rgb1 = self._hex_to_rgb(color1)
            pdf.set_fill_color(rgb1[0], rgb1[1], rgb1[2])
            pdf.rect(x, y, width, height, 'F')

    def _convert_turkish_chars(self, text: str) -> str:
        """Convert Turkish characters to safe characters for FPDF compatibility"""
        if not text:
            return ""
        
        # If using DejaVu font, return text as is since it supports Turkish characters
        if self.default_font == 'DejaVu':
            return str(text)
        
        # For Arial fallback, convert Turkish characters
        replacements = {
            'ç': 'c', 'Ç': 'C',
            'ğ': 'g', 'Ğ': 'G', 
            'ı': 'i', 'I': 'I',
            'İ': 'I',
            'ö': 'o', 'Ö': 'O',
            'ş': 's', 'Ş': 'S',
            'ü': 'u', 'Ü': 'U'
        }
        
        result = str(text)
        for turkish_char, replacement in replacements.items():
            result = result.replace(turkish_char, replacement)
        
        return result

    def _draw_modern_photo_placeholder(self, pdf: FPDF, x: float, y: float, width: float, height: float):
        """Draw modern styled photo placeholder"""
        # Gradient-like background
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(x, y, width, height, 'F')

        # Icon-like placeholder
        center_x = x + width/2
        center_y = y + height/2

        # Simple camera icon representation
        pdf.set_draw_color(180, 180, 180)
        pdf.set_line_width(0.5)

        # Camera body
        icon_size = min(width, height) * 0.3
        pdf.rect(center_x - icon_size/2, center_y - icon_size/3, icon_size, icon_size * 0.6)

        # Camera lens (circle approximation with small rectangles)
        lens_size = icon_size * 0.4
        # Circle approximation using small lines
        import math
        radius = lens_size/2
        steps = 16
        for i in range(steps):
            angle1 = 2 * math.pi * i / steps
            angle2 = 2 * math.pi * (i + 1) / steps
            x1 = center_x + radius * math.cos(angle1)
            y1 = center_y + radius * math.sin(angle1)
            x2 = center_x + radius * math.cos(angle2) 
            y2 = center_y + radius * math.sin(angle2)
            pdf.line(x1, y1, x2, y2)

        # Text below icon
        pdf.set_xy(x, y + height * 0.75)
        pdf.set_font(self.default_font, 'I', 6)
        pdf.set_text_color(160, 160, 160)
        pdf.cell(width, 3, 'FOTOGRAF', 0, 0, 'C')

    def _add_qr_code_to_pdf(self, pdf: FPDF, content: str, x: float, y: float, size: float):
        """Add QR code to PDF using simple pattern generation"""
        try:
            # Try to use qrcode library if available
            try:
                import qrcode
                from PIL import Image as PILImage
                import io
                
                # Generate QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(content)
                qr.make(fit=True)
                
                # Create QR code image
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                # Convert to bytes
                img_buffer = io.BytesIO()
                qr_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Add to PDF
                pdf.image(img_buffer, x, y, size, size)
                
            except ImportError:
                # Fallback: Simple pattern placeholder
                self._draw_qr_placeholder(pdf, x, y, size)
                
        except Exception as e:
            self.logger.warning(f"QR code generation failed: {e}")
            # Draw placeholder
            self._draw_qr_placeholder(pdf, x, y, size)

    def _draw_qr_placeholder(self, pdf: FPDF, x: float, y: float, size: float):
        """Draw a simple QR code placeholder pattern"""
        # QR code border
        pdf.set_line_width(0.2)
        pdf.set_draw_color(0, 0, 0)
        pdf.rect(x, y, size, size)
        
        # Simple pattern to simulate QR code
        grid_size = 8  # 8x8 grid
        cell_size = size / grid_size
        
        pdf.set_fill_color(0, 0, 0)
        
        # Create a simple pattern
        pattern = [
            [1,1,1,0,0,1,1,1],
            [1,0,1,0,0,1,0,1],
            [1,0,1,1,1,1,0,1],
            [0,0,0,0,0,0,0,0],
            [0,1,0,1,0,1,0,1],
            [1,0,1,0,1,0,1,0],
            [0,1,0,1,0,1,0,1],
            [1,1,1,0,0,1,1,1]
        ]
        
        for row in range(grid_size):
            for col in range(grid_size):
                if pattern[row][col]:
                    cell_x = x + col * cell_size
                    cell_y = y + row * cell_size
                    pdf.rect(cell_x, cell_y, cell_size, cell_size, 'F')
        
        # QR label
        pdf.set_xy(x, y + size + 0.5)
        pdf.set_font(self.default_font, '', 4)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(size, 2, 'QR', 0, 0, 'C')