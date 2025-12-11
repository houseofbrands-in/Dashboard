# Project M - Myntra Analytics Dashboard

A web-based replacement for Excel VBA analytics tool for Myntra marketplace partners.

## Features
- ✅ **Exact VBA logic replication** - All calculations match Excel
- ✅ **No quantity column handling** - Each sales row = 1 unit
- ✅ **Auto column detection** - Like VBA fuzzy matching
- ✅ **Style ID normalization** - Lowercase + trim
- ✅ **Real-time dashboards** - KPIs update instantly
- ✅ **All Excel reports** - Master Table, Watchlist, Returns, Forecast

## Quick Start

1. **Go to Streamlit Cloud**: [share.streamlit.io](https://share.streamlit.io)
2. **Connect your GitHub** with this repository
3. **Deploy** the app (main file: `app.py`)
4. **Upload your CSV files** from Excel

## Data Preparation

### Export from Excel:
1. **Sales_Raw sheet** → Save as CSV
2. **Returns_Raw sheet** → Save as CSV  
3. **Catalog_Raw sheet** → Save as CSV (optional)

### Important Notes:
- **Sales data has no quantity column** - Each row = 1 unit
- **Style IDs are normalized automatically** (like VBA)
- **Dates are parsed automatically** (supports Excel formats)

## Pages

1. **Dashboard** - KPIs and charts
2. **Data Import** - Upload CSV files
3. **Master Table** - Complete style analysis
4. **Watchlist** - 30-day performance tracking
5. **Returns Analysis** - RTO vs Return splits
6. **Inventory Forecast** - Demand prediction
7. **Settings** - Configure parameters

## Parameters

All VBA parameters are available in Settings:
- Zero-Sale Age: 14 days default
- High Return %: 35% default  
- New Age Days: 60 days default
- Forecast Lookback: 30 days default

## Deployment

This app is ready for **Streamlit Cloud deployment**. No local setup needed!

## Support

For issues with data import or calculations, check:
1. CSV format matches Excel export
2. Date and Style columns exist
3. File encoding is UTF-8
