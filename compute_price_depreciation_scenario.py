#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description: Compute Formula-Based Retail Price, 5% USD/IDR Depreciation Scenario
Author: @sihir_sains
"""

#############################################################################
#   0. Load Necessary Library and Set Up Necessary Variables
#############################################################################

import pandas as pd
import numpy as np

dt_path =  "<insert your home directory here>"


# Define Price Rounding (Up) and Fixed Statutory Subsidy

round_up = 50
subs_biogasoil = 500 
vat = 0.11 # PPN @ 11%
fuel_tax = 0.05 # PBBKB @ 5%
eoy_er = 15750 # End-of-year exchange rate projection

#############################################################################
#   1. Define Sub-Functions
#############################################################################

"""
Statutorily, the exchange rate for the base price calculation for month X 
is the average of the BI exchange rate from the 25th day of (X-2) to the 24th
day of (X-1). Following functions are used to determine the appropriate month
for which the data will be used in monthly calculation
"""

def assign_ref_month(df,dt_var):
    
    df['day'] = df[dt_var].dt.day
    df['month'] = df[dt_var].dt.month
    df['year'] = df[dt_var].dt.year
    
    # For cases of Late December Data
    df.loc[(df['month']==12) & (df['day']>=25), 'ref_month'] = 2    
    df.loc[(df['month']==12) & (df['day']>=25), 'ref_year'] = df['year']+1  
    
    # For cases of Late November to Early December Data
    df.loc[(df['month']==12) & (df['day']<25), 'ref_month'] = 1 
    df.loc[(df['month']==11) & (df['day']>=25), 'ref_month'] = 1
    df.loc[(df['month']==12) & (df['day']<25), 'ref_year'] = df['year']+1
    df.loc[(df['month']==11) & (df['day']>=25), 'ref_year'] = df['year']+1
   
    # For everything else
    df.loc[(df['day']<25) & (df['ref_month'].isnull()), 'ref_month'] = df['month'] + 1    
    df.loc[(df['day']>=25) & (df['ref_month'].isnull()), 'ref_month'] = df['month'] + 2
    df.loc[df['ref_year'].isnull(), 'ref_year'] = df['year']
    
    return df


"""
There is also some statutory requirement for base and final price calculation 
"""
def compute_base_price(df,gastype,cons,mult,er):
    max_prc = ((df[gastype] * mult * df[er])/158.99 + cons)*(100/90)
    min_prc = ((df[gastype] * mult * df[er])/158.99 + cons)
    return [max_prc,min_prc]

def compute_retail_price(gas_prc,rounding,subsidy,vat,fuel_tax):
    return rounding * np.ceil(float(gas_prc*(1+vat)-subsidy)*(1+fuel_tax)/rounding)

#############################################################################
#   2. Import USD/IDR Exchange Rate
#############################################################################


exchg_rt = pd.read_excel(dt_path+"data/JISDOR.xlsx",usecols="B:C",skiprows=4)

exchg_rt.rename(columns={'Tanggal':'data_dt',
                         'Kurs':'USDIDR'},inplace=True)

exchg_rt['data_dt'] = pd.to_datetime(exchg_rt['data_dt'])

exchg_rt = assign_ref_month(exchg_rt,'data_dt')

monthly_er = exchg_rt.groupby(['ref_month','ref_year'])['USDIDR'].mean()


#############################################################################
#   2. Import Oil Price
#############################################################################

# Historical MOPS Price
mops = pd.read_csv(dt_path+'data/platts_price.csv')
mops['data_dt'] = pd.to_datetime(mops['data_dt'])
mops = assign_ref_month(mops,'data_dt')

monthly_mops = mops.groupby(['ref_month','ref_year'])['mogas_92','mogas_95','gasoil_10','gasoil_500'].mean()

# MOPS Price for Post-July Months
fut_mops = pd.read_csv(dt_path+'data/platts_price_futures.csv')
fut_mops['temp_mo'] = pd.to_datetime(fut_mops['month']).dt.month
fut_mops['temp_yr'] = pd.to_datetime(fut_mops['month']).dt.year

# Assign Reference Months for Post-July Months
fut_mops.loc[fut_mops['temp_mo']==12,'ref_month'] =  1
fut_mops.loc[fut_mops['temp_mo']==12,'ref_year'] = fut_mops['temp_yr'] + 1

fut_mops.loc[fut_mops['temp_mo']<12,'ref_month'] = fut_mops['temp_mo'] + 1
fut_mops.loc[fut_mops['temp_mo']<12,'ref_year'] = fut_mops['temp_yr']

# Keep future months that are not available in the current data
fut_mops.set_index(['ref_month','ref_year'],inplace=True,drop=True)
fut_mops = fut_mops[~fut_mops.index.isin(monthly_mops.index)]
fut_mops = fut_mops[['mogas_92','mogas_95','gasoil_10','gasoil_500']]

# Concatenate data for future months to data for historical months
monthly_mops = pd.concat([monthly_mops,fut_mops],axis=0).sort_index()

#############################################################################
#   3. Combine Monthly Variables to Compute Base Price
#############################################################################

price_df = pd.merge(monthly_mops,monthly_er,how='outer',
                     left_index=True,right_index=True).reset_index()

# Add Month Variable
price_df['month'] = pd.to_datetime(price_df['ref_year'].astype(int).astype(str) + '-' + 
                                   price_df['ref_month'].astype(int).astype(str) + '-1', 
                                   format = '%Y-%m').dt.to_period('M')
price_df = price_df.sort_values(['month'])

# Keep for 2022 Data Only
price_df = price_df.loc[price_df['ref_year']==2022]

# Set Exchange Rate to EOY Projection (if NaN)
price_df.loc[price_df['USDIDR'].isnull(),'USDIDR'] = eoy_er

# Pertalite (RON90)
price_df['bp_pertalite_max'] = compute_base_price(price_df,'mogas_92',1800,0.9921,'USDIDR')[0]
price_df['bp_pertalite_min'] = compute_base_price(price_df,'mogas_92',1800,0.9921,'USDIDR')[1]

# Pertamax (RON92)
price_df['bp_pertamax_max'] = compute_base_price(price_df,'mogas_92',1800,1,'USDIDR')[0]
price_df['bp_pertamax_min'] = compute_base_price(price_df,'mogas_92',1800,1,'USDIDR')[1]

# Pertamax Turbo (RON98)
price_df['bp_turbo_max'] = compute_base_price(price_df,'mogas_95',2000,1.01,'USDIDR')[0]
price_df['bp_turbo_min'] = compute_base_price(price_df,'mogas_95',2000,1.01,'USDIDR')[1]

# Pertadex (Cetane 53, Sulphur 50ppm)
price_df['bp_pertadex_max'] = compute_base_price(price_df,'gasoil_10',2000,1,'USDIDR')[0]
price_df['bp_pertadex_min'] = compute_base_price(price_df,'gasoil_10',2000,1,'USDIDR')[1]

# Dexlite (Cetane 51, Sulphur 500ppm)
price_df['bp_dexlite_max'] = compute_base_price(price_df,'gasoil_500',2000,1,'USDIDR')[0]
price_df['bp_dexlite_min'] = compute_base_price(price_df,'gasoil_500',2000,1,'USDIDR')[1]

# Biosolar (Cetane 48, Sulphur 2500ppm)
price_df['bp_biosolar_max'] = compute_base_price(price_df,'gasoil_500',1800,1,'USDIDR')[0]
price_df['bp_biosolar_min'] = compute_base_price(price_df,'gasoil_500',1800,1,'USDIDR')[1]


#############################################################################
#   4. Compute Price at Retail Level
#############################################################################

# Compute Retail Price for Unsubsidized Gas Types
unsubsidized_ls = ['pertalite','pertamax','turbo','pertadex','dexlite']

for x in unsubsidized_ls:
    price_df[x+'_max'] = np.vectorize(compute_retail_price)\
        (price_df['bp_'+x+'_max'],round_up,0,vat,fuel_tax)
    price_df[x+'_min'] = np.vectorize(compute_retail_price)\
        (price_df['bp_'+x+'_min'],round_up,0,vat,fuel_tax)

# Compute Retail Price for Biogasoil (After Fixed Subsidy)
price_df['biosolar_max'] = np.vectorize(compute_retail_price)\
    (price_df['bp_biosolar_max'],round_up,subs_biogasoil,vat,fuel_tax)
price_df['biosolar_min'] = np.vectorize(compute_retail_price)\
    (price_df['bp_biosolar_min'],round_up,subs_biogasoil,vat,fuel_tax)


#############################################################################
#   5. Export Estimated Retail Price
#############################################################################

# Specify Variables to Keep
gastype_ls = unsubsidized_ls + ['biosolar']

ret_price_ls = [x+'_max' for x in gastype_ls] + [x+'_min' for x in gastype_ls]
base_price_ls = ['bp_'+x+'_max' for x in gastype_ls] + ['bp_'+x+'_min' for x in gastype_ls]

ret_price = price_df[['month'] + ret_price_ls]
base_price = price_df[['month'] + base_price_ls]

ret_price.to_csv(dt_path+'data/retail_price_depre_scenario.csv',index=False)
base_price.to_csv(dt_path+'data/base_price_depre_scenario.csv',index=False)

