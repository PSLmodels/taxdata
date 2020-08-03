function Dataprep(puf, Stage_I_factors, Stage_II_targets, year)

	println("Preparing coefficient matrix for $year .....")

	s006 = @. ifelse(puf["e02400"] > 0,
	                    puf["s006"] * Stage_I_factors[string(year)]["APOPSNR"] / 100,
	                    puf["s006"] * Stage_I_factors[string(year)]["ARETS"] / 100)

	single_return = @. ifelse((puf["mars"] == 1) & (puf["filer"] == 1), s006, 0)
    joint_return = @. ifelse(((puf["mars"] == 2) | (puf["mars"] == 3)) &
                            (puf["filer"] == 1), s006, 0)

    hh_return = @. ifelse((puf["mars"] == 4) & (puf["filer"] == 1), s006, 0)
    return_w_SS = @. ifelse((puf["e02400"] > 0) & (puf["filer"] == 1), s006, 0)

    dependent_exempt_num = (puf["xocah"] + puf["xocawh"] +
                            puf["xoodep"] + puf["xopar"]) * s006
    interest = puf["e00300"] * s006
    dividend = puf["e00600"] * s006
    biz_income = @. ifelse(puf["e00900"] > 0, puf["e00900"], 0) * s006
    biz_loss = @. ifelse(puf["e00900"] < 0, -puf["e00900"], 0) * s006
    cap_gain = @. ifelse((puf["p23250"] + puf["p22250"]) > 0,
                        puf["p23250"] + puf["p22250"], 0) * s006
    annuity_pension = puf["e01700"] * s006
    sch_e_income = @. ifelse(puf["e02000"] > 0, puf["e02000"], 0) * s006
    sch_e_loss = @. ifelse(puf["e02000"] < 0, -puf["e02000"], 0) * s006
    ss_income = @. ifelse(puf["filer"] == 1, puf["e02400"], 0) * s006
    unemployment_comp = puf["e02300"] * s006

    # Wage distribution
    wage_1 = @. ifelse(puf["e00100"] <= 0, puf["e00200"], 0) * s006
    wage_2 = @. ifelse((puf["e00100"] > 0) & (puf["e00100"] <= 10000),
                      puf["e00200"], 0) * s006
    wage_3 = @. ifelse((puf["e00100"] > 10000) & (puf["e00100"] <= 20000),
                      puf["e00200"], 0) * s006
    wage_4 = @. ifelse((puf["e00100"] > 20000) & (puf["e00100"] <= 30000),
                      puf["e00200"], 0) * s006
    wage_5 = @. ifelse((puf["e00100"] > 30000) & (puf["e00100"] <= 40000),
                      puf["e00200"], 0) * s006
    wage_6 = @. ifelse((puf["e00100"] > 40000) & (puf["e00100"] <= 50000),
                      puf["e00200"], 0) * s006
    wage_7 = @. ifelse((puf["e00100"] > 50000) & (puf["e00100"] <= 75000),
                      puf["e00200"], 0) * s006
    wage_8 = @. ifelse((puf["e00100"] > 75000) & (puf["e00100"] <= 100000),
                      puf["e00200"], 0) * s006
    wage_9 = @. ifelse((puf["e00100"] > 100000) & (puf["e00100"] <= 200000),
                      puf["e00200"], 0) * s006
    wage_10 = @. ifelse((puf["e00100"] > 200000) & (puf["e00100"] <= 500000),
                       puf["e00200"], 0) * s006
    wage_11 = @. ifelse((puf["e00100"] > 500000) & (puf["e00100"] <= 1000000),
                       puf["e00200"], 0) * s006
    wage_12 = @. ifelse(puf["e00100"] > 1000000, puf["e00200"], 0) * s006

    # Set up the matrix
    One_half_LHS = vcat(single_return, joint_return, hh_return,
                              return_w_SS,
                              dependent_exempt_num, interest, dividend,
                              biz_income, biz_loss, cap_gain, annuity_pension,
                              sch_e_income, sch_e_loss,
                              ss_income, unemployment_comp,
                              wage_1, wage_2, wage_3, wage_4, wage_5,
                              wage_6, wage_7, wage_8, wage_9, wage_10,
                              wage_11, wage_12)

    # Coefficients for r and s
    A1 = One_half_LHS
    A2 = -1*One_half_LHS

    print("Preparing targets for year $year .....")

    APOPN = Stage_I_factors[string(year)]["APOPN"]

    b = []

    append!(b, Stage_II_targets[string(year)]["Single Returns"] - sum(single_return))
    append!(b, Stage_II_targets[string(year)]["Joint Returns"] - sum(joint_return))
    target_name = "Head of Household Returns"
    append!(b, Stage_II_targets[string(year)][target_name] - sum(hh_return))
    target_name = "Number of Returns w/ Gross Security Income"
    append!(b, Stage_II_targets[string(year)][target_name] - sum(return_w_SS))
    target_name = "Number of Dependent Exemptions"
    append!(b, Stage_II_targets[string(year)][target_name] - sum(dependent_exempt_num))


    AINTS = Stage_I_factors[string(year)]["AINTS"]
    INTEREST = (Stage_II_targets[string(year)]["Taxable Interest Income"] *
                APOPN / AINTS * 1000 - sum(interest))

    ADIVS = Stage_I_factors[string(year)]["ADIVS"]
    DIVIDEND = (Stage_II_targets[string(year)]["Ordinary Dividends"] *
                APOPN / ADIVS * 1000 - sum(dividend))

    ASCHCI = Stage_I_factors[string(year)]["ASCHCI"]
    BIZ_INCOME = (Stage_II_targets[string(year)]["Business Income (Schedule C)"] *
                  APOPN / ASCHCI * 1000 - sum(biz_income))

    ASCHCL = Stage_I_factors[string(year)]["ASCHCL"]
    BIZ_LOSS = (Stage_II_targets[string(year)]["Business Loss (Schedule C)"] *
                APOPN / ASCHCL * 1000 - sum(biz_loss))

    ACGNS = Stage_I_factors[string(year)]["ACGNS"]
    CAP_GAIN = (Stage_II_targets[string(year)]["Net Capital Gains in AGI"] *
                APOPN / ACGNS * 1000 - sum(cap_gain))

    ATXPY = Stage_I_factors[string(year)]["ATXPY"]
    target_name = "Taxable Pensions and Annuities"
    ANNUITY_PENSION = (Stage_II_targets[string(year)][target_name] *
                       APOPN / ATXPY * 1000 - sum(annuity_pension))

    ASCHEI = Stage_I_factors[string(year)]["ASCHEI"]
    target_name = "Supplemental Income (Schedule E)"
    SCH_E_INCOME = (Stage_II_targets[string(year)][target_name] *
                    APOPN / ASCHEI * 1000 - sum(sch_e_income))

    ASCHEL = Stage_I_factors[string(year)]["ASCHEL"]
    SCH_E_LOSS = (Stage_II_targets[string(year)]["Supplemental Loss (Schedule E)"] *
                  APOPN / ASCHEL * 1000 - sum(sch_e_loss))

    ASOCSEC = Stage_I_factors[string(year)]["ASOCSEC"]
    APOPSNR = Stage_I_factors[string(year)]["APOPSNR"]
    SS_INCOME = (Stage_II_targets[string(year)]["Gross Social Security Income"] *
                 APOPSNR / ASOCSEC * 1000 - sum(ss_income))

    AUCOMP = Stage_I_factors[string(year)]["AUCOMP"]
    UNEMPLOYMENT_COMP = (Stage_II_targets[string(year)]["Unemployment Compensation"] *
                         APOPN / AUCOMP * 1000 - sum(unemployment_comp))

    AWAGE = Stage_I_factors[string(year)]["AWAGE"]
	target_name = "Wages and Salaries: Zero or Less"
	WAGE_1 = (Stage_II_targets[string(year)][target_name] *
	          APOPN / AWAGE * 100 - sum(wage_1))
	target_name = "Wages and Salaries: \$1 Less Than \$10,000"
	WAGE_2 = (Stage_II_targets[string(year)][target_name] *
	          APOPN / AWAGE * 100 - sum(wage_2))
	target_name = "Wages and Salaries: \$10,000 Less Than \$20,000"
	WAGE_3 = (Stage_II_targets[string(year)][target_name] *
	          APOPN / AWAGE * 100 - sum(wage_3))
	target_name = "Wages and Salaries: \$20,000 Less Than \$30,000"
	WAGE_4 = (Stage_II_targets[string(year)][target_name] *
	          APOPN / AWAGE * 100 - sum(wage_4))
	target_name = "Wages and Salaries: \$30,000 Less Than \$40,000"
	WAGE_5 = (Stage_II_targets[string(year)][target_name] *
	          APOPN / AWAGE * 100 - sum(wage_5))
	target_name = "Wages and Salaries: \$40,000 Less Than \$50,000"
	WAGE_6 = (Stage_II_targets[string(year)][target_name] *
	          APOPN / AWAGE * 100 - sum(wage_6))
	target_name = "Wages and Salaries: \$50,000 Less Than \$75,000"
	WAGE_7 = (Stage_II_targets[string(year)][target_name] *
	          APOPN / AWAGE * 100 - sum(wage_7))
	target_name = "Wages and Salaries: \$75,000 Less Than \$100,000"
	WAGE_8 = (Stage_II_targets[string(year)][target_name] *
	          APOPN / AWAGE * 100 - sum(wage_8))
	target_name = "Wages and Salaries: \$100,000 Less Than \$200,000"
	WAGE_9 = (Stage_II_targets[string(year)][target_name] *
	          APOPN / AWAGE * 100 - sum(wage_9))
	target_name = "Wages and Salaries: \$200,000 Less Than \$500,000"
	WAGE_10 = (Stage_II_targets[string(year)][target_name] *
	           APOPN / AWAGE * 100 - sum(wage_10))
	target_name = "Wages and Salaries: \$500,000 Less Than \$1 Million"
	WAGE_11 = (Stage_II_targets[string(year)][target_name] *
	           APOPN / AWAGE * 100 - sum(wage_11))
	target_name = "Wages and Salaries: \$1 Million and Over"
	WAGE_12 = (Stage_II_targets[string(year)][target_name] *
	           APOPN / AWAGE * 100 - sum(wage_12))

	temp = [INTEREST, DIVIDEND, BIZ_INCOME, BIZ_LOSS, CAP_GAIN,
	        ANNUITY_PENSION, SCH_E_INCOME, SCH_E_LOSS, SS_INCOME,
	        UNEMPLOYMENT_COMP,
	        WAGE_1, WAGE_2, WAGE_3, WAGE_4, WAGE_5, WAGE_6,
	        WAGE_7, WAGE_8, WAGE_9, WAGE_10, WAGE_11, WAGE_12]
	for m in temp
		append!(b, m)
	end


	return 



	println("Test: Program has finished")

end