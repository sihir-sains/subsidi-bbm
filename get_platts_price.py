#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description: Webscrape Continuous Futures Price of Relevant MOPS Commodities (up to July '22)
Author: @sihir_sains
"""


#############################################################################
#   0. Load Necessary Library and Set Up Necessary Variables
#############################################################################

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import get_context

import pandas as pd
import time

exec_path = "<insert chromedriver path here>"
out_path =  "<insert your home directory here>"

url_mo95 = 'https://www.tradingview.com/chart/?symbol=NYMEX%3AAV01!'
url_mo92 = 'https://www.tradingview.com/chart/?symbol=NYMEX%3AN1B1!'

url_gs10 = 'https://www.tradingview.com/chart/?symbol=NYMEX%3ASGB1!'
url_gs500 = 'https://www.tradingview.com/chart/?symbol=NYMEX%3AGHS1!'

options = Options()
options.add_argument('--disable-popup-blocking') # differ on driver version. can ignore. 
options.add_argument('--disable-notifications') # differ on driver version. can ignore. 


#############################################################################
#   1. Define Sub-Functions
#############################################################################

## To wait when initializing the page until elements are located
def wait_at_start(driver):
    while True:
        try:
            WDW(driver,15).until(EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[2]/div[6]/div/div[2]/div/div/div/div/div[4]')))
            break
        except:
            driver.refresh()
            continue

## To fetch closing price at a given date
def fetch_price(driver):
    date  = WDW(driver,5).until(EC.presence_of_element_located(
            (By.XPATH , '''/html/body/div[2]/div[6]/div/div[1]/div[1]/div[5]/
             div/div[2]/div[1]/div[1]/div[2]/div/div[2]/span'''))).text
    close = WDW(driver,5).until(EC.presence_of_element_located(
            (By.XPATH , '''/html/body/div[2]/div[6]/div/div[1]/div[1]/div[5]/
             div/div[2]/div[1]/div[2]/div[2]/div[4]/div[2]/span'''))).text
    return date, close

## Sub-function to slightly move mouse until the next date
def move_mouse(driver):
    ActionChains(driver)\
        .move_by_offset(1, 0)\
        .perform()
    
#############################################################################
#   2. Create Wrapper Function for Webscraping
#############################################################################

def webscrape_price(comms):
    
    ### Variables and Dataframe Setup ###
    
    url_comms = mp_dict[comms]
    dup_threshold = 80
    
    cols = ['date',comms]
    price_df = pd.DataFrame(columns=cols)
    ls_prev = pd.DataFrame(columns=cols)
    state_var = 0 # Initializing state var to count # of duplicate observation    
    
    
    ### Loop to Obtain 1-Year Period Price Dataset ###
    
    driver = webdriver.Chrome(executable_path=exec_path,options=options)
    driver.get(url_comms)
    
    wait_at_start(driver)
    WDW(driver,15).until(EC.presence_of_element_located(
        (By.XPATH, '/html/body/div[2]/div[6]/div/div[2]/div/div/div/div/div[4]'))).click()
    WDW(driver,15).until(EC.presence_of_element_located(
        (By.XPATH, '/html/body/div[2]/div[1]/div[1]/div/div[2]/div/div[1]/div[7]'))).click()
    
    start_point = driver.find_element(By.XPATH, '//*[@id="drawing-toolbar"]/div/div/div/div/div[4]/div/div/div[1]/div')
    ActionChains(driver)\
        .move_to_element(start_point)\
        .perform()
    
    ### Loop to Obtain YTD Price Dataset ###
    while state_var <= dup_threshold:
        
        temp_ls = [fetch_price(driver)]
        temp_df = pd.DataFrame(temp_ls,columns=cols)
        
        if temp_df.equals(ls_prev):
            state_var = state_var + 1
            ls_prev = temp_df
        else:
            state_var = 0
            ls_prev = temp_df
        
        price_df = pd.concat([price_df,temp_df],axis=0)
        move_mouse(driver)
        time.sleep(0.15)
    
    
    ### Ensure No Duplicate Date (Same Date, Different Closing Price) ###
    price_df = price_df.drop_duplicates().reset_index(drop=True)
    
    price_df = price_df.loc[price_df['date']!='∅']
    price_df['dup'] = price_df.duplicated(subset='date')
    assert price_df['dup'].unique().shape[0], "Duplicate obs identified!"
    
    ### Clean Price Dataset ###
    
    price_df['data_dt'] = pd.to_datetime(price_df['date']).dt.date
    price_df = price_df[['data_dt',comms]].set_index(['data_dt'])
    
    ### Close Webdriver ###
    try:
        driver.close()
    except:
        alert = WDW(driver, 3).until(EC.alert_is_present())
        alert.accept()
        driver.close()

    
    return price_df

#############################################################################
#   3. Fetch Closing Price Time Series by Commodities
#############################################################################

### Multiprocess the webscraping

colname = ['mogas_92','mogas_95','gasoil_10','gasoil_500']
to_mp = [url_mo92, url_mo95, url_gs10, url_gs500]
mp_dict = dict(zip(colname,to_mp))

if __name__ == '__main__':
    with get_context("spawn").Pool(processes=4) as p:
        res = p.map(webscrape_price,mp_dict)
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
    consol_prc.to_csv(out_path+'data/platts_price.csv') 
except:
    pass