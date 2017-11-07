library(censReg)
# https://cran.r-project.org/web/packages/censReg/censReg.pdf
puf <- read.csv("taxdata/puf_data/StatMatch/Matching/puf2011.csv")
# create total income variable
puf["totinc"] = (puf["E00200"] + puf["E00300"] + puf["E00600"] +
                   puf["E00650"] + puf["E01700"] + puf["E02100"] +
                   puf["E02000"] + puf["E02400"])
# find log of total income
puf["totinc"][puf["totinc"] < 0] <- 0
puf["lnincome"] <- log1p(puf["totinc"])

# determine number of people above 65 in a tax unit
# single filer, abouve 65 based on standard deduction
puf["single_elderly_st"] <- FALSE
puf["single_elderly_st"][(puf["MARS"] == 1) &
                           (puf["FDED"] == 2) &
                           (puf["P04470"] >= 7250)] <- TRUE
# head of household filer
puf["hoh_elderly_st"] <- FALSE
puf["hoh_elderly_st"][(puf["MARS"] == 4) &
                        (puf["FDED"] == 2) &
                        (puf["P04470"] >= 9950)] <- TRUE

# estimate number above 65 on a joint return
puf["joint_one_st"] <- FALSE
puf["joint_one_st"][(puf["MARS"] == 3) &
                      (puf["FDED"] == 2) &
                      (puf["P04470"] >= 12750) &
                      (puf["P04470"] < 13900)] <- TRUE
puf["joint_two_st"] <- FALSE
puf["joint_two_st"][(puf["MARS"] == 3) &
                      (puf["FDED"] == 2) &
                      (puf["P04470"] >= 13900)] <- TRUE

# same calculations as above with itemized deduction filers
puf["single_elderly_it"] <- FALSE
puf["single_elderly_it"][(puf["MARS"] == 1) &
                           (puf["FDED"] == 1) &
                           (puf["E02400"] > 0)] <- 0
puf["hoh_elderly_it"] <- FALSE
puf["hoh_elderly_it"][(puf["MARS"] == 4) &
                        (puf["FDED"] == 1) &
                        (puf["E02400"] > 0)] <- 0

puf["joint_one_it"] <- FALSE
puf["joint_one_it"][(puf["MARS"] == 3) &
                      (puf["FDED"] == 1) &
                      (puf["E02400"] > 0) &
                      (puf["E02400"] < 25000)] <- TRUE
puf["joint_two_it"] <- FALSE
puf["joint_two_it"][(puf["MARS"] == 3) &
                      (puf["FDED"] == 1) &
                      (puf["E02400"] > 25000)] <- TRUE
puf["agede"] <- 0
puf["agede"][(puf["single_elderly_st"] == TRUE) |
               (puf["hoh_elderly_st"] == TRUE) |
               (puf["joint_one_st"] == TRUE) |
               (puf["single_elderly_it"] == TRUE) |
               (puf["hoh_elderly_it"] == TRUE) |
               (puf["joint_one_it"] == TRUE)] <- 1
puf["agede"][(puf["joint_two_st"] == TRUE) |
               (puf["joint_two_it"] == TRUE)] <- 2
puf["constant"] <- 1

# prep other data for regression
puf["charitable"] <- log1p(puf["E19800"]+ puf["E20100"]) 
puf["lnintst"] <- log1p(puf["E00300"])
puf["lndbe"] <- log1p(puf["E00600"] + puf["E00650"])
puf["lnpensions"] <- log1p(puf["E01700"])
puf["marsReg"] <- 0
puf["marsReg"][(puf["MARS"] == 1) |
                 (puf["MARS"] == 4)] <- 1
puf["miscellaneous"] <- log1p(puf["E20400"])

# run censored regressions
tobit_char <- censReg(charitable  ~ lnincome + marsReg + XTOT + agede, left = 0, 
                      data = puf)
tobit_misc <- censReg(miscellaneous  ~ lnincome + marsReg + XTOT + agede, left = 0, 
                      data = puf)
summary(tobit_char)
coef(tobit_char)
# write.csv(as.data.frame(coef(tobit_char)), file = "cpstaxunits/data/coef_tobit_charitable.csv")
coefs = data.frame(coef(tobit_char), coef(tobit_misc))
colnames(coefs) <- c('charitable', 'misc')
rownames(coefs) <- c('constant', 'lnincome', 'mars_reg', 'famsize', 'agede', 'logSigma')
coefs <- coefs[c('constant', 'lnincome', 'mars_reg', 'famsize', 'agede'), ]

# export coefficients
write.csv(coefs, file = 'cpstaxunits/data/tobit_betas.csv')
