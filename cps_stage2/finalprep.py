import pandas as pd
import subprocess


weights = pd.read_csv('cps_weights_raw.csv.gz', compression='gzip')
weights = weights.drop('SEQUENCE', axis=1)
weights *= 100.
weights = weights.round(0).astype('int64')
# add weights from CPS as 2014 value
cps = pd.read_csv('../cps_data/cps.csv.gz')
df = pd.concat([cps.s006, weights], axis=1)
df = df.rename({'s006': 'WT2014'}, axis=1)
df.to_csv('cps_weights.csv', index=False)
subprocess.check_call(['gzip', '-nf', 'cps_weights.csv'])
