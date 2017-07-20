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
DATA EXTRACT.PROD2015_V4E;
MERGE EXTRACT.PROD2015_V3E EXTRACT.SLTX_IMPUTE;
BY SEQUENCE;
RUN;

PROC CONTENTS DATA=EXTRACT.PROD2015_V2E;
TITLE1 "Final Production File - 2015";
RUN;
*****
	CLEAN UP THE FILE
*****;
DATA EXTRACT.PROD2015_V3E(COMPRESS=YES);
SET EXTRACT.PROD2015_V2E;
DROP
BETA1-BETA288
I
Equation_Number
ISEED1 ISEED2 JNJ
JSEED1 JSEED2 LAMBDA
LNDBE LNINCOME LNINTST LNPENSIONS LNVALUE
MARRIED NCOPIES NV NAME PROB RATIO SIGMA
TC1_P TC2_P TC3_P TC4_P TC5_P TC6_P TC7_P TC8_P
TC1_S TC2_S TC3_S TC4_S TC5_S TC6_S TC7_S TC8_S TC_ALL
XB XVAR1-XVAR8 Z1 Z2
;
RUN;
PROC EXPORT DATA = EXTRACT.PROD2015_V4E
OUTFILE = "C:\Users\anderson.frailey\My Documents\State Database - 2015\Production File\Extracts\cps_raw.csv"
DBMS = CSV
REPLACE;
RUN;
