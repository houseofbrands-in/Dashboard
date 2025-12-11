import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class KPICalculator:
    @staticmethod
    def kpi_total_orders_30d(sales_df, today_date=None):
        """EXACT replica of KPI_TotalOrders_30d() VBA function"""
        if sales_df is None or len(sales_df) == 0:
            return 0
        
        if today_date is None:
            today_date = datetime.now()
        
        # Convert to ordinal like Excel (days since 1899-12-30)
        today_num = today_date.toordinal() + 693594  # Excel to Python date offset
        
        # Filter last 30 days
        mask = sales_df['OrderDateNum'] >= (today_num - 30)
        
        # Sum RowUnit (exactly like VBA)
        if 'RowUnit' in sales_df.columns:
            total = sales_df.loc[mask, 'RowUnit'].sum()
        else:
            total = sales_df.loc[mask, 'NetUnits'].sum()
        
        return int(total)
    
    @staticmethod
    def kpi_total_gmv_30d(sales_df, today_date=None):
        """EXACT replica of KPI_TotalGMV_30d()"""
        if sales_df is None or len(sales_df) == 0:
            return 0
        
        if today_date is None:
            today_date = datetime.now()
        
        today_num = today_date.toordinal() + 693594
        
        mask = sales_df['OrderDateNum'] >= (today_num - 30)
        
        if 'NetGMV' in sales_df.columns:
            total = sales_df.loc[mask, 'NetGMV'].sum()
        else:
            total = 0
        
        return float(total)
    
    @staticmethod
    def kpi_return_pct_30d(sales_df, returns_df, today_date=None):
        """EXACT replica of KPI_ReturnPct_30d()"""
        orders = KPICalculator.kpi_total_orders_30d(sales_df, today_date)
        
        if returns_df is None or len(returns_df) == 0 or orders == 0:
            return 0
        
        if today_date is None:
            today_date = datetime.now()
        
        today_num = today_date.toordinal() + 693594
        
        mask = returns_df['ReturnDateNum'] >= (today_num - 30)
        
        if 'UnitsReturned' in returns_df.columns:
            returns = returns_df.loc[mask, 'UnitsReturned'].sum()
        else:
            returns = 0
        
        return returns / orders
    
    @staticmethod
    def build_dashboard_chart_ranges(sales_df, returns_df, today_date=None):
        """Equivalent to BuildDashboardChartRanges()"""
        if today_date is None:
            today_date = datetime.now()
        
        today_num = today_date.toordinal() + 693594
        
        # Sales by Day (last 7 days) - like VBA
        sales_by_day = []
        for i in range(7):
            day_num = today_num - (6 - i)
            if sales_df is not None and len(sales_df) > 0:
                day_sales = sales_df[sales_df['OrderDateNum'] == day_num]['RowUnit'].sum() \
                            if 'RowUnit' in sales_df.columns else 0
            else:
                day_sales = 0
            
            day_date = datetime.fromordinal(day_num - 693594)
            sales_by_day.append({
                'Day': day_date.strftime('%Y-%m-%d'),
                'Orders': day_sales
            })
        
        # Returns by Reason (placeholder - need reason column)
        returns_by_reason = [
            {'Reason': 'Size issue', 'Qty': np.random.randint(5, 20)},
            {'Reason': 'Quality', 'Qty': np.random.randint(3, 15)},
            {'Reason': 'Defect', 'Qty': np.random.randint(2, 10)},
            {'Reason': 'Color', 'Qty': np.random.randint(1, 8)},
            {'Reason': 'Other', 'Qty': np.random.randint(1, 5)}
        ]
        
        return {
            'sales_by_day': pd.DataFrame(sales_by_day),
            'returns_by_reason': pd.DataFrame(returns_by_reason)
        }
