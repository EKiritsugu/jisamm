# "C:/Users/aalab_linziyao/Documents/GitHub/jisamm/data/20221207-180003_reverb_interf_performance_2fd4afb7fe/data.json"
dir = ["data/20200227-114954_speed_contest_f96a1824ad"]


import json
from data_loader import load_data

df, rt60, parameters = load_data(dir)

print(df)

df.to_csv('out.csv')
# with open(dir, 'r') as file:
print('done')