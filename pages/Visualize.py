import pandas as pd
import numpy as np
import streamlit as st
import random
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

from Data import init_connection

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

st.title('Visualize')

client = init_connection()
db = client['mydb']
tranx = db['tranx']

# Get first and last date in db
first_last_date = list(tranx.aggregate([
        {'$sort': {'Transaction_Date': 1}},
        {'$group': {'_id': None, 'first': {'$first': '$Transaction_Date'}, 'last': {'$last': '$Transaction_Date'}}}
    ]))

try:
    first_date = first_last_date[0]['first']
    last_date = first_last_date[0]['last']
except IndexError:
    st.warning('Please load data first.')
    st.stop()

date_range = st.slider(
    "Select Date Range",
    value=(first_date, last_date),
    #value=(datetime.strptime(first_date, '%m/%d/%Y'), datetime.strptime(last_date, '%m/%d/%Y')),
    format="MM/DD/YY")

# Query collection and get an aggregate of the data grouped by category for both income and expenses
agg = pd.DataFrame(list(tranx.aggregate(
    [{
        '$match': {'$and': [{'Transaction_Date': {'$gte': date_range[0]}}, {'Transaction_Date': {'$lte': date_range[1]}}]}
    },
    {
        '$group':
            {'_id': '$Category',
            'Total': {'$sum': '$CAD$'}
            }
    }]
)))

incomes = agg[agg['Total'] > 0].to_dict('records')
expenses = agg[agg['Total'] < 0].to_dict('records')

# Create sankey chart
label = [x['_id'] for x in incomes] + ["Total Income"] + [x['_id'] for x in expenses]
source = list(range(len(incomes))) + [len(incomes)] * len(expenses)
target = [len(incomes)] * len(incomes) + [label.index(expense['_id']) for expense in expenses]
value = [x['Total'] for x in incomes] + [-1*x['Total'] for x in expenses]

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