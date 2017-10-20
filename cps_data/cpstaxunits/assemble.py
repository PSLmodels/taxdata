"""
This file combines the three CPS files into one
"""
import pandas as pd


def assemble(cps1, cps2, cps3):
    """
    """
    final_cps = pd.concat([cps1, cps2, cps3])
    final_cps['wt'] = final_cps['wt'] / 3.0
    final_cps = final_cps.fillna(value=0)
    return final_cps
