"""
Converts nonfiler tax units created from CPS-RETS into "SOI"-like records.
Input file: cpsnonf2014.csv, cpsrets.csv
Output file: prod2009_v2.csv
"""

import pandas as pd
import copy


def add_nonfiler(cpsrets, nonfiler):
    # nonfiler = pd.read_csv('cpsnonf2014.csv')
    # cpsrets = pd.read_csv('cpsrets.csv')

    ifdept = nonfiler['ifdept']
    js = nonfiler['js']
    xxocah = nonfiler['xxocah']
    xxocawh = nonfiler['xxocawh']
    xxoodep = nonfiler['xxoodep']
    xxopar = nonfiler['xxopar']
    was = nonfiler['was']
    intst = nonfiler['intst']
    dbe = nonfiler['dbe']
    alimony = nonfiler['alimony']
    bil = nonfiler['bil']
    pensions = nonfiler['pensions']
    rents = nonfiler['rents']
    fil = nonfiler['fil']
    ucomp = nonfiler['ucomp']
    socsec = nonfiler['socsec']
    wt = nonfiler['wt']

    nonfiler = copy.deepcopy(nonfiler.filter(regex='jcps\d{1,2}$|icps\d{1}$|' +
                                                   'jcps100| cpsseq|' +
                                                   'nu\d{1,2}|nu18_dep|' +
                                                   'n1820|n21|' +
                                                   'elderly_dependent|wasp|' +
                                                   'wass|xstate'))

    nonfiler['filer'] = 0
    nonfiler['soiseq'] = 0
    nonfiler['prodseq'] = 0

    # Taxpayer Exemptions
    nonfiler['xfpt'] = 0
    nonfiler['xfst'] = 0
    nonfiler.loc[(ifdept == 0, 'xfpt')] = 1
    nonfiler.loc[((ifdept == 0) & (js == 2), 'xfst')] = 1

    # SET THE C(*) ARRAY
    nonfiler['agir1'] = 0
    nonfiler['dsi'] = ifdept
    nonfiler['efi'] = 0
    nonfiler['eic'] = 0
    nonfiler['elect'] = 0
    nonfiler['fded'] = 0
    nonfiler['flpdyr'] = 2009
    nonfiler['flpdmo'] = 12
    nonfiler['f2441'] = 0
    nonfiler['f3800'] = 0
    nonfiler['f6251'] = 0
    nonfiler['f8582'] = 0
    nonfiler['f8606'] = 0
    nonfiler['f8829'] = 0
    nonfiler['f8910'] = 0
    nonfiler['ie'] = 0
    nonfiler['mars'] = js
    # hh has code = 4 for mars
    nonfiler.loc[(nonfiler['mars'] == 3, 'mars')] = 4
    nonfiler['midr'] = 0
    nonfiler['n20'] = 0
    nonfiler['n24'] = 0
    nonfiler['n25'] = 0
    nonfiler['n30'] = 0
    nonfiler['prep'] = 0
    nonfiler['schb'] = 0
    nonfiler['schcf'] = 0
    nonfiler['sche'] = 0
    nonfiler['tform'] = 0
    nonfiler['txst'] = 0

    nonfiler['xocah'] = xxocah
    nonfiler['xocawh'] = xxocawh
    nonfiler['xoodep'] = xxoodep
    nonfiler['xopar'] = xxopar
    nonfiler['xtot'] = (nonfiler['xfpt'] + nonfiler['xfst'] +
                        nonfiler['xocah'] + nonfiler['xocawh'] +
                        nonfiler['xoodep'] + nonfiler['xopar'])

    # SET THE F(*) ARRAY
    nonfiler['e00200'] = was
    nonfiler['e00300'] = intst
    nonfiler['e00400'] = 0
    nonfiler['e00600'] = dbe
    nonfiler['e00650'] = 0
    nonfiler['e00700'] = alimony
    nonfiler['e00800'] = bil
    nonfiler['e00900'] = 0
    nonfiler['e01000'] = 0
    nonfiler['e01100'] = 0
    nonfiler['e01200'] = 0
    nonfiler['e01400'] = 0
    nonfiler['e01500'] = pensions
    nonfiler['e01700'] = pensions
    nonfiler['e02000'] = rents
    nonfiler['e02100'] = fil
    nonfiler['e02300'] = ucomp
    nonfiler['e02400'] = socsec
    nonfiler['e03150'] = 0
    nonfiler['e03210'] = 0
    nonfiler['e03220'] = 0
    nonfiler['e03230'] = 0
    nonfiler['e03260'] = 0
    nonfiler['e03270'] = 0
    nonfiler['e03240'] = 0
    nonfiler['e03290'] = 0
    nonfiler['e03300'] = 0
    nonfiler['e03400'] = 0
    nonfiler['e03500'] = 0
    nonfiler['e00100'] = 0
    nonfiler['p04470'] = 0
    nonfiler['e04250'] = 0
    nonfiler['e04600'] = 0
    nonfiler['e04800'] = 0
    nonfiler['e05100'] = 0
    nonfiler['e05200'] = 0
    nonfiler['e05800'] = 0
    nonfiler['e06000'] = 0
    nonfiler['e06200'] = 0
    nonfiler['e06300'] = 0
    nonfiler['e09600'] = 0
    nonfiler['e07180'] = 0
    nonfiler['e07200'] = 0
    nonfiler['e07220'] = 0
    nonfiler['e07220'] = 0
    nonfiler['e07230'] = 0
    nonfiler['e07140'] = 0
    nonfiler['e07260'] = 0
    nonfiler['e07300'] = 0
    nonfiler['e07400'] = 0
    nonfiler['e07600'] = 0
    nonfiler['p08000'] = 0
    nonfiler['e07150'] = 0
    nonfiler['e06500'] = 0
    nonfiler['e08800'] = 0
    nonfiler['e09400'] = 0
    nonfiler['e09700'] = 0
    nonfiler['e09800'] = 0
    nonfiler['e09900'] = 0
    nonfiler['e10300'] = 0
    nonfiler['e10700'] = 0
    nonfiler['e10900'] = 0
    nonfiler['e10950'] = 0
    nonfiler['e10960'] = 0
    nonfiler['e59560'] = 0
    nonfiler['e59680'] = 0
    nonfiler['e59700'] = 0
    nonfiler['e11550'] = 0
    nonfiler['e11070'] = 0
    nonfiler['e11100'] = 0
    nonfiler['e11200'] = 0
    nonfiler['e11300'] = 0
    nonfiler['e11400'] = 0
    nonfiler['e11570'] = 0
    nonfiler['e11580'] = 0
    nonfiler['e11582'] = 0
    nonfiler['e11583'] = 0
    nonfiler['e10605'] = 0
    nonfiler['e11900'] = 0
    nonfiler['e12000'] = 0
    nonfiler['e12200'] = 0
    nonfiler['e15100'] = 0
    nonfiler['e15210'] = 0
    nonfiler['e15250'] = 0
    nonfiler['e15360'] = 0
    nonfiler['e17500'] = 0
    nonfiler['e18400'] = 0
    nonfiler['e18500'] = 0
    nonfiler['e18600'] = 0
    nonfiler['e19200'] = 0
    nonfiler['e19550'] = 0
    nonfiler['e19800'] = 0
    nonfiler['e20100'] = 0
    nonfiler['e19700'] = 0
    nonfiler['e20550'] = 0
    nonfiler['e20600'] = 0
    nonfiler['e20400'] = 0
    nonfiler['e20800'] = 0
    nonfiler['e20500'] = 0
    nonfiler['e21040'] = 0
    nonfiler['p22250'] = 0
    nonfiler['e22320'] = 0
    nonfiler['e22370'] = 0
    nonfiler['p23250'] = 0
    nonfiler['e24515'] = 0
    nonfiler['e24516'] = 0
    nonfiler['e24518'] = 0
    nonfiler['e24560'] = 0
    nonfiler['e24598'] = 0
    nonfiler['e24615'] = 0
    nonfiler['e24570'] = 0
    nonfiler['p25350'] = 0
    nonfiler['p25380'] = 0
    nonfiler['p25700'] = 0
    nonfiler['e25820'] = 0
    nonfiler['e25850'] = 0
    nonfiler['e25860'] = 0
    nonfiler['e25940'] = 0
    nonfiler['e25980'] = 0
    nonfiler['e25920'] = 0
    nonfiler['e25960'] = 0
    nonfiler['e26110'] = 0
    nonfiler['e26170'] = 0
    nonfiler['e26190'] = 0
    nonfiler['e26160'] = 0
    nonfiler['e26180'] = 0
    nonfiler['e26270'] = 0
    nonfiler['e26100'] = 0
    nonfiler['e26390'] = 0
    nonfiler['e26400'] = 0
    nonfiler['e27200'] = 0
    nonfiler['e30400'] = 0
    nonfiler['e30500'] = 0
    nonfiler['e32800'] = 0
    nonfiler['e33000'] = 0
    nonfiler['e53240'] = 0
    nonfiler['e53280'] = 0
    nonfiler['e53410'] = 0
    nonfiler['e53300'] = 0
    nonfiler['e53317'] = 0
    nonfiler['e53458'] = 0
    nonfiler['e58950'] = 0
    nonfiler['e58990'] = 0
    nonfiler['p60100'] = 0
    nonfiler['p61850'] = 0
    nonfiler['e60000'] = 0
    nonfiler['e62100'] = 0
    nonfiler['e62900'] = 0
    nonfiler['e62720'] = 0
    nonfiler['e62730'] = 0
    nonfiler['e62740'] = 0
    nonfiler['p65300'] = 0
    nonfiler['p65400'] = 0
    nonfiler['e68000'] = 0
    nonfiler['e82200'] = 0
    nonfiler['t27800'] = 0
    nonfiler['s27860'] = 0
    nonfiler['p27895'] = 0
    nonfiler['p87482'] = 0
    nonfiler['e87521'] = 0
    nonfiler['e87530'] = 0
    nonfiler['e87550'] = 0
    nonfiler['p86421'] = 0
    nonfiler['e52852'] = 0
    nonfiler['e52872'] = 0
    nonfiler['e87870'] = 0
    nonfiler['e87875'] = 0
    nonfiler['e87880'] = 0
    nonfiler['recid'] = 0
    nonfiler['s006'] = wt
    nonfiler['s008'] = 0
    nonfiler['s009'] = 0
    nonfiler['wsamp'] = 0
    nonfiler['txrt'] = 0

    # weight
    nonfiler['matched_weight'] = wt

    final = pd.concat([cpsrets, nonfiler], ignore_index=True)
    final['finalseq'] = final.index + 1
    # final.to_csv('prod2009_v2.csv', index=False)
    return final
