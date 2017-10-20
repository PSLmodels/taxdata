from copy import deepcopy
import pandas as pd

target_list = ['STATE', 'A00200', 'A00300', 'A00600', 'A00650', 'A00900',
               'A01000', 'A01400', 'A01700', 'A02300', 'A03300', 'A03270',
               'A03150', 'A03210', 'A03240', 'AGI_STUB']  # target columns
state_data = pd.read_csv('https://www.irs.gov/pub/irs-soi/15in54cmcsv.csv',
                         usecols=target_list, thousands=',')
sub_df = deepcopy(state_data[state_data['AGI_STUB'] == 0])
sub_df.to_csv('data/agg_state_data.csv', index=None)
