#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description: Compute Total Subsidy
Author: @sihir_sains
"""

#############################################################################
#   0. Load Necessary Library and Set Up Necessary Variables
#############################################################################

import pandas as pd
import plotly.graph_objects as go

dt_path =  "<insert your home directory here>"
gas_type = ['biosolar','pertalite','pertamax','turbo','pertadex','dexlite']

#############################################################################
#   1. Define Sub-Functions
#############################################################################

# Assign Current Price
def assign_curr_price(df):
    ## Extract Year Variable
    df['month'] = pd.to_datetime(df['month']).dt.to_period('M')
    df['year'] = df['month'].dt.year

    ## Input Current Price for Each Petrol Type; we use Jakarta price for reference
    df['curr_p_biosolar'] = 5150
    df['curr_p_pertalite'] = 7650

    ## Actual retail price after Jan 1
    df.loc[df['month']>='2022-01-01','curr_p_turbo'] = 12000
    df.loc[df['month']>='2022-01-01','curr_p_pertadex'] = 11150
    df.loc[df['month']>='2022-01-01','curr_p_dexlite'] = 9500
    df.loc[df['month']>='2021-01-01','curr_p_pertamax'] = 9000


    ## Actual retail price after Feb 12 (we apply price retroactively to the whole month)
    df.loc[df['month']>='2022-02-01','curr_p_turbo'] = 13500
    df.loc[df['month']>='2022-02-01','curr_p_pertadex'] = 13200
    df.loc[df['month']>='2022-02-01','curr_p_dexlite'] = 12150

    ## Actual retail price after March 1
    df.loc[df['month']>='2022-03-01','curr_p_turbo'] = 14500
    df.loc[df['month']>='2022-03-01','curr_p_pertadex'] = 13700
    df.loc[df['month']>='2022-03-01','curr_p_dexlite'] = 12950

    ## Actual retail price after April 1
    df.loc[df['month']>='2022-04-01','curr_p_pertamax'] = 12500

    ## Actual retail price after July 10 (we apply price retroactively to the whole month)
    df.loc[df['month']>='2022-07-01','curr_p_turbo'] = 16200
    df.loc[df['month']>='2022-07-01','curr_p_pertadex'] = 16500
    df.loc[df['month']>='2022-07-01','curr_p_dexlite'] = 15000

# Compute Share of Each Petrol 
def compute_share(df,gas_type,vol_total):
    df[gas_type+'_shr'] = df['vol_'+gas_type]/df[vol_total]

def compute_stealth_unit_subsidy(df,gas_type):
    df[gas_type+'_unit_sub_min'] = df[gas_type+'_min'] - df['curr_p_'+gas_type]
    df[gas_type+'_unit_sub_max'] = df[gas_type+'_max'] - df['curr_p_'+gas_type]
  
# Set subsidy floor to zero (i.e if the estimated price exceed max/min MSRP)    
def set_subsidy_floor(df,gas_type):
    df.loc[df[gas_type+'_unit_sub_min']<0,gas_type+'_unit_sub_min'] = 0
    df.loc[df[gas_type+'_unit_sub_max']<0,gas_type+'_unit_sub_max'] = 0

def compute_total_subsidy(df,gas_type,cons_var):
    df['cons_'+gas_type] = df[cons_var] * df[gas_type+'_shr']
    df[gas_type+'_sub_min'] = df[gas_type+'_unit_sub_min'] * df['cons_'+gas_type] / (10**9)
    df[gas_type+'_sub_max'] = df[gas_type+'_unit_sub_max'] * df['cons_'+gas_type] / (10**9)

def total_subsidy(df):
    df['tot_sub_min'] = df[[x+'_sub_min' for x in gas_type]].sum(axis=1) 
    df['tot_sub_max'] = df[[x+'_sub_max' for x in gas_type]].sum(axis=1) 
    
def waterfall_plot_subsidy(data_ls,name_ls):
    
    fig = go.Figure(go.Waterfall(
        name = "2018",
        orientation="h",
        measure = ["relative","relative","relative","relative","relative","relative","total"],
        text = data_ls,
        y = name_ls,
        x = data_ls,
        increasing = {"marker":{"color":'rgb(213,94,0)'}},
        totals = {"marker":{"color":'rgb(0,114,178)'}},
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
        showlegend=False,
        font=dict(family='Helvetica',
                  size=36),
        plot_bgcolor='white',
    )
    
    # Adding labels
    annotations = []
    
    # Title
    annotations.append(dict(xref='paper', yref='paper', x=0.01, y=1,
                                  xanchor='left', yanchor='bottom',
                                  text='Subsidy Breakdown by Type (IDR Trillion)',
                                  font=dict(family='Helvetica',
                                            size=60,
                                            color='rgb(37,37,37)'),
                                  showarrow=False))
    
    fig.update_layout(annotations=annotations,margin=dict(l=300, r=100, t=150, b=150))
    
    return fig

#############################################################################
#   2. Input Price on Different Types of Gasoline for Each Scenario
#############################################################################

## Load MSRP for Each Petrol Type and Assign Current Price (Baseline ER Scenario)
retail_price = pd.read_csv(dt_path+'data/retail_price.csv')
assign_curr_price(retail_price)

## Load MSRP for Each Petrol Type and Assign Current Price (5% Depreciation Scenario)
retail_price_depr = pd.read_csv(dt_path+'data/retail_price_depre_scenario.csv')
assign_curr_price(retail_price_depr)


#############################################################################
#   3. Estimate Total Volumetric Consumption
#############################################################################


"""
Note: we do not have data on petrol consumption breakdown by type
Therefore, detailed calculation needs to be inferred from the Kemen ESDM's 
historical data on petrol consumption by types.

Admittedly, these figures include non-Pertamina sales; therefore, a conservative
approach would be to use the share from Kemen ESDM's handbook and to apply
these shares to reported 2019 sales (pre-Covid) from Pertamina, and assume
that fuel consumption grows 1:1 with economic growth
"""

hist_cons = pd.read_excel(dt_path+'data/petrol_consumption_transport_sector.xlsx')

hist_cons.rename(columns={'Gasoil_CN51':'vol_dexlite',
                          'Gasoil_CN53':'vol_pertadex',
                          'Gasoil_CN48':'vol_solar',
                          'Biogasoil':'vol_biosolar',
                          'RON90':'vol_pertalite',
                          'RON88':'vol_premium',
                          'RON92':'vol_pertamax',
                          'RON95_higher':'vol_turbo'},inplace=True)

hist_cons.set_index(['Year'],inplace=True)


# Consolidate Relevant Gas Categories
hist_cons['vol_biosolar'] = hist_cons['vol_solar'] + hist_cons['vol_biosolar']
hist_cons['vol_pertalite'] = hist_cons['vol_premium'] + hist_cons['vol_pertalite']

hist_cons = hist_cons.drop(columns=['vol_premium','vol_solar'])
hist_cons.loc[:,'vol_total']= hist_cons.sum(numeric_only=True, axis=1)

# Compute Share of Petrol Type
[compute_share(hist_cons,x,'vol_total') for x in gas_type]

# Assert that individual share sum up to 100% 
hist_cons['total_shr'] = hist_cons[[x+'_shr' for x in gas_type]].sum(axis=1) 
assert hist_cons['total_shr'].mean() == 1, "At least 1 row not sum up to 100%"

hist_cons.reset_index(inplace=True)

hist_cons = hist_cons.loc[hist_cons['Year']>=2018].reset_index(drop=True)

# Compute Average Share of Each Gas Type
avg_share = hist_cons[[x+'_shr' for x in gas_type]].mean().to_frame().reset_index()
avg_share.rename(columns={0:'share'},inplace=True)
avg_share['year'] = 2022
avg_share = avg_share.pivot(index ='year',columns='index').reset_index()
avg_share = avg_share.T.reset_index(level=0,drop=True).T

avg_share.rename(columns={'':'year'},inplace=True)

## Input Reported 2019 Level of Fuel Sales at Gas Stations, 51.31 mil kL
avg_share['cons_2019'] = 51.31*(10**9)

## Assume that Fuel Sales growth track economic growth 1:1
avg_share['cons_2022'] = avg_share['cons_2019']*(1-0.0207)*(1+0.0369)*(1+0.051)

#############################################################################
#   4. Merge Volumetric Consumption on Retail Price Dataset
#############################################################################

""" Merge on Baseline (15,000) USD/IDR Scenario """
retail_price = retail_price.merge(avg_share,on='year',how='outer')

## Assign Equal Consumption Weight to Each Month (No Monthly Fluctuation)
retail_price['cons_2019'] = retail_price['cons_2019']/12
retail_price['cons_2022'] = retail_price['cons_2022']/12

""" Merge on 5% Depreciation (15,750) USD/IDR Scenario """
retail_price_depr = retail_price_depr.merge(avg_share,on='year',how='outer')

## Assign Equal Consumption Weight to Each Month (No Monthly Fluctuation)
retail_price_depr['cons_2019'] = retail_price_depr['cons_2019']/12
retail_price_depr['cons_2022'] = retail_price_depr['cons_2022']/12

#############################################################################
#   5. Estimate the Subsidy Scenario as Stated by Government
#############################################################################

# Compute Energy Subsidy According to APBN 2022

orig_lpg_subsidy = 66300
orig_fuel_subsidy = 11300
orig_electric_subsidy = 56500
orig_fuel_compensation = 18500
orig_electric_compensation = 0

orig_energy_subsidy = orig_lpg_subsidy + orig_fuel_subsidy + orig_electric_subsidy + \
                      orig_fuel_compensation + orig_electric_compensation

# Compute Additional Subsidy Proposed by Govt and Approved by House

add_lpg_subsidy = 71800*(66300/77500) # Assuming increase in fuel + LPG subsidy is pro-rated
add_fuel_subsidy = 71800*(11300/77500) # Assuming increase in fuel + LPG subsidy is pro-rated
add_electric_subsidy = 3100
add_fuel_compensation = 234000
add_electric_compensation = 41000

add_energy_subsidy = add_lpg_subsidy + add_fuel_subsidy + add_electric_subsidy + \
                     add_fuel_compensation + add_electric_compensation

total_fuel_subsidy = orig_fuel_subsidy + add_fuel_subsidy + \
    orig_fuel_compensation + add_fuel_compensation
    
total_energy_subsidy = orig_energy_subsidy + add_energy_subsidy
total_nonfuel_subsidy = total_energy_subsidy - total_fuel_subsidy
print(total_energy_subsidy,total_nonfuel_subsidy)


#############################################################################
#   5. Estimate the Total Subsidy, Baseline Scenario
#############################################################################

subsidy_a = retail_price

# Apply Unit Subsidy Calculation
[compute_stealth_unit_subsidy(subsidy_a,x) for x in gas_type]

# Apply Subsidy Floor Calculation
[set_subsidy_floor(subsidy_a,x) for x in gas_type]

# Apply Total Subsidy Calculation, Assuming 2022 Predicted Total Consumption
[compute_total_subsidy(subsidy_a,x,'cons_2022') for x in gas_type]

# Compute Minimum Total Subsidy
total_subsidy(subsidy_a)

# Annualized Subsidy (Stated in Billion IDR)
print(subsidy_a['tot_sub_min'].sum())
print(subsidy_a['tot_sub_max'].sum())

# Actual Energy Subsidy (Stated in Billion IDR)
print(subsidy_a['tot_sub_min'].sum() + total_nonfuel_subsidy)
print(subsidy_a['tot_sub_max'].sum() + total_nonfuel_subsidy)


#############################################################################
#   6. Estimate the Total Subsidy, 5% Depreciation Scenario
#############################################################################

subsidy_b = retail_price_depr

# Apply Unit Subsidy Calculation
[compute_stealth_unit_subsidy(subsidy_b,x) for x in gas_type]

# Apply Subsidy Floor Calculation
[set_subsidy_floor(subsidy_b,x) for x in gas_type]

# Apply Total Subsidy Calculation, Assuming 2022 Predicted Total Consumption
[compute_total_subsidy(subsidy_b,x,'cons_2022') for x in gas_type]

# Compute Minimum Total Subsidy
total_subsidy(subsidy_b)

# Annualized Subsidy (Stated in Billion IDR)
print(subsidy_b['tot_sub_min'].sum())
print(subsidy_b['tot_sub_max'].sum())

#############################################################################
#   7. Create Visualization for Subsidy Breakdown by Fuel Type
#############################################################################

figname = ["Turbo","Pertadex","Dexlite","Pertamax","Pertalite","Biosolar","Total"]

# Plot for Minimum
totsub_min = (subsidy_a[[x+'_sub_min' for x in gas_type]].sum(axis=0).sort_values())/1000
totsub_min['total'] = totsub_min.sum()
totsub_min = round(totsub_min,2)

fig_min = waterfall_plot_subsidy(totsub_min,figname)
fig_min.write_image(dt_path+"output/waterfall_subsidy_min.png",scale=5, width=2000, height=1500)

# Plot for Maximum
totsub_max = (subsidy_a[[x+'_sub_max' for x in gas_type]].sum(axis=0).sort_values())/1000
totsub_max['total'] = totsub_max.sum()
totsub_max = round(totsub_max,2)

fig_max = waterfall_plot_subsidy(totsub_max,figname)
fig_max.write_image(dt_path+"output/waterfall_subsidy_max.png",scale=5, width=2000, height=1500)


