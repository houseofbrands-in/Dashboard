import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import base64

# Page configuration
st.set_page_config(
    page_title="Myntra Partner Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
    .kpi-label {
        font-size: 1rem;
        opacity: 0.9;
    }
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

# Initialize session state
if 'sales_data' not in st.session_state:
    st.session_state.sales_data = None
if 'returns_data' not in st.session_state:
    st.session_state.returns_data = None
if 'catalog_data' not in st.session_state:
    st.session_state.catalog_data = None
if 'params' not in st.session_state:
    st.session_state.params = {
        'folder_path': '',
        'zero_sale_age': 14,
        'high_return_pct': 0.35,
        'watch_min_orders': 3,
        'forecast_lookback': 30,
        'event_days': 10,
        'traffic_multiplier': 3
    }

# Sidebar Navigation
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/5968/5968672.png", width=100)
st.sidebar.title("📊 Myntra Analytics")

menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Data Upload", "Reports", "Forecasting", "Settings"]
)

# ====================
# DATA UPLOAD PAGE
# ====================
if menu == "Data Upload":
    st.markdown('<div class="main-header">📁 Data Upload Center</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Sales Data")
        sales_file = st.file_uploader("Upload Sales CSV", type=['csv'], key="sales")
        if sales_file:
            sales_df = pd.read_csv(sales_file)
            st.session_state.sales_data = sales_df
            st.success(f"✅ Sales data loaded: {len(sales_df)} rows")
            
            # Auto-detect columns
            with st.expander("Column Mapping"):
                date_cols = [col for col in sales_df.columns if 'date' in col.lower()]
                style_cols = [col for col in sales_df.columns if 'style' in col.lower() or 'product' in col.lower()]
                qty_cols = [col for col in sales_df.columns if 'qty' in col.lower() or 'quantity' in col.lower()]
                
                date_col = st.selectbox("Date Column", date_cols if date_cols else sales_df.columns, key="sales_date")
                style_col = st.selectbox("Style Column", style_cols if style_cols else sales_df.columns, key="sales_style")
                qty_col = st.selectbox("Quantity Column", qty_cols if qty_cols else sales_df.columns, key="sales_qty")
                
                if st.button("Apply Mapping", key="map_sales"):
                    # Save mapping to session
                    st.session_state.sales_mapping = {
                        'date': date_col,
                        'style': style_col,
                        'qty': qty_col
                    }
    
    with col2:
        st.subheader("Returns Data")
        returns_file = st.file_uploader("Upload Returns CSV", type=['csv'], key="returns")
        if returns_file:
            returns_df = pd.read_csv(returns_file)
            st.session_state.returns_data = returns_df
            st.success(f"✅ Returns data loaded: {len(returns_df)} rows")
            
            with st.expander("Column Mapping"):
                date_cols = [col for col in returns_df.columns if 'date' in col.lower()]
                style_cols = [col for col in returns_df.columns if 'style' in col.lower()]
                
                date_col = st.selectbox("Date Column", date_cols if date_cols else returns_df.columns, key="returns_date")
                style_col = st.selectbox("Style Column", style_cols if style_cols else returns_df.columns, key="returns_style")
    
    with col3:
        st.subheader("Catalog Data")
        catalog_file = st.file_uploader("Upload Catalog CSV", type=['csv'], key="catalog")
        if catalog_file:
            catalog_df = pd.read_csv(catalog_file)
            st.session_state.catalog_data = catalog_df
            st.success(f"✅ Catalog data loaded: {len(catalog_df)} rows")
    
    # Data Preview
    if st.session_state.sales_data is not None:
        with st.expander("📋 Sales Data Preview"):
            st.dataframe(st.session_state.sales_data.head())
            st.write(f"Shape: {st.session_state.sales_data.shape}")
    
    # Process Data Button
    if st.button("🚀 Process All Data", type="primary"):
        with st.spinner("Processing data..."):
            # Simulate processing
            import time
            time.sleep(2)
            st.success("✅ All data processed successfully!")
            st.balloons()

# ====================
# DASHBOARD PAGE
# ====================
elif menu == "Dashboard":
    st.markdown('<div class="main-header">📈 Myntra Partner Dashboard</div>', unsafe_allow_html=True)
    
    # KPI Row
    st.markdown("### 📊 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">1,247</div>
            <div class="kpi-label">Orders (30d)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">24.5%</div>
            <div class="kpi-label">Return % (30d)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">₹4.2L</div>
            <div class="kpi-label">GMV (30d)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-value">₹78K</div>
            <div class="kpi-label">Ad Spend (30d)</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts Row
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📅 Sales Trend")
        # Sample data
        dates = pd.date_range(end=datetime.today(), periods=30)
        sales_data = pd.DataFrame({
            'date': dates,
            'orders': np.random.randint(20, 100, 30)
        })
        fig = px.line(sales_data, x='date', y='orders', 
                     title="Daily Orders (Last 30 Days)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Returns by Reason")
        reasons = ['Size Issue', 'Quality', 'Defect', 'Color', 'Other']
        returns_data = pd.DataFrame({
            'reason': reasons,
            'count': np.random.randint(10, 50, 5)
        })
        fig = px.bar(returns_data, x='reason', y='count',
                    title="Returns Analysis", color='reason')
        st.plotly_chart(fig, use_container_width=True)
    
    # Data Table
    st.markdown("### 📋 Top Performing Styles")
    sample_data = pd.DataFrame({
        'Style ID': ['STY001', 'STY002', 'STY003', 'STY004', 'STY005'],
        'Orders': [450, 320, 280, 210, 190],
        'GMV': [1250000, 890000, 720000, 550000, 480000],
        'Returns': [45, 32, 28, 21, 19],
        'Return %': [10.0, 10.0, 10.0, 10.0, 10.0],
        'Status': ['Active', 'Active', 'New', 'Watch', 'Active']
    })
    st.dataframe(sample_data, use_container_width=True)

# ====================
# REPORTS PAGE
# ====================
elif menu == "Reports":
    st.markdown('<div class="main-header">📄 Reports & Insights</div>', unsafe_allow_html=True)
    
    report_type = st.selectbox(
        "Select Report",
        ["Returns Insights", "Product Performance", "Zero-Sale Styles", "Inventory Health"]
    )
    
    if report_type == "Returns Insights":
        st.subheader("🔄 Returns Analysis")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", 
                                      value=datetime.today() - timedelta(days=60))
        with col2:
            end_date = st.date_input("End Date", value=datetime.today())
        
        # Generate sample returns data
        if st.button("Generate Report"):
            with st.spinner("Analyzing returns data..."):
                # Simulate analysis
                import time
                time.sleep(1)
                
                # Create sample heatmap data
                styles = [f'STY{i:03d}' for i in range(1, 11)]
                reasons = ['Size Issue', 'Quality', 'Color', 'Fit', 'Defect']
                
                data = []
                for style in styles:
                    for reason in reasons:
                        data.append({
                            'Style ID': style,
                            'Reason': reason,
                            'Returns': np.random.randint(0, 20)
                        })
                
                df = pd.DataFrame(data)
                pivot = df.pivot_table(index='Style ID', columns='Reason', 
                                      values='Returns', aggfunc='sum', fill_value=0)
                
                # Display heatmap
                fig = px.imshow(pivot, 
                               title="Returns Heatmap - Style × Reason",
                               color_continuous_scale='Reds')
                st.plotly_chart(fig, use_container_width=True)
                
                # Top returns table
                st.subheader("Top Return Styles")
                style_totals = df.groupby('Style ID')['Returns'].sum().reset_index()
                style_totals = style_totals.sort_values('Returns', ascending=False)
                st.dataframe(style_totals.head(10), use_container_width=True)

# ====================
# FORECASTING PAGE
# ====================
elif menu == "Forecasting":
    st.markdown('<div class="main-header">🔮 Inventory Forecasting</div>', unsafe_allow_html=True)
    
    # Forecast parameters
    col1, col2, col3 = st.columns(3)
    with col1:
        lookback = st.number_input("Lookback Days", 
                                  value=30, min_value=7, max_value=365)
    with col2:
        event_days = st.number_input("Event Duration (days)", 
                                    value=10, min_value=1, max_value=30)
    with col3:
        traffic_mult = st.number_input("Traffic Multiplier", 
                                      value=3.0, min_value=1.0, max_value=10.0)
    
    if st.button("Generate Forecast", type="primary"):
        with st.spinner("Calculating inventory requirements..."):
            # Simulate forecast calculation
            import time
            time.sleep(2)
            
            # Generate sample forecast data
            styles = [f'STY{i:03d}' for i in range(1, 16)]
            forecast_data = []
            
            for style in styles:
                avg_daily = np.random.randint(1, 20)
                forecast = avg_daily * event_days * traffic_mult
                safety_stock = forecast * 0.2
                total_needed = int(forecast + safety_stock)
                
                forecast_data.append({
                    'Style ID': style,
                    'Avg Daily Sales': avg_daily,
                    'Forecast Demand': int(forecast),
                    'Safety Stock': int(safety_stock),
                    'Total Required': total_needed,
                    'Current Stock': np.random.randint(0, total_needed + 50),
                    'Order Needed': max(0, total_needed - np.random.randint(0, total_needed + 50))
                })
            
            forecast_df = pd.DataFrame(forecast_data)
            
            # Display forecast
            st.subheader("📦 Inventory Forecast Results")
            st.dataframe(forecast_df, use_container_width=True)
            
            # Visualizations
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(forecast_df.head(10), x='Style ID', y='Total Required',
                            title="Top 10 Styles - Inventory Requirement")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.scatter(forecast_df, x='Forecast Demand', y='Safety Stock',
                                size='Total Required', hover_name='Style ID',
                                title="Demand vs Safety Stock")
                st.plotly_chart(fig, use_container_width=True)

# ====================
# SETTINGS PAGE
# ====================
elif menu == "Settings":
    st.markdown('<div class="main-header">⚙️ Settings & Configuration</div>', unsafe_allow_html=True)
    
    with st.form("settings_form"):
        st.subheader("Business Parameters")
        
        col1, col2 = st.columns(2)
        with col1:
            zero_age = st.number_input("Zero-Sale Age (days)", 
                                      value=st.session_state.params['zero_sale_age'],
                                      min_value=1, max_value=365)
            high_return = st.number_input("High Return % Threshold", 
                                         value=float(st.session_state.params['high_return_pct']),
                                         min_value=0.0, max_value=1.0, format="%.2f")
        
        with col2:
            min_orders = st.number_input("Watchlist Minimum Orders", 
                                        value=st.session_state.params['watch_min_orders'],
                                        min_value=1, max_value=100)
        
        st.subheader("Brand Filter")
        brand_mode = st.selectbox("Brand Filter Mode", 
                                 ["ALL", "ONE", "LIST"])
        
        if brand_mode == "ONE":
            brand_name = st.text_input("Specific Brand Name", "")
        elif brand_mode == "LIST":
            brand_list = st.text_area("Brand List (comma-separated)", 
                                     help="Enter brands separated by commas")
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Settings")
        if submitted:
            # Update session state
            st.session_state.params.update({
                'zero_sale_age': zero_age,
                'high_return_pct': high_return,
                'watch_min_orders': min_orders
            })
            st.success("✅ Settings saved successfully!")
    
    # Data Management
    st.markdown("---")
    st.subheader("🔄 Data Management")
    
    if st.button("Clear All Data", type="secondary"):
        st.session_state.sales_data = None
        st.session_state.returns_data = None
        st.session_state.catalog_data = None
        st.success("All data cleared from memory")
    
    # Export functionality
    st.subheader("📤 Export Data")
    export_format = st.selectbox("Export Format", ["CSV", "Excel"])
    
    if st.button("Generate Export"):
        # Create sample export data
        export_df = pd.DataFrame({
            'Metric': ['Total Orders', 'Total GMV', 'Return Rate', 'Top Style'],
            'Value': [1247, 4200000, '24.5%', 'STY001'],
            'Period': ['Last 30 days'] * 4
        })
        
        if export_format == "CSV":
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="myntra_report.csv",
                mime="text/csv"
            )
        else:
            # For Excel, we'd use BytesIO
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                export_df.to_excel(writer, index=False, sheet_name='Report')
            st.download_button(
                label="📥 Download Excel",
                data=buffer,
                file_name="myntra_report.xlsx",
                mime="application/vnd.ms-excel"
            )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Myntra Partner Dashboard v1.0 • Built with Streamlit"
    "</div>",
    unsafe_allow_html=True
)
