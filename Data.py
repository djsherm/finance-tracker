#import pymongo
import pandas as pd
import numpy as np
from datetime import datetime, date
import streamlit as st
#from bson.objectid import ObjectId

import sqlite3

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

def init_db(conn):
    conn.execute('CREATE TABLE IF NOT EXISTS tranx(id PRIMARY KEY, account_type, account_number, transaction_date, cad$, description, category)')
    conn.commit()

@st.cache_resource(hash_funcs={sqlite3.Connection: id})
def init_connection():
    '''Connect to SQLite db'''
    return sqlite3.connect('transactions.db', check_same_thread=False)

#@st.experimental_memo(ttl=600)
def get_data(conn):
    '''Return a list of all items in the db'''
    try:
        results_df = pd.read_sql('SELECT * FROM tranx', con=conn, index_col='id')
    except Exception as e:
        st.write(e)
        results_df = e
    
    return results_df

def insert_data(conn, df, cur_length):
    '''Inserts data into db'''
    df.index += cur_length
    try:
        df.to_sql(name='tranx', con=conn, if_exists='append', index_label='id')
    except Exception as e:
        st.write(e)

def update_rows(conn, edited_data):
    '''Update existing rows in db'''
    if len(edited_data) > 0:

        for idx in edited_data:
            update_query = f"UPDATE tranx SET " + ", ".join([f"{column} = ?" for column in edited_data[idx].keys()]) + " WHERE id = ?"
            values = [edited_data[idx][column] for column in edited_data[idx].keys()] + [idx]

            try:
                conn.execute(update_query, values)
            except Exception as e:
                st.write(e)

        conn.commit()

def add_rows(conn, new_data, tbl_length):
    '''Add new rows to db from data_editor'''
    if len(new_data) > 0:
        
        # Add index to new row
        for row in new_data:
            row['id'] = tbl_length
            tbl_length += 1

        columns = ', '.join(new_data[0].keys())
        placeholders = ', '.join(['?'] * len(new_data[0]))
        insert_query = f"INSERT INTO tranx ({columns}) VALUES ({placeholders})"

        for row_data in new_data:
            values = list(row_data.values())
            conn.execute(insert_query, values)
        
        conn.commit()

def delete_rows(conn, indices_to_delete):
    '''Delete existing rows from db'''
    if len(indices_to_delete) > 0:
        
        delete_query = f"DELETE FROM tranx WHERE id IN ({', '.join(map(str, indices_to_delete))})"
        try:
            conn.execute(delete_query)
        except Exception as e:
            st.write(e)
        conn.commit()

def format_data(df, bank='rbc'):
    '''Converts imported data from multiple banks into one format'''
    if bank == 'rbc':
        df.columns = map(str.lower, df.columns)
        df[['description_1', 'description_2']] = df[['description_1', 'description_2']] .fillna('')
        clean_df = df.drop(['description_1', 'description_2', 'usd$'], axis=1).copy()
        clean_df['description'] = df['description_1'] + ' ' + df['description_2']
        clean_df = clean_df[~clean_df['description'].isin(['MISC PAYMENT RBC CREDIT CARD', 'AUTOMATIC PAYMENT - THANK YOU', 'PAYMENT - THANK YOU / PAIEMENT - MERCI '])]
        clean_df['transaction_date'] = pd.to_datetime(clean_df['transaction_date']).dt.strftime("%m/%d/%Y")
        clean_df = clean_df.drop('cheque_number', axis=1)
        return clean_df
    else:
        return df

st.title('Import and Edit Data')

# Establish connection to db
conn = init_connection()
init_db(conn)

# Initialize classifier
classifier = Classifier()

# Load data
items_df = get_data(conn)

# Only load data into classifier if data exists
if not items_df.empty:
    classifier.load_data(items_df)
    table_length = items_df.shape[0]
else:
    table_length = 0

# Let user upload raw transaction data
with st.sidebar:
    with st.form('File Uploader', clear_on_submit=True):
        file = st.file_uploader('Import CSV', type='csv')
        submitted = st.form_submit_button('Import')
        raw = None

        if submitted and file:
            st.session_state["uploaded_files"] = file

            raw = pd.read_csv(file, encoding='utf-8')
            raw.columns = raw.columns.str.replace(' ', '_')
            formatted = format_data(raw)

            # Do no try to predict categories if less than 10 entries have been categorized
            if not items_df.empty:
                print('Category length', (items_df['category'] != '').sum())
                if (items_df['category'] != '').sum() <= 10:
                    formatted['category'] = ''
                else:
                    formatted['category'] = classifier.predict(formatted['description'])
                    print(formatted['description'])
                    print(formatted['category'])
            else:
                formatted['category'] = ''

            inserted = insert_data(conn, formatted, table_length)
            st.rerun()

    delete_col = st.button('Delete Table')
    if delete_col:
        conn.execute('DROP TABLE IF EXISTS tranx')
        st.session_state['table_length'] = 0
    
if len(items_df) > 0:
    # Configure columns for editable dataframe
    column_config = {
        'account_type': st.column_config.TextColumn(
            required=True,
            default='Credit Card'
        ),
        'account_number': st.column_config.NumberColumn(
            required=True,
            default=0
        ),
        'transaction_date': st.column_config.TextColumn(
            required=True,
            default=date.today().strftime('%m/%d/%Y')
        ),
        'cad$': st.column_config.NumberColumn(
            required=True,
            format='$ %.2f',
            default=0.00
        ),
        'description': st.column_config.TextColumn(
            required=True,
            default='Edit Description'
        ),
        'category': st.column_config.TextColumn(
            required=True,
            default='Edit Category'
        )
    }

    st.data_editor(items_df, key='data_editor', hide_index=True, num_rows='dynamic', height=((table_length+1) * 35 + 3), use_container_width=True, column_config=column_config)
    edit_button = st.button('Confirm')

    # Push changes on button press
    if edit_button:
        update_rows(conn, st.session_state['data_editor']['edited_rows'])
        add_rows(conn, st.session_state['data_editor']['added_rows'], table_length)
        delete_rows(conn, st.session_state['data_editor']['deleted_rows'])

        st.success('Data updated')
        


