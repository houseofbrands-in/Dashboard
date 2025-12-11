"""
File Handling and CSV Processing Utilities
Handles CSV uploads, validation, and processing
"""
import pandas as pd
import numpy as np
from datetime import datetime
import io
import csv
from typing import Dict, List, Tuple, Optional, Any
import chardet
import warnings
warnings.filterwarnings('ignore')

class FileHandler:
    """
    Handles CSV file uploads, validation, and processing
    Replicates Excel VBA file handling logic
    """
    
    @staticmethod
    def detect_encoding(file_content: bytes) -> str:
        """Detect file encoding"""
        result = chardet.detect(file_content)
        return result.get('encoding', 'utf-8')
    
    @staticmethod
    def read_csv_with_encoding(file_content: bytes, filename: str) -> pd.DataFrame:
        """
        Read CSV with automatic encoding detection
        Handles various CSV formats like Excel exports
        """
        try:
            # Try UTF-8 first (most common)
            try:
                content_str = file_content.decode('utf-8-sig')  # Handle BOM
                df = pd.read_csv(io.StringIO(content_str))
                return df
            except:
                # Try other encodings
                encodings = ['latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
                for encoding in encodings:
                    try:
                        content_str = file_content.decode(encoding)
                        df = pd.read_csv(io.StringIO(content_str))
                        return df
                    except:
                        continue
                
                # If all fail, use detected encoding
                detected_encoding = FileHandler.detect_encoding(file_content)
                content_str = file_content.decode(detected_encoding, errors='ignore')
                df = pd.read_csv(io.StringIO(content_str))
                return df
                
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {str(e)}")
    
    @staticmethod
    def validate_sales_csv(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate sales CSV structure
        Returns (is_valid, error_messages)
        """
        errors = []
        
        if df.empty:
            errors.append("CSV file is empty")
            return False, errors
        
        # Check for required column patterns
        has_date = False
        has_style = False
        
        for col in df.columns:
            col_lower = str(col).lower()
            
            # Check for date column
            if any(pattern in col_lower for pattern in 
                  ['date', 'created', 'order', 'dispatch']):
                has_date = True
            
            # Check for style column
            if any(pattern in col_lower for pattern in 
                  ['style', 'product', 'code', 'id', 'article']):
                has_style = True
        
        if not has_date:
            errors.append("No date column found. Expected column containing 'date', 'created', or 'order'")
        
        if not has_style:
            errors.append("No style column found. Expected column containing 'style', 'product', 'code', or 'id'")
        
        # Check sample data
        if len(df) > 0:
            sample_row = df.iloc[0]
            
            # Check date format in sample
            date_cols = [col for col in df.columns if 'date' in str(col).lower()]
            if date_cols:
                date_col = date_cols[0]
                date_value = sample_row[date_col]
                try:
                    pd.to_datetime(date_value, errors='raise')
                except:
                    errors.append(f"Date column '{date_col}' has invalid format in first row: {date_value}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_returns_csv(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate returns CSV structure
        """
        errors = []
        
        if df.empty:
            errors.append("CSV file is empty")
            return False, errors
        
        # Check for required columns
        has_date = False
        has_style = False
        has_qty = False
        
        for col in df.columns:
            col_lower = str(col).lower()
            
            if any(pattern in col_lower for pattern in 
                  ['date', 'return', 'created', 'registered']):
                has_date = True
            
            if any(pattern in col_lower for pattern in 
                  ['style', 'product', 'code', 'id']):
                has_style = True
            
            if any(pattern in col_lower for pattern in 
                  ['qty', 'quantity', 'units']):
                has_qty = True
        
        if not has_date:
            errors.append("No date column found")
        
        if not has_style:
            errors.append("No style column found")
        
        if not has_qty:
            errors.append("No quantity column found. Returns data should have quantity column")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def extract_column_mapping(df: pd.DataFrame, file_type: str) -> Dict[str, str]:
        """
        Extract column mapping based on VBA header detection logic
        """
        mapping = {}
        columns_lower = {str(col).lower(): col for col in df.columns}
        
        if file_type == 'sales':
            # Date column patterns (from VBA)
            date_patterns = [
                'created on', 'order date', 'order_date', 'created_on',
                'created date', 'date', 'order creation date'
            ]
            
            # Style column patterns
            style_patterns = [
                'style id', 'style_id', 'style code', 'stylecode',
                'product id', 'productid', 'product code'
            ]
            
            # Price/GMV patterns
            price_patterns = [
                'final price', 'selling price', 'selling_price',
                'sale price', 'net price', 'unit price', 'item price', 'price',
                'gmv', 'gross gmv', 'net amount', 'item total'
            ]
            
            # Find matches
            for pattern in date_patterns:
                if pattern in columns_lower:
                    mapping['date'] = columns_lower[pattern]
                    break
            
            for pattern in style_patterns:
                if pattern in columns_lower:
                    mapping['style'] = columns_lower[pattern]
                    break
            
            for pattern in price_patterns:
                if pattern in columns_lower:
                    mapping['price'] = columns_lower[pattern]
                    break
        
        elif file_type == 'returns':
            # Date patterns
            date_patterns = [
                'return_registered_on', 'return registered on',
                'return date', 'return_date', 'registered on',
                'registered_on', 'created on', 'created_on'
            ]
            
            # Style patterns
            style_patterns = [
                'style_id', 'style id', 'style code', 'stylecode',
                'product id', 'productid'
            ]
            
            # Quantity patterns
            qty_patterns = [
                'quantity', 'qty returned', 'quantity returned',
                'units returned', 'return qty', 'qty', 'return quantity'
            ]
            
            # Type patterns
            type_patterns = [
                'status', 'return reason type', 'return_type', 'type'
            ]
            
            # Reason patterns
            reason_patterns = [
                'reason', 'return reason', 'return_reason', 'sub reason'
            ]
            
            # Find matches
            for pattern in date_patterns:
                if pattern in columns_lower:
                    mapping['date'] = columns_lower[pattern]
                    break
            
            for pattern in style_patterns:
                if pattern in columns_lower:
                    mapping['style'] = columns_lower[pattern]
                    break
            
            for pattern in qty_patterns:
                if pattern in columns_lower:
                    mapping['quantity'] = columns_lower[pattern]
                    break
            
            for pattern in type_patterns:
                if pattern in columns_lower:
                    mapping['type'] = columns_lower[pattern]
                    break
            
            for pattern in reason_patterns:
                if pattern in columns_lower:
                    mapping['reason'] = columns_lower[pattern]
                    break
        
        elif file_type == 'catalog':
            # Catalog patterns
            style_patterns = [
                'style id', 'style_id', 'style code', 'stylecode',
                'product id', 'productid', 'product code'
            ]
            
            brand_patterns = [
                'brand', 'brand name', 'brand_name'
            ]
            
            date_patterns = [
                'first updated', 'first_updated', 'created', 'live date'
            ]
            
            for pattern in style_patterns:
                if pattern in columns_lower:
                    mapping['style'] = columns_lower[pattern]
                    break
            
            for pattern in brand_patterns:
                if pattern in columns_lower:
                    mapping['brand'] = columns_lower[pattern]
                    break
            
            for pattern in date_patterns:
                if pattern in columns_lower:
                    mapping['date'] = columns_lower[pattern]
                    break
        
        return mapping
    
    @staticmethod
    def normalize_dataframe(df: pd.DataFrame, file_type: str) -> pd.DataFrame:
        """
        Normalize dataframe column names and data types
        """
        normalized_df = df.copy()
        
        # Convert column names to standard format
        column_rename = {}
        for col in normalized_df.columns:
            col_lower = str(col).lower().strip()
            
            # Standardize column names
            if 'date' in col_lower or 'created' in col_lower or 'order' in col_lower:
                if file_type == 'sales':
                    column_rename[col] = 'OrderDate'
                elif file_type == 'returns':
                    column_rename[col] = 'ReturnDate'
                elif file_type == 'catalog':
                    column_rename[col] = 'FirstUpdated'
            
            elif 'style' in col_lower or 'product' in col_lower or 'code' in col_lower:
                column_rename[col] = 'StyleID'
            
            elif 'qty' in col_lower or 'quantity' in col_lower:
                column_rename[col] = 'Quantity'
            
            elif 'price' in col_lower or 'gmv' in col_lower or 'amount' in col_lower:
                column_rename[col] = 'Price'
            
            elif 'brand' in col_lower:
                column_rename[col] = 'Brand'
            
            elif 'reason' in col_lower:
                column_rename[col] = 'Reason'
            
            elif 'type' in col_lower or 'status' in col_lower:
                column_rename[col] = 'ReturnType'
        
        # Rename columns
        if column_rename:
            normalized_df = normalized_df.rename(columns=column_rename)
        
        # Convert date columns
        date_columns = [col for col in normalized_df.columns if 'Date' in col]
        for date_col in date_columns:
            normalized_df[date_col] = pd.to_datetime(
                normalized_df[date_col], errors='coerce'
            )
        
        # Convert numeric columns
        numeric_columns = ['Quantity', 'Price']
        for num_col in numeric_columns:
            if num_col in normalized_df.columns:
                normalized_df[num_col] = pd.to_numeric(
                    normalized_df[num_col], errors='coerce'
                )
        
        return normalized_df
    
    @staticmethod
    def create_sample_data(file_type: str, rows: int = 10) -> pd.DataFrame:
        """
        Create sample data for testing/demo purposes
        Replicates Myntra data structure
        """
        np.random.seed(42)
        
        if file_type == 'sales':
            # Create sample sales data (no quantity column)
            dates = pd.date_range(end=datetime.now(), periods=rows)
            styles = [f'STY{np.random.randint(10000, 99999)}' for _ in range(rows)]
            
            df = pd.DataFrame({
                'Order Date': dates,
                'Style ID': styles,
                'Selling Price': np.random.uniform(299, 2999, rows).round(2),
                'Size': np.random.choice(['S', 'M', 'L', 'XL', 'XXL'], rows),
                'Brand': np.random.choice(['Nike', 'Adidas', 'Puma', 'UCB', 'Levis'], rows)
            })
            
            return df
        
        elif file_type == 'returns':
            # Create sample returns data (has quantity column)
            dates = pd.date_range(end=datetime.now(), periods=rows)
            styles = [f'STY{np.random.randint(10000, 99999)}' for _ in range(rows)]
            
            df = pd.DataFrame({
                'Return Date': dates,
                'Style ID': styles,
                'Quantity': np.random.randint(1, 3, rows),
                'Return Type': np.random.choice(['RTO', 'Return', 'Exchange'], rows),
                'Return Reason': np.random.choice([
                    'Size Issue', 'Quality', 'Defect', 'Color Mismatch', 'Wrong Item'
                ], rows),
                'Brand': np.random.choice(['Nike', 'Adidas', 'Puma', 'UCB', 'Levis'], rows)
            })
            
            return df
        
        elif file_type == 'catalog':
            # Create sample catalog data
            styles = [f'STY{np.random.randint(10000, 99999)}' for _ in range(rows)]
            
            df = pd.DataFrame({
                'Style ID': styles,
                'Brand': np.random.choice(['Nike', 'Adidas', 'Puma', 'UCB', 'Levis'], rows),
                'Category': np.random.choice(['T-Shirts', 'Jeans', 'Shirts', 'Shoes', 'Accessories'], rows),
                'First Updated': pd.date_range(
                    start='2024-01-01', 
                    periods=rows, 
                    freq='D'
                ),
                'MRP': np.random.uniform(499, 4999, rows).round(2)
            })
            
            return df
        
        else:
            raise ValueError(f"Unknown file type: {file_type}")
    
    @staticmethod
    def export_to_csv(df: pd.DataFrame, filename: str) -> bytes:
        """
        Export dataframe to CSV bytes
        """
        output = io.BytesIO()
        
        # Use Excel-compatible CSV format
        df.to_csv(output, index=False, encoding='utf-8-sig')
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def export_to_excel(df: pd.DataFrame, filename: str) -> bytes:
        """
        Export dataframe to Excel bytes
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Data']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def get_file_summary(df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """
        Generate summary of uploaded file
        """
        summary = {
            'filename': filename,
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': list(df.columns),
            'data_types': {col: str(df[col].dtype) for col in df.columns},
            'missing_values': {col: int(df[col].isna().sum()) for col in df.columns},
            'sample_data': df.head(5).to_dict('records')
        }
        
        # Add specific column detection
        date_cols = [col for col in df.columns if 'date' in str(col).lower()]
        style_cols = [col for col in df.columns if any(x in str(col).lower() 
                       for x in ['style', 'product', 'code', 'id'])]
        qty_cols = [col for col in df.columns if any(x in str(col).lower() 
                     for x in ['qty', 'quantity', 'units'])]
        
        summary['detected_columns'] = {
            'date_columns': date_cols,
            'style_columns': style_cols,
            'quantity_columns': qty_cols
        }
        
        return summary
    
    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean column names: remove special characters, extra spaces
        """
        cleaned_df = df.copy()
        
        new_columns = []
        for col in cleaned_df.columns:
            # Convert to string
            col_str = str(col)
            
            # Remove special characters (keep alphanumeric and spaces)
            col_str = ''.join(c for c in col_str if c.isalnum() or c.isspace())
            
            # Replace multiple spaces with single space
            col_str = ' '.join(col_str.split())
            
            # Convert to proper case
            col_str = col_str.title()
            
            new_columns.append(col_str)
        
        cleaned_df.columns = new_columns
        return cleaned_df
    
    @staticmethod
    def handle_excel_date(value) -> Optional[datetime]:
        """
        Handle Excel date serial numbers and various date formats
        """
        if pd.isna(value):
            return None
        
        try:
            # If it's already a datetime
            if isinstance(value, (datetime, pd.Timestamp)):
                return value
            
            # If it's an Excel serial number (float)
            if isinstance(value, (int, float)):
                # Excel date system starts from 1899-12-30
                return datetime(1899, 12, 30) + timedelta(days=value)
            
            # Try parsing as string
            return pd.to_datetime(value, errors='coerce')
            
        except Exception:
            return None