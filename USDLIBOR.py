# -*- coding: utf-8 -*-
"""
Created on Tue Sep  4 14:13:03 2018

@author: osawa
"""

import pandas as pd
import sympy
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import math
from scipy import optimize

def fwrd(df_s, df_e, calcd):
    return (df_s / df_e -1) * 360 / (calcd) 


#USDLIBORを読み込む
df_usl = pd.read_csv('input/USDLIBOR .csv',
                 parse_dates =['Start date', 'Maturity'],
                 index_col='Maturity_name')
#基準日を設定
value_date = df_usl.at['O/N', 'Start date']
print(df_usl)

Capital = 1000000
spot_days = (df_usl.at['1W', 'Start date'] - value_date).days

df_usl['day_difference'] = (df_usl['Maturity'] - df_usl['Start date']).apply(lambda x: x.days)

df_usl['dsf'] = 1.0

df_usl.at['O/N', 'dsf'] = 1 / (1 + df_usl.at['O/N', 'Market_quote']/100 * df_usl.at['O/N', 'day_difference'] / 360)
z_on = -365 /(df_usl.at['O/N', 'day_difference'])* math.log(df_usl.at['O/N', 'dsf'])

dsf_spot_1w = 1/ (1+ df_usl.at['1W', 'Market_quote']/100 * df_usl.at['1W', 'day_difference']/ 360)


s = sympy.Symbol('s')
w = sympy.Symbol('w')

f = w + 365 / (df_usl.at['1W', 'day_difference'] + spot_days) * (math.log(dsf_spot_1w) - s * spot_days / 365)
g = (z_on * df_usl.at['1W', 'day_difference'] / 365 + 
     w * (spot_days / 365 - df_usl.at['O/N', 'day_difference'] / 365)) / (((df_usl.at['1W', 'day_difference'] + spot_days)/ 365) - df_usl.at['O/N', 'day_difference']/365) - s

t = sympy.solve([f,g],[s,w])

print(t)

z_spot = t[s]
dsf_spot = math.exp(-z_spot * spot_days / 365)
df_usl.at['1W', 'dsf'] = dsf_spot * dsf_spot_1w
print(z_spot)

df_usl.loc['1M':'1Y', 'dsf'] = dsf_spot / (1 + df_usl['Market_quote']/100 * df_usl['day_difference'] / 360)

#1Y以降

df_usl['dsr'] = np.log(df_usl['dsf'])* -365/(df_usl['day_difference']) 

df_usswap = pd.DataFrame({'Payment date': [df_usl.at['3M', 'Maturity'] + relativedelta(months=i*3) for i in range(120)]})

df_usswap['day_difference'] = (df_usswap['Payment date'] - df_usl.at['1W', 'Start date']).apply(lambda x: x.days)
df_usswap['dsrate'] = np.interp(df_usswap['day_difference'], df_usl['day_difference'], df_usl['dsr'])

df_usswap['dsf'] = np.exp(-1 * (df_usswap['day_difference'] + spot_days) * df_usswap['dsrate'] / 365)

df_usswap['float_leg'] = 1.0
df_usswap.at[0, 'float_leg'] = Capital * df_usl.at['3M', 'Market_quote'] / 100 * df_usswap.at[0, 'day_difference'] / 360
print(df_usswap)
df_usswap['calc_dates'] = df_usswap['day_difference'].diff()
df_usswap['dsf_forcal'] = df_usswap['dsf'].diff()
df_usswap.loc[1:3, 'float_leg'] =  Capital * fwrd(df_usswap['dsf_forcal'], df_usswap['dsf'], df_usswap['calc_dates'])

def npv(df, n, fixed, dsf=df_usswap['dsf'], float_leg=df_usswap['float_leg'], day_difference=df_usswap['day_difference'], dsrate = df_usswap['dsrate']):
    float_pv = 0
    fixed_pv = 0
    
    


print(df_usswap[['Payment date', 'dsrate', 'dsf', 'float_leg']])
