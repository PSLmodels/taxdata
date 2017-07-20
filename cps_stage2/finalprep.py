import pandas as pd


weights = pd.read_csv('cps_weights_raw.csv.gz', compression='gzip')
weights = weights.round(0).astype('int64')
weights *= 100
weights.to_csv('cps_weights.csv.gz', index=False, compression='gzip')
