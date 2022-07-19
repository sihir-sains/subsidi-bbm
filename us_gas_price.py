#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description: Consistency Check with US Retail Gas Price
Author: @sihir_sains
"""

#############################################################################
#   0. Load Necessary Library and Set Up Necessary Variables
#############################################################################

import pandas as pd
import pandas_datareader as pdr
import os
import plotly.graph_objects as go

dt_path =  "<insert your home directory here>"
os.chdir(dt_path)

import config

"""
Notes: The API Key for FRED is stored in private config.py file. 
FRED gives free and easy access to economic data from around the world by 
signing up on their website to get free account and your own API Key
"""

fred_api_key = config.api_key

# Define Start Date and End Date

start_dt = '2022-01-01'
end_dt = '2022-05-31'

#############################################################################
#   1. Define Sub-Functions
#############################################################################

def get_fred_data(param_list, start_date, end_date):
    df = pdr.DataReader(param_list, 'fred', start_date, end_date)
    return df.reset_index()

def agg_monthly(df,comm_var,date_var):
    df['month'] = df[date_var].dt.to_period('M')
    dfn = df.groupby(['month'])[comm_var].mean()
    return dfn.to_frame()

def convert_metric_idr(df,comm_var,curr_var):
    series = df[comm_var]*df[curr_var]/3.785411784
    return series

def create_plot(df,var_gas,lab_gas,title):
    
    ### I use Okabe-Ito's colorblind-friendly palette for the line graphs
    color_gas = ['rgb(213,94,0)', 'rgb(0,0,0)', 'rgb(0,114,178)']
        
    fig = go.Figure()
    
    # USD Gasoline Line
    fig.add_trace(go.Scatter(x=df['month'], y=df[var_gas[0]], mode='lines',
        name=lab_gas[0],
        line=dict(color=color_gas[0],width=8),
        connectgaps=True,
    ))
    
    
    for i in range(1,3):
        fig.add_trace(go.Scatter(x=df['month'], y=df[var_gas[i]], mode='lines',
            name=lab_gas[i],
            line=dict(color=color_gas[i],width=8,dash='dash'),
            connectgaps=True,
        ))
    
    
    fig.update_layout(
        xaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside',
            tickfont=dict(
                family='Helvetica',
                size=42,
                color='rgb(82, 82, 82)',
            ),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            showticklabels=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside',
            tickfont=dict(
                family='Helvetica',
                size=42,
                color='rgb(82, 82, 82)',
            ),
        ),
        autosize=True,
        margin=dict(
            autoexpand=False,
            l=100,
            r=20,
            t=110,
        ),
        showlegend=True,
        plot_bgcolor='white',
        legend=dict(
            yanchor="top",
            y=0.95,
            xanchor="left",
            x=0.8,
            font=dict(family='Helvetica',
                      size=36,
                      color='rgb(37,37,37)')
        ),
    )
    
    # Adding labels
    annotations = []
    
    # Title
    annotations.append(dict(xref='paper', yref='paper', x=0.01, y=1,
                                  xanchor='left', yanchor='bottom',
                                  text=title,
                                  font=dict(family='Helvetica',
                                            size=60,
                                            color='rgb(37,37,37)'),
                                  showarrow=False))
    
    fig.update_layout(annotations=annotations,margin=dict(l=200, r=200, t=150, b=150))
    
    return fig


#############################################################################
#   2. Query Commodities Price and Exchange Rate from FRED
#############################################################################

# Regular Conventional Gasoline Price
gas_reg = get_fred_data(param_list=['GASREGCOVW'], 
                   start_date=start_dt, 
                   end_date=end_dt)
gas_reg.rename(columns={'GASREGCOVW':'gasoline'},inplace=True)

# Diesel Price
diesel = get_fred_data(param_list=['GASDESW'], 
                   start_date=start_dt, 
                   end_date=end_dt)
diesel.rename(columns={'GASDESW':'diesel'},inplace=True)

# Exchange Rate
er_fred = get_fred_data(param_list=['CCUSSP02IDM650N'], 
                   start_date=start_dt, 
                   end_date=end_dt)
er_fred.rename(columns={'CCUSSP02IDM650N':'USDIDR'},inplace=True)

#############################################################################
#   3. Process Data and 
#############################################################################

mops = pd.read_csv(dt_path+'data/platts_price.csv')
mops['month'] = pd.to_datetime(mops['data_dt']).dt.to_period('M')

gas_reg_monthly = agg_monthly(gas_reg,'gasoline','DATE')
diesel_monthly = agg_monthly(diesel,'diesel','DATE')
er_monthly = agg_monthly(er_fred,'USDIDR','DATE')

monthly_us = pd.concat([gas_reg_monthly,diesel_monthly,er_monthly],axis=1)

# Convert from Gallon to Litre and from USD to IDR

monthly_us['gasoline_idr'] = convert_metric_idr(monthly_us,'gasoline','USDIDR')
monthly_us['diesel_idr'] = convert_metric_idr(monthly_us,'diesel','USDIDR')


#############################################################################
#   4. Check with Monthly Data
#############################################################################

retail_price = pd.read_csv(dt_path+'data/retail_price.csv')
retail_price['month'] = pd.to_datetime(retail_price['month']).dt.to_period('M')

retail_price = retail_price.set_index(['month'],drop=True)

merged = pd.concat([monthly_us,retail_price],axis=1).reset_index()
merged['month'] = merged['month'].dt.to_timestamp()

# Create Reference Graphs

var_gas = ['gasoline_idr','pertamax_min','pertamax_max']
lab_gas = ['US Gasoline (IDR)', 'Pertamax (Min)', 'Pertamax (Max)']

var_diesel = ['diesel_idr','pertadex_min','pertadex_max']
lab_diesel = ['US Diesel (IDR)', 'Pertadex (Min)', 'Pertadex (Max)']


fig_gas = create_plot(merged,var_gas,lab_gas,'US Reg Gasoline and Est. Pertamax Price (IDR)')
fig_diesel = create_plot(merged,var_diesel,lab_diesel,'US Reg Diesel and Est. Pertadex Price (IDR)')

fig_gas.write_image(dt_path+"output/gas_price.png",scale=5, width=2000, height=1500)
fig_diesel.write_image(dt_path+"output/diesel_price.png",scale=5, width=2000, height=1500)
