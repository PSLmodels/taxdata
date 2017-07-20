*******************************************************************************************;
***                                                                                     ***;
***                                                                                     ***;
***                          State Modeling Project                                     ***;
***                                                                                     ***;
***                                                                                     ***;
*******************************************************************************************;
OPTIONS PAGESIZE=59 LINESIZE=160 CENTER ; /* LANDSCAPE */
*****
	PRODUCTION FILE
*****;
LIBNAME EXTRACT "C:\Users\anderson.frailey\Documents\State Database - 2015\Production File\EXTRACTS\";
*****
	PROCESS THE PRODUCTION FILE
*****;
DATA PROD2015(COMPRESS=YES);
SET EXTRACT.PROD2015_V1B;
ARRAY BETA1( 11 , 8 );
ARRAY BETA2( 11 , 8 );
ARRAY XVAR(*) XVAR1-XVAR8;
RETAIN BETA1;
RETAIN BETA2;
RETAIN ISEED1 17713 ISEED2 554431;
RETAIN JSEED1 33221 JSEED2 998877;
*****
	INITIALIZATION
*****;
IF( _N_ EQ 1 )THEN
	DO;
		DO I = 1 TO 11;
			PTR = I;
			SET EXTRACT.BETALOGIT2 POINT=PTR;
			BETA1( I , 1 ) = LNINCOME;
			BETA1( I , 2 ) = MARS;
			BETA1( I , 3 ) = FAMSIZE;
			BETA1( I , 4 ) = AGEDE;
			BETA1( I , 5 ) = LNINTST;
			BETA1( I , 6 ) = LNDBE;
			BETA1( I , 7 ) = LNPENSIONS;
			BETA1( I , 8 ) = CONSTANT;
		END;
		DO I = 1 TO 11;
			PTR = I;
			SET EXTRACT.BETAOLS2 POINT=PTR;
			BETA2( I , 1 ) = LNINCOME;
			BETA2( I , 2 ) = MARS;
			BETA2( I , 3 ) = FAMSIZE;
			BETA2( I , 4 ) = AGEDE;
			BETA2( I , 5 ) = LNINTST;
			BETA2( I , 6 ) = LNDBE;
			BETA2( I , 7 ) = LNPENSIONS;
			BETA2( I , 8 ) = CONSTANT;
		END;
	END;
*****
	TOTAL (CPS) INCOME
*****;
TOTAL_INCOME = WAS + INTST + DBE + ALIMONY + BIL + PENSIONS + RENTS + FIL + UCOMP + SOCSEC;
TINCX = TOTAL_INCOME;
LNINCOME = LOG( 1. + MAX( 0. , TINCX ) );
*****
	X-VARIABLES
*****;
XVAR( 1 ) = LNINCOME;
XVAR( 2 ) = 0.;IF( JS = 2 )THEN XVAR( 2 ) = 1.;
XVAR( 3 ) = 1 + DEPNE;IF( JS = 2 )THEN XVAR( 3 ) = XVAR( 3 ) + 1.;
XVAR( 4 ) = 0.;IF( ICPS01 GE 65. )THEN XVAR( 4 ) = 1.; IF( ICPS02 GE 65. )THEN XVAR( 4 ) = XVAR( 4 ) + 1. ;
XVAR( 5 ) = LOG( 1. + MAX( 0. , INTST ) );
XVAR( 6 ) = LOG( 1. + MAX( 0. , DBE   ) );
XVAR( 7 ) = LOG( 1. + MAX( 0. , PENSIONS ) );
XVAR( 8 ) = 1.0;
********************************************************************************************;
***                         BEGIN IMPUTATION SECTION                                     ***;
***                             FILERS ONLY                                              ***;
********************************************************************************************;
*****
	ITEMS TO BE IMPUTED
*****;
CGAGIX = 0.0;
TIRAD = 0.0;
ADJIRA = 0.0;
KEOGH = 0.0;
SEHEALTH = 0.0;
SLINT = 0.0;
CHARITABLE = 0.0;
MISCITEM = 0.0;
OTHERITEM = 0.0;
CCE = 0.0;
MEDEXPDED = 0.0;
HMIE = 0.0;
HOMEVALUE = 0.0;
HOMEEQUITY = 0.0;
REALEST = 0.0;
DPAD = 0.0;
IF( FILST EQ 1 )THEN
DO;
	*****
		1.	CAPITAL GAINS
	*****;
	XB = 0.0;
	DO NV = 1 TO 8;
		XB = XB + BETA1( 1 , NV ) * XVAR( NV );
	END;
	PROB = EXP( XB ) / ( 1. + EXP( XB ) ) + .065 ;
	CALL RANUNI( ISEED1 , Z1 );
	IF( Z1 LE PROB )THEN
			DO;
				XB = 0.0;
				DO NV = 1 TO 8;
					XB = XB + BETA2( 1 , NV ) * XVAR( NV );
				END;
			CALL RANNOR( ISEED2 , Z2 );
			CGAGIX = EXP( XB + 1.9500 * Z2 );
			END;
	*****
		2.	TAXABLE IRA DISTRIBUTIONS
	*****;
	XB = 0.0;
	DO NV = 1 TO 8;
		XB = XB + BETA1( 2 , NV ) * XVAR( NV );
	END;
	PROB = EXP( XB ) / ( 1. + EXP( XB ) ) + .000 ;
	PROB = PROB * 1.25 ;
	CALL RANUNI( ISEED1 , Z1 );
	IF( Z1 LE PROB )THEN
			DO;
				XB = 0.0;
				DO NV = 1 TO 8;
					XB = XB + BETA2( 2 , NV ) * XVAR( NV );
				END;
			CALL RANNOR( ISEED2 , Z2 );
			TIRAD = EXP( XB + 1.7000 * Z2 );
			END;
	*****
		3.	ADJUSTED IRA CONTRIBUTIONS
	*****;
	XB = 0.0;
	DO NV = 1 TO 8;
		XB = XB + BETA1( 3 , NV ) * XVAR( NV );
	END;
	PROB = EXP( XB ) / ( 1. + EXP( XB ) ) + 0.000 ;
	PROB = PROB * .60;
	CALL RANUNI( ISEED1 , Z1 );
	IF( Z1 LE PROB )THEN
			DO;
				XB = 0.0;
				DO NV = 1 TO 8;
					XB = XB + BETA2( 3 , NV ) * XVAR( NV );
				END;
			CALL RANNOR( ISEED2 , Z2 );
			ADJIRA = EXP( XB + 1.0000 * Z2 );
			END;
	*****
		4.	KEOGH PLANS (SEP, SIMPLE)
	*****;
	XB = 0.0;
	DO NV = 1 TO 8;
		XB = XB + BETA1( 4 , NV ) * XVAR( NV );
	END;
	PROB = EXP( XB ) / ( 1. + EXP( XB ) ) + .000 ;
	PROB = PROB * 1.00;
	CALL RANUNI( ISEED1 , Z1 );
	IF( ( BIL NE 0.0 ) OR ( RENTS NE 0.0 ) )THEN
	DO;
	IF( ( Z1 LE PROB ) )THEN
			DO;
				XB = 0.0;
				DO NV = 1 TO 8;
					XB = XB + BETA2( 4 , NV ) * XVAR( NV );
				END;
			CALL RANNOR( ISEED2 , Z2 );
			KEOGH = EXP( XB + 1.0000 * Z2 );
			END;
	END;
	*****
		5.	SELF-EMPLOYED HEALTH INSURANCE DEDUCTION
	*****;
	XB = 0.0;
	DO NV = 1 TO 8;
		XB = XB + BETA1( 5 , NV ) * XVAR( NV );
	END;
	PROB = EXP( XB ) / ( 1. + EXP( XB ) ) + .0000 ;
	PROB = PROB * 1.6 ;
	CALL RANUNI( ISEED1 , Z1 );
	IF( ( BIL NE 0.0 ) OR ( RENTS NE 0.0 ) )THEN
	DO;
	IF( Z1 LE PROB )THEN
			DO;
				XB = 0.0;
				DO NV = 1 TO 8;
					XB = XB + BETA2( 5 , NV ) * XVAR( NV );
				END;
			CALL RANNOR( ISEED2 , Z2 );
			SEHEALTH = EXP( XB + 1.0000 * Z2 );
			END;
	END;
	*****
		6.	STUDENT LOAN INTEREST DEDUCTION
	*****;
	XB = 0.0;
	DO NV = 1 TO 8;
		XB = XB + BETA1( 6 , NV ) * XVAR( NV );
	END;
	PROB = EXP( XB ) / ( 1. + EXP( XB ) ) ;
	PROB = PROB * 1.100;
	CALL RANUNI( ISEED1 , Z1 );
	IF( Z1 LE PROB )THEN
			DO;
				XB = 0.0;
				DO NV = 1 TO 8;
					XB = XB + BETA2( 6 , NV ) * XVAR( NV );
				END;
			CALL RANNOR( ISEED2 , Z2 );
			SLINT = EXP( XB + 1.0000 * Z2 );
			END;
	*****
		7.	CHARITABLE DEDUCTION (TOBIT MODEL)
	*****;
	XB = 0.0;
	LAMBDA = 0.0;
	SIGMA = 48765.45;
	DO NV = 1 TO 8;
		XB = XB + BETA2( 7 , NV ) * XVAR( NV );
	END;
	PROB = CDF('NORMAL' , XB/SIGMA );
	PROB = PROB * 1.0000;
	CALL RANUNI( ISEED1 , Z1 );
	IF( Z1 LE PROB )THEN
			DO;
				LAMBDA = PDF( 'NORMAL' , XB/SIGMA ) / CDF( 'NORMAL' , XB/SIGMA ) ;
				CALL RANNOR( ISEED2 , Z2 );
				CHARITABLE = XB + SIGMA*LAMBDA ;
			END;
	*****
		8.	MISCELLANEOUS ITEMIZED DEDUCTIONS (TOBIT MODEL)
	*****;
	XB = 0.0;
	LAMBDA = 0.0;
	SIGMA = 14393.99;
	DO NV = 1 TO 8;
		XB = XB + BETA2( 8 , NV ) * XVAR( NV );
	END;
	PROB = CDF( 'NORMAL' , XB/SIGMA ) ;
	PROB = PROB * .30;
	CALL RANUNI( ISEED1 , Z1 );
	IF( Z1 LE PROB )THEN
			DO;
				LAMBDA = PDF( 'NORMAL' , XB/SIGMA ) / CDF( 'NORMAL' , XB/SIGMA ) ;
				CALL RANNOR( ISEED2 , Z2 );
				MISCITEM = XB + SIGMA*LAMBDA;
			END;
	*****
		9.	OTHER MISCELLANEOUS ITEMIZED DEDUCTIONS (NONE)
	*****;
	OTHERITEM = 0.0;		
	*****
		10.	CHILD CARE EXPENSES
	*****;
	XB = 0.0;
	DO NV = 1 TO 8;
		XB = XB + BETA1( 10 , NV ) * XVAR( NV );
	END;
	PROB = EXP( XB ) / ( 1. + EXP( XB ) )  ;
	PROB = PROB * 1.000 ;
	CALL RANUNI( ISEED1 , Z1 );
	IF( (Z1 LE PROB) AND (DEPNE NE 0) )THEN
			DO;
				XB = 0.0;
				DO NV = 1 TO 8;
					XB = XB + BETA2( 10 , NV ) * XVAR( NV );
				END;
			CALL RANNOR( ISEED2 , Z2 );
			CCE = EXP( XB + 1.0000 * Z2 );
			END;
	*****
		11.	MEDICAL EXPENSE DEDUCTION
	*****;
	XB = 0.0;
	DO NV = 1 TO 8;
		XB = XB + BETA1( 11 , NV ) * XVAR( NV );
	END;
	PROB = EXP( XB ) / ( 1. + EXP( XB ) ) ;
	CALL RANUNI( ISEED1 , Z1 );
	IF( Z1 LE PROB )THEN
			DO;
				XB = 0.0;
				DO NV = 1 TO 8;
					XB = XB + BETA2( 11 , NV ) * XVAR( NV );
				END;
			CALL RANNOR( ISEED2 , Z2 );
			MEDICALEXP = EXP( XB + 1.0000 * Z2 );
			END;

END;
*****
	ADDITIONAL IMPUTATIONS
*****;
	*****
	12.	HOME MORTGAGE INTEREST EXPENSE
	13.	HOME VALUE
	14.	HOME EQUITY
	*****;
*****
	ANALYSIS VARIABLES
*****;
HOMEOWNER = 0.;
IF( ICPS29 EQ 1 )THEN HOMEOWNER = 1.;
IF( IFDEPT EQ 1 )THEN HOMEOWNER = 0.;
JNJ = 1;
IF( JS NE 2 )THEN JNJ = 2;
AGED = 0;
IF( ICPS01 GE 65. )THEN AGED = 1;
AGE = ICPS01;
MARRIED = 0;
IF( JS = 2 )THEN MARRIED = 1;
*****
	ADD BACK IN GAINS AND IRA DISTRIBUTIONS
*****;
TINCX = TOTAL_INCOME + CGAGIX + TIRAD;
LNINCOME = LOG( 1. + MAX( 0. , TINCX ) );
INCOME = MAX( 0. , TINCX );
FAMSIZE = 1. + DEPNE;
IF( JS = 2 )THEN FAMSIZE = FAMSIZE + 1;
LNINCOME = LOG( 1. + INCOME);
LNVALUE = 0.006494 * AGE
        + 0.0170197 * FAMSIZE
		+ 0.1150217 * MARRIED
		+ 0.4372681 * LNINCOME
		+ 6.753875;
HOMEVALUE = EXP( LNVALUE );
RATIO   = -0.0115935 * AGE
        + 0.0138109 * FAMSIZE
		- 0.0336637 * MARRIED
		+ 0.0163805 * LNINCOME
		+ 0.8048336;
RATIO = MAX( 0. , MIN(1. , RATIO) );
***
	ADJUSTMENT FACTOR
***;
FACTOR = 1.73855;
HOMEVALUE = HOMEVALUE * HOMEOWNER * FACTOR;
MORTGAGEDEBT = RATIO * HOMEVALUE;
HOMEEQUITY = (1. - RATIO) * HOMEVALUE;
MORTGAGEINTEREST = MORTGAGEDEBT * 0.0575;
HMIE = MORTGAGEINTEREST;
*****
	REAL ESTATE TAXES
*****;
REALEST = 0.0075 * HOMEVALUE;
*****
	DOMESTIC PRODUCTION ACTIVITY DEDUCTION;
*****;
DPAD = 0.0;
IF(  ( BIL NE 0. ) OR ( RENTS NE 0.0 ) )THEN
DO;
	IF( TINCX LE 1 )THEN
		DO;
			PROB = 0.7000 *.01524;
			CALL RANUNI( JSEED1 , Z1 );
			IF( Z1 LE PROB )THEN
				DO;
					CALL RANNOR( JSEED2 , Z2 );
					DPAD = 20686. + 0.25 * Z2 ;
				END;
		END;
	IF( ( TINCX GE 1 ) AND ( TINCX LT 25000. ) )THEN
		DO;
			PROB = 0.7000 *.00477;
			CALL RANUNI( JSEED1 , Z1 );
			IF( Z1 LE PROB )THEN
				DO;
					CALL RANNOR( JSEED2 , Z2 );
					DPAD = 1784. + 0.25 * Z2 ;
				END;
		END;
	IF( ( TINCX GE 25000. ) AND ( TINCX LT 50000. ) )THEN
		DO;
			PROB = 0.7000 *.01517;
			CALL RANUNI( JSEED1 , Z1 );
			IF( Z1 LE PROB )THEN
				DO;
					CALL RANNOR( JSEED2 , Z2 );
					DPAD = 2384. + 0.25 * Z2 ;
				END;
		END;
	IF( ( TINCX GE 50000. ) AND ( TINCX LT 75000. ) )THEN
		DO;
			PROB = 0.7000 *.02488;
			CALL RANUNI( JSEED1 , Z1 );
			IF( Z1 LE PROB )THEN
				DO;
					CALL RANNOR( JSEED2 , Z2 );
					DPAD = 2779. + 0.25 * Z2 ;
				END;
		END;
	IF( ( TINCX GE 75000. ) AND ( TINCX LT 100000. ) )THEN
		DO;
			PROB = 0.7000 *.03368;
			CALL RANUNI( JSEED1 , Z1 );
			IF( Z1 LE PROB )THEN
				DO;
					CALL RANNOR( JSEED2 , Z2 );
					DPAD = 3312. + 0.25 * Z2 ;
				END;
		END;
	IF( ( TINCX GE 100000. ) AND ( TINCX LT 200000. ) )THEN
		DO;
			PROB = 0.7000 *.05089;
			CALL RANUNI( JSEED1 , Z1 );
			IF( Z1 LE PROB )THEN
				DO;
					CALL RANNOR( JSEED2 , Z2 );
					DPAD = 4827. + 0.25 * Z2 ;
				END;
		END;
	IF( ( TINCX GE 200000. ) AND ( TINCX LT 500000. ) )THEN
		DO;
			PROB = 0.7000 *.11659;
			CALL RANUNI( JSEED1 , Z1 );
			IF( Z1 LE PROB )THEN
				DO;
					CALL RANNOR( JSEED2 , Z2 );
					DPAD = 10585. + 0.25 * Z2 ;
				END;
		END;
	IF( ( TINCX GE 500000. ) AND ( TINCX LT 1000000. ) )THEN
		DO;
			PROB = 0.7000 *.26060;
			CALL RANUNI( JSEED1 , Z1 );
			IF( Z1 LE PROB )THEN
				DO;
					CALL RANNOR( JSEED2 , Z2 );
					DPAD = 24358. + 0.25 * Z2 ;
				END;
		END;
	IF( ( TINCX GE 1000000. )  )THEN
		DO;
			PROB = 0.7000 *.54408;
			CALL RANUNI( JSEED1 , Z1 );
			IF( Z1 LE PROB )THEN
				DO;
					CALL RANNOR( JSEED2 , Z2 );
					DPAD = 116275. + 0.25 * Z2 ;
				END;
		END;
END;
DPAD = DPAD * .3000 ;
*****
	FINAL ADJUSTMENTS
*****;
ADJIRA = MIN( ADJIRA , 6000. )* 1.3;
KEOGH = MIN( KEOGH , 150000. ) * 0.7000;
SLINT = SLINT * 1.90 ;
CCE = MIN( CCE , 5000. ) * .3333;
SEHEALTH = MIN( SEHEALTH , 50000. ) * 1.1;
CHARITABLE = CHARITABLE * 0.17500 ;
*****
	ZEROS TO MISSING
*****;
IF( CGAGIX EQ 0.0 )THEN CGAGIX = .;
IF( TIRAD EQ 0.0 )THEN TIRAD = .;
IF( ADJIRA EQ 0.0 )THEN ADJIRA = .;
IF( KEOGH EQ 0.0 )THEN KEOGH = .;
IF( SEHEALTH EQ 0.0 )THEN SEHEALTH = .;
IF( SLINT EQ 0.0 )THEN SLINT = .;
IF( CHARITABLE EQ 0.0 )THEN CHARITABLE = .;
IF( MISCITEM EQ 0.0 )THEN MISCITEM = .;
IF( OTHERITEM EQ 0.0 )THEN OTHERITEM = .;
IF( CCE EQ 0.0 )THEN CCE = .;
IF( MEDICALEXP EQ 0.0 )THEN MEDICALEXP = .;
IF( HMIE EQ 0.0 )THEN HMIE = .;
IF( HOMEVALUE EQ 0.0 )THEN HOMEVALUE = .;
IF( HOMEEQUITY EQ 0.0 )THEN HOMEEQUITY = .;
IF( REALEST EQ 0.0 )THEN REALEST = .;
IF( DPAD EQ 0.0 )THEN DPAD = .;
DROP FACTOR;
RUN;
DATA EXTRACT.PROD2015_V1C(COMPRESS=YES);
SET PROD2015;
RUN;
PROC MEANS N SUMWGT MIN MAX MEAN SUM DATA=EXTRACT.PROD2015_V1C;
WEIGHT WT;
VAR CGAGIX TIRAD ADJIRA KEOGH SEHEALTH SLINT CHARITABLE MISCITEM
    OTHERITEM CCE MEDICALEXP HMIE HOMEVALUE HOMEEQUITY REALEST DPAD;
TITLE1 "2015 State Database";
TITLE2 "Imputation of Selected Income Tax Variables";
RUN;
