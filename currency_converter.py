# =============================================
# REAL CURRENCY CONVERTER - LIVE EXCHANGE RATES
# =============================================

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="Real Currency Converter",
    page_icon="💱",
    layout="wide"
)

# Title
st.title("💱 Real Currency Converter")
st.markdown("### Live exchange rates from real API")

# =============================================
# API FUNCTIONS
# =============================================

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_all_rates(base_currency="USD"):
    """
    Fetch all exchange rates from API
    Cached for 1 hour to avoid too many requests
    """
    try:
        # Using ExchangeRate-API Open Access (no key required)
        url = f"https://open.er-api.com/v6/latest/{base_currency}"
        
        with st.spinner("Fetching live exchange rates..."):
            response = requests.get(url, timeout=10)
            
        if response.status_code == 200:
            data = response.json()
            if data["result"] == "success":
                return data
            else:
                st.error(f"API Error: {data.get('error-type', 'Unknown error')}")
                return None
        else:
            st.error(f"Failed to fetch rates. Status code: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Connection error! Please check your internet connection.")
        return None
    except requests.exceptions.Timeout:
        st.error("❌ Request timeout! API is taking too long to respond.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def get_direct_rate(from_currency, to_currency, amount=1):
    """
    Get direct conversion rate between two currencies
    """
    try:
        # Alternative API (also free, no key required)
        url = f"https://api.budjet.org/fiat/{from_currency}/{to_currency}/{amount}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
            
    except Exception as e:
        st.error(f"Error fetching direct rate: {str(e)}")
        return None

# =============================================
# MAIN APP
# =============================================

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Choose API source
    api_source = st.radio(
        "API Source:",
        ["ExchangeRate-API (Open)", "Budjet.org API (Unlimited)"]
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.info(
        "This app uses real exchange rate APIs:\n"
        "- ExchangeRate-API: Updates daily, 1500+ requests/day\n"
        "- Budjet.org: Unlimited requests, real-time\n\n"
        "Data refreshes every hour."
    )
    
    # Attribution required for ExchangeRate-API [citation:4]
    st.markdown("---")
    st.markdown(
        '<a href="https://www.exchangerate-api.com">Rates By Exchange Rate API</a>',
        unsafe_allow_html=True
    )

# Main content
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("💱 Convert Currency")
    
    # Initialize session state for currencies
    if 'currency_list' not in st.session_state:
        st.session_state.currency_list = ["USD", "EUR", "GBP", "JPY", "TZS", "KES", "UGX", "ZAR"]
    
    # Try to fetch real currencies
    with st.expander("🔄 Load real currencies from API", expanded=False):
        if st.button("Fetch Available Currencies"):
            rates_data = get_all_rates("USD")
            if rates_data and "rates" in rates_data:
                st.session_state.currency_list = sorted(list(rates_data["rates"].keys()))
                st.success(f"✅ Loaded {len(st.session_state.currency_list)} currencies!")
    
    # Input amount
    amount = st.number_input(
        "Amount:",
        min_value=0.01,
        value=1000.00,
        step=100.00,
        format="%.2f"
    )
    
    # Currency selection
    col_from, col_to, col_swap = st.columns([4, 4, 1])
    
    with col_from:
        from_currency = st.selectbox(
            "From:", 
            st.session_state.currency_list,
            index=st.session_state.currency_list.index("TZS") if "TZS" in st.session_state.currency_list else 0
        )
    
    with col_to:
        to_currency = st.selectbox(
            "To:", 
            st.session_state.currency_list,
            index=st.session_state.currency_list.index("USD") if "USD" in st.session_state.currency_list else 1
        )
    
    with col_swap:
        st.markdown("#####  ")
        if st.button("🔄"):
            # Swap currencies
            from_currency, to_currency = to_currency, from_currency
            st.rerun()
    
    # Convert button
    if st.button("Convert Now", type="primary", use_container_width=True):
        
        with st.spinner("Converting..."):
            
            if api_source == "ExchangeRate-API (Open)":
                # Method 1: Get all rates then calculate
                rates_data = get_all_rates(from_currency)
                
                if rates_data and "rates" in rates_data and to_currency in rates_data["rates"]:
                    rate = rates_data["rates"][to_currency]
                    result = amount * rate
                    
                    # Get last update time
                    last_update = datetime.fromtimestamp(
                        rates_data["time_last_update_unix"]
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Display result
                    st.balloons()
                    st.success(f"### {amount:,.2f} {from_currency} = {result:,.2f} {to_currency}")
                    
                    # Show details
                    col_rate, col_time = st.columns(2)
                    with col_rate:
                        st.metric("Exchange Rate", f"1 {from_currency} = {rate:.4f} {to_currency}")
                    with col_time:
                        st.metric("Last Updated", last_update)
                        
                else:
                    st.error(f"❌ Could not get rate for {to_currency}")
            
            else:  # Budjet.org API
                # Method 2: Direct conversion
                result_data = get_direct_rate(from_currency, to_currency, amount)
                
                if result_data and "rate" in result_data:
                    result = result_data["result"] if "result" in result_data else amount * result_data["rate"]
                    
                    st.balloons()
                    st.success(f"### {amount:,.2f} {from_currency} = {result:,.2f} {to_currency}")
                    
                    col_rate, col_info = st.columns(2)
                    with col_rate:
                        st.metric("Exchange Rate", f"1 {from_currency} = {result_data['rate']:.4f} {to_currency}")
                    with col_info:
                        st.metric("Base", result_data.get("base", from_currency))
                        
                else:
                    st.error("❌ Conversion failed. Trying fallback method...")
                    # Fallback to first API
                    rates_data = get_all_rates(from_currency)
                    if rates_data and "rates" in rates_data and to_currency in rates_data["rates"]:
                        rate = rates_data["rates"][to_currency]
                        result = amount * rate
                        st.success(f"### {amount:,.2f} {from_currency} = {result:,.2f} {to_currency} (using fallback)")

with col2:
    st.subheader("📊 Live Exchange Rates")
    
    # Base currency for rates display
    base_for_rates = st.selectbox(
        "Base Currency:",
        ["USD", "EUR", "GBP", "TZS", "KES"],
        index=0,
        key="base_rates"
    )
    
    if st.button(f"Show Rates for {base_for_rates}", key="show_rates"):
        rates_data = get_all_rates(base_for_rates)
        
        if rates_data and "rates" in rates_data:
            # Create dataframe
            rates_list = []
            for currency, rate in list(rates_data["rates"].items())[:20]:  # Show first 20
                rates_list.append({
                    "Currency": currency,
                    f"Rate (per {base_for_rates})": f"{rate:.4f}"
                })
            
            df = pd.DataFrame(rates_list)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Show update time
            last_update = datetime.fromtimestamp(
                rates_data["time_last_update_unix"]
            ).strftime("%Y-%m-%d %H:%M:%S")
            next_update = datetime.fromtimestamp(
                rates_data["time_next_update_unix"]
            ).strftime("%Y-%m-%d %H:%M:%S")
            
            st.caption(f"🕒 Last: {last_update} | Next: {next_update}")
        else:
            st.warning("Click button to load rates")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 🔄 Real-time")
    st.caption("Live rates from real API")
with col2:
    st.markdown("### 🌍 150+ Currencies")
    st.caption("Major world currencies supported")
with col3:
    st.markdown("### ⚡ Instant")
    st.caption("Results in milliseconds")

st.markdown("---")
st.markdown("Created with ❤️ using Python, Streamlit, and real Exchange Rate APIs")

# Show attribution for ExchangeRate-API [citation:4]
st.markdown(
    '<p style="text-align: center; font-size: 0.8em;">'
    '<a href="https://www.exchangerate-api.com">Exchange rates provided by ExchangeRate-API</a> | '
    '<a href="https://github.com/AJELLY123/free-exchange-rate-api">Budjet.org API</a>'
    '</p>',
    unsafe_allow_html=True
)