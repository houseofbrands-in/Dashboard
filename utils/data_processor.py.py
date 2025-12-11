"""
VBA to Python Translation for Project M
Replicates exact Excel VBA logic
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Tuple
import io

class ProjectMProcessor:
    """Main processor replicating VBA Project M logic"""
    
    def __init__(self):
        # Initialize with VBA defaults
        self.params = {
            # Core parameters from VBA
            'zero_sale_age_days': 14,
            'high_return_pct': 0.35,
            'watch_min_orders': 3,
            'new_age_days': 60,
            'start_recent_min_orders': 2,
            'start_prev_max_orders': 0,
            'forecast_lookback_days': 30,
            'event_days': 10,
            'traffic_multiplier': 3.0,
            'forecast_return_rate': 0.25,
            'leadtime_days': 7,
            'service_level': 0.9,
            'seasonality_boost': 1.0,
            'use_momentum_adjust': True,
            'report_window_days': 7,
            'return_window_days': 60,
            'size_split_lookback_days': 60,
            'size_split_min_share': 0.05,
            'size_split_min_units': 1,
            'brand_filter_mode': 'ALL',
            'today': datetime.now().date()
        }
        
        # Data storage (like Excel sheets)
        self.sales_raw = None
        self.returns_raw = None
        self.catalog_raw = None
        self.catalog_clean = None
        self.master_styles = None
        self.watchlist_30d = None
        self.returns_insights = None
        self.forecast = None
        
    # ============================================================================
    # CORE IMPORT FUNCTIONS (VBA equivalents)
    # ============================================================================
    
    def import_sales_csv(self, df: pd.DataFrame, file_name: str = "") -> Dict:
        """
        Equivalent to VBA ImportSalesCSV function
        CRITICAL: Each row = 1 unit (Myntra data has no quantity column)
        """
        result = {
            'success': False,
            'rows_processed': 0,
            'columns_mapped': {},
            'errors': []
        }
        
        try:
            # Auto-detect columns (VBA style fuzzy matching)
            col_mapping = self._detect_sales_columns(df)
            
            # Validate required columns
            if not col_mapping.get('date_col') or not col_mapping.get('style_col'):
                raise ValueError("Sales CSV must contain Date and Style columns")
            
            # Create processed dataframe
            processed_df = df.copy()
            
            # Process date column (VBA style)
            date_col = col_mapping['date_col']
            processed_df['OrderDate'] = pd.to_datetime(
                processed_df[date_col], errors='coerce'
            )
            processed_df['OrderDateNum'] = processed_df['OrderDate'].apply(
                lambda x: x.toordinal() + 693594 if pd.notna(x) else 0
            )
            
            # Process style column (VBA normalization)
            style_col = col_mapping['style_col']
            processed_df['StyleKey'] = processed_df[style_col].apply(
                self._normalize_style_id
            )
            
            # CRITICAL: Each row = 1 unit
            processed_df['NetUnits'] = 1  # Always 1, no quantity column
            processed_df['RowUnit'] = 1   # VBA equivalent
            
            # Process GMV/price if available
            if col_mapping.get('price_col'):
                price_col = col_mapping['price_col']
                processed_df['NetGMV'] = pd.to_numeric(
                    processed_df[price_col], errors='coerce'
                ).fillna(0)
            else:
                processed_df['NetGMV'] = 0
            
            # Store result
            self.sales_raw = processed_df
            result['success'] = True
            result['rows_processed'] = len(processed_df)
            result['columns_mapped'] = col_mapping
            
            return result
            
        except Exception as e:
            result['errors'].append(str(e))
            return result
    
    def import_returns_csv(self, df: pd.DataFrame) -> Dict:
        """Equivalent to VBA ImportReturnsCSV function"""
        result = {
            'success': False,
            'rows_processed': 0,
            'columns_mapped': {},
            'errors': []
        }
        
        try:
            # Auto-detect columns
            col_mapping = self._detect_returns_columns(df)
            
            # Validate required columns
            if not col_mapping.get('date_col') or not col_mapping.get('style_col'):
                raise ValueError("Returns CSV must contain Date and Style columns")
            
            processed_df = df.copy()
            
            # Process date
            date_col = col_mapping['date_col']
            processed_df['ReturnDate'] = pd.to_datetime(
                processed_df[date_col], errors='coerce'
            )
            processed_df['ReturnDateNum'] = processed_df['ReturnDate'].apply(
                lambda x: x.toordinal() + 693594 if pd.notna(x) else 0
            )
            
            # Process style
            style_col = col_mapping['style_col']
            processed_df['StyleKey'] = processed_df[style_col].apply(
                self._normalize_style_id
            )
            
            # Process quantity (returns DO have quantity column)
            if col_mapping.get('qty_col'):
                qty_col = col_mapping['qty_col']
                processed_df['UnitsReturned'] = pd.to_numeric(
                    processed_df[qty_col], errors='coerce'
                ).fillna(1)
            else:
                processed_df['UnitsReturned'] = 1
            
            # Process return type (RTO vs Return)
            type_col = col_mapping.get('type_col')
            if type_col:
                processed_df['ReturnType'] = processed_df[type_col].fillna('(Unknown)')
            else:
                processed_df['ReturnType'] = '(Unknown)'
            
            self.returns_raw = processed_df
            result['success'] = True
            result['rows_processed'] = len(processed_df)
            result['columns_mapped'] = col_mapping
            
            return result
            
        except Exception as e:
            result['errors'].append(str(e))
            return result
    
    # ============================================================================
    # MASTER TABLE BUILDER (VBA BuildMasterTable equivalent)
    # ============================================================================
    
    def build_master_table(self) -> pd.DataFrame:
        """Equivalent to VBA BuildMasterTable function"""
        if self.sales_raw is None and self.catalog_raw is None:
            return pd.DataFrame()
        
        # Get unique styles (from catalog or sales)
        styles_data = []
        
        # First try catalog
        if self.catalog_raw is not None and not self.catalog_raw.empty:
            style_col = self._find_style_column(self.catalog_raw)
            if style_col:
                unique_styles = self.catalog_raw[style_col].dropna().unique()
                for style in unique_styles:
                    style_key = self._normalize_style_id(style)
                    styles_data.append({
                        'Style ID': style,
                        'StyleKey': style_key
                    })
        
        # Fallback to sales
        if not styles_data and self.sales_raw is not None:
            unique_styles = self.sales_raw['StyleKey'].dropna().unique()
            for style_key in unique_styles:
                styles_data.append({
                    'Style ID': style_key,
                    'StyleKey': style_key
                })
        
        if not styles_data:
            return pd.DataFrame()
        
        master_df = pd.DataFrame(styles_data)
        
        # Calculate metrics for each style
        metrics = []
        today = self.params['today']
        zero_age = self.params['zero_sale_age_days']
        high_ret = self.params['high_return_pct']
        
        for _, row in master_df.iterrows():
            style_key = row['StyleKey']
            
            # Sales metrics
            if self.sales_raw is not None:
                style_sales = self.sales_raw[
                    self.sales_raw['StyleKey'] == style_key
                ]
                
                orders = len(style_sales)  # COUNT of rows = units
                gmv = style_sales['NetGMV'].sum()
                
                if not style_sales.empty:
                    first_order = style_sales['OrderDate'].min()
                    last_order = style_sales['OrderDate'].max()
                else:
                    first_order = last_order = None
            else:
                orders = gmv = 0
                first_order = last_order = None
            
            # Returns metrics
            if self.returns_raw is not None:
                style_returns = self.returns_raw[
                    self.returns_raw['StyleKey'] == style_key
                ]
                units_returned = style_returns['UnitsReturned'].sum()
            else:
                units_returned = 0
            
            # Calculate percentages
            return_pct = units_returned / orders if orders > 0 else 0
            
            # Determine status (VBA logic)
            if first_order is None:
                status = "Catalog-Only"
            elif orders == 0:
                days_live = (today - first_order.date()).days
                if days_live >= zero_age:
                    status = "Zero-Sale"
                else:
                    status = "New"
            elif (today - first_order.date()).days <= 60:
                status = "New"
            elif orders > 0:
                status = "Active"
            else:
                status = "Unknown"
            
            # Risk flag (VBA logic)
            risk_flag = "High Returns" if return_pct >= high_ret else ""
            
            # Newness bucket (VBA logic)
            if first_order:
                days_since = (today - first_order.date()).days
                if days_since <= 7:
                    bucket = "0-7d"
                elif days_since <= 30:
                    bucket = "8-30d"
                elif days_since <= 60:
                    bucket = "31-60d"
                elif days_since <= 90:
                    bucket = "61-90d"
                else:
                    bucket = "91d+"
            else:
                bucket = "Unknown"
            
            metrics.append({
                'Style ID': row['Style ID'],
                'FirstUpdated': first_order,
                'Days_Since_FirstUpdate': (today - first_order.date()).days 
                                         if first_order else None,
                'Newness_Bucket': bucket,
                'Orders': orders,
                'GMV': gmv,
                'FirstOrderDate': first_order,
                'LastOrderDate': last_order,
                'UnitsReturned': units_returned,
                'ReturnPct': return_pct,
                'Status': status,
                'RiskFlag': risk_flag
            })
        
        self.master_styles = pd.DataFrame(metrics)
        return self.master_styles
    
    # ============================================================================
    # WATCHLIST BUILDER (VBA BuildWatchlist30d equivalent)
    # ============================================================================
    
    def build_watchlist_30d(self) -> pd.DataFrame:
        """Equivalent to VBA BuildWatchlist30d function"""
        if self.sales_raw is None:
            return pd.DataFrame()
        
        today = self.params['today']
        window_days = self.params.get('report_window_days', 30)
        new_age = self.params['new_age_days']
        min_orders = self.params['watch_min_orders']
        high_ret = self.params['high_return_pct']
        
        # Date ranges
        recent_start = today - timedelta(days=window_days)
        prev_start = today - timedelta(days=window_days * 2)
        
        # Get unique styles from master or sales
        if self.master_styles is not None:
            styles = self.master_styles[['Style ID', 'StyleKey']].drop_duplicates()
        else:
            styles = pd.DataFrame({
                'Style ID': self.sales_raw['StyleKey'].unique(),
                'StyleKey': self.sales_raw['StyleKey'].unique()
            })
        
        watchlist_data = []
        
        for _, style_row in styles.iterrows():
            style_key = style_row['StyleKey']
            style_id = style_row['Style ID']
            
            # Sales in recent period
            recent_sales = self.sales_raw[
                (self.sales_raw['StyleKey'] == style_key) &
                (self.sales_raw['OrderDate'].dt.date >= recent_start) &
                (self.sales_raw['OrderDate'].dt.date <= today)
            ]
            orders_recent = len(recent_sales)
            
            # Sales in previous period
            prev_sales = self.sales_raw[
                (self.sales_raw['StyleKey'] == style_key) &
                (self.sales_raw['OrderDate'].dt.date >= prev_start) &
                (self.sales_raw['OrderDate'].dt.date < recent_start)
            ]
            orders_prev = len(prev_sales)
            
            # Returns in recent period
            if self.returns_raw is not None:
                recent_returns = self.returns_raw[
                    (self.returns_raw['StyleKey'] == style_key) &
                    (self.returns_raw['ReturnDate'].dt.date >= recent_start) &
                    (self.returns_raw['ReturnDate'].dt.date <= today)
                ]
                returns_qty = recent_returns['UnitsReturned'].sum()
                
                # RTO vs Return split
                rto_qty = recent_returns[
                    recent_returns['ReturnType'].str.contains('RTO', case=False, na=False)
                ]['UnitsReturned'].sum()
                return_qty = returns_qty - rto_qty
            else:
                returns_qty = rto_qty = return_qty = 0
            
            # Calculate momentum
            if orders_prev > 0:
                momentum = (orders_recent - orders_prev) / orders_prev
            elif orders_recent > 0:
                momentum = 1.0
            else:
                momentum = 0.0
            
            # Return percentage
            return_pct = returns_qty / orders_recent if orders_recent > 0 else 0
            
            # Determine tag (VBA logic)
            # Get age from master table if available
            age_days = None
            if self.master_styles is not None:
                style_master = self.master_styles[
                    self.master_styles['StyleKey'] == style_key
                ]
                if not style_master.empty:
                    age_days = style_master.iloc[0]['Days_Since_FirstUpdate']
            
            if age_days is not None and age_days <= new_age:
                tag = "NEW"
            elif orders_recent >= min_orders and orders_prev == 0:
                tag = "STARTED"
            elif momentum > 0.15:
                tag = "RISING"
            elif momentum < -0.15:
                tag = "FALLING"
            else:
                tag = "FLAT"
            
            # Note (VBA logic)
            note = ""
            if tag == "NEW":
                note = f"New (≤ {new_age}d)"
            elif tag == "STARTED":
                note = "Started performing recently"
            elif return_pct >= high_ret:
                note = f"High returns ({return_pct:.1%})"
            elif tag in ["RISING", "FALLING"]:
                note = tag
            
            watchlist_data.append({
                'Style ID': style_id,
                'Tag': tag,
                'Orders30d Est': orders_recent,
                'Returns30d Qty': returns_qty,
                'Returns% Est': return_pct,
                'Momentum%': momentum,
                'New?': 'YES' if age_days and age_days <= new_age else '',
                'Note': note,
                'RTO Qty': rto_qty,
                'Return Qty': return_qty
            })
        
        self.watchlist_30d = pd.DataFrame(watchlist_data)
        return self.watchlist_30d
    
    # ============================================================================
    # RETURNS ANALYSIS (VBA BuildReturnsTypeSplit equivalent)
    # ============================================================================
    
    def build_returns_type_split(self) -> pd.DataFrame:
        """Equivalent to VBA BuildReturnsTypeSplit function"""
        if self.returns_raw is None or self.master_styles is None:
            return pd.DataFrame()
        
        today = self.params['today']
        window_days = self.params.get('return_window_days', 30)
        cutoff_date = today - timedelta(days=window_days)
        
        returns_data = []
        
        for _, style_row in self.master_styles.iterrows():
            style_key = style_row['StyleKey']
            style_id = style_row['Style ID']
            
            # Filter returns for this style in window
            style_returns = self.returns_raw[
                (self.returns_raw['StyleKey'] == style_key) &
                (self.returns_raw['ReturnDate'].dt.date >= cutoff_date) &
                (self.returns_raw['ReturnDate'].dt.date <= today)
            ]
            
            if style_returns.empty:
                continue
            
            # Calculate RTO and Return quantities
            rto_mask = style_returns['ReturnType'].str.contains('RTO', case=False, na=False)
            rto_qty = style_returns[rto_mask]['UnitsReturned'].sum()
            return_qty = style_returns[~rto_mask]['UnitsReturned'].sum()
            total_returns = rto_qty + return_qty
            
            if total_returns == 0:
                continue
            
            returns_data.append({
                'Style ID': style_id,
                'RTO Qty': int(rto_qty),
                'Return Qty': int(return_qty),
                'Total Returns': int(total_returns),
                'RTO %': rto_qty / total_returns,
                'Return %': return_qty / total_returns
            })
        
        return pd.DataFrame(returns_data)
    
    # ============================================================================
    # INVENTORY FORECAST (VBA BuildInventoryForecast equivalent)
    # ============================================================================
    
    def build_inventory_forecast(self) -> pd.DataFrame:
        """Equivalent to VBA BuildInventoryForecast function"""
        if self.sales_raw is None:
            return pd.DataFrame()
        
        # Get parameters
        lookback = self.params['forecast_lookback_days']
        event_days = self.params['event_days']
        traffic_mult = self.params['traffic_multiplier']
        return_rate = self.params['forecast_return_rate']
        leadtime = self.params['leadtime_days']
        service_level = self.params['service_level']
        use_momentum = self.params['use_momentum_adjust']
        
        today = self.params['today']
        cutoff_date = today - timedelta(days=lookback)
        
        # Get unique styles
        if self.master_styles is not None:
            styles = self.master_styles[['Style ID', 'StyleKey']].drop_duplicates()
        else:
            styles = pd.DataFrame({
                'Style ID': self.sales_raw['StyleKey'].unique(),
                'StyleKey': self.sales_raw['StyleKey'].unique()
            })
        
        forecast_data = []
        
        for _, style_row in styles.iterrows():
            style_key = style_row['StyleKey']
            style_id = style_row['Style ID']
            
            # Get sales in lookback period
            style_sales = self.sales_raw[
                (self.sales_raw['StyleKey'] == style_key) &
                (self.sales_raw['OrderDate'].dt.date >= cutoff_date) &
                (self.sales_raw['OrderDate'].dt.date <= today)
            ]
            
            if style_sales.empty:
                continue
            
            # Calculate average daily sales (COUNT of rows = units)
            avg_daily = len(style_sales) / lookback
            
            # Get momentum from watchlist if available
            momentum = 0
            if use_momentum and self.watchlist_30d is not None:
                style_watch = self.watchlist_30d[
                    self.watchlist_30d['Style ID'] == style_id
                ]
                if not style_watch.empty:
                    momentum = style_watch.iloc[0]['Momentum%']
            
            # Calculate forecast (VBA logic)
            base_forecast = avg_daily * event_days * traffic_mult
            if use_momentum:
                # Apply momentum adjustment (capped)
                momentum_adj = max(min(momentum, 0.5), -0.3)
                gross_forecast = base_forecast * (1 + momentum_adj)
            else:
                gross_forecast = base_forecast
            
            net_forecast = gross_forecast * (1 - return_rate)
            
            # Safety stock (simplified z-score calculation)
            z_score = 1.28  # ~90% service level
            safety_stock = z_score * (gross_forecast ** 0.5)
            
            total_required = int(np.ceil(net_forecast + safety_stock))
            
            forecast_data.append({
                'Style ID': style_id,
                'Avg Daily Sales': round(avg_daily, 2),
                'Gross Forecast': round(gross_forecast, 0),
                'Net Forecast': round(net_forecast, 0),
                'Safety Stock': round(safety_stock, 0),
                'Total Required': total_required,
                'Lead Time (days)': leadtime,
                'Service Level': f"{service_level:.0%}"
            })
        
        self.forecast = pd.DataFrame(forecast_data)
        return self.forecast
    
    # ============================================================================
    # HELPER FUNCTIONS (VBA equivalents)
    # ============================================================================
    
    def _normalize_style_id(self, value) -> str:
        """
        Exact VBA equivalent: LCase$(Trim$(IF(ISNUMBER([style]),TEXT([style],"0"),[style])))
        """
        if pd.isna(value):
            return ""
        
        # Convert to string
        s = str(value)
        
        # Trim whitespace
        s = s.strip()
        
        # Handle numbers (remove .0 decimals like Excel)
        try:
            # Try to convert to number
            num = float(s)
            # If it's a whole number, remove decimal
            if num.is_integer():
                s = str(int(num))
        except:
            pass
        
        # Convert to lowercase
        s = s.lower()
        
        return s
    
    def _detect_sales_columns(self, df: pd.DataFrame) -> Dict:
        """VBA-style column detection for sales data"""
        col_mapping = {}
        
        # Convert column names to lowercase for matching
        columns_lower = {col.lower(): col for col in df.columns}
        
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
            'gmv', 'gross gmv', 'net amount'
        ]
        
        # Find matches
        for pattern in date_patterns:
            if pattern in columns_lower:
                col_mapping['date_col'] = columns_lower[pattern]
                break
        
        for pattern in style_patterns:
            if pattern in columns_lower:
                col_mapping['style_col'] = columns_lower[pattern]
                break
        
        for pattern in price_patterns:
            if pattern in columns_lower:
                col_mapping['price_col'] = columns_lower[pattern]
                break
        
        return col_mapping
    
    def _detect_returns_columns(self, df: pd.DataFrame) -> Dict:
        """VBA-style column detection for returns data"""
        col_mapping = {}
        
        columns_lower = {col.lower(): col for col in df.columns}
        
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
        
        # Find matches
        for pattern in date_patterns:
            if pattern in columns_lower:
                col_mapping['date_col'] = columns_lower[pattern]
                break
        
        for pattern in style_patterns:
            if pattern in columns_lower:
                col_mapping['style_col'] = columns_lower[pattern]
                break
        
        for pattern in qty_patterns:
            if pattern in columns_lower:
                col_mapping['qty_col'] = columns_lower[pattern]
                break
        
        for pattern in type_patterns:
            if pattern in columns_lower:
                col_mapping['type_col'] = columns_lower[pattern]
                break
        
        return col_mapping
    
    def _find_style_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find style column in any dataframe"""
        for col in df.columns:
            col_lower = str(col).lower()
            if any(pattern in col_lower for pattern in 
                  ['style', 'product', 'code', 'id', 'sku']):
                return col
        return None
    
    def update_parameter(self, key: str, value):
        """Update a parameter value"""
        if key in self.params:
            self.params[key] = value
            return True
        return False
    
    def get_kpis(self) -> Dict:
        """Calculate KPIs like VBA KPI functions"""
        if self.sales_raw is None:
            return {}
        
        today = self.params['today']
        window_days = 30
        cutoff_date = today - timedelta(days=window_days)
        
        # Total orders (COUNT of rows = units)
        recent_sales = self.sales_raw[
            (self.sales_raw['OrderDate'].dt.date >= cutoff_date) &
            (self.sales_raw['OrderDate'].dt.date <= today)
        ]
        total_orders = len(recent_sales)
        
        # Total GMV
        total_gmv = recent_sales['NetGMV'].sum()
        
        # Return percentage
        if self.returns_raw is not None:
            recent_returns = self.returns_raw[
                (self.returns_raw['ReturnDate'].dt.date >= cutoff_date) &
                (self.returns_raw['ReturnDate'].dt.date <= today)
            ]
            returns_qty = recent_returns['UnitsReturned'].sum()
            return_pct = returns_qty / total_orders if total_orders > 0 else 0
        else:
            return_pct = 0
        
        # Active styles
        active_styles = 0
        if self.master_styles is not None:
            active_styles = len(self.master_styles[
                self.master_styles['Status'] == 'Active'
            ])
        
        return {
            'total_orders_30d': total_orders,
            'total_gmv_30d': total_gmv,
            'return_pct_30d': return_pct,
            'active_styles': active_styles,
            'date_range': f"{cutoff_date} to {today}"
        }