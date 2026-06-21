# -*- coding: utf-8 -*-
from datetime import datetime
import pandas as pd
import streamlit as st
import yfinance as yf

# 1. Page Configuration
st.set_page_config(page_title="Boris Quant & News Radar", layout="wide")
st.title("⚡ Boris Personal Portfolio, Quant & News Radar")

# 2. Portfolio Watchlist
PORTFOLIO = ["SOXL", "NVDA", "TSLA", "PLTR", "AMD", "QQQ", "TQQQ"]

# 3. Sidebar Control Panel
st.sidebar.header("⚙️ Radar Settings")
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=True)
refresh_interval = st.sidebar.slider(
    "Refresh Interval (seconds)", min_value=10, max_value=60, value=30
)

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.sidebar.write(f"🕒 Last Updated: {current_time}")

# --- 核心安全刷新引擎：HTML 元标签刷新 ---
if auto_refresh:
    html_refresh_code = f"""
    <meta http-equiv="refresh" content="{refresh_interval}">
    """
    st.components.v1.html(html_refresh_code, height=0, width=0)

# 4. Core Quant Table
st.subheader("📊 Intraday Technical Levels & Changes")

portfolio_data = []
active_tickers_info = {}

with st.spinner("Fetching data and calculating intraday pivots..."):
    for ticker_symbol in PORTFOLIO:
        try:
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period="2mo")
            if df.empty:
                continue

            # ✨ 核心优化 1：去除因交易所闭盘或时区导致的重复日期行
            df = df.loc[~df.index.duplicated(keep='last')]

            # Bollinger Bands
            df["MA20"] = df["Close"].rolling(20).mean()
            df["STD20"] = df["Close"].rolling(20).std()
            df["Lower_Band"] = df["MA20"] - (df["STD20"] * 2)

            if len(df) < 2:
                continue

            # ✨ 核心优化 2：精准动态回溯，确保完美计算枢轴点（Pivot Points）
            latest_day = df.iloc[-1]
            prev_day = df.iloc[-2]  # 确保定位到前一个真实的完整交易日

            prev_high = prev_day["High"]
            prev_low = prev_day["Low"]
            prev_close = prev_day["Close"]

            # 经典 Pivot 计算公式
            pivot = (prev_high + prev_low + prev_close) / 3
            r1_resistance = (2 * pivot) - prev_low
            s1_support = (2 * pivot) - prev_high

            close_price = latest_day["Close"]

            # Calculate Price Change
            prev_close_price = ticker.info.get("previousClose", latest_day["Open"])
            percent_change = ((close_price - prev_close_price) / prev_close_price) * 100

            stock_data = {
                "Ticker": ticker_symbol,
                "Current Price": round(close_price, 2),
                "Daily Change": f"{'+' if percent_change >= 0 else ''}{round(percent_change, 2)}%",
                "Intraday Resistance": round(r1_resistance, 2),
                "Intraday Support": round(s1_support, 2),
                "Bollinger Lower Band": round(latest_day["Lower_Band"], 2),
                "Status": "OVERSOLD" if close_price < latest_day["Lower_Band"] else "NORMAL",
            }

            portfolio_data.append(stock_data)
            active_tickers_info[ticker_symbol] = {"change_pct": percent_change}

        except Exception as e:
            st.error(f"Error processing {ticker_symbol}: {e}")

    if portfolio_data:
        df_portfolio = pd.DataFrame(portfolio_data)
        st.dataframe(df_portfolio, use_container_width=True)
    else:
        st.info("No stock data returned.")

st.markdown("---")

# 5. Live News Streaming & Macro Grid
col_news, col_macro = st.columns([2, 1])

with col_news:
    st.subheader("📰 Live Portfolio News Stream")
    
    news_placeholder = st.container()
    
    with news_placeholder:
        all_news = []
        for ticker_symbol in PORTFOLIO:
            try:
                ticker = yf.Ticker(ticker_symbol)
                news_list = ticker.news
                if news_list:
                    for item in news_list[:3]:
                        content = item.get("content", item)
                        
                        title = content.get("title", item.get("title", "No Title"))
                        link = content.get("clickThroughUrl", {}).get("url", content.get("link", item.get("link", "#")))
                        if not link or link == "#":
                            link = item.get("url", "#")
                            
                        publisher = content.get("provider", {}).get("displayName", content.get("publisher", item.get("publisher", "Unknown")))
                        pub_timestamp = content.get("pubDate", item.get("providerPublishTime", 0))
                        
                        if isinstance(pub_timestamp, str):
                            try:
                                pub_time = datetime.strptime(pub_timestamp[:16], "%Y-%m-%dT%H:%M").strftime("%m-%d %H:%M")
                            except:
                                pub_time = str(pub_timestamp)
                        elif isinstance(pub_timestamp, (int, float)) and pub_timestamp > 0:
                            try:
                                pub_time = datetime.fromtimestamp(pub_timestamp).strftime("%m-%d %H:%M")
                            except:
                                pub_time = f"Recent ({pub_timestamp})"
                        else:
                            pub_time = "Recent Data"
                        
                        perf_pct = active_tickers_info.get(ticker_symbol, {}).get("change_pct", 0)

                        all_news.append({
                            "Ticker": ticker_symbol,
                            "Perf": perf_pct,
                            "Time": str(pub_time),
                            "Title": title,
                            "Publisher": publisher,
                            "Link": link,
                        })
            except Exception:
                pass

        if all_news:
            df_news = pd.DataFrame(all_news).sort_values(by="Time", ascending=False)
            for _, row in df_news.iterrows():
                tag = ""
                if row["Perf"] > 3.0: tag = "🔥 [SURGING]"
                elif row["Perf"] < -3.0: tag = "🚨 [DROPPING]"

                st.markdown(
                    f"✨ **[{row['Time']}] {tag} {row['Ticker']} ({round(row['Perf'], 2)}%)**\n"
                    f"*{row['Title']}* (Source: {row['Publisher']})  \n"
                    f"🔗 **[Click Here to Open Full Article]({row['Link']})**"
                )
                st.markdown("---")
        else:
            st.info("No incoming news stream found at the moment.")

with col_macro:
    st.subheader("🚨 Macro Data Reminders")
    st.info("**Weekly Jobless Claims**\n\nEvery Thursday at 8:30 AM EST. Impacts QQQ.")
    st.warning("**CPI / Inflation Report**\n\nMonthly release. Shifter for NVDA & SOXL.")
    st.error("**FOMC Interest Rate Decision**\n\nEvery 6 weeks on Wednesday at 2:00 PM EST.")