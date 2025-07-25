import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import s3fs
from streamlit_js_eval import streamlit_js_eval

# --- PAGE CONFIG ---
st.set_page_config(page_title="Stock & Sentiment Dashboard", layout="wide")

# --- AWS credentials from secrets ---
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]

# --- Paths ---
stock_path = "s3://stock-analysis-yk/agg-data/stockdata/"
sentiment_path = "s3://stock-analysis-yk/agg-data/stocksentiment/"

# --- Load from S3 ---
@st.cache_data
def load_s3_data(s3_path):
    fs = s3fs.S3FileSystem(
        key=AWS_ACCESS_KEY_ID,
        secret=AWS_SECRET_ACCESS_KEY,
        client_kwargs={'region_name': st.secrets["AWS_REGION"]}
    )
    files = [f"s3://{f}" for f in fs.ls(s3_path) if "part" in f and f.endswith(".csv")]
    return pd.concat([pd.read_csv(f) for f in files])

# --- Load Data ---
sentiment_df = load_s3_data(sentiment_path)
price_df = load_s3_data(stock_path)

# --- Page Title ---
st.markdown("<h1 style='text-align: center;'>📊 Stock & Sentiment Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Visualize market movements and public sentiment together.</p>", unsafe_allow_html=True)

# --- Detect Device Width ---
window_width = streamlit_js_eval(js_expressions='window.innerWidth', key="device-width")
#window_width = device_info.get("window.innerWidth", 1024)
if window_width is None:
    st.warning("Detecting screen size, please wait...")
    st.stop()
print(window_width)
if window_width < 768:
    # Mobile View
    left_col = st.container()
    right_col = st.container()
else:
    # Desktop View
    left_col, right_col = st.columns([3, 2])
if window_width < 768:
    num_cols = 2
    
elif window_width < 1024:
    num_cols = 3
else:
    num_cols = 5

# --- Prepare Data ---
latest_date = price_df['Date'].max()




# --- LEFT COLUMN ---
with left_col:
    tickers = sorted(price_df["ticker"].unique())
    selected_ticker = st.selectbox("Select a Stock", tickers)
    sentiment_filtered = sentiment_df[sentiment_df["ticker"] == selected_ticker].sort_values("Date")
    price_filtered = price_df[price_df["ticker"] == selected_ticker].sort_values("Date")
    st.header("📈 Technical Indicators")

    # Price vs Sentiment Chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=price_filtered["Date"], y=price_filtered["Close"],
                             name="Close Price", line=dict(color="skyblue")), secondary_y=False)
    fig.add_trace(go.Scatter(x=sentiment_filtered["Date"], y=sentiment_filtered["Sentiment_Score"],
                             name="Sentiment Score", line=dict(color="orange")), secondary_y=True)
    fig.update_layout(title_text=f"{selected_ticker} - Price vs Sentiment", template="plotly_dark")
    fig.update_yaxes(title_text="Close Price", secondary_y=False)
    fig.update_yaxes(title_text="Sentiment Score", secondary_y=True)

    # Moving Averages
    melted = price_filtered.melt(id_vars="Date", value_vars=["Close", "MA_7", "MA_14"],
                                 var_name="Metric", value_name="Value")
    fig_ma = px.line(melted, x="Date", y="Value", color="Metric",
                     title=f"{selected_ticker} - Close & Moving Averages")
    fig_vol = px.line(price_filtered, x="Date", y="Volatility_7",
                      title=f"7-Day Volatility - {selected_ticker}")

    st.plotly_chart(fig_ma, use_container_width=True)
    st.plotly_chart(fig_vol, use_container_width=True)
    st.plotly_chart(fig, use_container_width=True)

    # Volume
    st.subheader(f"Stock Volume Movement Average - {selected_ticker}")
    price_filtered["vol_ma_7"] = price_filtered["Volume"].rolling(7).mean()
    fig_volume = px.line(price_filtered, x="Date", y=["Volume", "vol_ma_7"],
                         title="Volume & 7-Day Avg", template="plotly_dark")
    st.plotly_chart(fig_volume, use_container_width=True)

    # Top Bullish Days
    st.subheader(f"Top Bullish Days for {selected_ticker}")
    top_days = sentiment_filtered[sentiment_filtered['sentiment_label'] == 'Bullish']\
               .sort_values(by='Sentiment_Score', ascending=False).head(5)
    st.dataframe(top_days[['Date', 'Sentiment_Score', 'Daily_Return']], use_container_width=True)

# --- RIGHT COLUMN ---
with right_col:
    st.header("📌 Market Overview")

    latest_date = price_df['Date'].max()
    snapshot_df = price_df[price_df['Date'] == latest_date][['ticker', 'Close', 'Daily_Return']].copy()
    snapshot_df = snapshot_df.dropna(subset=['Daily_Return'])
    snapshot_df = snapshot_df.sort_values(by='Daily_Return', ascending=False)

    # Responsive columns
    rows = [snapshot_df.iloc[i:i+num_cols] for i in range(0, len(snapshot_df), num_cols)]

    st.markdown("""
    <style>
    .heatmap-card {
        background-color: var(--color);
        padding: 8px;
        border-radius: 8px;
        text-align: center;
        margin: 4px 0;
    }
    .card-title {
        color: white;
        font-weight: bold;
        line-height: 1.2;
        font-size: 4vw;
    }
    .card-value {
        color: white;
        font-size: 3.5vw;
    }

    /* Desktop override */
    @media (min-width: 768px) {
        .card-title {
            font-size: 18px !important;
        }
        .card-value {
            font-size: 16px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Then generate cards
    cols = st.columns(5)
    for i, (index, row) in enumerate(snapshot_df.iterrows()):
        with cols[i % 5]:
            color = 'green' if row['Daily_Return'] >= 0 else 'red'
            st.markdown(f"""
                <div class="heatmap-card" style="--color:{color}">
                    <div class="card-title">{row['ticker']}</div>
                    <div class="card-value">{row['Daily_Return']:.2f}%</div>
                </div>
            """, unsafe_allow_html=True)

    # Dividend History
    st.subheader(f"Stocks Dividend History")
    div_days = price_df[(price_df['Dividends'] > 0)]\
               .sort_values(by='Date')
    st.dataframe(div_days[['Date', 'ticker', 'Dividends']], use_container_width=True, hide_index=True)

# --- Footer ---
st.markdown("---")
st.markdown("<p style='text-align:center'>Made by Yadu • Powered by Streamlit & AWS</p>", unsafe_allow_html=True)
