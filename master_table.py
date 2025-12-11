import pandas as pd
import numpy as np
from datetime import datetime

class MasterTableBuilder:
    @staticmethod
    def build_master_table(sales_df, returns_df, catalog_df, params):
        """
        EXACT replica of BuildMasterTable() VBA function
        Creates the comprehensive master view
        """
        # Step 1: Get unique styles from catalog
        master_rows = []
        
        if catalog_df is not None and len(catalog_df) > 0:
            # Find style column in catalog
            style_cols = [col for col in catalog_df.columns 
                         if any(keyword in str(col).lower() 
                               for keyword in ['style', 'product', 'code', 'id'])]
            
            if style_cols:
                style_col = style_cols[0]
                unique_styles = catalog_df[style_col].dropna().unique()
                
                for style in unique_styles:
                    style_key = str(style).strip().lower()
                    master_rows.append({
                        'Style ID': style,
                        'StyleKey': style_key
                    })
        
        if len(master_rows) == 0 and sales_df is not None:
            # Fallback to sales data
            unique_styles = sales_df['StyleKey'].dropna().unique()
            for style_key in unique_styles:
                master_rows.append({
                    'Style ID': style_key,
                    'StyleKey': style_key
                })
        
        if len(master_rows) == 0:
            return pd.DataFrame()
        
        master_df = pd.DataFrame(master_rows)
        
        # Step 2: Calculate metrics for each style
        today_date = params.get('today', datetime.now())
        zero_age = params.get('zero_sale_age', 14)
        high_ret_pct = params.get('high_return_pct', 0.35)
        
        metrics = []
        
        for _, row in master_df.iterrows():
            style_key = row['StyleKey']
            
            # Sales metrics
            if sales_df is not None and len(sales_df) > 0:
                style_sales = sales_df[sales_df['StyleKey'] == style_key]
                
                orders = style_sales['NetUnits'].sum() if 'NetUnits' in style_sales.columns else 0
                gmv = style_sales['NetGMV'].sum() if 'NetGMV' in style_sales.columns else 0
                
                if len(style_sales) > 0:
                    first_order = style_sales['OrderDate'].min()
                    last_order = style_sales['OrderDate'].max()
                else:
                    first_order = last_order = None
            else:
                orders = gmv = 0
                first_order = last_order = None
            
            # Returns metrics
            if returns_df is not None and len(returns_df) > 0:
                style_returns = returns_df[returns_df['StyleKey'] == style_key]
                units_returned = style_returns['UnitsReturned'].sum() if 'UnitsReturned' in style_returns.columns else 0
            else:
                units_returned = 0
            
            # Calculate percentages
            return_pct = units_returned / orders if orders > 0 else 0
            
            # Determine status (like VBA logic)
            if first_order is None:
                status = "Catalog-Only"
            elif orders == 0 and ((today_date - first_order.date()).days >= zero_age 
                                 if first_order else False):
                status = "Zero-Sale"
            elif (today_date - first_order.date()).days <= 60:
                status = "New"
            elif orders > 0:
                status = "Active"
            else:
                status = "Unknown"
            
            # Risk flag
            risk_flag = "High Returns" if return_pct >= high_ret_pct else ""
            
            metrics.append({
                'Style ID': row['Style ID'],
                'FirstUpdated': first_order,
                'Days_Since_FirstUpdate': (today_date - first_order.date()).days if first_order else None,
                'Newness_Bucket': MasterTableBuilder._get_newness_bucket(first_order, today_date),
                'Orders': orders,
                'GMV': gmv,
                'FirstOrderDate': first_order,
                'LastOrderDate': last_order,
                'UnitsReturned': units_returned,
                'ReturnPct': return_pct,
                'Status': status,
                'RiskFlag': risk_flag
            })
        
        return pd.DataFrame(metrics)
    
    @staticmethod
    def _get_newness_bucket(first_date, today_date):
        """Helper for newness bucket logic"""
        if not first_date:
            return "Unknown"
        
        days_live = (today_date - first_date.date()).days
        
        if days_live <= 7:
            return "0-7d"
        elif days_live <= 30:
            return "8-30d"
        elif days_live <= 60:
            return "31-60d"
        elif days_live <= 90:
            return "61-90d"
        else:
            return "91d+"
