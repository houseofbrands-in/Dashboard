import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MyntraAnalytics:
    def __init__(self):
        self.sales_data = None
        self.returns_data = None
        self.catalog_data = None
        self.params = {}
    
    def import_sales_csv(self, df, date_col, style_col, qty_col):
        """Equivalent to ImportSalesCSV VBA function"""
        try:
            # Clean and normalize
            df_clean = df.copy()
            
            # Convert date
            df_clean['OrderDate'] = pd.to_datetime(df_clean[date_col], errors='coerce')
            df_clean['OrderDateNum'] = df_clean['OrderDate'].map(pd.Timestamp.toordinal)
            
            # Clean style key
            df_clean['StyleKey'] = df_clean[style_col].astype(str).str.lower().str.strip()
            
            # Clean quantity
            if qty_col in df_clean.columns:
                df_clean['NetUnits'] = pd.to_numeric(df_clean[qty_col], errors='coerce').fillna(1)
            else:
                df_clean['NetUnits'] = 1
            
            # Add row counter
            df_clean['RowUnit'] = 1
            
            self.sales_data = df_clean
            return True, f"Sales data imported: {len(df_clean)} rows"
            
        except Exception as e:
            return False, f"Error importing sales: {str(e)}"
    
    def import_returns_csv(self, df, date_col, style_col, qty_col):
        """Equivalent to ImportReturnsCSV"""
        try:
            df_clean = df.copy()
            df_clean['ReturnDate'] = pd.to_datetime(df_clean[date_col], errors='coerce')
            df_clean['ReturnDateNum'] = df_clean['ReturnDate'].map(pd.Timestamp.toordinal)
            df_clean['StyleKey'] = df_clean[style_col].astype(str).str.lower().str.strip()
            
            if qty_col in df_clean.columns:
                df_clean['UnitsReturned'] = pd.to_numeric(df_clean[qty_col], errors='coerce').fillna(1)
            else:
                df_clean['UnitsReturned'] = 1
            
            self.returns_data = df_clean
            return True, f"Returns data imported: {len(df_clean)} rows"
            
        except Exception as e:
            return False, f"Error importing returns: {str(e)}"
    
    def kpi_total_orders_30d(self):
        """Equivalent to KPI_TotalOrders_30d()"""
        if self.sales_data is None:
            return 0
        
        today = pd.Timestamp.today()
        cutoff = today - timedelta(days=30)
        
        mask = (self.sales_data['OrderDate'] >= cutoff) & (self.sales_data['OrderDate'] <= today)
        return self.sales_data.loc[mask, 'NetUnits'].sum()
    
    def kpi_return_pct_30d(self):
        """Equivalent to KPI_ReturnPct_30d()"""
        orders = self.kpi_total_orders_30d()
        
        if self.returns_data is None or orders == 0:
            return 0
        
        today = pd.Timestamp.today()
        cutoff = today - timedelta(days=30)
        
        mask = (self.returns_data['ReturnDate'] >= cutoff) & (self.returns_data['ReturnDate'] <= today)
        returns = self.returns_data.loc[mask, 'UnitsReturned'].sum()
        
        return returns / orders
    
    def build_master_table(self):
        """Equivalent to BuildMasterTable()"""
        if self.sales_data is None and self.catalog_data is None:
            return None
        
        # Simplified version - you can expand this
        master_data = []
        
        if self.sales_data is not None:
            # Group by style
            sales_summary = self.sales_data.groupby('StyleKey').agg({
                'NetUnits': 'sum',
                'OrderDate': ['min', 'max']  # First and last order
            }).reset_index()
            
            for _, row in sales_summary.iterrows():
                master_data.append({
                    'Style ID': row['StyleKey'],
                    'Orders': row[('NetUnits', 'sum')],
                    'First Order': row[('OrderDate', 'min')],
                    'Last Order': row[('OrderDate', 'max')]
                })
        
        return pd.DataFrame(master_data)
    
    def build_watchlist_30d(self, min_orders=3):
        """Equivalent to BuildWatchlist30d()"""
        if self.sales_data is None:
            return None
        
        today = pd.Timestamp.today()
        cutoff_30d = today - timedelta(days=30)
        cutoff_60d = today - timedelta(days=60)
        
        # Recent sales (last 30 days)
        recent_mask = (self.sales_data['OrderDate'] >= cutoff_30d) & (self.sales_data['OrderDate'] <= today)
        recent_sales = self.sales_data[recent_mask].groupby('StyleKey')['NetUnits'].sum().reset_index()
        recent_sales.columns = ['StyleKey', 'Orders30d']
        
        # Previous period (30-60 days ago)
        prev_mask = (self.sales_data['OrderDate'] >= cutoff_60d) & (self.sales_data['OrderDate'] < cutoff_30d)
        prev_sales = self.sales_data[prev_mask].groupby('StyleKey')['NetUnits'].sum().reset_index()
        prev_sales.columns = ['StyleKey', 'OrdersPrev30d']
        
        # Merge
        watchlist = pd.merge(recent_sales, prev_sales, on='StyleKey', how='left')
        watchlist['OrdersPrev30d'] = watchlist['OrdersPrev30d'].fillna(0)
        
        # Calculate momentum
        watchlist['Momentum%'] = np.where(
            watchlist['OrdersPrev30d'] > 0,
            (watchlist['Orders30d'] - watchlist['OrdersPrev30d']) / watchlist['OrdersPrev30d'],
            np.where(watchlist['Orders30d'] > 0, 1, 0)
        )
        
        # Apply tags
        conditions = [
            (watchlist['Orders30d'] >= min_orders) & (watchlist['OrdersPrev30d'] == 0),
            (watchlist['Momentum%'] > 0.15),
            (watchlist['Momentum%'] < -0.15)
        ]
        choices = ['NEW_STARTER', 'RISING', 'FALLING']
        watchlist['Tag'] = np.select(conditions, choices, default='STABLE')
        
        return watchlist
    
    def inventory_forecast(self, lookback_days=30, event_days=10, 
                          traffic_mult=3, return_rate=0.25):
        """Equivalent to inventory forecasting logic"""
        if self.sales_data is None:
            return None
        
        today = pd.Timestamp.today()
        cutoff = today - timedelta(days=lookback_days)
        
        # Calculate daily averages
        mask = (self.sales_data['OrderDate'] >= cutoff) & (self.sales_data['OrderDate'] <= today)
        recent_sales = self.sales_data[mask]
        
        if recent_sales.empty:
            return None
        
        daily_avg = recent_sales.groupby('StyleKey')['NetUnits'].sum() / lookback_days
        
        # Forecast calculation
        forecast_data = []
        for style, avg in daily_avg.items():
            gross_forecast = avg * event_days * traffic_mult
            net_forecast = gross_forecast * (1 - return_rate)
            safety_stock = net_forecast * 0.2  # Simplified safety stock
            total_needed = net_forecast + safety_stock
            
            forecast_data.append({
                'Style ID': style,
                'Avg Daily Sales': round(avg, 2),
                'Gross Forecast': round(gross_forecast, 0),
                'Net Forecast': round(net_forecast, 0),
                'Safety Stock': round(safety_stock, 0),
                'Total Required': round(total_needed, 0)
            })
        
        return pd.DataFrame(forecast_data)

# Example usage in Streamlit:
# analyzer = MyntraAnalytics()
# analyzer.import_sales_csv(df, 'Order Date', 'Style ID', 'Qty')
# orders = analyzer.kpi_total_orders_30d()
# forecast = analyzer.inventory_forecast()
