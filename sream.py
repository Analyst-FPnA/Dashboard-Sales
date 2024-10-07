import streamlit as st
import requests
import zipfile
import io
import pandas as pd
import os
import gdown
import tempfile
import matplotlib.pyplot as plt
import seaborn as sns

import plotly.graph_objs as go

st.set_page_config(layout="wide")

def download_file_from_google_drive(file_id, dest_path):
    if not os.path.exists(dest_path):
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, dest_path, quiet=False)

file_id = '1HKQGDtuD5jh8Fj1XMJ-AEAKPMTnSeIBm'
dest_path = f'downloaded_file.zip'
download_file_from_google_drive(file_id, dest_path)


if 'Penjualan.csv' not in os.listdir():
    with zipfile.ZipFile(f'downloaded_file.zip', 'r') as z:
        dfs = []
        for file in z.namelist():
            with z.open(file_name) as f:
                df = pd.read_html(f)[0]
                df = df[df.iloc[1:,].columns[df.iloc[1:,].apply(lambda col: col.astype(str).str.contains('Rp', case=False, na=False).any())]]
                df.columns = df.iloc[0,:]
                df = df.iloc[2:,:-2].iloc[:-1].drop(columns='OFFLINE')
                df.iloc[:,1:] = df.iloc[:,1:].astype(float)
                df['ONLINE LAINNYA'] = df.iloc[:,9:].astype(float).sum(axis=1)
                df = df.iloc[:,[i for i in range(0,9)]+[-1]]
                df = df.melt(id_vars=['RESTO'], value_vars=df.iloc[:,1:].columns,value_name='RP',var_name='CATEGORY')
                df['TYPE'] = df['CATEGORY'].apply(lambda x: x if x=='DINE IN' else 'TAKE AWAY')
                df['PAYMENT'] = df['CATEGORY'].apply(lambda x: 'OFFLINE' if x in ['DINE IN','TAKE AWAY'] else 'ONLINE')
                df = df.sort_values(['RESTO','PAYMENT']).reset_index(drop=True)
                df['MONTH'] = re.findall(r'_(\w+)', file)[-1]
                dfs.append(df)
        pd.concat(dfs, ignore_index=True).to_csv('Penjualan.csv',index=False)

if 'df_sales' not in locals():
    df_sales = pd.read_csv('Penjualan.csv')

list_bulan = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December']

df_sales['MONTH'] = pd.Categorical(df_sales['MONTH'], categories=[x for x in list_bulan if x in df_sales['MONTH'].unique()], ordered=True)
df_line = df.groupby(['MONTH','TYPE'])['RP'].sum().reset_index()#.pivot(index=['TYPE'],columns='MONTH',values='RP')

# Data untuk line chart pertama (Sales)
months = df_line[['MONTH']].drop_duplicates()['MONTH'].tolist()
sales_1 = df_line[df_line['TYPE']=='DINE IN']['RP'].tolist()
sales_2 = df_line[df_line['TYPE']=='TAKE AWAY']['RP'].tolist()

# Menghitung persentase kenaikan atau penurunan untuk kedua line chart
percentage_change_1 = [(sales_1[i] - sales_1[i-1]) / sales_1[i-1] * 100 if i > 0 else 0 for i in range(len(sales_1))]
percentage_change_2 = [(sales_2[i] - sales_2[i-1]) / sales_2[i-1] * 100 if i > 0 else 0 for i in range(len(sales_2))]

# Membuat grafik line chart dengan 2 trace
fig = go.Figure()

# Line chart pertama (Sales 1)
fig.add_trace(go.Scatter(
    x=months, 
    y=sales_1, 
    mode='lines+markers', 
    name='DINE IN',
    line=dict(color='dodgerblue', width=3)
))

# Line chart kedua (Sales 2)
fig.add_trace(go.Scatter(
    x=months, 
    y=sales_2, 
    mode='lines+markers', 
    name='TAKE AWAY',
    line=dict(color='orange', width=3)
))

# Menambahkan anotasi persentase untuk Sales 1
for i in range(1, len(sales_1)):
    change = percentage_change_1[i]
    arrow = "↑" if change > 0 else "↓"
    color = "green" if change > 0 else "red"
    
    fig.add_annotation(
        x=months[i],
        y=sales_1[i],
        text=f"{arrow} {abs(change):.2f}%",  # Menambahkan simbol panah
        showarrow=True,
        arrowhead=0,
        ax=0,
        ay=-40,
        font=dict(color=color)  # Menyesuaikan warna panah
    )


# Menambahkan anotasi persentase untuk Sales 2
for i in range(1, len(sales_2)):
    change = percentage_change_2[i]
    arrow = "↑" if change > 0 else "↓"
    color = "green" if change > 0 else "red"
    
    fig.add_annotation(
        x=months[i],
        y=sales_2[i],
        text=f"{arrow} {abs(change):.2f}%",  # Menambahkan simbol panah
        showarrow=True,
        arrowhead=0,
        ax=0,
        ay=-40,
        font=dict(color=color)  # Menyesuaikan warna panah
    )


# Mengubah layout untuk lebih jelas
fig.update_layout(
    title="Sales with Percentage Change (2 Line Charts)",
    xaxis_title="Month",
    yaxis_title="Sales",
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)
