import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import base64
import sys
import os

# Add our custom modules
sys.path.append(os.path.dirname(__file__))

# Import VBA-converted modules
try:
    from core_setup import ProjectMCore
    from data_importers import DataImporters
    from kpi_calculator import KPICalculator
    from master_table import MasterTableBuilder
    # We'll create these next:
    # from watchlist_builder import WatchlistBuilder
    # from returns_analytics import ReturnsAnalytics
    # from forecast_engine import ForecastEngine
    # from ads_recommender import AdsRecommender
except ImportError as e:
    st.error(f"Module import error: {e}")
    # Create dummy classes for initial run
    class ProjectMCore:
        def __init__(self): pass
    class DataImporters:
        @staticmethod
        def import_sales_csv(df): return {'data': df, 'mapping': {}}
    class KPICalculator:
        @staticmethod
    class MasterTableBuilder:
        @staticmethod
        def build_master_table(*args): return pd.DataFrame()

# Initialize session state
if 'project_core' not in st.session_state:
    st.session_state.project_core = ProjectMCore()

if 'sales_data' not in st.session_state:
    st.session_state.sales_data = None
    st.session_state.sales_mapping = None

if 'returns_data' not in st.session_state:
    st.session_state.returns_data = None
    st.session_state.returns_mapping = None

if 'catalog_data' not in st.session_state:
    st.session_state.catalog_data = None

if 'master_table' not in st.session_state:
    st.session_state.master_table = None

if 'params' not in st.session_state:
    st.session_state.params = st.session_state.project_core.seed_params_if_empty()

# Page configuration
st.set_page_config(
    page_title="Myntra Partner Dashboard (VBA Migrated)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS matching your Excel theme
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86C1;
        font-weight: bold;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #2E86C1, #4A90E2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .excel-theme {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
    }
    .kpi-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 10px 0;
    }
    .kpi-label {
        font-size: 1rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2C3E50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #3498DB;
    }
    .data-table {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        background: linear-gradient(90deg, #4CAF50, #2E7D32);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #45A049, #1B5E20);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/5968/5968672.png", width=100)
st.sidebar.title("📊 Project M Dashboard")

menu = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "📁 Data Import", "📊 Master Table", "🚨 Watchlist", 
     "📈 Reports", "🔮 Forecasting", "🎯 Ad Recommendations", "⚙️ Settings"]
)

# ====================
# DASHBOARD PAGE (Main)
# ====================
if menu == "🏠 Dashboard":
    st.markdown('<div class="main-header">📈 Myntra Partner Dashboard</div>', unsafe_allow_html=True)
    
    # Last refresh indicator
    refresh_col1, refresh_col2 = st.columns([3, 1])
    with refresh_col1:
        if st.button("🔄 Refresh Dashboard Data", key="refresh_dash"):
            st.rerun()
    with refresh_col2:
        st.caption(f"Last update: {datetime.now().strftime('%d-%b-%Y %I:%M %p')}")
    
    # KPI Row - Using VBA Functions
    st.markdown("### 📊 Key Performance Indicators (30 Days)")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_orders = KPICalculator.kpi_total_orders_30d(
            st.session_state.sales_data, 
            st.session_state.params.get('today', datetime.now())
        )
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{total_orders:,.0f}</div>
            <div class="kpi-label">Orders</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        return_pct = KPICalculator.kpi_return_pct_30d(
            st.session_state.sales_data,
            st.session_state.returns_data,
            st.session_state.params.get('today', datetime.now())
        )
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{return_pct:.1%}</div>
            <div class="kpi-label">Return %</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_gmv = KPICalculator.kpi_total_gmv_30d(
            st.session_state.sales_data,
            st.session_state.params.get('today', datetime.now())
        )
        gmv_text = f"₹{total_gmv/100000:.1f}L" if total_gmv >= 100000 else f"₹{total_gmv:,.0f}"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{gmv_text}</div>
            <div class="kpi-label">GMV</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Placeholder for ad spend (from your VBA)
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">—</div>
            <div class="kpi-label">Ad Spend</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts Row
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📅 Sales Trend (Last 7 Days)")
        if st.session_state.sales_data is not None:
            chart_data = KPICalculator.build_dashboard_chart_ranges(
                st.session_state.sales_data,
                st.session_state.returns_data
            )
            fig = px.line(chart_data['sales_by_day'], x='Day', y='Orders',
                         title="Daily Orders", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Upload sales data to see charts")
    
    with col2:
        st.markdown("### 🎯 Returns Analysis")
        if st.session_state.returns_data is not None:
            chart_data = KPICalculator.build_dashboard_chart_ranges(
                st.session_state.sales_data,
                st.session_state.returns_data
            )
            fig = px.bar(chart_data['returns_by_reason'], x='Reason', y='Qty',
                        title="Returns by Reason", color='Reason')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Upload returns data to see analysis")
    
    # Quick Actions (like your Excel buttons)
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.info("Refresh Data clicked - Add your logic")
    
    with action_col2:
        if st.button("📈 Build Charts", use_container_width=True):
            st.info("Build Charts clicked - Add your logic")
    
    with action_col3:
        if st.button("🚨 Run Alerts", use_container_width=True):
            st.info("Run Alerts clicked - Will build Watchlist")
    
    with action_col4:
        if st.button("🔮 Forecast", use_container_width=True):
            st.info("Forecast clicked - Will run inventory forecast")

# ====================
# DATA IMPORT PAGE
# ====================
elif menu == "📁 Data Import":
    st.markdown('<div class="main-header">📁 Data Import Center</div>', unsafe_allow_html=True)
    
    # Setup button (like your VBA SetupProjectM)
    if st.button("⚙️ Run SetupProjectM", type="secondary"):
        with st.spinner("Setting up Project M..."):
            result = st.session_state.project_core.setup_project_m()
            st.success(result)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📈 Sales Data")
        sales_file = st.file_uploader("Upload Sales CSV", type=['csv'], key="sales_upload")
        
        if sales_file is not None:
            try:
                sales_df = pd.read_csv(sales_file)
                
                # Show preview
                with st.expander("📋 Preview (First 5 rows)"):
                    st.dataframe(sales_df.head())
                    st.write(f"**Shape:** {sales_df.shape[0]} rows × {sales_df.shape[1]} columns")
                
                # Auto-detect button
                if st.button("🔍 Auto-detect Columns", key="auto_sales"):
                    with st.spinner("Detecting columns (like VBA)..."):
                        try:
                            import_result = DataImporters.import_sales_csv(sales_df)
                            st.session_state.sales_data = import_result['data']
                            st.session_state.sales_mapping = import_result['mapping']
                            
                            # Show mapping
                            st.success("✅ Columns auto-detected successfully!")
                            st.json(import_result['mapping'])
                            
                            # Show sample of normalized data
                            with st.expander("👀 View Normalized Data"):
                                st.dataframe(st.session_state.sales_data[['StyleKey', 'OrderDate', 'NetUnits', 'NetGMV']].head())
                        except Exception as e:
                            st.error(f"Auto-detect failed: {str(e)}")
                
                # Manual mapping option
                with st.expander("🛠️ Manual Column Mapping"):
                    if not sales_df.empty:
                        date_col = st.selectbox("Date Column", sales_df.columns, key="manual_date")
                        style_col = st.selectbox("Style Column", sales_df.columns, key="manual_style")
                        
                        if st.button("Apply Manual Mapping"):
                            # Simple processing for manual mapping
                            sales_df['OrderDate'] = pd.to_datetime(sales_df[date_col], errors='coerce')
                            sales_df['StyleKey'] = sales_df[style_col].astype(str).str.lower().str.strip()
                            sales_df['NetUnits'] = 1  # Default
                            
                            st.session_state.sales_data = sales_df
                            st.success("✅ Manual mapping applied!")
                
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with col2:
        st.subheader("🔄 Returns Data")
        returns_file = st.file_uploader("Upload Returns CSV", type=['csv'], key="returns_upload")
        
        if returns_file is not None:
            try:
                returns_df = pd.read_csv(returns_file)
                
                with st.expander("📋 Preview (First 5 rows)"):
                    st.dataframe(returns_df.head())
                    st.write(f"**Shape:** {returns_df.shape[0]} rows × {returns_df.shape[1]} columns")
                
                if st.button("🔍 Auto-detect Columns", key="auto_returns"):
                    with st.spinner("Detecting columns..."):
                        try:
                            import_result = DataImporters.import_returns_csv(returns_df)
                            st.session_state.returns_data = import_result['data']
                            st.session_state.returns_mapping = import_result['mapping']
                            
                            st.success("✅ Returns columns auto-detected!")
                            st.json(import_result['mapping'])
                        except Exception as e:
                            st.error(f"Auto-detect failed: {str(e)}")
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with col3:
        st.subheader("📚 Catalog Data")
        catalog_file = st.file_uploader("Upload Catalog CSV", type=['csv'], key="catalog_upload")
        
        if catalog_file is not None:
            try:
                catalog_df = pd.read_csv(catalog_file)
                st.session_state.catalog_data = catalog_df
                
                with st.expander("📋 Preview"):
                    st.dataframe(catalog_df.head())
                    st.write(f"**Shape:** {catalog_df.shape[0]} rows × {catalog_df.shape[1]} columns")
                    st.success(f"✅ Catalog loaded: {len(catalog_df)} rows")
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    # Process All Data Button (like your RefreshData VBA)
    st.markdown("---")
    if st.button("🚀 PROCESS ALL DATA (RefreshData)", type="primary", use_container_width=True):
        with st.spinner("Processing all data (VBA RefreshData equivalent)..."):
            # Step 
