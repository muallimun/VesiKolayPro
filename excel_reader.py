"""
VesiKolay Pro - Excel File Reader
Handles reading and parsing Excel files containing student and teacher data
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re

class ExcelReader:
    """Handles Excel file reading and data extraction"""

    def __init__(self):
        """Initialize Excel reader"""
        self.logger = logging.getLogger(__name__)

    def read_excel_flexible(self, file_path: Path, data_type: str = 'students') -> Tuple[List[Dict], List[str], List[str]]:
        """
        Read Excel file flexibly without requiring specific columns
        Returns: (data_list, errors, available_columns)
        """
        errors = []
        data_list = []
        available_columns = []

        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            self.logger.info(f"Read Excel file with {len(df)} rows and {len(df.columns)} columns")

            if df.empty:
                errors.append("Excel dosyası boş / Excel file is empty")
                return data_list, errors, available_columns

            # Get original column names for user selection
            original_columns = df.columns.tolist()
            available_columns = [col for col in original_columns if col.strip()]

            # Normalize column names for internal processing
            df.columns = df.columns.str.strip()

            # Create flexible column mapping
            flexible_mappings = self._create_flexible_mappings()

            # Map available columns to standard names
            mapped_columns = {}
            column_usage = {}

            for col in df.columns:
                col_lower = col.lower().strip()
                for standard_name, patterns in flexible_mappings.items():
                    for pattern in patterns:
                        if re.search(pattern, col_lower):
                            mapped_columns[col] = standard_name
                            column_usage[standard_name] = col
                            break
                    if col in mapped_columns:
                        break

            # Rename mapped columns
            df_mapped = df.rename(columns=mapped_columns)

            # Process each row
            for index, row in df.iterrows():
                try:
                    # Create record with all available data
                    record = {}

                    # Map all columns that have data
                    for original_col in df.columns:
                        value = row[original_col]
                        if pd.notna(value) and str(value).strip():
                            # Use mapped name if available, otherwise use original
                            field_name = mapped_columns.get(original_col, original_col)
                            record[field_name] = str(value).strip()

                    # Add original column values for user selection
                    record['_original_data'] = {}
                    for col in original_columns:
                        if col in df.columns:
                            value = row[col]
                            if pd.notna(value):
                                record['_original_data'][col] = str(value).strip()

                    # Validate TC kimlik number if present
                    if 'tc_no' in record:
                        tc_validated = self._validate_tc_number(record['tc_no'])
                        if not tc_validated:
                            errors.append(f"Row {index + 2}: Invalid TC number format (must be 11 digits)")

                    # Only add if record has some data
                    if any(record.get(key) for key in record if key != '_original_data'):
                        data_list.append(record)

                except Exception as e:
                    errors.append(f"Row {index + 2}: Error processing data - {str(e)}")

            self.logger.info(f"Successfully processed {len(data_list)} records")

        except Exception as e:
            error_msg = f"Error reading Excel file: {str(e)}"
            self.logger.error(error_msg)
            errors.append(error_msg)

        return data_list, errors, available_columns

    def _create_flexible_mappings(self) -> Dict[str, List[str]]:
        """Create flexible column mappings for different naming conventions"""
        return {
            'first_name': [
                r'^ad$', r'^first.*name$', r'^ad[ıi]$', r'^isim$', r'^name$',
                r'.*ad.*', r'.*first.*', r'.*isim.*'
            ],
            'last_name': [
                r'^soyad$', r'^last.*name$', r'^surname$', r'^family.*name$',
                r'.*soyad.*', r'.*last.*', r'.*surname.*'
            ],
            'student_no': [
                r'^numara$', r'^no$', r'^student.*no$', r'^öğrenci.*no$',
                r'^number$', r'.*numara.*', r'.*student.*', r'.*no.*'
            ],
            'tc_no': [
                r'^tc$', r'^tc.*no$', r'^tc.*kimlik$', r'^kimlik.*no$',
                r'.*tc.*', r'.*kimlik.*', r'.*identity.*'
            ],
            'class_name': [
                r'^sınıf$', r'^sinif$', r'^class$', r'^sınıf.*adı$',
                r'.*sınıf.*', r'.*sinif.*', r'.*class.*'
            ],
            'branch': [
                r'^branş$', r'^brans$', r'^branch$', r'^dal$',
                r'.*branş.*', r'.*brans.*', r'.*branch.*'
            ],
            'school_name': [
                r'^okul$', r'^okul.*adı$', r'^school$', r'^school.*name$',
                r'.*okul.*', r'.*school.*'
            ],
            'department': [
                r'^bölüm$', r'^bolum$', r'^department$', r'^birim$',
                r'.*bölüm.*', r'.*bolum.*', r'.*department.*'
            ],
            'phone': [
                r'^telefon$', r'^tel$', r'^phone$', r'^gsm$',
                r'.*telefon.*', r'.*phone.*', r'.*tel.*'
            ],
            'email': [
                r'^email$', r'^e.*mail$', r'^eposta$', r'^mail$',
                r'.*email.*', r'.*mail.*', r'.*posta.*'
            ],
            'birth_date': [
                r'^doğum.*tarih$', r'^birth.*date$', r'^tarih$',
                r'.*doğum.*', r'.*birth.*', r'.*tarih.*'
            ],
            'academic_year': [
                r'^egitim.*yili$', r'^academic.*year$', r'^year$', r'^yil$', r'^dönem$', r'^donem$'
                r'.*egitim.*', r'.*academic.*', r'.*year.*', r'.*yil.*', r'.*donem.*'
            ]
        }

    def _validate_tc_number(self, tc_str: str) -> bool:
        """Validate Turkish TC identity number format"""
        try:
            tc_str = str(tc_str).strip()

            # Must be exactly 11 digits
            if len(tc_str) != 11 or not tc_str.isdigit():
                return False

            # First digit cannot be 0
            if tc_str[0] == '0':
                return False

            # TC number algorithm validation
            digits = [int(d) for d in tc_str]

            # Sum of odd positioned digits (1,3,5,7,9)
            odd_sum = sum(digits[i] for i in range(0, 9, 2))

            # Sum of even positioned digits (2,4,6,8)
            even_sum = sum(digits[i] for i in range(1, 8, 2))

            # 10th digit check
            tenth_digit = (odd_sum * 7 - even_sum) % 10
            if tenth_digit != digits[9]:
                return False

            # 11th digit check
            eleventh_digit = (sum(digits[:10])) % 10
            if eleventh_digit != digits[10]:
                return False

            return True

        except:
            return False

    def get_filename_from_data(self, record: Dict, column_name: str, 
                              pattern: str = 'selected_column') -> str:
        """
        Generate filename based on selected column and pattern
        """
        if column_name in record.get('_original_data', {}):
            # Use original column data
            base_name = record['_original_data'][column_name]
        elif column_name in record:
            # Use mapped data
            base_name = record[column_name]
        else:
            # Fallback to first available identifier
            base_name = self._get_fallback_identifier(record)

        # Apply pattern
        if pattern == 'selected_column':
            filename = str(base_name)
        elif pattern == 'with_class':
            class_info = record.get('class_name', record.get('sınıf', ''))
            if class_info:
                filename = f"{base_name}_{class_info}"
            else:
                filename = str(base_name)
        elif pattern == 'with_number':
            number = record.get('student_no', record.get('numara', ''))
            if number:
                filename = f"{number}_{base_name}"
            else:
                filename = str(base_name)
        elif pattern == 'full_info':
            parts = [str(base_name)]
            if 'class_name' in record:
                parts.append(record['class_name'])
            if 'student_no' in record:
                parts.insert(0, record['student_no'])
            filename = '_'.join(parts)
        else:
            filename = str(base_name)

        # Clean filename
        filename = self._clean_filename(filename)
        return filename + '.jpg'

    def _get_fallback_identifier(self, record: Dict) -> str:
        """Get fallback identifier when selected column is not available"""
        # Try different fields in order of preference
        fallback_fields = [
            'student_no', 'numara', 'tc_no', 'first_name', 'ad',
            'last_name', 'soyad', 'full_name'
        ]

        for field in fallback_fields:
            if field in record and record[field]:
                return record[field]

        # Use first available field from original data
        original_data = record.get('_original_data', {})
        for value in original_data.values():
            if value and str(value).strip():
                return str(value).strip()

        return 'unknown'

    def _clean_filename(self, filename: str) -> str:
        """Clean filename for filesystem compatibility"""
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Replace multiple spaces/underscores with single underscore
        filename = re.sub(r'[\s_]+', '_', filename)
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        # Ensure not empty
        if not filename:
            filename = 'unnamed'
        return filename

    def get_available_columns_for_naming(self, data_list: List[Dict]) -> List[str]:
        """Get list of columns that can be used for naming photos"""
        if not data_list:
            return []

        # Get all unique column names from original data
        all_columns = set()
        for record in data_list:
            original_data = record.get('_original_data', {})
            all_columns.update(original_data.keys())

        # Filter out empty columns
        useful_columns = []
        for col in sorted(all_columns):
            # Check if this column has data in most records
            non_empty_count = sum(
                1 for record in data_list 
                if record.get('_original_data', {}).get(col, '').strip()
            )
            if non_empty_count > 0:
                useful_columns.append(col)

        return useful_columns

    # Keep backward compatibility methods
    def read_students_excel(self, file_path: Path) -> Tuple[List[Dict], List[str]]:
        """Backward compatibility method for students"""
        data_list, errors, _ = self.read_excel_flexible(file_path, 'students')
        return data_list, errors

    def read_teachers_excel(self, file_path: Path) -> Tuple[List[Dict], List[str]]:
        """Backward compatibility method for teachers"""
        data_list, errors, _ = self.read_excel_flexible(file_path, 'teachers')
        return data_list, errors

    def validate_excel_file(self, file_path: Path, file_type: str = 'students') -> Tuple[bool, List[str]]:
        """Validate Excel file format"""
        errors = []

        try:
            if not file_path.exists():
                errors.append("File does not exist")
                return False, errors

            # Check file extension
            if file_path.suffix.lower() not in ['.xlsx', '.xls']:
                errors.append("File must be an Excel file (.xlsx or .xls)")
                return False, errors

            # Try to read the file
            df = pd.read_excel(file_path)

            if df.empty:
                errors.append("Excel file is empty")
                return False, errors

            self.logger.info(f"Excel file validation successful: {file_path}")
            return True, errors

        except Exception as e:
            error_msg = f"Error validating Excel file: {str(e)}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            return False, errors

    def get_file_info(self, file_path: Path) -> Dict:
        """Get basic information about Excel file"""
        try:
            df = pd.read_excel(file_path)
            return {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'file_size': file_path.stat().st_size
            }
        except Exception as e:
            self.logger.error(f"Error getting file info: {e}")
            return {'error': str(e)}