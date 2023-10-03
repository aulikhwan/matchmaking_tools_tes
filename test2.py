
from datetime import datetime, date
import altair as alt
import pandas as pd
# from metabase import get_df_from_question
# import pandas_ta as ta  # noqa
import streamlit as st
#import talib
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np


icon = Image.open("icon.ico")
logo = Image.open("logo1.png")

st.set_page_config(
    page_title="Merlin Alpha | Shrimp Supply Demand Matchmaking ",
    layout="wide",
    page_icon=icon
)

page_bg_img = f"""
<style>
[data-testid="stSidebar"] > div:first-child {{
background-color: #32BB9F;
background-position: center; 
background-repeat: no-repeat;
background-attachment: fixed;
}}

[data-testid="stHeader"] {{
background: rgba(0,0,0,0);
}}
"""

st.markdown(page_bg_img, unsafe_allow_html=True)

today = pd.to_datetime(date.today())


st.title("Shrimp Supply-Demand Matchmaking Tools")

###### Input Dataset #######

@st.cache_data
def all_demand():
    df = pd.read_csv('35243.csv')
    df['row_number_demand'] = df['row_number']
    return df 

@st.cache_data
def all_supply():
    df = pd.read_csv('35245.csv')
    return df 

# @st.cache_data
# def get_demand_section():
#     data = pd.read_csv('dataprep - table 1.csv')
#     data['demand_id'] = data['row_number_demand']
#     df = data[['demand_id','customer_name','customer_area','customer_location','demand_month'
#                ,'po_number','ordered_sku_code','ordered_sku_name'
#                ,'ordered_sku_type','etd_type','etd','raw_material_size_size'
#                ,'total_rm_kg','order_notes']]
#     return df 

@st.cache_data
def get_supply_section():
    df = pd.read_csv('35308.csv')
    return df 

@st.cache_data
def get_supply_detail_section():
    df = pd.read_csv('35315.csv')
    return df 

@st.cache_data
def monthly_supply():
    df_supply = pd.read_csv('35245.csv')
    df_fulfilled = pd.read_csv('35315.csv')
    #df_demand = pd.read_csv('demand_data.csv')
    df_supply['supply_values'] = df_supply['estimated_harvest_tonnage'] * 1000
    df_fulfilled['demand_values'] = df_fulfilled['estimated_harvest_kg'] 
    df_supply['estimated_harvest_date'] = pd.to_datetime(df_supply['estimated_harvest_date'])
    df_fulfilled['estimated_harvest_date'] = pd.to_datetime(df_fulfilled['estimated_harvest_date'])


    df_fulfilled['month'] = df_fulfilled['estimated_harvest_date'].dt.strftime('%Y-%m')
    df_supply['month'] = df_supply['estimated_harvest_date'].dt.strftime('%Y-%m')

    monthly_supply = df_supply.groupby('month')['supply_values'].sum()
    monthly_fufilled = df_fulfilled.groupby('month')['demand_values'].sum()

    combined_data = pd.DataFrame({'Month': monthly_supply.index, 'Supply': monthly_supply.values, 'Supply Fulfilled': monthly_fufilled.reindex(monthly_supply.index, fill_value=0).values})
    
    return combined_data

@st.cache_data
def monthly_demand():
    df_demand = pd.read_csv('35243.csv')
    df_fulfilled = pd.read_csv('35308.csv')
    #df_demand = pd.read_csv('demand_data.csv')
    df_demand['row_number_demand'] = df_demand['row_number']
    df_demand['etd'] = pd.to_datetime(df_demand['etd'])
    df_demand['month'] = df_demand['etd'].dt.strftime('%Y-%m')

    df_fulfilled_demand = df_fulfilled.merge(df_demand, on='row_number_demand').loc[df_fulfilled['is_fulfilled_demand'] == 'yes']
    df_fulfilled_demand = df_fulfilled_demand[df_fulfilled_demand['priority'] == 1]

    df_fulfilled_demand['etd'] = pd.to_datetime(df_demand['etd'])
    df_fulfilled_demand['month_et'] = df_demand['etd'].dt.strftime('%Y-%m')
    
    monthly_demand= df_demand.groupby('month')['total_rm_kg'].sum()
    monthly_fufilled = df_fulfilled_demand.groupby('month_et')['total_rm_kg'].sum()

    combined_data = pd.DataFrame({'Month': monthly_demand.index, 'Demand': monthly_demand.values, 'Demand Fulfilled': monthly_fufilled.reindex(monthly_demand.index, fill_value=0).values})
    
    return combined_data

demand_all = all_demand()
supply_all = all_supply()
# demand = get_demand_section()
supply = get_supply_section()
supply_detail = get_supply_detail_section()
supply_trend = monthly_supply()
demand_trend = monthly_demand()




###### Overview of Main Metrics #######

st.divider()

st.markdown('## Overall')

total_demand,total_supply, total_demand_fulfilled, perc_full = st.columns(4)

with total_demand:
    td = round(demand_all['total_rm_kg'].sum(),2)
    st.metric(
        "Total Overall Demand (in KG)",
        '{:,.0f}'.format(td)
    )
    st.markdown('<span style="font-size: 9px;"> <i>Total of Overall Biomass Demand Quantity</i><span>', unsafe_allow_html=True)


with total_supply:
    ts = round(supply_all['estimated_harvest_tonnage'].sum()*1000,2)
    st.metric(
        "Total Overall Supply (in KG)",
        '{:,.0f}'.format(ts)
    )
    st.markdown('<span style="font-size: 9px;"> <i>Total of Overall Biomass Supply Quantity</i><span>', unsafe_allow_html=True)

with total_demand_fulfilled:
    tdf = round(demand_trend['Demand Fulfilled'].sum(),2)
    st.metric(
        "Total Overall Demand Fulfilled (in KG)",
        '{:,.0f}'.format(tdf)
    )
    st.markdown('<span style="font-size: 9px;"> <i>Total of Overall Biomass Demand Fulfilled by Available Supply</i><span>', unsafe_allow_html=True)

with perc_full:
    # fulfilled_demand = supply[supply['pct_fulfilled_demand_qty'] >= 100] #ganti pake flag is_fulfilled = 'yes'
    # sum_demand = fulfilled_demand['demand_id'].nunique()
    # perc = (sum_demand/demand['demand_id'].nunique())*100
    perc = (demand_trend['Demand Fulfilled'].sum()/demand_all['total_rm_kg'].sum())*100
    st.metric(
        "Percentage of Demand Fulfilled",
        '{:.2f}%'.format(perc)
        
    )
    st.markdown('<span style="font-size: 9px;"> <i>Percentage of Demand Quantity which Fulfilled (KG) by Available Supply divided by Overall Demand Quantity(KG)</i><span>', unsafe_allow_html=True)

st.divider()

###### Bar chart for supply demand trend #######

st.markdown('## Supply-Demand Trend')

supply_1, demand_1, demand_ful = st.columns(3)

with supply_1:
     
    chart = alt.Chart(supply_trend).mark_bar().encode(
        x=alt.X('Month', title='Estimated Harvest Time (Month)'),  # Specify the X-axis title
        y=alt.Y('Supply', title='Supply Quantity (KG)'),  # Specify the Y-axis title
        color=alt.value('blue'),
        tooltip=['Month', 'Supply']
    ).properties(
        title='Monthly Supply Quantity (in KG)'
    )
    st.altair_chart(chart, use_container_width=True)
    st.markdown('<span style="font-size: 9px;"> <i>Showing information of Monthly Total Quantity of Biomass Supply</i><span>', unsafe_allow_html=True)   

with demand_1:   
    chart = alt.Chart(demand_trend).mark_bar().encode(
        x=alt.X('Month', title='Estimated Time Delivery (Month)'),  # Specify the X-axis title
        y=alt.Y('Demand', title='Demand Quantity (KG)'),  # Specify the Y-axis title
        color=alt.value('blue'),
        tooltip=['Month', 'Demand']
    ).properties(
        title='Monthly Demand Quantity (in KG)'
    )
    st.altair_chart(chart, use_container_width=True)
    st.markdown('<span style="font-size: 9px;"> <i>Showing information of Monthly Total Quantity of Biomass Demand</i><span>', unsafe_allow_html=True)   


with demand_ful:   
    chart = alt.Chart(demand_trend).mark_bar().encode(
        x=alt.X('Month', title='Estimated Time Delivery (Month)'),  # Specify the X-axis title
        y=alt.Y('Demand Fulfilled', title='Demand Fulfilled (KG)'),  # Specify the Y-axis title
        color=alt.value('blue'),
        tooltip=['Month', 'Demand Fulfilled']
    ).properties(
        title='Monthly Demand Fulfilled (in KG)'
    )
    st.altair_chart(chart, use_container_width=True)
    st.markdown('<span style="font-size: 9px;"> <i>Showing information of Monthly Total Quantity of Biomass Demand Fully Fulfilled by Available Supply </i><span>', unsafe_allow_html=True)   


###### Filtered Row Number of Demand #######

st.divider()
    
st.markdown('<p style="font-size: 18px;"> <i>How To use: </i><p>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 15px; margin-top: 5px;"> <i>Select Row Number Demand to show what combination of harvest plan ID that will fullfil and detail of information of supply (including estimated harvest time, distance to processing, etc.) </i><p>', unsafe_allow_html=True)

url = 'https://bi-dash.efishery.com/question/35243-shrimp-raw-data-export-demand'
st.markdown('Row Numbers Demand are referred to this [link](%s)' %url)


# (
#     demand_col,
#     po_num
# ) = st.columns(2)

# with demand_col:
demand_filter = st.multiselect("Please Select Row Number Demand",  demand_all["row_number_demand"].unique().tolist(),default=demand_all["row_number_demand"].unique().tolist())

# with po_num:
#     po_num_filter = st.selectbox("Please Select PO Number", demand_all["po_number"].unique())

#Demand section
st.subheader("Demand Section")
st.markdown('<span style="font-size: 10px;"> <i>This table consists of information about the detail of demand requirements</i><span>', unsafe_allow_html=True)
st.dataframe(demand_all[demand_all['row_number_demand'].isin(demand_filter)],use_container_width=True, hide_index=True)

#Supply section
st.subheader("Supply Section")
st.markdown('<span style="font-size: 9px;"> <i>This table consists of information about the combination of harvest plan ID that can fufill certain demand</i><span>', unsafe_allow_html=True)
st.dataframe(supply[supply['row_number_demand'].isin(demand_filter)],use_container_width=True, hide_index=True)

#Supply detail section
st.subheader("Supply Detail Section")
st.markdown('<span style="font-size: 9px;"> <i>This table consists of information about the detail of single harvest plan ID that can fulfill certain demand</i><span>', unsafe_allow_html=True)
st.dataframe(supply_detail[supply_detail['row_number_demand'].isin(demand_filter)],use_container_width=True, hide_index=True)