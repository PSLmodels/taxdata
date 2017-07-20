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
SET EXTRACT.PROD2015_V1A;
ARRAY JCPS(*) JCPS1-JCPS200;
RETAIN NCOPIES 15;
RETAIN ISEED1 34713 ISEED2 72477;
ORIGINAL_WT = WT;
*****
	WAGE AND SALARY INCOME
*****;
WAS = JCPS21 + JCPS31;
INTST = JCPS22 + JCPS32;
DBE = JCPS23 + JCPS33;
ALIMONY = JCPS24 + JCPS34;
BIL = JCPS25 + JCPS35;
PENSIONS = JCPS26 + JCPS36;
RENTS = JCPS27 + JCPS37;
FIL = JCPS28 + JCPS38;
TC1_P = 0;
TC1_S = 0;
TC2_P = 0;
TC2_S = 0;
TC3_P = 0;
TC3_S = 0;
TC4_P = 0;
TC4_S = 0;
TC5_P = 0;
TC5_S = 0;
TC6_P = 0;
TC6_S = 0;
TC7_P = 0;
TC7_S = 0;
TC8_P = 0;
TC8_S = 0;
IF( JCPS21 GT 200000. )THEN TC1_P = 1;
IF( JCPS31 GT 200000. )THEN TC1_S = 1;
IF( JCPS22 GT 24000. )THEN TC2_P = 1;
IF( JCPS32 GT 24000. )THEN TC2_S = 1;
IF( JCPS23 GT 20000. )THEN TC3_P = 1;
IF( JCPS33 GT 20000. )THEN TC3_S = 1;
IF( JCPS24 GT 45000. )THEN TC4_P = 1;
IF( JCPS34 GT 45000. )THEN TC4_S = 1;
IF( JCPS25 GT 50000. )THEN TC5_P = 1;
IF( JCPS35 GT 50000. )THEN TC5_S = 1;
IF( JCPS26 GT 45000. )THEN TC6_P = 1;
IF( JCPS36 GT 45000. )THEN TC6_S = 1;
IF( JCPS27 GT 40000. )THEN TC7_P = 1;
IF( JCPS37 GT 40000. )THEN TC7_S = 1;
IF( JCPS28 GT 25000. )THEN TC8_P = 1;
IF( JCPS38 GT 25000. )THEN TC8_S = 1;
*****
	NUMBER OF TOP-CODED RECORDS
*****;
TC_ALL = TC1_P + TC2_P + TC3_P + TC4_P + TC5_P + TC6_P + TC7_P + TC8_P
       + TC1_S + TC2_S + TC3_S + TC4_S + TC5_S + TC6_S + TC7_S + TC8_S ;
IF( (TC_ALL) GT 0 )THEN /* RECORD IS TOP-CODED SOMEWHERE	*/
DO;
	DO I = 1 TO NCOPIES;
*****
	WAGES AND SALARY
*****;
		IF( TC1_P GT 0 )THEN
			DO;
				CALL RANNOR( ISEED1 , Z1 );
				JCPS21 = EXP( 12. + 1.00 * Z1 );
				IF( JCPS21 LT 200000. )THEN JCPS21 = 200000.;
			END;
		IF( TC1_S GT 0 )THEN
			DO;
				CALL RANNOR( ISEED2 , Z2 );
				JCPS31 = EXP( 12. + 1.00 * Z2 );
				IF( JCPS31 LT 200000. )THEN JCPS31 = 200000.;
			END;
*****
	TAXABLE INTEREST INCOME
*****;
		IF( TC2_P GT 0 )THEN
			DO;
				CALL RANNOR( ISEED1 , Z1 );
				JCPS22 = EXP( 9.00 + 1.00 * Z1 );
				IF( JCPS22 LT 24000. )THEN JCPS22 = 24000.;
			END;
		IF( TC2_S GT 0 )THEN
			DO;
				CALL RANNOR( ISEED2 , Z2 );
				JCPS32 = EXP( 9.00 + 1.00 * Z2 );
				IF( JCPS32 LT 24000. )THEN JCPS32 = 24000.;
			END;
*****
	DIVIDENDS
*****;
		IF( TC3_P GT 0 )THEN
			DO;
				CALL RANNOR( ISEED1 , Z1 );
				JCPS23 = EXP( 10.50 + 1.50 * Z1 );
				IF( JCPS23 LT 20000. )THEN JCPS23 = 20000.;
			END;
		IF( TC3_S GT 0 )THEN
			DO;
				CALL RANNOR( ISEED2 , Z2 );
				JCPS33 = EXP( 10.50 + 1.50 * Z2 );
				IF( JCPS33 LT 20000. )THEN JCPS33 = 20000.;
			END;
*****
	ALIMONY
*****;
		IF( TC4_P GT 0 )THEN
			DO;
				CALL RANNOR( ISEED1 , Z1 );
				JCPS24 = EXP( 13. + 1.00 * Z1 );
				IF( JCPS24 LT 45000. )THEN JCPS24 = 45000.;
			END;
		IF( TC4_S GT 0 )THEN
			DO;
				CALL RANNOR( ISEED2 , Z2 );
				JCPS34 = EXP( 13. + 1.00 * Z2 );
				IF( JCPS34 LT 45000. )THEN JCPS34 = 45000.;
			END;
*****
	BUSINESS INCOME/LOSS
*****;
		IF( TC5_P GT 0 )THEN
			DO;
				CALL RANNOR( ISEED1 , Z1 );
				JCPS25 = EXP( 10.4 + 1.00 * Z1 );
				IF( JCPS25 LT 50000. )THEN JCPS25 = 50000.;
			END;
		IF( TC5_S GT 0 )THEN
			DO;
				CALL RANNOR( ISEED2 , Z2 );
				JCPS35 = EXP( 10.4 + 1.00 * Z2 );
				IF( JCPS35 LT 50000. )THEN JCPS35 = 50000.;
			END;
*****
	PENSIONS
*****;
		IF( TC6_P GT 0 )THEN
			DO;
				CALL RANNOR( ISEED1 , Z1 );
				JCPS26 = EXP( 10.5 + 1.00 * Z1 );
				IF( JCPS26 LT 45000. )THEN JCPS26 = 45000.;
			END;
		IF( TC6_S GT 0 )THEN
			DO;
				CALL RANNOR( ISEED2 , Z2 );
				JCPS36 = EXP( 10.5 + 1.00 * Z2 );
				IF( JCPS36 LT 45000. )THEN JCPS36 = 45000.;
			END;
*****
	RENTS
*****;
		IF( TC7_P GT 0 )THEN
			DO;
				CALL RANNOR( ISEED1 , Z1 );
				JCPS27 = EXP( 13.15 + 1.00 * Z1 );
				IF( JCPS27 LT 40000. )THEN JCPS27 = 40000.;
			END;
		IF( TC7_S GT 0 )THEN
			DO;
				CALL RANNOR( ISEED2 , Z2 );
				JCPS37 = EXP( 13.15 + 1.00 * Z2 );
				IF( JCPS37 LT 40000. )THEN JCPS37 = 40000.;
			END;
*****
	FARM INCOME/LOSS
*****;
		IF( TC8_P GT 0 )THEN
			DO;
				CALL RANNOR( ISEED1 , Z1 );
				JCPS28 = EXP( 13. + 1.00 * Z1 );
				IF( JCPS28 LT 25000. )THEN JCPS28 = 25000.;
			END;
		IF( TC8_S GT 0 )THEN
			DO;
				CALL RANNOR( ISEED2 , Z2 );
				JCPS38 = EXP( 13. + 1.00 * Z2 );
				IF( JCPS38 LT 25000. )THEN JCPS38 = 25000.;
			END;

		*****
			WRAP-UP
		*****;
		WT = ORIGINAL_WT / NCOPIES;
		WAS = JCPS( 21 ) + JCPS( 31 );
		INTST = JCPS( 22 ) + JCPS( 32 );
		DBE = JCPS( 23 ) + JCPS( 33 );
		ALIMONY = JCPS( 24 ) + JCPS( 34 );
		BIL = JCPS( 25 ) + JCPS( 35 );
		PENSIONS = JCPS( 26 ) + JCPS( 36 );
		RENTS = JCPS( 27 ) + JCPS( 37 );
		FIL = JCPS( 28 ) + JCPS( 38 );
		OUTPUT;
	END;
END;
	ELSE
		OUTPUT;
DROP I;
RUN;
*****
	GROSS-UP CERTAIN INCOME AMOUNTS
*****;
DATA EXTRACT.PROD2015_V1B(COMPRESS=YES);
SET PROD2015;

IF( TC2_P = 0. )THEN JCPS22 = JCPS22 / .85;
IF( TC2_S = 0. )THEN JCPS32 = JCPS32 / .85;
INTST = JCPS22 + JCPS32;

IF( TC3_P = 0. )THEN JCPS23 = JCPS23 / .65;
IF( TC3_S = 0. )THEN JCPS33 = JCPS33 / .65;
DBE = JCPS23 + JCPS33;

IF( TC6_P = 0. )THEN JCPS26 = JCPS26 / .50;
IF( TC6_S = 0. )THEN JCPS36 = JCPS36 / .50;
PENSIONS = JCPS26 + JCPS36;
RUN;
PROC MEANS N SUMWGT MEAN MIN MAX SUM DATA=EXTRACT.PROD2015_V1B;
WHERE( (FILST = 1) );
WEIGHT WT;
VAR WAS INTST DBE ALIMONY BIL PENSIONS RENTS FIL;
TITLE "2015 PRODUCTION FILE - TOP CODING";
RUN;
