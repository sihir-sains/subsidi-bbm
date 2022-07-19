#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description: Webscrape Futures Price of Relevant MOPS Commodities for Rest of 2022
Author: @sihir_sains
"""

#############################################################################
#   0. Load Necessary Library and Set Up Necessary Variables
#############################################################################

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import get_context

import pandas as pd
import numpy as np
import time 
import re

exec_path = "<insert chromedriver path here>"
out_path =  "<insert your home directory here>"

url_mo95 = 'https://www.tradingview.com/chart/?symbol=NYMEX%3AAV0'
url_mo92 = 'https://www.tradingview.com/chart/?symbol=NYMEX%3AN1B'

url_gs10 = 'https://www.tradingview.com/chart/?symbol=NYMEX%3ASGB'
url_gs500 = 'https://www.tradingview.com/chart/?symbol=NYMEX%3AGHS'

options = Options()
options.add_argument('--disable-popup-blocking') # differ on driver version. can ignore. 
options.add_argument('--disable-notifications') # differ on driver version. can ignore. 

# Get List of Months for Futures Price in NYMEX
nymex_mo = ['F','G','H','J','K','M','N','Q','U','V','X','Z']
yrs = ['2022']

#############################################################################
#   1. Define Sub-Functions
#############################################################################

## To wait when initializing the page until elements are located
def wait_at_start(driver):
    while True:
        try:
            WDW(driver,10).until(EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[2]/div[6]/div/div[2]/div/div/div/div/div[4]')))
            break
        except:
            driver.refresh()
            continue

## To fetch closing price at a given date
def fetch_price(driver):
    date  = WDW(driver,5).until(EC.presence_of_element_located(
            (By.XPATH , '''/html/body/div[2]/div[1]/div[2]/div[1]/div/table/
             tr[1]/td[2]/div/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]'''))).text
    close = WDW(driver,5).until(EC.presence_of_element_located(
            (By.XPATH , '''/html/body/div[2]/div[6]/div/div[1]/div[1]/div[5]/
             div/div[2]/div[1]/div[2]/div[2]/div[4]/div[2]/span'''))).text
    return date, close

def extract_date_string(txt):
    return re.findall(r'\((.*?)\)',txt)[1].title()

#############################################################################
#   2. Create Wrapper Function for Webscraping
#############################################################################

def webscrape_fut_prc(comms):
    
    ### Variables and Dataframe Setup, Initialize Webdriver ###
        
    url_comms = mp_dict[comms]
    cols = ['date',comms]
    fut_df = pd.DataFrame(columns=cols)
    
  
    driver = webdriver.Chrome(executable_path=exec_path,options=options)
    
    ### Loop to Obtain YTD Price Dataset ###
    for yr in yrs:
        for mo in nymex_mo:       
            driver.get(url_comms+mo+yr)
            
            wait_at_start(driver)
            
            if (yr == yrs[0]) & (mo == nymex_mo[0]):
                WDW(driver,10).until(EC.presence_of_element_located(
                    (By.XPATH, '/html/body/div[2]/div[6]/div/div[2]/div/div/div/div/div[4]'))).click()
            else:
                WDW(driver,10).until(EC.presence_of_element_located(
                    (By.XPATH, '/html/body/div[2]/div[6]/div/div[2]/div/div/div/div/div[4]'))).click()
                WDW(driver,10).until(EC.presence_of_element_located(
                    (By.XPATH, '/html/body/div[2]/div[6]/div/div[2]/div/div/div/div/div[4]'))).click()
            
            time.sleep(2)
            temp_ls = [fetch_price(driver)]
            temp_df = pd.DataFrame(temp_ls,columns=cols)
            
            fut_df = pd.concat([fut_df,temp_df],axis=0)
            time.sleep(2)
            
            
    
    ### Ensure No Duplicate Date (Same Date, Different Closing Price) ###
    fut_df['date'] = np.vectorize(extract_date_string)(fut_df['date'])

    fut_df = fut_df.drop_duplicates().reset_index(drop=True)
    fut_df['dup'] = fut_df.duplicated(subset='date')
    assert fut_df['dup'].unique().shape[0], "Duplicate obs identified!"
    
    ### Clean Price Dataset ###
    
    fut_df['month'] = pd.to_datetime(fut_df['date']).dt.to_period('M')
    fut_df = fut_df[['month',comms]].set_index(['month'])
    
    ### Close Webdriver ###
    try:
        driver.close()
    except:
        alert = WDW(driver, 3).until(EC.alert_is_present())
        alert.accept()
        driver.close()

    
    return fut_df

#############################################################################
#   3. Fetch Closing Price Time Series by Commodities
#############################################################################

### Multiprocess the webscraping

colname = ['mogas_92','mogas_95','gasoil_10','gasoil_500']
to_mp = [url_mo92, url_mo95, url_gs10, url_gs500]
mp_dict = dict(zip(colname,to_mp))

if __name__ == '__main__':
    with get_context("spawn").Pool(processes=4) as p:
        res = p.map(webscrape_fut_prc,mp_dict)
        p.close()
        p.join()
        
        consol_prc = pd.concat(res,axis=1)
                
else:
    pass

#############################################################################
#   4. Clean and Process the Platts Price Dataset
#############################################################################
    
try:
    print(consol_prc)
    consol_prc.to_csv(out_path+'data/platts_price_futures.csv') 
except:
    pass
