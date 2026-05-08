import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import os

# Configuration and styling
st.set_page_config(
    page_title="Financial Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS for dark theme styling
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Metrics Cards */
    div[data-testid="metric-container"] {
        background-color: #1E2127;
        border: 1px solid #2D313A;
        padding: 5% 5% 5% 10%;
        border-radius: 10px;
        color: white;
        overflow-wrap: break-word;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    div[data-testid="metric-container"] > div {
        color: #B0B3B8;
        font-size: 1.1rem;
    }
    
    div[data-testid="metric-container"] > div + div {
        color: #4CAF50;
        font-size: 1.8rem;
        font-weight: bold;
    }

    /* Titles */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #FFFFFF;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #12151B;
    }
</style>
""", unsafe_allow_html=True)

# Database connection logic
@st.cache_resource
def init_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "datawarehouse"),
            user=os.getenv("DB_USER", "airflow"),
            password=os.getenv("DB_PASSWORD", "airflow")
        )
    except Exception as e:
        st.error(f"Failed to connect to Data Warehouse: {e}")
        return None

conn = init_connection()

# Helper function to execute and cache queries
@st.cache_data(ttl=600)
def run_query(query):
    if conn:
        try:
            return pd.read_sql(query, conn)
        except Exception as e:
            st.error(f"Query Error: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# Main application layout
st.title("Financial Analytics Data Warehouse")
st.markdown("Monitor key financial metrics and transaction volume.")

# Check if the database has been populated by Airflow yet
# If not, we render a scaffolded view instead of throwing an error

def check_data_exists():
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM fact_transactions;")
            count = cur.fetchone()[0]
            cur.close()
            return count > 0
        except Exception as e:
            st.error(f"Error checking data: {e}")
            return False
    return False

data_exists = check_data_exists()

if not data_exists:
    st.warning("Data Warehouse is currently empty. Please run the Airflow DAG to ingest data.")
    
    # Render placeholder layout
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Volume", "$1.2M", "+15% MoM")
    col2.metric("Active Accounts", "4,320", "+2.5%")
    col3.metric("Fraud Flags", "12", "-3")
    
    st.markdown("### Transaction Trends (Mocked)")
    # Generate mock data for visualization layout testing
    mock_dates = pd.date_range(start='2023-01-01', periods=30)
    mock_volumes = pd.Series([x + (x*0.1) for x in range(30)]) * 1000
    df_mock = pd.DataFrame({'Date': mock_dates, 'Volume': mock_volumes})
    fig = px.line(df_mock, x='Date', y='Volume', template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)

else:
    # Render actual data if available
    st.success("Connected to Data Warehouse.")
    
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    
    # Total Volume Metric
    df_vol = run_query("SELECT SUM(amount) as total_volume FROM fact_transactions")
    if not df_vol.empty and pd.notna(df_vol['total_volume'][0]):
        kpi_col1.metric("Total Volume", f"${df_vol['total_volume'][0]:,.2f}")
        
    # Active Accounts Metric
    df_accounts = run_query("SELECT COUNT(*) as active_accounts FROM dim_accounts WHERE status = 'Active'")
    if not df_accounts.empty:
        kpi_col2.metric("Active Accounts", f"{df_accounts['active_accounts'][0]:,}")
        
    # Fraud Cases Metric
    df_fraud = run_query("SELECT COUNT(*) as fraud_count FROM fact_transactions WHERE is_fraud = TRUE")
    if not df_fraud.empty:
        kpi_col3.metric("Fraud Cases", f"{df_fraud['fraud_count'][0]:,}")
        
    # Time Series Chart
    st.markdown("### Transaction Volume Over Time")
    query_trends = """
        SELECT DATE(transaction_date) as date, SUM(amount) as daily_volume 
        FROM fact_transactions 
        GROUP BY DATE(transaction_date) 
        ORDER BY date DESC LIMIT 30
    """
    df_trends = run_query(query_trends)
    if not df_trends.empty:
        fig = px.line(df_trends, x='date', y='daily_volume', title='Daily Transaction Volume (Last 30 Days)', template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)

    # Segmentation and Breakdowns
    st.markdown("### Advanced Analytics")
    col_chart1, col_chart2 = st.columns(2)
    
    # Customer Segmentation
    with col_chart1:
        st.markdown("#### Customer Segmentation by Activity")
        query_segmentation = """
            WITH CustomerActivity AS (
                SELECT 
                    c.customer_id,
                    SUM(a.balance) AS total_balance,
                    COUNT(t.transaction_id) AS total_transactions
                FROM dim_customers c
                JOIN dim_accounts a ON c.customer_id = a.customer_id
                LEFT JOIN fact_transactions t ON a.account_id = t.account_id
                GROUP BY c.customer_id
            )
            SELECT 
                CASE 
                    WHEN total_balance > 50000 AND total_transactions > 50 THEN 'High Value - Active'
                    WHEN total_balance > 50000 THEN 'High Value - Inactive'
                    WHEN total_transactions > 50 THEN 'Active User'
                    ELSE 'Standard User'
                END AS customer_segment,
                COUNT(*) as count
            FROM CustomerActivity
            GROUP BY customer_segment
        """
        df_seg = run_query(query_segmentation)
        if not df_seg.empty:
            fig_seg = px.pie(df_seg, values='count', names='customer_segment', template='plotly_dark', hole=0.4)
            st.plotly_chart(fig_seg, use_container_width=True)
            
    # Fraud Analysis Breakdowns
    with col_chart2:
        st.markdown("#### Top Merchants by Fraud Rate")
        query_fraud_merchants = """
            SELECT 
                merchant_name,
                COUNT(transaction_id) AS total_transactions,
                SUM(CASE WHEN is_fraud = TRUE THEN 1 ELSE 0 END) AS fraud_transactions,
                (SUM(CASE WHEN is_fraud = TRUE THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(transaction_id), 0)) AS fraud_rate_percentage
            FROM fact_transactions
            GROUP BY merchant_name
            HAVING COUNT(transaction_id) > 10
            ORDER BY fraud_rate_percentage DESC
            LIMIT 10
        """
        df_fraud_merchants = run_query(query_fraud_merchants)
        if not df_fraud_merchants.empty:
            fig_fraud = px.bar(df_fraud_merchants, x='merchant_name', y='fraud_rate_percentage', 
                               template='plotly_dark', 
                               color='fraud_rate_percentage', color_continuous_scale='Reds')
            fig_fraud.update_layout(xaxis_title="Merchant", yaxis_title="Fraud Rate (%)", showlegend=False)
            st.plotly_chart(fig_fraud, use_container_width=True)

