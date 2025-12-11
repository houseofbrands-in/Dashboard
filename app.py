import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

# ============================================================================
# CORE FUNCTIONS (Simplified VBA equivalents)
# ============================================================================

def normalize_style_id(style_value):
    """Normalize style ID like VBA: lowercase, trim, handle numbers"""
    if pd.isna(style_value):
        return ""
    
    # Convert to string
    style_str = str(style_value)
    
    # Remove extra spaces
    style_str = style_str.strip()
    
    # If it's a number with .0, remove decimal
    try:
        if '.' in style_str and style_str.split('.')[1] == '0':
            style_str = style_str.split('.')[0]
    except:
        pass
    
    return style_str.lower()

def import_sales_csv(df):
    """VBA ImportSalesCSV equivalent"""
    result = df.copy()
    
    # Auto-detect columns
    date_col = None
    style_col = None
    qty_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        
        if not date_col and any(x in col_lower for x in ['date', 'created', 'order']):
            date_col = col
        
        if not style_col and any(x in col_lower for x in ['style', 'product', 'code', 'id']):
            style_col = col
        
        if not qty_col and any(x in col_lower for x in ['qty', 'quantity', 'units']):
            qty_col = col
    
    # Required columns
    if not date_col or not style_col:
        raise ValueError("Need Date and Style columns")
    
    # Process dates
    result['OrderDate'] = pd.to_datetime(result[date_col], errors='coerce')
    
    # Style key (CRITICAL - fixes your issue)
    result['StyleKey'] = result[style_col].apply(normalize_style_id)
    
    # Quantity
    if qty_col:
        result['NetUnits'] = pd.to_numeric(result[qty_col], errors='coerce').fillna(1)
    else:
        result['NetUnits'] = 1
    
    # Row counter (like VBA RowUnit)
    result['RowUnit'] = 1
    
    return result, {'date_col': date_col, 'style_col': style_col, 'qty_col': qty_col}

def import_returns_csv(df):
    """VBA ImportReturnsCSV equivalent"""
    result = df.copy()
    
    # Auto-detect
    date_col = None
    style_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        
        if not date_col and any(x in col_lower for x in ['date', 'return', 'created']):
            date_col = col
        
        if not style_col and any(x in col_lower for x in ['style', 'product', 'code', 'id']):
            style_col = col
    
    if not date_col or not style_col:
        raise ValueError("Need Date and Style columns")
    
    result['ReturnDate'] = pd.to_datetime(result[date_col], errors='coerce')
    result['StyleKey'] = result[style_col].apply(normalize_style_id)
    
    # Quantity
    qty_cols = [col for col in df.columns if 'qty' in str(col).lower() or 'quantity' in str(col).lower()]
    if qty_cols:
        result['UnitsReturned'] = pd.to_numeric(result[qty_cols[0]], errors='coerce').fillna(1)
    else:
        result['UnitsReturned'] = 1
    
    return result, {'date_col': date_col, 'style_col': style_col}

def kpi_total_orders_30d(sales_df):
    """VBA KPI_TotalOrders_30d equivalent"""
    if sales_df is None or len(sales_df) == 0:
        return 0
    
    today = datetime.now()
    cutoff = today - timedelta(days=30)
    
    mask = (sales_df['OrderDate'] >= cutoff) & (sales_df['OrderDate'] <= today)
    
    if 'RowUnit' in sales_df.columns:
        return int(sales_df.loc[mask, 'RowUnit'].sum())
    elif 'NetUnits' in sales_df.columns:
        return int(sales_df.loc[mask, 'NetUnits'].sum())
    else:
        return int(mask.sum())

def kpi_return_pct_30d(sales_df, returns_df):
    """VBA KPI_ReturnPct_30d equivalent"""
    orders = kpi_total_orders_30d(sales_df)
    
    if returns_df is None or len(returns_df) == 0 or orders == 0:
        return 0
    
    today = datetime.now()
    cutoff = today - timedelta(days=30)
    
    mask = (returns_df['ReturnDate'] >= cutoff) & (returns_df['ReturnDate'] <= today)
    
    if 'UnitsReturned' in returns_df.columns:
        returns = returns_df.loc[mask, 'UnitsReturned'].sum()
    else:
        returns = 0
    
    return returns / orders

def build_master_table(sales_df, returns_df, catalog_df, params):
    """VBA BuildMasterTable equivalent"""
    master_rows = []
    
    # Get unique styles
    if catalog_df is not None and len(catalog_df) > 0:
        # Find style column
        style_cols = [col for col in catalog_df.columns 
                     if any(x in str(col).lower() for x in ['style', 'product', 'code', 'id'])]
        
        if style_cols:
            style_col = style_cols[0]
            unique_styles = catalog_df[style_col].dropna().unique()
            
            for style in unique_styles:
                style_key = normalize_style_id(style)
                master_rows.append({
                    'Style ID': style,
                    'StyleKey': style_key
                })
    
    # If no catalog, use sales data
    if len(master_rows) == 0 and sales_df is not None:
        unique_styles = sales_df['StyleKey'].dropna().unique()
        for style_key in unique_styles:
            master_rows.append({
                'Style ID': style_key,
                'StyleKey': style_key
            })
    
    if len(master_rows) == 0:
        return pd.DataFrame()
    
    master_df = pd.DataFrame(master_rows)
    
    # Calculate metrics
    metrics = []
    today_date = datetime.now()
    zero_age = params.get('zero_age', 14)
    high_ret_pct = params.get('high_return_pct', 0.35)
    
    for _, row in master_df.iterrows():
        style_key = row['StyleKey']
        
        # Sales metrics
        if sales_df is not None and len(sales_df) > 0:
            style_sales = sales_df[sales_df['StyleKey'] == style_key]
            orders = style_sales['NetUnits'].sum() if 'NetUnits' in style_sales.columns else 0
            
            if len(style_sales) > 0:
                first_order = style_sales['OrderDate'].min()
                last_order = style_sales['OrderDate'].max()
            else:
                first_order = last_order = None
        else:
            orders = 0
            first_order = last_order = None
        
        # Returns metrics
        if returns_df is not None and len(returns_df) > 0:
            style_returns = returns_df[returns_df['StyleKey'] == style_key]
            units_returned = style_returns['UnitsReturned'].sum() if 'UnitsReturned' in style_returns.columns else 0
        else:
            units_returned = 0
        
        # Calculate percentages
        return_pct = units_returned / orders if orders > 0 else 0
        
        # Determine status
        if first_order is None:
            status = "Catalog-Only"
        elif orders == 0:
            days_live = (today_date - first_order).days if first_order else 0
            if days_live >= zero_age:
                status = "Zero-Sale"
            else:
                status = "New"
        elif (today_date - first_order).days <= 60:
            status = "New"
        elif orders > 0:
            status = "Active"
        else:
            status = "Unknown"
        
        # Risk flag
        risk_flag = "High Returns" if return_pct >= high_ret_pct else ""
        
        metrics.append({
            'Style ID': row['Style ID'],
            'Orders': int(orders),
            'UnitsReturned': int(units_returned),
            'ReturnPct': return_pct,
            'FirstOrderDate': first_order,
            'LastOrderDate': last_order,
            'Status': status,
            'RiskFlag': risk_flag
        })
    
    return pd.DataFrame(metrics)

# ============================================================================
# STREAMLIT APP
# ============================================================================

# Page config
st.set_page_config(
    page_title="Myntra Dashboard (VBA Migration)",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86C1;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .stButton>button {
        background: linear-gradient(90deg, #4CAF50, #2E7D32);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'sales_data' not in st.session_state:
    st.session_state.sales_data = None
if 'returns_data' not in st.session_state:
    st.session_state.returns_data = None
if 'catalog_data' not in st.session_state:
    st.session_state.catalog_data = None
if 'master_table' not in st.session_state:
    st.session_state.master_table = None
if 'params' not in st.session_state:
    st.session_state.params = {
        'zero_age': 14,
        'high_return_pct': 0.35,
        'watch_min_orders': 3
    }

# Sidebar
st.sidebar.title("📊 Myntra Dashboard")
menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Data Upload", "Master Table", "Settings"]
)

# ====================
# DASHBOARD PAGE
# ====================
if menu == "Dashboard":
    st.markdown('<div class="main-header">📈 Myntra Partner Dashboard</div>', unsafe_allow_html=True)
    
    # KPI Row
    st.markdown("### 📊 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        orders = kpi_total_orders_30d(st.session_state.sales_data)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{orders:,}</div>
            <div>Orders (30d)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        return_pct = kpi_return_pct_30d(st.session_state.sales_data, st.session_state.returns_data)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{return_pct:.1%}</div>
            <div>Return % (30d)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">—</div>
            <div>GMV (30d)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">—</div>
            <div>Ad Spend (30d)</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick Stats
    if st.session_state.master_table is not None:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_styles = len(st.session_state.master_table)
            st.metric("Total Styles", total_styles)
        
        with col2:
            active_styles = len(st.session_state.master_table[
                st.session_state.master_table['Status'] == 'Active'
            ])
            st.metric("Active Styles", active_styles)
        
        with col3:
            zero_sale = len(st.session_state.master_table[
                st.session_state.master_table['Status'] == 'Zero-Sale'
            ])
            st.metric("Zero-Sale Styles", zero_sale)
    
    # Charts
    if st.session_state.sales_data is not None:
        st.markdown("---")
        st.markdown("### 📅 Sales Trend")
        
        # Sample chart
        sales_by_day = st.session_state.sales_data.copy()
        sales_by_day['Date'] = sales_by_day['OrderDate'].dt.date
        
        daily_sales = sales_by_day.groupby('Date')['NetUnits'].sum().reset_index()
        daily_sales = daily_sales.sort_values('Date').tail(30)
        
        fig = px.line(daily_sales, x='Date', y='NetUnits', title="Daily Orders (Last 30 Days)")
        st.plotly_chart(fig, use_container_width=True)

# ====================
# DATA UPLOAD PAGE
# ====================
elif menu == "Data Upload":
    st.markdown('<div class="main-header">📁 Data Upload Center</div>', unsafe_allow_html=True)
    
    # Setup button (like VBA SetupProjectM)
    if st.button("⚙️ Run SetupProjectM", help="Initialize the system like Excel VBA"):
        st.session_state.sales_data = None
        st.session_state.returns_data = None
        st.session_state.catalog_data = None
        st.session_state.master_table = None
        st.success("✅ System initialized! Ready for data import.")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📈 Sales Data")
        sales_file = st.file_uploader("Upload Sales CSV", type=['csv'], key="sales")
        
        if sales_file is not None:
            try:
                sales_df = pd.read_csv(sales_file)
                
                with st.expander("📋 Preview"):
                    st.dataframe(sales_df.head())
                    st.write(f"**Shape:** {sales_df.shape[0]} rows, {sales_df.shape[1]} columns")
                
                if st.button("🔍 Auto-import Sales", key="auto_sales"):
                    with st.spinner("Importing sales data (VBA equivalent)..."):
                        try:
                            sales_processed, mapping = import_sales_csv(sales_df)
                            st.session_state.sales_data = sales_processed
                            
                            st.success("✅ Sales data imported successfully!")
                            st.write("**Detected columns:**")
                            st.json(mapping)
                            
                            # Show style IDs
                            if 'StyleKey' in sales_processed.columns:
                                with st.expander("👀 View Style IDs"):
                                    st.write("First 10 Style IDs (normalized):")
                                    st.write(sales_processed[['StyleKey']].head(10).values.tolist())
                            
                        except Exception as e:
                            st.error(f"Import failed: {str(e)}")
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with col2:
        st.subheader("🔄 Returns Data")
        returns_file = st.file_uploader("Upload Returns CSV", type=['csv'], key="returns")
        
        if returns_file is not None:
            try:
                returns_df = pd.read_csv(returns_file)
                
                with st.expander("📋 Preview"):
                    st.dataframe(returns_df.head())
                
                if st.button("🔍 Auto-import Returns", key="auto_returns"):
                    with st.spinner("Importing returns data..."):
                        try:
                            returns_processed, mapping = import_returns_csv(returns_df)
                            st.session_state.returns_data = returns_processed
                            st.success("✅ Returns data imported!")
                        except Exception as e:
                            st.error(f"Import failed: {str(e)}")
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with col3:
        st.subheader("📚 Catalog Data")
        catalog_file = st.file_uploader("Upload Catalog CSV", type=['csv'], key="catalog")
        
        if catalog_file is not None:
            try:
                catalog_df = pd.read_csv(catalog_file)
                st.session_state.catalog_data = catalog_df
                st.success(f"✅ Catalog loaded: {len(catalog_df)} rows")
                
                with st.expander("📋 Preview"):
                    st.dataframe(catalog_df.head())
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    # Process All Data Button (VBA RefreshData equivalent)
    st.markdown("---")
    if st.button("🚀 PROCESS ALL DATA (RefreshData)", type="primary", use_container_width=True):
        with st.spinner("Processing all data..."):
            # Build Master Table
            if (st.session_state.sales_data is not None or 
                st.session_state.catalog_data is not None):
                
                master_table = build_master_table(
                    st.session_state.sales_data,
                    st.session_state.returns_data,
                    st.session_state.catalog_data,
                    st.session_state.params
                )
                
                st.session_state.master_table = master_table
                
                if not master_table.empty:
                    st.success(f"✅ Master Table built: {len(master_table)} styles")
                else:
                    st.warning("⚠️ Master Table is empty")
            
            st.success("🎉 All data processed successfully!")
            st.balloons()

# ====================
# MASTER TABLE PAGE
# ====================
elif menu == "Master Table":
    st.markdown('<div class="main-header">📊 Master Styles Table</div>', unsafe_allow_html=True)
    
    if st.session_state.master_table is None or st.session_state.master_table.empty:
        st.warning("No data available. Please import data first.")
        
        if st.button("🔄 Build Master Table Now"):
            with st.spinner("Building Master Table..."):
                master_table = build_master_table(
                    st.session_state.sales_data,
                    st.session_state.returns_data,
                    st.session_state.catalog_data,
                    st.session_state.params
                )
                st.session_state.master_table = master_table
                st.rerun()
    else:
        st.success(f"✅ Master Table loaded: {len(st.session_state.master_table)} styles")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            if 'Status' in st.session_state.master_table.columns:
                status_options = st.session_state.master_table['Status'].unique()
                status_filter = st.multiselect("Filter by Status", status_options)
        
        with col2:
            search_term = st.text_input("🔍 Search Style ID")
        
        # Apply filters
        filtered_df = st.session_state.master_table.copy()
        
        if 'status_filter' in locals() and status_filter:
            filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
        
        if 'search_term' in locals() and search_term:
            filtered_df = filtered_df[
                filtered_df['Style ID'].astype(str).str.contains(search_term, case=False, na=False)
            ]
        
        # Display
        st.dataframe(
            filtered_df,
            use_container_width=True,
            column_config={
                "ReturnPct": st.column_config.ProgressColumn(
                    "Return %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=1
                )
            }
        )
        
        # Export
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                "master_table.csv",
                "text/csv"
            )
        
        with col2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Master_Styles')
            st.download_button(
                "📥 Download Excel",
                buffer,
                "master_table.xlsx",
                "application/vnd.ms-excel"
            )

# ====================
# SETTINGS PAGE
# ====================
elif menu == "Settings":
    st.markdown('<div class="main-header">⚙️ Settings & Parameters</div>', unsafe_allow_html=True)
    
    # Current params
    with st.expander("📋 Current Parameters"):
        st.json(st.session_state.params)
    
    # Update params
    st.markdown("### Update Parameters")
    
    with st.form("params_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            zero_age = st.number_input("Zero-Sale Age (days)", 
                                      value=st.session_state.params['zero_age'],
                                      min_value=1, max_value=365)
            high_return = st.number_input("High Return %", 
                                         value=float(st.session_state.params['high_return_pct']),
                                         min_value=0.0, max_value=1.0, format="%.2f")
        
        with col2:
            watch_min = st.number_input("Watchlist Min Orders", 
                                       value=st.session_state.params['watch_min_orders'],
                                       min_value=1, max_value=100)
        
        submitted = st.form_submit_button("💾 Save Parameters")
        
        if submitted:
            st.session_state.params.update({
                'zero_age': zero_age,
                'high_return_pct': high_return,
                'watch_min_orders': watch_min
            })
            st.success("✅ Parameters saved!")
    
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
    "<div style='text-align: center; color: gray;'>"
    "Myntra Partner Dashboard • VBA Excel Migration • Built with Streamlit"
    "</div>",
    unsafe_allow_html=True
)
