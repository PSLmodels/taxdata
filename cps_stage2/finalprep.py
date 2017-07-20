import pandas as pd
import subprocess


weights = pd.read_csv('cps_weights_raw.csv.gz', compression='gzip')
weights *= 100.
weights = weights.round(0).astype('int64')
weights.to_csv('cps_weights.csv', index=False)
subprocess.check_call(['gzip', '-nf', 'cps_weights.csv'])
