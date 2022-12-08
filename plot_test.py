# "C:/Users/aalab_linziyao/Documents/GitHub/jisamm/data/20221207-180003_reverb_interf_performance_2fd4afb7fe/data.json"
dir = ['data/20221208-163059_reverb_interf_performance_8d8a980436/']


import json
from data_loader import load_data

df, rt60, parameters = load_data(dir)

print(df)

df.to_csv(dir[0] + 'out.csv')
# with open(dir, 'r') as file:
print('done')