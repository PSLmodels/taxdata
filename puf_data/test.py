import numpy as np
import pulp
import pandas as pd

puf = pd.read_csv('puf.csv')

LP = pulp.LpProblem('PUF Stage 2', pulp.LpMinimize)
r = pulp.LpVariable.dicts('r', puf.index, lowBound=0)
s = pulp.LpVariable.dicts('s', puf.index, lowBound=0)
# add objective functoin
LP += pulp.lpSum([r[i] + s[i] for i in puf.index])
# add constraints
for i in puf.index:
    LP += r[i] + s[i] <= tol
for i in range(len(b)):
    LP += pulp.lpSum([(A1[i][j] * r[j] + A2[i][j] * s[j])
                      for j in puf.index]) == b[i]

print('Solving Model...')
pulp.LpSolverDefault.msg = 1  # ensure there is
