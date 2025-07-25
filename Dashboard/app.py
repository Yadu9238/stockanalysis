import streamlit as st
import pandas as pd
import plotly.express as px
import s3fs

# --- CONFIG ---
st.set_page_config(page_title="Stock & Sentiment Dashboard", layout="wide")

# --- AWS credentials from secrets ---
aws_id = st.secrets["aws"]["aws_access"]
aws_secret = st.secrets["aws"]["aws_secret"]
#print(aws_id,aws_secret)
# --- Set up S3 filesystem ---
fs = s3fs.S3FileSystem(
    key=aws_id,
    secret=aws_secret
)
stock_path = "s3://stock-analysis-yk/agg-data/stockdata/"
sentiment_path = "s3://stock-analysis-yk/agg-data/stocksentiment/"
# --- LOAD DATA ---
@st.cache_data

def load_s3_data(s3_path):
    fs = s3fs.S3FileSystem(
    key=aws_id,
    secret=aws_secret
)
    files = [f"s3://{f}" for f in fs.ls(s3_path) if "part" in f and f.endswith(".csv")]
    return pd.concat([pd.read_csv(f) for f in files])



sentiment_df = load_s3_data(sentiment_path)
price_df = load_s3_data(stock_path)

# --- PAGE SETTINGS ---
st.set_page_config(layout="wide")
st.markdown("""
    <div style='text-align: center; padding-bottom: 10px;'>
        <h1 style='margin-bottom: 0;'>📊 Stock & Sentiment Dashboard</h1>
        <p style='font-size: 18px; color: gray;'>Visualize market movements and public sentiment together.</p>
    </div>
""", unsafe_allow_html=True)

# --- LATEST SNAPSHOT ---
latest_date = price_df['Date'].max()
snapshot_df = price_df[price_df['Date'] == latest_date][['ticker', 'Close', 'Daily_Return']].dropna()
snapshot_df = snapshot_df.sort_values(by='Daily_Return', ascending=False)

# --- HEATMAP + ANALYSIS LAYOUT ---

left_col, right_col = st.columns([3, 2])

# LEFT: Select stock and show detailed analysis
with left_col:
    tickers = sorted(price_df["ticker"].unique())
    selected_ticker = st.selectbox("Select a Stock", tickers)

    sentiment_filtered = sentiment_df[sentiment_df["ticker"] == selected_ticker].sort_values("Date")
    price_filtered = price_df[price_df["ticker"] == selected_ticker].sort_values("Date")

    # 1. Sentiment vs Price Change
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    st.header("📈 Technical Indicators")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(x=price_filtered["Date"], y=price_filtered["Close"],
               name="Close Price", line=dict(color="skyblue")),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=sentiment_filtered["Date"], y=sentiment_filtered["Sentiment_Score"],
               name="Sentiment Score", line=dict(color="orange")),
        secondary_y=True
    )   

    fig.update_layout(
        title_text=f"{selected_ticker} - Price vs Sentiment",
            template="plotly_dark"
        )
    fig.update_yaxes(title_text="Close Price", secondary_y=False)
    fig.update_yaxes(title_text="Sentiment Score", secondary_y=True)

    # Moving Averages
    stock_df = price_df[price_df["ticker"] == selected_ticker].sort_values("Date")
    melted = stock_df.melt(id_vars="Date", value_vars=["Close", "MA_7", "MA_14"],
                      var_name="Metric", value_name="Value")
    fig5 = px.line(melted, x="Date", y="Value", color="Metric",
              title=f"{selected_ticker} - Close & Moving Averages")

    st.plotly_chart(fig5, use_container_width=True)

    # Volatility

    fig6 = px.line(price_filtered, x="Date", y="Volatility_7",
               title=f"7-Day Volatility - {selected_ticker}")
    st.plotly_chart(fig6, use_container_width=True)

    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader(f"Stock Volume Movement Average {selected_ticker}")
    price_filtered["vol_ma_7"] = price_filtered["Volume"].rolling(7).mean()

    fig_vol = px.line(price_filtered, x="Date", y=["Volume", "vol_ma_7"],
                  title="Volume & 7-Day Avg", template="plotly_dark")
    st.plotly_chart(fig_vol, use_container_width=True)


    st.subheader(f"Top Bullish Days for {selected_ticker}")
    top_days = sentiment_filtered[sentiment_filtered['sentiment_label'] == 'Bullish']\
           .sort_values(by='Sentiment_Score', ascending=False).head(5)
    st.dataframe(top_days[['Date', 'Sentiment_Score', 'Daily_Return']])

# RIGHT: Heatmap-style percentage boxes
with right_col:
    st.header("📌 Market Overview")
    latest_date = price_df['Date'].max()
    snapshot_df = price_df[price_df['Date'] == latest_date][['ticker', 'Close', 'Daily_Return']].copy()
    snapshot_df = snapshot_df.dropna(subset=['Daily_Return'])

    # sort by top movers
    snapshot_df = snapshot_df.sort_values(by='Daily_Return', ascending=False)

    cols = st.columns(5)
    for i, (index, row) in enumerate(snapshot_df.iterrows()):
        with cols[i % 5]:
            color = 'green' if row['Daily_Return'] >= 0 else 'red'
            st.markdown(f"""
            <div style='background-color:{color};padding:10px;border-radius:10px'>
                <h5 style='color:white;text-align:center'>{row['ticker']}</h5>
                <h6 style='color:white;text-align:center'>{row['Daily_Return']:.2f}%</h6>
            </div>
        """, unsafe_allow_html=True)
    # --- TECHNICAL ANALYSIS ---
    st.subheader(f"Stocks Dividend History{selected_ticker}")
    div_days = price_df[price_df['Dividends']>0]\
           .sort_values(by='Date')


    st.dataframe(div_days[['Date', 'ticker', 'Dividends']], use_container_width=True, hide_index=True)

    





# Footer
st.markdown("---")
st.markdown("Made by Yadu • Powered by Streamlit & AWS")
