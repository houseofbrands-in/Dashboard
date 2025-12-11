"""
Project M - Myntra Analytics Dashboard
Streamlit Web App replacing Excel VBA
"""

# Update imports section
from utils.data_processor import ProjectMProcessor
from utils.calculations import BusinessCalculations
from utils.file_handler import FileHandler

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import base64
from typing import Optional
import sys
import traceback

try:
    from utils.calculations import BusinessCalculations
    print("✓ Successfully imported BusinessCalculations")
except SyntaxError as e:
    print(f"✗ SyntaxError: {e}")
    print(f"File: {e.filename}, Line: {e.lineno}")
    traceback.print_exc()
    sys.exit(1)
except ImportError as e:
    print(f"✗ ImportError: {e}")
    traceback.print_exc()
    sys.exit(1)

# Import our VBA processor
from utils.data_processor import ProjectMProcessor

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Project M - Myntra Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    /* Main header */
    .main-header {
        font-size: 2.5rem;
        color: #2E86C1;
        font-weight: bold;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #2E86C1, #4A90E2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* KPI cards */
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
    
    /* Status badges */
    .status-active { background-color: #10B981; color: white; }
    .status-new { background-color: #3B82F6; color: white; }
    .status-zero { background-color: #F59E0B; color: white; }
    .status-catalog { background-color: #6B7280; color: white; }
    
    /* Risk badges */
    .risk-high { background-color: #EF4444; color: white; }
    .risk-none { background-color: #D1D5DB; color: #374151; }
    
    /* Data table styling */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        color: #2C3E50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #3498DB;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================
if 'processor' not in st.session_state:
    st.session_state.processor = ProjectMProcessor()

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Dashboard'

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def format_number(num):
    """Format numbers with Indian numbering system"""
    if pd.isna(num):
        return "0"
    num = float(num)
    if num >= 10000000:
        return f"₹{num/10000000:.2f} Cr"
    elif num >= 100000:
        return f"₹{num/100000:.2f} L"
    elif num >= 1000:
        return f"₹{num/1000:.1f}K"
    else:
        return f"₹{num:,.0f}"

def create_download_link(df, filename):
    """Create a download link for dataframe"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Download CSV</a>'
    return href

def show_status_badge(status):
    """Show styled status badge"""
    color_map = {
        'Active': 'status-active',
        'New': 'status-new',
        'Zero-Sale': 'status-zero',
        'Catalog-Only': 'status-catalog'
    }
    color_class = color_map.get(status, 'status-catalog')
    return f'<span class="{color_class} badge">{status}</span>'

def show_risk_badge(risk_flag):
    """Show styled risk badge"""
    if risk_flag:
        return f'<span class="risk-high badge">⚠️ {risk_flag}</span>'
    return '<span class="risk-none badge">—</span>'

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/5968/5968672.png", width=100)
    st.title("📊 Project M")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "📁 Data Import", "📊 Master Table", "🚨 Watchlist", 
         "📈 Returns Analysis", "🔮 Inventory Forecast", "⚙️ Settings"],
        key="nav_radio"
    )
    
    # Extract page name
    page_name = page.split(" ")[-1]
    
    # Data status
    st.markdown("---")
    st.subheader("Data Status")
    
    if st.session_state.processor.sales_raw is not None:
        sales_count = len(st.session_state.processor.sales_raw)
        st.success(f"✅ Sales: {sales_count:,} rows")
    else:
        st.warning("⚠️ No sales data")
    
    if st.session_state.processor.returns_raw is not None:
        returns_count = len(st.session_state.processor.returns_raw)
        st.success(f"✅ Returns: {returns_count:,} rows")
    else:
        st.warning("⚠️ No returns data")
    
    if st.session_state.processor.master_styles is not None:
        styles_count = len(st.session_state.processor.master_styles)
        st.success(f"✅ Styles: {styles_count:,}")
    else:
        st.info("ℹ️ Master table not built")
    
    # Last refresh
    if st.session_state.last_refresh:
        st.caption(f"Last refresh: {st.session_state.last_refresh}")
    
    # Quick actions
    st.markdown("---")
    st.subheader("Quick Actions")
    
    if st.button("🔄 Refresh All Data", use_container_width=True):
        st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.rerun()
    
    if st.button("📊 Build All Reports", use_container_width=True):
        with st.spinner("Building all reports..."):
            # Build all tables
            st.session_state.processor.build_master_table()
            st.session_state.processor.build_watchlist_30d()
            st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success("All reports built!")
        st.rerun()

# ============================================================================
# DASHBOARD PAGE
# ============================================================================
if page_name == "Dashboard":
    st.markdown('<div class="main-header">📈 Project M Dashboard</div>', unsafe_allow_html=True)
    
    # Refresh button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.caption("Myntra Partner Analytics Dashboard")
    with col2:
        if st.button("🔄 Refresh KPIs"):
            st.rerun()
    
    # KPIs
    st.markdown("### 📊 Key Performance Indicators (30 Days)")
    
    kpis = st.session_state.processor.get_kpis()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        orders = kpis.get('total_orders_30d', 0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{orders:,}</div>
            <div class="kpi-label">Total Orders</div>
            <div style="font-size: 0.8rem; opacity: 0.8;">Count of sales rows</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        gmv = kpis.get('total_gmv_30d', 0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{format_number(gmv)}</div>
            <div class="kpi-label">Total GMV</div>
            <div style="font-size: 0.8rem; opacity: 0.8;">Gross Merchandise Value</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        return_pct = kpis.get('return_pct_30d', 0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{return_pct:.1%}</div>
            <div class="kpi-label">Return %</div>
            <div style="font-size: 0.8rem; opacity: 0.8;">Returns ÷ Orders</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        active_styles = kpis.get('active_styles', 0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{active_styles:,}</div>
            <div class="kpi-label">Active Styles</div>
            <div style="font-size: 0.8rem; opacity: 0.8;">With recent sales</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts Section
    st.markdown("---")
    
    if st.session_state.processor.sales_raw is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📅 Daily Sales Trend")
            
            # Prepare daily sales data
            sales_df = st.session_state.processor.sales_raw.copy()
            sales_df['Date'] = sales_df['OrderDate'].dt.date
            
            # Last 30 days
            cutoff_date = datetime.now().date() - timedelta(days=30)
            recent_sales = sales_df[sales_df['Date'] >= cutoff_date]
            
            if not recent_sales.empty:
                daily_sales = recent_sales.groupby('Date').size().reset_index()
                daily_sales.columns = ['Date', 'Orders']
                daily_sales = daily_sales.sort_values('Date')
                
                fig = px.line(daily_sales, x='Date', y='Orders',
                             title="Orders per Day (Last 30 Days)",
                             markers=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sales data in last 30 days")
        
        with col2:
            st.markdown("### 🏷️ Style Status Distribution")
            
            if st.session_state.processor.master_styles is not None:
                status_counts = st.session_state.processor.master_styles['Status'].value_counts()
                
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Style Status Breakdown",
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Build Master Table to see status distribution")
    
    # Top Performers
    st.markdown("---")
    st.markdown("### 🏆 Top Performing Styles (Last 30 Days)")
    
    if st.session_state.processor.master_styles is not None:
        top_styles = st.session_state.processor.master_styles.sort_values(
            'Orders', ascending=False
        ).head(10)
        
        # Display as metrics grid
        cols = st.columns(5)
        for idx, (_, row) in enumerate(top_styles.head(5).iterrows()):
            with cols[idx % 5]:
                st.metric(
                    label=row['Style ID'][:15] + ("..." if len(row['Style ID']) > 15 else ""),
                    value=f"{row['Orders']:,}",
                    delta=f"₹{format_number(row['GMV'])}"
                )
        
        # Show full table
        with st.expander("View All Top Styles"):
            display_cols = ['Style ID', 'Orders', 'GMV', 'ReturnPct', 'Status', 'RiskFlag']
            st.dataframe(
                top_styles[display_cols],
                column_config={
                    "GMV": st.column_config.NumberColumn(format="₹%d"),
                    "ReturnPct": st.column_config.ProgressColumn(format="%.1f%%")
                }
            )
    else:
        st.info("Import data and build Master Table to see top performers")

# ============================================================================
# DATA IMPORT PAGE
# ============================================================================
elif page_name == "Import":
    st.markdown('<div class="main-header">📁 Data Import Center</div>', unsafe_allow_html=True)
    
    # Setup instructions
    with st.expander("📋 Import Instructions", expanded=True):
        st.markdown("""
        ### How to import your Excel data:
        
        1. **Export from Excel**:
           - Go to each sheet (Sales_Raw, Returns_Raw, Catalog_Raw)
           - Click File → Save As → CSV (Comma delimited)
        
        2. **Upload here**:
           - Sales CSV: Must contain Date and Style columns
           - Returns CSV: Must contain Date, Style, and Quantity
           - Catalog CSV: Optional, for style metadata
        
        3. **Auto-detection**:
           - System will auto-detect columns (like VBA)
           - Style IDs are normalized automatically
        
        ### Important Notes:
        - **Sales data has no quantity column**: Each row = 1 unit
        - **Style IDs are normalized**: Converted to lowercase, trimmed
        - **Dates are parsed automatically**: Supports Excel date formats
        """)
    
    # File upload sections
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📈 Sales Data")
        sales_file = st.file_uploader(
            "Upload Sales CSV",
            type=['csv'],
            key="sales_uploader",
            help="Myntra sales export (each row = 1 unit)"
        )
        
        if sales_file is not None:
            try:
                df = pd.read_csv(sales_file)
                
                with st.expander("📋 Preview (First 10 rows)"):
                    st.dataframe(df.head(10))
                    st.write(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
                
                if st.button("🚀 Import Sales Data", key="import_sales", use_container_width=True):
                    with st.spinner("Importing sales data (VBA equivalent)..."):
                        result = st.session_state.processor.import_sales_csv(df, sales_file.name)
                        
                        if result['success']:
                            st.success(f"✅ Successfully imported {result['rows_processed']:,} rows")
                            st.json(result['columns_mapped'])
                            
                            # Show style ID sample
                            if 'StyleKey' in st.session_state.processor.sales_raw.columns:
                                sample_ids = st.session_state.processor.sales_raw['StyleKey'].head(5).tolist()
                                st.write("**Sample normalized Style IDs:**", sample_ids)
                        else:
                            st.error(f"Import failed: {result['errors']}")
                    
                    st.session_state.data_loaded = True
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with col2:
        st.subheader("🔄 Returns Data")
        returns_file = st.file_uploader(
            "Upload Returns CSV",
            type=['csv'],
            key="returns_uploader",
            help="Myntra returns export (has quantity column)"
        )
        
        if returns_file is not None:
            try:
                df = pd.read_csv(returns_file)
                
                with st.expander("📋 Preview (First 10 rows)"):
                    st.dataframe(df.head(10))
                
                if st.button("🚀 Import Returns Data", key="import_returns", use_container_width=True):
                    with st.spinner("Importing returns data..."):
                        result = st.session_state.processor.import_returns_csv(df)
                        
                        if result['success']:
                            st.success(f"✅ Successfully imported {result['rows_processed']:,} rows")
                            st.json(result['columns_mapped'])
                        else:
                            st.error(f"Import failed: {result['errors']}")
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with col3:
        st.subheader("📚 Catalog Data")
        catalog_file = st.file_uploader(
            "Upload Catalog CSV",
            type=['csv'],
            key="catalog_uploader",
            help="Optional: Style catalog/metadata"
        )
        
        if catalog_file is not None:
            try:
                df = pd.read_csv(catalog_file)
                st.session_state.processor.catalog_raw = df
                st.success(f"✅ Catalog loaded: {len(df):,} rows")
                
                with st.expander("📋 Preview"):
                    st.dataframe(df.head(10))
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    # Process All Data Button (VBA RefreshData equivalent)
    st.markdown("---")
    st.markdown("### 🚀 Process All Data")
    
    if st.button("🔄 PROCESS ALL DATA (Excel VBA Equivalent)", type="primary", use_container_width=True):
        with st.spinner("Processing all data (VBA RefreshData)..."):
            # Step 1: Build Master Table
            if (st.session_state.processor.sales_raw is not None or 
                st.session_state.processor.catalog_raw is not None):
                
                master_table = st.session_state.processor.build_master_table()
                
                if not master_table.empty:
                    st.success(f"✅ Master Table built: {len(master_table):,} styles")
                else:
                    st.warning("⚠️ Master Table is empty")
            
            # Step 2: Build other tables
            if st.session_state.processor.sales_raw is not None:
                watchlist = st.session_state.processor.build_watchlist_30d()
                if not watchlist.empty:
                    st.success(f"✅ Watchlist built: {len(watchlist):,} styles")
            
            st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success("🎉 All data processed successfully!")
            st.balloons()

# ============================================================================
# MASTER TABLE PAGE
# ============================================================================
elif page_name == "Table":
    st.markdown('<div class="main-header">📊 Master Styles Table</div>', unsafe_allow_html=True)
    
    if st.session_state.processor.master_styles is None:
        st.warning("Master table not built. Please import data first.")
        
        if st.button("🔄 Build Master Table Now"):
            with st.spinner("Building Master Table (VBA equivalent)..."):
                master_table = st.session_state.processor.build_master_table()
                if not master_table.empty:
                    st.success(f"✅ Master Table built with {len(master_table):,} styles")
                    st.rerun()
                else:
                    st.error("Failed to build Master Table")
    else:
        master_df = st.session_state.processor.master_styles
        st.success(f"✅ Master Table loaded: {len(master_df):,} styles")
        
        # Filters
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=master_df['Status'].unique(),
                default=[]
            )
        
        with col2:
            bucket_filter = st.multiselect(
                "Filter by Newness Bucket",
                options=master_df['Newness_Bucket'].unique(),
                default=[]
            )
        
        with col3:
            risk_filter = st.multiselect(
                "Filter by Risk",
                options=['High Returns', ''],
                default=[]
            )
        
        with col4:
            search_term = st.text_input("🔍 Search Style ID")
        
        # Apply filters
        filtered_df = master_df.copy()
        
        if status_filter:
            filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
        
        if bucket_filter:
            filtered_df = filtered_df[filtered_df['Newness_Bucket'].isin(bucket_filter)]
        
        if risk_filter:
            filtered_df = filtered_df[filtered_df['RiskFlag'].isin(risk_filter)]
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df['Style ID'].astype(str).str.contains(
                    search_term, case=False, na=False
                )
            ]
        
        # Display table
        st.dataframe(
            filtered_df,
            use_container_width=True,
            column_config={
                "Orders": st.column_config.NumberColumn(
                    format="%d",
                    help="Count of sales rows = units sold"
                ),
                "GMV": st.column_config.NumberColumn(
                    format="₹%d",
                    help="Gross Merchandise Value"
                ),
                "ReturnPct": st.column_config.ProgressColumn(
                    format="%.1f%%",
                    min_value=0,
                    max_value=1,
                    help="Returns ÷ Orders"
                ),
                "Status": st.column_config.TextColumn(
                    help="Catalog-Only, Zero-Sale, New, Active"
                ),
                "RiskFlag": st.column_config.TextColumn(
                    help="High Returns if return % ≥ 35%"
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
                file_name="master_styles.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Master_Styles')
            st.download_button(
                label="📥 Download as Excel",
                data=buffer,
                file_name="master_styles.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )

# ============================================================================
# WATCHLIST PAGE
# ============================================================================
elif page_name == "Watchlist":
    st.markdown('<div class="main-header">🚨 Watchlist 30 Days</div>', unsafe_allow_html=True)
    
    # Parameters
    with st.expander("⚙️ Watchlist Parameters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            window_days = st.number_input(
                "Window Days",
                value=st.session_state.processor.params.get('report_window_days', 30),
                min_value=1,
                max_value=365,
                help="Number of days for analysis"
            )
            st.session_state.processor.update_parameter('report_window_days', window_days)
        
        with col2:
            min_orders = st.number_input(
                "Minimum Orders",
                value=st.session_state.processor.params.get('watch_min_orders', 3),
                min_value=1,
                help="Minimum orders to be considered 'STARTED'"
            )
            st.session_state.processor.update_parameter('watch_min_orders', min_orders)
        
        with col3:
            new_age = st.number_input(
                "New Age Days",
                value=st.session_state.processor.params.get('new_age_days', 60),
                min_value=1,
                help="Styles ≤ this age are tagged 'NEW'"
            )
            st.session_state.processor.update_parameter('new_age_days', new_age)
    
    # Generate/Refresh button
    if st.button("🔄 Generate Watchlist", type="primary", use_container_width=True):
        with st.spinner("Building watchlist (VBA equivalent)..."):
            watchlist = st.session_state.processor.build_watchlist_30d()
            if not watchlist.empty:
                st.success(f"✅ Watchlist generated: {len(watchlist):,} styles")
            else:
                st.warning("No data available for watchlist")
    
    # Display watchlist
    if st.session_state.processor.watchlist_30d is not None:
        watchlist_df = st.session_state.processor.watchlist_30d
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            tag_filter = st.multiselect(
                "Filter by Tag",
                options=watchlist_df['Tag'].unique(),
                default=[]
            )
        
        with col2:
            search_term = st.text_input("🔍 Search Style")
        
        # Apply filters
        filtered_watchlist = watchlist_df.copy()
        if tag_filter:
            filtered_watchlist = filtered_watchlist[filtered_watchlist['Tag'].isin(tag_filter)]
        if search_term:
            filtered_watchlist = filtered_watchlist[
                filtered_watchlist['Style ID'].astype(str).str.contains(
                    search_term, case=False, na=False
                )
            ]
        
        # Display table
        st.dataframe(
            filtered_watchlist,
            use_container_width=True,
            column_config={
                "Orders30d Est": st.column_config.NumberColumn(
                    format="%d",
                    help="Orders in last 30 days (row count)"
                ),
                "Returns% Est": st.column_config.ProgressColumn(
                    format="%.1f%%",
                    min_value=0,
                    max_value=1
                ),
                "Momentum%": st.column_config.NumberColumn(
                    format="%.1f%%",
                    help="(Recent - Previous) ÷ Previous"
                ),
                "Tag": st.column_config.TextColumn(
                    help="NEW, STARTED, RISING, FALLING, FLAT"
                )
            }
        )
        
        # Export
        st.download_button(
            label="📥 Download Watchlist CSV",
            data=filtered_watchlist.to_csv(index=False),
            file_name="watchlist_30d.csv",
            mime="text/csv"
        )
    else:
        st.info("Click 'Generate Watchlist' to build the watchlist")

# ============================================================================
# RETURNS ANALYSIS PAGE
# ============================================================================
elif page_name == "Analysis":
    st.markdown('<div class="main-header">📈 Returns Analysis</div>', unsafe_allow_html=True)
    
    # Tabs for different returns reports
    tab1, tab2, tab3 = st.tabs(["Returns Type Split", "Returns Insights", "High Return Styles"])
    
    with tab1:
        st.markdown("### 🔄 Returns Type Split (RTO vs Return)")
        
        with st.expander("⚙️ Parameters", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                window_days = st.number_input(
                    "Analysis Window (days)",
                    value=st.session_state.processor.params.get('return_window_days', 30),
                    min_value=1,
                    max_value=365,
                    key="returns_window"
                )
                st.session_state.processor.update_parameter('return_window_days', window_days)
            
            with col2:
                high_return_threshold = st.number_input(
                    "High Return Threshold",
                    value=st.session_state.processor.params.get('high_return_pct', 0.35),
                    min_value=0.0,
                    max_value=1.0,
                    format="%.2f",
                    help="Return % ≥ this value is 'High Returns'"
                )
                st.session_state.processor.update_parameter('high_return_pct', high_return_threshold)
        
        if st.button("🔄 Generate Returns Split", key="gen_returns_split"):
            with st.spinner("Calculating returns split (VBA equivalent)..."):
                returns_split = st.session_state.processor.build_returns_type_split()
                
                if not returns_split.empty:
                    st.success(f"✅ Returns split generated: {len(returns_split):,} styles")
                    
                    # Display
                    st.dataframe(
                        returns_split,
                        use_container_width=True,
                        column_config={
                            "RTO Qty": st.column_config.NumberColumn(format="%d"),
                            "Return Qty": st.column_config.NumberColumn(format="%d"),
                            "Total Returns": st.column_config.NumberColumn(format="%d"),
                            "RTO %": st.column_config.ProgressColumn(format="%.1f%%"),
                            "Return %": st.column_config.ProgressColumn(format="%.1f%%")
                        }
                    )
                    
                    # Chart
                    col1, col2 = st.columns(2)
                    with col1:
                        # Top RTO styles
                        top_rto = returns_split.nlargest(10, 'RTO %')
                        fig = px.bar(top_rto, x='Style ID', y='RTO %',
                                    title="Top 10 Styles by RTO %")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Top return styles
                        top_return = returns_split.nlargest(10, 'Return %')
                        fig = px.bar(top_return, x='Style ID', y='Return %',
                                    title="Top 10 Styles by Return %")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Export
                    st.download_button(
                        label="📥 Download Returns Split CSV",
                        data=returns_split.to_csv(index=False),
                        file_name="returns_type_split.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No returns data available for analysis")
    
    with tab2:
        st.markdown("### 📊 Returns Insights")
        st.info("Returns Insights feature coming soon (VBA BuildReturnsInsights equivalent)")
        
        if st.session_state.processor.returns_raw is not None:
            # Simple returns summary
            returns_df = st.session_state.processor.returns_raw
            
            col1, col2, col3 = st.columns(3)
            with col1:
                total_returns = returns_df['UnitsReturned'].sum()
                st.metric("Total Returns", f"{total_returns:,}")
            
            with col2:
                rto_qty = returns_df[
                    returns_df['ReturnType'].str.contains('RTO', case=False, na=False)
                ]['UnitsReturned'].sum()
                st.metric("RTO Quantity", f"{rto_qty:,}")
            
            with col3:
                return_qty = total_returns - rto_qty
                st.metric("Return Quantity", f"{return_qty:,}")
            
            # Returns by reason (if available)
            if 'reason' in returns_df.columns or 'Reason' in returns_df.columns:
                reason_col = 'reason' if 'reason' in returns_df.columns else 'Reason'
                reason_counts = returns_df[reason_col].value_counts().head(10)
                
                fig = px.bar(
                    x=reason_counts.index,
                    y=reason_counts.values,
                    title="Top 10 Return Reasons",
                    labels={'x': 'Reason', 'y': 'Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### ⚠️ High Return Styles")
        
        if st.session_state.processor.master_styles is not None:
            high_return_styles = st.session_state.processor.master_styles[
                st.session_state.processor.master_styles['ReturnPct'] >= high_return_threshold
            ].sort_values('ReturnPct', ascending=False)
            
            if not high_return_styles.empty:
                st.warning(f"Found {len(high_return_styles):,} styles with return % ≥ {high_return_threshold:.0%}")
                
                st.dataframe(
                    high_return_styles[['Style ID', 'Orders', 'UnitsReturned', 'ReturnPct', 'Status']],
                    column_config={
                        "ReturnPct": st.column_config.ProgressColumn(format="%.1f%%")
                    },
                    use_container_width=True
                )
            else:
                st.success(f"No styles with return % ≥ {high_return_threshold:.0%}")

# ============================================================================
# INVENTORY FORECAST PAGE
# ============================================================================
elif page_name == "Forecast":
    st.markdown('<div class="main-header">🔮 Inventory Forecasting</div>', unsafe_allow_html=True)
    
    # Forecast parameters
    with st.expander("⚙️ Forecast Parameters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            lookback = st.number_input(
                "Lookback Days",
                value=st.session_state.processor.params.get('forecast_lookback_days', 30),
                min_value=7,
                max_value=365
            )
            st.session_state.processor.update_parameter('forecast_lookback_days', lookback)
        
        with col2:
            event_days = st.number_input(
                "Event Days",
                value=st.session_state.processor.params.get('event_days', 10),
                min_value=1,
                max_value=90
            )
            st.session_state.processor.update_parameter('event_days', event_days)
        
        with col3:
            traffic_mult = st.number_input(
                "Traffic Multiplier",
                value=float(st.session_state.processor.params.get('traffic_multiplier', 3.0)),
                min_value=1.0,
                max_value=10.0,
                step=0.5
            )
            st.session_state.processor.update_parameter('traffic_multiplier', traffic_mult)
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            return_rate = st.number_input(
                "Return Rate",
                value=float(st.session_state.processor.params.get('forecast_return_rate', 0.25)),
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                format="%.2f"
            )
            st.session_state.processor.update_parameter('forecast_return_rate', return_rate)
        
        with col5:
            leadtime = st.number_input(
                "Lead Time (days)",
                value=st.session_state.processor.params.get('leadtime_days', 7),
                min_value=0,
                max_value=90
            )
            st.session_state.processor.update_parameter('leadtime_days', leadtime)
        
        with col6:
            service_level = st.number_input(
                "Service Level",
                value=float(st.session_state.processor.params.get('service_level', 0.9)),
                min_value=0.5,
                max_value=0.99,
                step=0.05,
                format="%.2f"
            )
            st.session_state.processor.update_parameter('service_level', service_level)
    
    # Generate forecast
    if st.button("🚀 Generate Inventory Forecast", type="primary", use_container_width=True):
        with st.spinner("Calculating inventory forecast (VBA equivalent)..."):
            forecast = st.session_state.processor.build_inventory_forecast()
            
            if not forecast.empty:
                st.success(f"✅ Forecast generated: {len(forecast):,} styles")
                
                # Display forecast
                st.dataframe(
                    forecast,
                    use_container_width=True,
                    column_config={
                        "Avg Daily Sales": st.column_config.NumberColumn(format="%.2f"),
                        "Gross Forecast": st.column_config.NumberColumn(format="%d"),
                        "Net Forecast": st.column_config.NumberColumn(format="%d"),
                        "Safety Stock": st.column_config.NumberColumn(format="%d"),
                        "Total Required": st.column_config.NumberColumn(
                            format="%d",
                            help="Net Forecast + Safety Stock"
                        )
                    }
                )
                
                # Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    top_forecast = forecast.nlargest(10, 'Total Required')
                    fig = px.bar(top_forecast, x='Style ID', y='Total Required',
                                title="Top 10 Styles by Forecast Requirement")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.scatter(forecast, x='Avg Daily Sales', y='Total Required',
                                    size='Total Required', hover_name='Style ID',
                                    title="Daily Sales vs Total Required")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Export
                st.download_button(
                    label="📥 Download Forecast CSV",
                    data=forecast.to_csv(index=False),
                    file_name="inventory_forecast.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No sales data available for forecasting")

# ============================================================================
# SETTINGS PAGE
# ============================================================================
elif page_name == "Settings":
    st.markdown('<div class="main-header">⚙️ Project M Settings</div>', unsafe_allow_html=True)
    
    # Current parameters
    with st.expander("📋 Current Parameters", expanded=True):
        params_df = pd.DataFrame(
            list(st.session_state.processor.params.items()),
            columns=['Parameter', 'Value']
        )
        st.dataframe(params_df, use_container_width=True)
    
    # Update parameters
    st.markdown("---")
    st.markdown("### Update Parameters")
    
    with st.form("update_params"):
        col1, col2 = st.columns(2)
        
        with col1:
            zero_age = st.number_input(
                "Zero-Sale Age (days)",
                value=st.session_state.processor.params['zero_sale_age_days'],
                min_value=1,
                max_value=365
            )
            
            high_ret = st.number_input(
                "High Return % Threshold",
                value=float(st.session_state.processor.params['high_return_pct']),
                min_value=0.0,
                max_value=1.0,
                format="%.2f"
            )
            
            watch_min = st.number_input(
                "Watchlist Min Orders",
                value=st.session_state.processor.params['watch_min_orders'],
                min_value=1
            )
        
        with col2:
            new_age = st.number_input(
                "New Age (days)",
                value=st.session_state.processor.params['new_age_days'],
                min_value=1
            )
            
            start_recent = st.number_input(
                "Start Recent Min Orders",
                value=st.session_state.processor.params['start_recent_min_orders'],
                min_value=1
            )
            
            start_prev = st.number_input(
                "Start Previous Max Orders",
                value=st.session_state.processor.params['start_prev_max_orders'],
                min_value=0
            )
        
        submitted = st.form_submit_button("💾 Save Parameters", use_container_width=True)
        
        if submitted:
            updates = {
                'zero_sale_age_days': zero_age,
                'high_return_pct': high_ret,
                'watch_min_orders': watch_min,
                'new_age_days': new_age,
                'start_recent_min_orders': start_recent,
                'start_prev_max_orders': start_prev
            }
            
            for key, value in updates.items():
                st.session_state.processor.update_parameter(key, value)
            
            st.success("✅ Parameters updated successfully!")
    
    # Brand filter settings
    st.markdown("---")
    st.markdown("### 🏷️ Brand Filter Settings")
    
    brand_mode = st.selectbox(
        "Brand Filter Mode",
        ["ALL", "ONE", "LIST"],
        index=0,
        help="ALL: Include all brands, ONE: Specific brand, LIST: Multiple brands"
    )
    
    if brand_mode == "ONE":
        brand_name = st.text_input("Specific Brand Name")
    elif brand_mode == "LIST":
        brand_list = st.text_area(
            "Brand List (comma-separated)",
            help="Enter brand names separated by commas"
        )
    
    # Data management
    st.markdown("---")
    st.markdown("### 🗑️ Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Clear All Data", type="secondary", use_container_width=True):
            st.session_state.processor.sales_raw = None
            st.session_state.processor.returns_raw = None
            st.session_state.processor.catalog_raw = None
            st.session_state.processor.master_styles = None
            st.session_state.processor.watchlist_30d = None
            st.session_state.data_loaded = False
            st.success("All data cleared!")
            st.rerun()
    
    with col2:
        if st.button("Reset to Defaults", type="secondary", use_container_width=True):
            st.session_state.processor = ProjectMProcessor()
            st.success("Reset to default settings!")
            st.rerun()

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 20px;'>"
    "📊 Project M - Myntra Analytics Dashboard • "
    "VBA Excel Migration • Built with Streamlit<br>"
    "<small>Each sales row = 1 unit (Myntra data constraint) • "
    "Style IDs normalized: lowercase + trimmed</small>"
    "</div>",
    unsafe_allow_html=True
)