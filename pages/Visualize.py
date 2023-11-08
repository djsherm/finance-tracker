import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import random
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

from Data import init_connection, init_db

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

st.title('Visualize')

conn = init_connection()
init_db(conn)

# Get date range from db
first_last_date = conn.execute('SELECT min(transaction_date), max(transaction_date) FROM tranx').fetchall()[0]

try:
    first_date = first_last_date[0]
    last_date = first_last_date[1]
except IndexError as e:
    print(e)
    st.warning('Please load data first.')
    st.stop()

date_range = st.slider(
    "Select Date Range",
    #value=(first_date, last_date),
    value=(datetime.strptime(first_date, '%m/%d/%Y').date(), datetime.strptime(last_date, '%m/%d/%Y').date()),
    format="MM/DD/YY")

# Get all positive valued transactions
incomes = conn.execute(
    """SELECT category,
                sum(case when cad$ >=0 then cad$ else 0 end) as income
        FROM tranx
        WHERE transaction_date >= ? and transaction_date <= ?
        GROUP BY category
        HAVING sum(case when cad$ >=0 then cad$ else 0 end) != 0
    """
, (date_range[0].strftime('%m/%d/%Y'), date_range[1].strftime('%m/%d/%Y'))).fetchall()

# Get all negative valued transactions
expenses = conn.execute(
    """SELECT category,
                sum(case when cad$ <0 then cad$ else 0 end) as expenses
        FROM tranx
        WHERE transaction_date >= ? and transaction_date <= ?
        GROUP BY category
        HAVING sum(case when cad$ <0 then cad$ else 0 end) != 0
    """
, (date_range[0].strftime('%m/%d/%Y'), date_range[1].strftime('%m/%d/%Y'))).fetchall()

incomes = dict(incomes)
expenses = dict(expenses)

# Create sankey chart
label = [x for x in incomes.keys()] + ["Total Income"] + [x for x in expenses.keys()]
source = list(range(len(incomes))) + [len(incomes)] * len(expenses)
target = [len(incomes)] * len(incomes) + [label.index(expense) for expense in expenses.keys()]
value = [x for x in incomes.values()] + [-1*x for x in expenses.values()]

node_colours = [px.colors.qualitative.Pastel1[i % len(px.colors.qualitative.Pastel1)] for i in range(len(label))]
link_colours = [node_colours[trgt].replace('rgb', 'rgba').replace(')', ',0.7)') for trgt in target]

# Data to dict, dict to sankey
link = dict(source=source, target=target, value=value, color=link_colours)
node = dict(label=label, pad=20, thickness=30, color=node_colours)
data = go.Sankey(link=link, node=node)

# Plot
fig = go.Figure(data)
fig.update_layout(margin=dict(l=0, r=0, t=5, b=5))
st.plotly_chart(fig, use_container_width=True)