import pymongo
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
from bson.objectid import ObjectId

from Classifier import Classifier

st.set_page_config(page_title='Import Data', layout='wide')

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

@st.cache_resource
def init_connection():
    '''Connect to local MongoDB server'''
    return pymongo.MongoClient("mongodb://localhost:27017/")

#@st.experimental_memo(ttl=600)
def get_data():
    '''Return a list of all items in the db'''
    items = list(tranx.find()) # make hashable for st.experimental_memo
    return items

def insert_data(df):
    '''Inserts dataframe into db'''
    return tranx.insert_many(df.to_dict('records'))

def update_data(id, field, value):
    '''Updates existing entry in the db'''
    tranx.update_one({'_id' : ObjectId(id)},
                        {'$set': {
                            field : value
                        }})

def format_data(df, bank='rbc'):
    '''Converts imported data from multiple banks into one format'''
    if bank == 'rbc':
        df[['Description_1', 'Description_2']] = df[['Description_1', 'Description_2']] .fillna('')
        clean_df = df.drop(['Description_1', 'Description_2', 'USD$'], axis=1).copy()
        clean_df['Description'] = df['Description_1'] + ' ' + df['Description_2']
        clean_df = clean_df[~clean_df['Description'].isin(['MISC PAYMENT RBC CREDIT CARD', 'AUTOMATIC PAYMENT - THANK YOU', 'PAYMENT - THANK YOU / PAIEMENT - MERCI '])]
        clean_df['Transaction_Date'] = pd.to_datetime(clean_df['Transaction_Date'], infer_datetime_format=True)
        return clean_df
    else:
        return df

st.title('Import and Edit Data')

# Establish connection to db and load collection
client = init_connection()
db = client['mydb']
tranx = db['tranx']

# Initialize classifier
classifier = Classifier()

# Load data
items = get_data()
items_df = pd.DataFrame(items)
#items_df = items_df.astype(str) # Bug in PyArrow doesn't allow conversion of numpy dtypes so dataframe must be converted to strings

# Only load data into classifier if data exists
if not items_df.empty:
    classifier.load_data(items_df)

# Let user upload raw transaction data
with st.sidebar:
    with st.form('File Uploader', clear_on_submit=True):
        file = st.file_uploader('Import data', type='csv')
        submitted = st.form_submit_button('Upload')
        raw = None

        if submitted and file is not None:
            raw = pd.read_csv(file, encoding='utf-8')
            raw.columns = raw.columns.str.replace(' ', '_')
            formatted = format_data(raw)

            # Do no try to predict categories if less than 10 entries have categories
            if not items_df.empty:
                if (items_df['Category'] != '').sum() <= 10:
                    formatted['Category'] = ''
                else:
                    formatted['Category'] = classifier.predict(formatted['Description'])
                    st.write(formatted['Description'])
                    st.write(formatted['Category'])
            else:
                formatted['Category'] = ''

            inserted = insert_data(formatted)
            st.experimental_rerun()

    delete_col = st.button('Delete Collection')
    if delete_col:
        tranx.drop()
    
if len(items_df) > 0:
    with st.form('Edit Data'):
        st.experimental_data_editor(items_df.drop('_id', axis=1), key='data_editor')
        edit_button = st.form_submit_button('Update')

        if edit_button:
            row_list = [] # Keep track of row indexes so we know which rows to update
            for key, value in st.session_state['data_editor']['edited_cells'].items():
                idx = key.split(':')
                idx = [int(x) for x in idx]
                row_list.append(idx[0])
                
                # Get the id and field name of the cells that need to be upated
                update_id = items_df.loc[idx[0], '_id']
                update_field = items_df.columns[idx[1]]
                update_data(update_id, update_field, value)

