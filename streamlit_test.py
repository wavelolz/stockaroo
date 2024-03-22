
import time
import streamlit as st
st.set_page_config(layout="wide")
import numpy as np
import pandas as pd
from FinMind.data import DataLoader
import ta
from ta.utils import dropna
import mysql.connector
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import mplfinance as mpf
import plotly.graph_objects as go


def GetConnection():
    db_connection = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="@Fk10150305msds",
    database="test"
    )
    return db_connection

def FetchDatasetList():
    conn = GetConnection()
    cursor = conn.cursor()
    query = "select table_name from information_schema.tables where table_schema = 'test';"
    cursor.execute(query)
    result = cursor.fetchall()
    stock_id_l = [i[0] for i in result]
    return stock_id_l

def FetchData(stock_id):
    conn = GetConnection()
    cursor = conn.cursor()
    query_data = f"select * from test.{stock_id}"
    cursor.execute(query_data)
    data = pd.DataFrame(cursor.fetchall())

    query_colnames = f"select distinct column_name from information_schema.columns where table_schema = 'test';"
    cursor.execute(query_colnames)
    colname = cursor.fetchall()
    colname = [i[0] for i in colname]
    data.columns = colname
    return data

def CleanData(data):
    filter_data = data.loc[data["close"] != 0]
    return filter_data

def ComputeTA(data):
    data["EMA5"] = ta.trend.EMAIndicator(data["close"], 5, False).ema_indicator()
    data["EMA10"] = ta.trend.EMAIndicator(data["close"], 10, False).ema_indicator()
    data["EMA20"] = ta.trend.EMAIndicator(data["close"], 20, False).ema_indicator()
    data["SMA5"] = ta.trend.SMAIndicator(data["close"], 5, False).sma_indicator()
    data["SMA10"] = ta.trend.SMAIndicator(data["close"], 10, False).sma_indicator()
    data["SMA20"] = ta.trend.SMAIndicator(data["close"], 20, False).sma_indicator()
    return data

def PrepareData(data):
    candle = data[["date", "Trading_Volume", "open", "close", "max", "min"]]
    candle.columns = ["date", "volume", "open", "close", "high", "low"]

    ta = data[["date", "EMA5", "EMA10", "EMA20", "SMA5", "SMA10", "SMA20"]]
    return [candle, ta]


def FilterDate(candle_data, ta_data, code):
    if code == 0:
        filter_candle_data = candle_data[-30:]
        filter_ta_data = ta_data[-30:]
    elif code == 1:
        filter_candle_data = candle_data[-90:]
        filter_ta_data = ta_data[-90:]
    elif code == 2:
        filter_candle_data = candle_data[-150:]
        filter_ta_data = ta_data[-150:]
    elif code == 3:
        filter_candle_data = candle_data[-365:]
        filter_ta_data = ta_data[-365:]
    elif code == 4:
        filter_candle_data = candle_data[-1825:]
        filter_ta_data = ta_data[-1825:]
    else:
        return [candle_data, ta_data]
    return [filter_candle_data, filter_ta_data]


    close = data["close"].to_list()
    colorList = ["blue"]
    for i in range(1, len(close), 1):
        if close[i] > close[i-1]:
            colorList.append("red")
        elif close[i] == close[i-1]:
            colorList.append("purple")
        else:
            colorList.append("green")
    return colorList 

stock_id_l = FetchDatasetList()

option = st.selectbox(
    "Stock List",
    stock_id_l
)

data = FetchData(option)
data = CleanData(data)
data = ComputeTA(data)
candle_data_all, ta_data_all = PrepareData(data)



genre_duration = st.radio(
    "請選擇繪圖日期長度",
    ["1月", "3月", "5月", "1年", "5年", "全部時間"],
    horizontal=True
    )

if genre_duration == '1月':
    candle_data_part, ta_data_part = FilterDate(candle_data_all, ta_data_all, 0)
elif genre_duration == '3月':
    candle_data_part, ta_data_part = FilterDate(candle_data_all, ta_data_all, 1)
elif genre_duration == '5月':
    candle_data_part, ta_data_part = FilterDate(candle_data_all, ta_data_all, 2)
elif genre_duration == '1年':
    candle_data_part, ta_data_part = FilterDate(candle_data_all, ta_data_all, 3)
elif genre_duration == '5年':
    candle_data_part, ta_data_part = FilterDate(candle_data_all, ta_data_all, 4)
else:
    candle_data_part, ta_data_part = FilterDate(candle_data_all, ta_data_all, 5)

genre_MA_select = st.radio(
    "均線選擇",
    ["SMA", "EMA"],
    )

if genre_MA_select == "EMA":
    ma5 = go.Scatter(x=ta_data_part["date"], y=ta_data_part["EMA5"], mode="lines", name="EMA5")
    ma10 = go.Scatter(x=ta_data_part["date"], y=ta_data_part["EMA10"], mode="lines", name="EMA10")
    ma20 = go.Scatter(x=ta_data_part["date"], y=ta_data_part["EMA20"], mode="lines", name="EMA20")
else:
    ma5 = go.Scatter(x=ta_data_part["date"], y=ta_data_part["SMA5"], mode="lines", name="SMA5")
    ma10 = go.Scatter(x=ta_data_part["date"], y=ta_data_part["SMA10"], mode="lines", name="SMA10")
    ma20 = go.Scatter(x=ta_data_part["date"], y=ta_data_part["SMA20"], mode="lines", name="SMA20")


candle = go.Candlestick(
    x=candle_data_part["date"], 
    open=candle_data_part["open"], 
    high=candle_data_part["high"], 
    low=candle_data_part["low"], 
    close=candle_data_part["close"]
    )

fig = go.Figure(data=[candle, ma5, ma10, ma20])
st.plotly_chart(fig)



