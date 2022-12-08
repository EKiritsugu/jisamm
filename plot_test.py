# "C:/Users/aalab_linziyao/Documents/GitHub/jisamm/data/20221207-180003_reverb_interf_performance_2fd4afb7fe/data.json"
dir = ['data/20221208-164354_reverb_interf_performance_d6e9a4e599/']


import json
from data_loader import load_data

df, rt60, parameters = load_data(dir)

print(df)

df.to_csv(dir[0] + 'out.csv')
# with open(dir, 'r') as file:
print('done')