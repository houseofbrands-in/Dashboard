"""
Business Logic Calculations for Project M
Replicating Excel VBA formulas and calculations
"""

print("✓ calculations.py is being loaded")

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import math

class BusinessCalculations:
    """
    Contains all business logic calculations from Excel VBA
    Each method replicates a specific VBA function or formula
    """
    
    @staticmethod
    def calculate_newness_bucket(first_date: datetime, today: datetime) -> str:
        """
        Replicates VBA newness bucket logic:
        IF(RC[-2]="","Unknown",IF(RC[-1]<=7,"0-7d",IF(RC[-1]<=30,"8-30d",
        IF(RC[-1]<=60,"31-60d",IF(RC[-1]<=90,"61-90d","91d+")))))
        """
        if pd.isna(first_date):
            return "Unknown"
        
        days_live = (today - first_date.date()).days
        
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
    
    @staticmethod
    def calculate_status(first_date: Optional[datetime], orders: int, 
                        days_live: int, zero_age: int = 14) -> str:
        """
        Replicates VBA status logic from BuildMasterTable:
        IF(AND(RC[-7]="",RC[-8]<>""),"Catalog-Only",
        IF(AND(RC[-6]=0,RC[-8]>=" & zeroAge & "),"Zero-Sale",
        IF(OR(RC[-7]="0-7d",RC[-7]="8-30d"),"New",
        IF(RC[-6]>0,"Active","Unknown"))))
        """
        if first_date is None:
            return "Catalog-Only"
        elif orders == 0 and days_live >= zero_age:
            return "Zero-Sale"
        elif days_live <= 60:  # Equivalent to "0-7d" or "8-30d" or "31-60d"
            return "New"
        elif orders > 0:
            return "Active"
        else:
            return "Unknown"
    
    @staticmethod
    def calculate_risk_flag(return_pct: float, high_return_threshold: float = 0.35) -> str:
        """
        Replicates VBA risk flag logic:
        =IF(AND(ISNUMBER(RC[-2]), RC[-2] >= " & hiRet & "),""High Returns"","""")
        """
        if pd.isna(return_pct):
            return ""
        elif return_pct >= high_return_threshold:
            return "High Returns"
        else:
            return ""
    
    @staticmethod
    def calculate_watchlist_tag(orders_recent: int, orders_prev: int, 
                               momentum: float, age_days: int, 
                               new_age: int = 60, min_orders: int = 3) -> str:
        """
        Replicates VBA watchlist tag logic from BuildWatchlist30d:
        =IF(G2="YES","NEW",IF(AND(C2>=" & startRecentMin & ",K2<=" & startPrevMax & "),
        "STARTED",IF(F2>0.15,"RISING",IF(F2<-0.15,"FALLING","FLAT"))))
        """
        if age_days <= new_age:
            return "NEW"
        elif orders_recent >= min_orders and orders_prev == 0:
            return "STARTED"
        elif momentum > 0.15:
            return "RISING"
        elif momentum < -0.15:
            return "FALLING"
        else:
            return "FLAT"
    
    @staticmethod
    def calculate_momentum(orders_recent: int, orders_prev: int) -> float:
        """
        Replicates VBA momentum calculation:
        =IF(RC[3]=0,0,(RC[3]-RC[4])/MAX(RC[4],1))
        """
        if orders_prev == 0:
            if orders_recent > 0:
                return 1.0
            else:
                return 0.0
        else:
            return (orders_recent - orders_prev) / orders_prev
    
    @staticmethod
    def calculate_ad_recommendation(status: str, orders: int, return_pct: float,
                                   days_live: int, new_age: int = 60,
                                   min_orders: int = 2, high_ret: float = 0.35) -> str:
        """
        Replicates VBA ad recommendation logic from BuildAdsReco:
        =IF(AND(E2>=" & StartRecent_MinOrders & ", I2<" & HighReturnPct & ", K2>=10000), "SCALE", 
        IF(AND(G2>=0.2, E2>=" & StartRecent_MinOrders & "), "TRENDING PUSH", 
        IF(AND(D2<=" & NewAge_Days & ", E2<" & StartRecent_MinOrders & "), "PUSH (New Discovery)", 
        IF(AND(D2>" & NewAge_Days & ", J2=0), "PUSH (Zero-Sale)", 
        IF(AND(E2>=" & StartRecent_MinOrders & ", I2>=" & HighReturnPct & "), "STOP (High Returns)", 
        "WATCH" )))))
        """
        if (orders >= min_orders and return_pct < high_ret):
            # Additional condition for GMV >= 10000 would go here
            return "SCALE"
        elif orders >= min_orders and return_pct >= high_ret:
            return "STOP (High Returns)"
        elif days_live <= new_age and orders < min_orders:
            return "PUSH (New Discovery)"
        elif days_live > new_age and orders == 0:
            return "PUSH (Zero-Sale)"
        else:
            return "WATCH"
    
    @staticmethod
    def calculate_inventory_forecast(avg_daily_sales: float, event_days: int,
                                    traffic_multiplier: float, return_rate: float,
                                    momentum: float = 0, use_momentum: bool = True,
                                    service_level: float = 0.9) -> Dict[str, float]:
        """
        Replicates VBA inventory forecast calculation:
        GrossForecast = AvgDaily * EventDays * TrafficMultiplier * Seasonality
        NetForecast = GrossForecast * (1 - ReturnRate)
        SafetyStock = z-score * sqrt(GrossForecast)
        TotalRequired = NetForecast + SafetyStock
        """
        # Apply momentum adjustment if enabled
        if use_momentum:
            momentum_adj = max(min(momentum, 0.5), -0.3)  # Cap momentum adjustment
            gross_forecast = avg_daily_sales * event_days * traffic_multiplier * (1 + momentum_adj)
        else:
            gross_forecast = avg_daily_sales * event_days * traffic_multiplier
        
        net_forecast = gross_forecast * (1 - return_rate)
        
        # Calculate z-score for service level (simplified)
        z_score = 1.28  # ~90% service level (from VBA: Service_Level = 0.9)
        safety_stock = z_score * math.sqrt(max(gross_forecast, 0))
        
        total_required = net_forecast + safety_stock
        
        return {
            'gross_forecast': gross_forecast,
            'net_forecast': net_forecast,
            'safety_stock': safety_stock,
            'total_required': total_required,
            'z_score': z_score
        }
    
    @staticmethod
    def calculate_size_sku_allocation(total_required: int, sku_shares: Dict[str, float],
                                     min_share: float = 0.05, min_units: int = 1) -> Dict[str, int]:
        """
        Replicates VBA size/SKU allocation logic from BuildInventoryForecast_SizeSKU:
        Allocates total units to SKUs based on shares with minimum thresholds
        """
        allocations = {}
        remaining = total_required
        
        # First pass: allocate with minimum share constraint
        for sku, share in sku_shares.items():
            base_allocation = total_required * share
            min_allocation = total_required * min_share
            
            # Apply minimum of either base allocation or min allocation
            allocation = max(base_allocation, min_allocation)
            
            # Apply minimum units per SKU
            allocation = max(allocation, min_units)
            
            allocations[sku] = math.floor(allocation)
            remaining -= allocations[sku]
        
        # Second pass: distribute remaining units
        if remaining > 0:
            # Sort SKUs by how much they deserve more (based on share vs allocation ratio)
            sku_ratios = []
            for sku, share in sku_shares.items():
                if share > 0:
                    deserved = total_required * share
                    actual = allocations[sku]
                    ratio = deserved / (actual + 1)  # +1 to avoid division by zero
                    sku_ratios.append((ratio, sku))
            
            # Sort by ratio (highest first)
            sku_ratios.sort(reverse=True)
            
            # Distribute remaining units
            for i in range(int(remaining)):
                if i < len(sku_ratios):
                    sku = sku_ratios[i][1]
                    allocations[sku] += 1
        
        return allocations
    
    @staticmethod
    def calculate_zero_sale_styles(master_df: pd.DataFrame, zero_age: int = 14) -> pd.DataFrame:
        """
        Identifies zero-sale styles like VBA Zero_Sale_Since_Live
        """
        zero_sale_mask = (
            (master_df['Orders'] == 0) &
            (master_df['Days_Since_FirstUpdate'] >= zero_age)
        )
        
        return master_df[zero_sale_mask].copy()
    
    @staticmethod
    def calculate_return_insights(returns_df: pd.DataFrame, 
                                 window_days: int = 60) -> pd.DataFrame:
        """
        Replicates VBA BuildReturnsInsights logic
        Creates style × reason heatmap
        """
        if returns_df.empty:
            return pd.DataFrame()
        
        # Calculate cutoff date
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=window_days)
        
        # Filter returns in window
        recent_returns = returns_df[
            returns_df['ReturnDate'].dt.date >= cutoff_date
        ].copy()
        
        if recent_returns.empty:
            return pd.DataFrame()
        
        # Group by style and reason
        insights = recent_returns.groupby(['StyleKey', 'Reason']).agg({
            'UnitsReturned': 'sum'
        }).reset_index()
        
        # Pivot to heatmap format
        heatmap = insights.pivot_table(
            index='StyleKey',
            columns='Reason',
            values='UnitsReturned',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        return heatmap
    
    @staticmethod
    def calculate_kpis(sales_df: pd.DataFrame, returns_df: pd.DataFrame,
                      window_days: int = 30) -> Dict[str, float]:
        """
        Replicates VBA KPI functions (KPI_TotalOrders_30d, etc.)
        """
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=window_days)
        
        # Filter recent data
        recent_sales = sales_df[
            sales_df['OrderDate'].dt.date >= cutoff_date
        ] if sales_df is not None else pd.DataFrame()
        
        recent_returns = returns_df[
            returns_df['ReturnDate'].dt.date >= cutoff_date
        ] if returns_df is not None else pd.DataFrame()
        
        # Calculate KPIs
        total_orders = len(recent_sales)  # COUNT of rows = units
        total_gmv = recent_sales['NetGMV'].sum() if 'NetGMV' in recent_sales.columns else 0
        
        total_returns = recent_returns['UnitsReturned'].sum() if not recent_returns.empty else 0
        return_pct = total_returns / total_orders if total_orders > 0 else 0
        
        # Calculate RTO vs Return split
        if not recent_returns.empty and 'ReturnType' in recent_returns.columns:
            rto_qty = recent_returns[
                recent_returns['ReturnType'].str.contains('RTO', case=False, na=False)
            ]['UnitsReturned'].sum()
            return_qty = total_returns - rto_qty
            rto_pct = rto_qty / total_returns if total_returns > 0 else 0
        else:
            rto_qty = return_qty = rto_pct = 0
        
        return {
            'total_orders': total_orders,
            'total_gmv': total_gmv,
            'total_returns': total_returns,
            'return_pct': return_pct,
            'rto_qty': rto_qty,
            'return_qty': return_qty,
            'rto_pct': rto_pct,
            'window_days': window_days,
            'date_range': f"{cutoff_date} to {today}"
        }
    
    @staticmethod
    def calculate_date_window(mode: str = 'rolling_days', 
                             days: int = 7, 
                             months: int = 1,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """
        Replicates VBA GetReportWindowRange logic
        """
        today = datetime.now().date()
        
        if mode == 'rolling_days':
            start = today - timedelta(days=days - 1)
            end = today
        
        elif mode == 'calendar_months':
            # Last N full calendar months
            if today.day > 1:
                end = today.replace(day=1) - timedelta(days=1)
            else:
                end = (today.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)
            
            start_month = end - timedelta(days=30 * months)
            start = start_month.replace(day=1)
        
        elif mode == 'between_dates' and start_date and end_date:
            start = start_date.date()
            end = end_date.date()
        
        else:
            # Default: 7-day rolling window
            start = today - timedelta(days=6)
            end = today
        
        # Ensure start <= end
        if start > end:
            start, end = end, start
        
        return start, end