# 📈 Indian Stock Sentiment Analytics

This project builds a data pipeline using AWS + Databricks to analyze stock price trends and news sentiment for Indian equities.

## Features
- Fetch daily stock prices from NSE using `yfinance`
- Scrape financial headlines via Google News RSS
- Run sentiment scoring using VADER
- Store data in AWS S3 and process with PySpark
- Query enriched sentiment tables using Delta Lake
- Visualize using Databricks SQL

## Tech Stack
- AWS S3 (Storage)
- Databricks (PySpark, Delta Lake, SQL, Workflows)
- Python for ingestion
- VADER/TextBlob for sentiment
- Streamlit for Dashboard

## Folder Structure
Refer to main project folder structure above.
```bash
stockanalysis/
├── ingest/
│   ├── get_data.ipynb
├── transform/
│   ├── bronze_to_silver_transformation.ipynb
│   ├── silver_to_gold_transformation.ipynb
├── dashboards/
│   └── app.py
├── README.md
├── requirements.txt
└── architecture.png
```
## Setup
1. Create an S3 bucket (e.g., `stock-sentiment-pipeline`) and store credentials
2. Run `get_data.ipynb` to store price data, collect and score headlines
4. Open Databricks notebook `bronze_to_silver_transformation.ipynb` to load data to Delta, and perform checks for null values and duplicates
5. Use `silver_to_gold_transformation.ipynb` for creating calculated columns, joining with sentiment data and advanced transformations
6. Visualize in dashboard

## WIP
- Airflow for automation
- 
## Data Sources
- https://nseindia.com
- https://news.google.com/rss/search?q=stock+market+india

## License
MIT
