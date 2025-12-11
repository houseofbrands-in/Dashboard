import pandas as pd
import numpy as np
from datetime import datetime

class DataImporters:
    @staticmethod
    def import_sales_csv(df, user_params=None):
        """
        Equivalent to ImportSalesCSV() VBA function
        Converts raw CSV to standardized format
        """
        result_df = df.copy()
        
        # AUTO-DETECT COLUMNS (like your VBA does)
        date_candidates = ['created on', 'order date', 'order_date', 'created_on', 
                          'created date', 'date', 'order creation date']
        style_candidates = ['style id', 'style_id', 'style code', 'stylecode', 
                           'product id', 'productid', 'product code']
        qty_candidates = ['qty', 'quantity', 'units', 'order qty', 'qty ordered', 
                         'ordered qty', 'item qty']
        price_candidates = ['final price', 'selling price', 'selling_price', 
                           'sale price', 'net price', 'unit price', 'item price', 'price']
        
        # Find columns
        date_col = None
        style_col = None
        qty_col = None
        price_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            
            if not date_col and any(candidate in col_lower for candidate in date_candidates):
                date_col = col
            if not style_col and any(candidate in col_lower for candidate in style_candidates):
                style_col = col
            if not qty_col and any(candidate in col_lower for candidate in qty_candidates):
                qty_col = col
            if not price_col and any(candidate in col_lower for candidate in price_candidates):
                price_col = col
        
        # If not found, use first matching pattern
        if not date_col:
            for col in df.columns:
                if 'date' in str(col).lower():
                    date_col = col
                    break
        
        if not style_col:
            for col in df.columns:
                if 'style' in str(col).lower() or 'product' in str(col).lower():
                    style_col = col
                    break
        
        # REQUIRED: Date and Style must exist
        if not date_col or not style_col:
            raise ValueError("Sales CSV must contain Date and Style columns")
        
        # PROCESS LIKE VBA
        # 1. Date parsing
        result_df['OrderDate'] = pd.to_datetime(result_df[date_col], errors='coerce')
        result_df['OrderDateNum'] = result_df['OrderDate'].apply(
            lambda x: x.toordinal() if pd.notna(x) else 0
        )
        
        # 2. Style key normalization (CRITICAL - fixes your issue)
        result_df['StyleKey'] = result_df[style_col].apply(
            lambda x: str(x).strip().lower() if pd.notna(x) else ''
        )
        
        # 3. Quantity
        if qty_col:
            result_df['NetUnits'] = pd.to_numeric(result_df[qty_col], errors='coerce').fillna(1)
        else:
            result_df['NetUnits'] = 1
        
        # 4. GMV/Price
        if price_col:
            result_df['UnitPrice'] = pd.to_numeric(result_df[price_col], errors='coerce').fillna(0)
            result_df['NetGMV'] = result_df['NetUnits'] * result_df['UnitPrice']
        else:
            # Try to find GMV column
            gmv_cols = [col for col in df.columns if 'gmv' in str(col).lower()]
            if gmv_cols:
                result_df['NetGMV'] = pd.to_numeric(result_df[gmv_cols[0]], errors='coerce').fillna(0)
            else:
                result_df['NetGMV'] = 0
        
        # 5. Row counter (like VBA's RowUnit)
        result_df['RowUnit'] = 1
        
        return {
            'data': result_df,
            'mapping': {
                'date_col': date_col,
                'style_col': style_col,
                'qty_col': qty_col,
                'price_col': price_col
            }
        }
    
    @staticmethod
    def import_returns_csv(df):
        """Equivalent to ImportReturnsCSV()"""
        result_df = df.copy()
        
        # Auto-detect columns
        date_candidates = ['return_registered_on', 'return registered on', 
                          'return date', 'return_date', 'registered on', 
                          'registered_on', 'created on', 'created_on']
        style_candidates = ['style_id', 'style id', 'style code', 'stylecode', 
                           'product id', 'productid']
        qty_candidates = ['quantity', 'qty returned', 'quantity returned', 
                         'units returned', 'return qty', 'qty', 'return quantity']
        
        date_col = style_col = qty_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if not date_col and any(candidate in col_lower for candidate in date_candidates):
                date_col = col
            if not style_col and any(candidate in col_lower for candidate in style_candidates):
                style_col = col
            if not qty_col and any(candidate in col_lower for candidate in qty_candidates):
                qty_col = col
        
        # Required columns
        if not date_col or not style_col:
            raise ValueError("Returns CSV must contain Date and Style columns")
        
        # Process dates
        result_df['ReturnDate'] = pd.to_datetime(result_df[date_col], errors='coerce')
        result_df['ReturnDateNum'] = result_df['ReturnDate'].apply(
            lambda x: x.toordinal() if pd.notna(x) else 0
        )
        
        # Style key
        result_df['StyleKey'] = result_df[style_col].apply(
            lambda x: str(x).strip().lower() if pd.notna(x) else ''
        )
        
        # Quantity
        if qty_col:
            result_df['UnitsReturned'] = pd.to_numeric(result_df[qty_col], errors='coerce').fillna(1)
        else:
            result_df['UnitsReturned'] = 1
        
        # Return type (RTO vs Return)
        type_cols = [col for col in df.columns if 'status' in str(col).lower() or 
                    'return reason type' in str(col).lower()]
        if type_cols:
            result_df['ReturnType'] = result_df[type_cols[0]].fillna('(Unknown)')
        else:
            result_df['ReturnType'] = '(Unknown)'
        
        return {
            'data': result_df,
            'mapping': {
                'date_col': date_col,
                'style_col': style_col,
                'qty_col': qty_col
            }
        }
