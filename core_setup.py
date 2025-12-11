import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================================================
# CORE SETUP (Equivalent to your VBA SetupProjectM)
# ============================================================================

class ProjectMCore:
    def __init__(self):
        # Initialize default sheets/parameters like VBA
        self.sheets = {
            'params': None,
            'sales_raw': None,
            'returns_raw': None,
            'catalog_raw': None,
            'catalog_clean': None,
            'master': None,
            'ads_reco': None,
            'watchlist': None,
            'returns_insights': None
        }
        
        # Default parameters (from your VBA constants)
        self.defaults = {
            'sales_mask': '*sales*.csv',
            'returns_mask': '*return*.csv',
            'catalog_mask': '*listing*.csv,*listings*.csv,*MDirect_Listings*.csv',
            'zero_age_days': 14,
            'high_return_pct': 0.35,
            'watch_min_orders': 3,
            'new_age_days': 60,
            'start_recent_min_orders': 2,
            'start_prev_max_orders': 0,
            'forecast_lookback': 30,
            'event_days': 10,
            'traffic_multiplier': 3,
            'forecast_return_rate': 0.25,
            'leadtime_days': 7,
            'service_level': 0.9,
            'seasonality_boost': 1,
            'use_momentum_adjust': True
        }
        
        self.params = {}
    
    def ensure_core_sheets(self):
        """Equivalent to EnsureCoreSheets() in VBA"""
        # In web app, we'll create DataFrames instead of Excel sheets
        for sheet_name in self.sheets.keys():
            if self.sheets[sheet_name] is None:
                self.sheets[sheet_name] = pd.DataFrame()
        return True
    
    def seed_params_if_empty(self):
        """Equivalent to SeedParamsIfEmpty()"""
        # Initialize parameters with defaults
        for key, value in self.defaults.items():
            if key not in self.params:
                self.params[key] = value
        
        # Add today's date
        self.params['today'] = datetime.now().date()
        
        return self.params
    
    def setup_project_m(self):
        """Equivalent to SetupProjectM()"""
        self.ensure_core_sheets()
        self.seed_params_if_empty()
        
        # Initialize empty DataFrames for raw data
        self.sheets['sales_raw'] = pd.DataFrame(columns=['Awaiting Sales import...'])
        self.sheets['returns_raw'] = pd.DataFrame(columns=['Awaiting Returns import...'])
        self.sheets['catalog_raw'] = pd.DataFrame(columns=['Awaiting Catalog import...'])
        
        return "✅ Setup complete. Upload your data files."
