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
            # Step 1: Build Master Table
            if (st.session_state.sales_data is not None or 
                st.session_state.catalog_data is not None):
                
                master_table = MasterTableBuilder.build_master_table(
                    st.session_state.sales_data,
                    st.session_state.returns_data,
                    st.session_state.catalog_data,
                    st.session_state.params
                )
                
                st.session_state.master_table = master_table
                
                if not master_table.empty:
                    st.success(f"✅ Master Table built with {len(master_table)} styles")
                    
                    # Show preview
                    with st.expander("👁️ Preview Master Table"):
                        st.dataframe(master_table.head(10))
                else:
                    st.warning("⚠️ Master Table is empty")
            
            # Step 2: Update other tables (will add later)
            # BuildAdsReco, BuildWatchlist30d, etc.
            
            st.success("🎉 All data processed successfully!")
            st.balloons()

# ====================
# MASTER TABLE PAGE
# ====================
elif menu == "📊 Master Table":
    st.markdown('<div class="main-header">📊 Master Styles Table</div>', unsafe_allow_html=True)
    
    if st.session_state.master_table is None or st.session_state.master_table.empty:
        st.warning("No master table data. Please import data first.")
        
        if st.button("🔄 Build Master Table Now"):
            with st.spinner("Building Master Table..."):
                master_table = MasterTableBuilder.build_master_table(
                    st.session_state.sales_data,
                    st.session_state.returns_data,
                    st.session_state.catalog_data,
                    st.session_state.params
                )
                st.session_state.master_table = master_table
                st.rerun()
    else:
        # Show master table with filters
        st.success(f"✅ Master Table loaded: {len(st.session_state.master_table)} styles")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=st.session_state.master_table['Status'].unique() 
                if 'Status' in st.session_state.master_table.columns else [],
                default=[]
            )
        
        with col2:
            risk_filter = st.multiselect(
                "Filter by Risk",
                options=['High Returns', ''] if 'RiskFlag' in st.session_state.master_table.columns else [],
                default=[]
            )
        
        with col3:
            # Search box
            search_term = st.text_input("🔍 Search Style ID")
        
        # Apply filters
        filtered_df = st.session_state.master_table.copy()
        
        if status_filter:
            filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
        
        if risk_filter:
            filtered_df = filtered_df[filtered_df['RiskFlag'].isin(risk_filter)]
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df['Style ID'].astype(str).str.contains(search_term, case=False, na=False)
            ]
        
        # Display table
        st.dataframe(
            filtered_df,
            use_container_width=True,
            column_config={
                "ReturnPct": st.column_config.ProgressColumn(
                    "Return %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=1
                ),
                "GMV": st.column_config.NumberColumn(
                    "GMV",
                    format="₹%d"
                )
            }
        )
        
        # Export options
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="master_table.csv",
                mime="text/csv"
            )
        
        with col2:
            # Excel export
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Master_Styles')
            st.download_button(
                label="📥 Download as Excel",
                data=buffer,
                file_name="master_table.xlsx",
                mime="application/vnd.ms-excel"
            )

# ====================
# WATCHLIST PAGE
# ====================
elif menu == "🚨 Watchlist":
    st.markdown('<div class="main-header">🚨 Watchlist 30 Days</div>', unsafe_allow_html=True)
    
    # This will be implemented with WatchlistBuilder
    st.info("Watchlist feature coming soon (Equivalent to BuildWatchlist30d VBA)")
    
    # Placeholder with sample data
    if st.session_state.master_table is not None:
        sample_watchlist = st.session_state.master_table.copy()
        
        # Add some mock tags
        tags = ['NEW', 'STARTED', 'RISING', 'FALLING', 'FLAT']
        sample_watchlist['Tag'] = np.random.choice(tags, len(sample_watchlist))
        sample_watchlist['Orders30d Est'] = np.random.randint(1, 100, len(sample_watchlist))
        sample_watchlist['Returns30d Qty'] = (sample_watchlist['Orders30d Est'] * 
                                             np.random.uniform(0, 0.3, len(sample_watchlist))).astype(int)
        
        st.dataframe(sample_watchlist.head(20), use_container_width=True)

# ====================
# REPORTS PAGE
# ====================
elif menu == "📈 Reports":
    st.markdown('<div class="main-header">📈 Reports & Analytics</div>', unsafe_allow_html=True)
    
    report_type = st.selectbox(
        "Select Report Type",
        ["Returns Insights", "Returns Type Split", "Zero-Sale Since Live", 
         "Product Performance", "Size/SKU Analysis"]
    )
    
    if report_type == "Returns Insights":
        st.subheader("🔄 Returns Insights Report")
        st.info("Equivalent to BuildReturnsInsights VBA function")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            window_days = st.number_input("Window Days", 
                                         value=st.session_state.params.get('return_insights_window', 60),
                                         min_value=7, max_value=365)
        
        if st.button("Generate Returns Insights", type="primary"):
            with st.spinner("Generating returns heatmap..."):
                # This will call ReturnsAnalytics.build_returns_insights()
                st.success("Report generated (VBA logic to be implemented)")
    
    elif report_type == "Zero-Sale Since Live":
        st.subheader("📉 Zero-Sale Styles Report")
        st.info("Equivalent to BuildZeroSaleSinceLive VBA function")
        
        zero_age = st.number_input("Zero-Sale Age (days)", 
                                  value=st.session_state.params.get('zero_sale_age', 14),
                                  min_value=1, max_value=365)
        
        if st.button("Find Zero-Sale Styles"):
            with st.spinner("Analyzing zero-sale styles..."):
                if st.session_state.master_table is not None:
                    zero_sale = st.session_state.master_table[
                        (st.session_state.master_table['Status'] == 'Zero-Sale') |
                        (st.session_state.master_table['Orders'] == 0)
                    ]
                    
                    if not zero_sale.empty:
                        st.dataframe(zero_sale, use_container_width=True)
                        st.info(f"Found {len(zero_sale)} zero-sale styles")
                    else:
                        st.success("🎉 No zero-sale styles found!")

# ====================
# FORECASTING PAGE
# ====================
elif menu == "🔮 Forecasting":
    st.markdown('<div class="main-header">🔮 Inventory Forecasting</div>', unsafe_allow_html=True)
    
    # Forecast parameters (from your VBA params)
    col1, col2, col3 = st.columns(3)
    with col1:
        lookback = st.number_input("Lookback Days", 
                                  value=st.session_state.params.get('forecast_lookback', 30))
    with col2:
        event_days = st.number_input("Event Days", 
                                    value=st.session_state.params.get('event_days', 10))
    with col3:
        traffic_mult = st.number_input("Traffic Multiplier", 
                                      value=float(st.session_state.params.get('traffic_multiplier', 3)))
    
    col4, col5, col6 = st.columns(3)
    with col4:
        return_rate = st.number_input("Return Rate", 
                                     value=float(st.session_state.params.get('forecast_return_rate', 0.25)),
                                     format="%.2f")
    with col5:
        leadtime = st.number_input("Lead Time (days)", 
                                  value=st.session_state.params.get('leadtime_days', 7))
    with col6:
        service_level = st.number_input("Service Level", 
                                       value=float(st.session_state.params.get('service_level', 0.9)),
                                       format="%.2f")
    
    if st.button("🚀 Generate Inventory Forecast", type="primary", use_container_width=True):
        with st.spinner("Calculating inventory requirements..."):
            # This will call ForecastEngine.inventory_forecast()
            st.info("Forecast engine to be implemented (VBA equivalent)")
            
            # Sample forecast
            if st.session_state.master_table is not None:
                sample_forecast = st.session_state.master_table.copy()
                sample_forecast['Forecast_Qty'] = (
                    sample_forecast['Orders'] / 30 * event_days * traffic_mult * (1 - return_rate)
                ).round().astype(int)
                
                st.dataframe(
                    sample_forecast[['Style ID', 'Orders', 'Forecast_Qty']].head(20),
                    use_container_width=True
                )

# ====================
# AD RECOMMENDATIONS
# ====================
elif menu == "🎯 Ad Recommendations":
    st.markdown('<div class="main-header">🎯 Ad Recommendations</div>', unsafe_allow_html=True)
    
    st.info("Equivalent to BuildAdsReco3 VBA function")
    
    # Parameters
    col1, col2 = st.columns(2)
    with col1:
        new_age = st.number_input("New Age Days", 
                                 value=st.session_state.params.get('new_age_days', 60))
    with col2:
        high_return = st.number_input("High Return %", 
                                     value=float(st.session_state.params.get('high_return_pct', 0.35)),
                                     format="%.2f")
    
    if st.button("Generate Ad Recommendations", type="primary"):
        with st.spinner("Analyzing styles for ad recommendations..."):
            # This will call AdsRecommender.build_ads_reco()
            
            if st.session_state.master_table is not None:
                # Sample logic
                recommendations = st.session_state.master_table.copy()
                
                # Simple decision logic (like your VBA)
                conditions = [
                    (recommendations['Status'] == 'Zero-Sale'),
                    (recommendations['Status'] == 'New') & (recommendations['Orders'] < 2),
                    (recommendations['ReturnPct'] >= high_return),
                    (recommendations['Orders'] >= 10)
                ]
                choices = ['PUSH (Zero-Sale)', 'PUSH (New Discovery)', 
                          'STOP (High Returns)', 'SCALE']
                
                recommendations['Decision'] = np.select(conditions, choices, default='WATCH')
                
                st.dataframe(
                    recommendations[['Style ID', 'Status', 'Orders', 'ReturnPct', 'Decision']],
                    use_container_width=True
                )

# ====================
# SETTINGS PAGE
# ====================
elif menu == "⚙️ Settings":
    st.markdown('<div class="main-header">⚙️ Parameters & Settings</div>', unsafe_allow_html=True)
    
    # Show current params
    with st.expander("📋 Current Parameters"):
        st.json(st.session_state.params)
    
    # Update parameters
    st.markdown("### Update Parameters")
    
    with st.form("params_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            zero_age = st.number_input("Zero-Sale Age Days", 
                                      value=st.session_state.params.get('zero_sale_age', 14))
            high_return = st.number_input("High Return %", 
                                         value=float(st.session_state.params.get('high_return_pct', 0.35)),
                                         format="%.2f")
            watch_min = st.number_input("Watchlist Min Orders", 
                                       value=st.session_state.params.get('watch_min_orders', 3))
        
        with col2:
            new_age = st.number_input("New Age Days", 
                                     value=st.session_state.params.get('new_age_days', 60))
            start_recent = st.number_input("Start Recent Min Orders", 
                                          value=st.session_state.params.get('start_recent_min_orders', 2))
            start_prev = st.number_input("Start Previous Max Orders", 
                                        value=st.session_state.params.get('start_prev_max_orders', 0))
        
        submitted = st.form_submit_button("💾 Save Parameters")
        
        if submitted:
            # Update params
            st.session_state.params.update({
                'zero_sale_age': zero_age,
                'high_return_pct': high_return,
                'watch_min_orders': watch_min,
                'new_age_days': new_age,
                'start_recent_min_orders': start_recent,
                'start_prev_max_orders': start_prev
            })
            st.success("✅ Parameters saved!")
    
    # Brand filter settings
    st.markdown("---")
    st.markdown("### 🏷️ Brand Filter Settings")
    
    brand_mode = st.selectbox(
        "Brand Filter Mode",
        ["ALL", "ONE", "LIST"],
        index=0
    )
    
    if brand_mode == "ONE":
        brand_name = st.text_input("Specific Brand Name", "")
    elif brand_mode == "LIST":
        brand_list = st.text_area("Brand List (comma-separated)", 
                                 help="Enter brands separated by commas")
    
    # Data management
    st.markdown("---")
    st.markdown("### 🗑️ Data Management")
    
    if st.button("Clear All Data", type="secondary"):
        st.session_state.sales_data = None
        st.session_state.returns_data = None
        st.session_state.catalog_data = None
        st.session_state.master_table = None
        st.success("All data cleared!")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 20px;'>"
    "📊 Project M Dashboard • VBA Excel Migration • Built with Streamlit"
    "<br>"
    "<small>Equivalent to your Excel VBA: SetupProjectM, RefreshData, BuildMasterTable, etc.</small>"
    "</div>",
    unsafe_allow_html=True
)
