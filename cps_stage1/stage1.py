import pandas as pd


def main():
    SYR = '2014'  # Start year of CPS
    EYR = 2027

    # Read in state SOI estimates
    soi_estimates = pd.read_csv('SOI_estimates.csv', index_col=0)
    stage_2_targets = pd.read_csv('../puf_stage1/Stage_II_targets.csv',
                                  index_col=0)
    stage_2_targets.drop(columns=['2011', '2012', '2013'], inplace=True)
    factors = pd.DataFrame()
    cbo_baseline = pd.read_csv('../stage1/CBO_baseline.csv', index_col=0)
    cbobase = cbo_baseline.transpose()
    data = stage_2_targets.loc[stage_2_targets.index[3:6]].sum()
    factors['ARETS'] = data / data[SYR]
    data = stage_2_targets.loc[stage_2_targets.index[18:30]].sum()
    factors['AWAGE'] = data / data[SYR]
    data = cbobase.loc[cbobase.index[6:]]['TPY']
    factors['ATXPY'] = data / data[SYR]

    factors_list = [('US Population', 'APOPN'),
                    ('Taxable Interest Income', 'AINTS'),
                    ('Ordinary Dividends', 'ADIVS'),
                    ('Business Income (Schedule C)', 'ASCHCI'),
                    ('Business Loss (Schedule C)', 'ASCHCL'),
                    ('Net Capital Gains in AGI', 'ACGNS'),
                    ('Supplemental Income (Schedule E)', 'ASCHEI'),
                    ('Supplemental Loss (Schedule E)', 'ASCHEL'),
                    ('Gross Social Security Income', 'ASOCSEC'),
                    ('POP_SNR', 'APOPSNR'),
                    ('Unemployment Compensation', 'AUCOMP'),
                    ('Net Capital Gains in AGI', 'ACGNS')]

    for index_name, factor_name in factors_list:
        factors[factor_name] = (stage_2_targets.loc[index_name] /
                                stage_2_targets[SYR][index_name])

    for year in range(int(SYR) + 1, EYR + 1):
        stryr = str(year)
        single = soi_estimates[SYR]['Single'] * factors['ARETS'][stryr]
        joint = soi_estimates[SYR]['Joint'] * factors['ARETS'][stryr]
        hh = soi_estimates[SYR]['HH'] * factors['ARETS'][stryr]
        ss_return = soi_estimates[SYR]['SS_return'] * factors['APOPSNR'][stryr]
        dep_return = soi_estimates[SYR]['Dep_return'] * factors['APOPN'][stryr]
        ints = soi_estimates[SYR]['INTS'] * factors['AINTS'][stryr]
        divs = soi_estimates[SYR]['DIVS'] * factors['ADIVS'][stryr]
        schci = soi_estimates[SYR]['SCHCI'] * factors['ASCHCI'][stryr]
        schcl = soi_estimates[SYR]['SCHCL'] * factors['ASCHCL'][stryr]
        cgns = soi_estimates[SYR]['CGNS'] * factors['ACGNS'][stryr]
        pension = soi_estimates[SYR]['Pension'] * factors['ATXPY'][stryr]
        schei = soi_estimates[SYR]['SCHEI'] * factors['ASCHEI'][stryr]
        schel = soi_estimates[SYR]['SCHEL'] * factors['ASCHEL'][stryr]
        ss = soi_estimates[SYR]['SS'] * factors['ASOCSEC'][stryr]
        ucomp = soi_estimates[SYR]['UCOMP'] * factors['AUCOMP'][stryr]
        wage1 = soi_estimates[SYR]['wage1'] * factors['AWAGE'][stryr]
        wage2 = soi_estimates[SYR]['wage2'] * factors['AWAGE'][stryr]
        wage3 = soi_estimates[SYR]['wage3'] * factors['AWAGE'][stryr]
        wage4 = soi_estimates[SYR]['wage4'] * factors['AWAGE'][stryr]
        wage5 = soi_estimates[SYR]['wage5'] * factors['AWAGE'][stryr]
        wage6 = soi_estimates[SYR]['wage6'] * factors['AWAGE'][stryr]
        wage7 = soi_estimates[SYR]['wage7'] * factors['AWAGE'][stryr]
        wage8 = soi_estimates[SYR]['wage8'] * factors['AWAGE'][stryr]

        current_year = pd.Series([single, joint, hh, ss_return, dep_return,
                                  ints, divs, schci, schcl, cgns, pension,
                                  schei, schel, ss, ucomp,
                                  wage1, wage2, wage3, wage4, wage5,
                                  wage6, wage7, wage8],
                                 index=soi_estimates.index)
        soi_estimates[year] = current_year

    soi_estimates.to_csv('stage_2_targets.csv')
    factors.to_csv('stage_1_factors.csv')


if __name__ == '__main__':
    main()
