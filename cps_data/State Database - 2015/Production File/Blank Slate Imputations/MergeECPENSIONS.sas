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
/*
PROC CONTENTS DATA=EXTRACT.ECPENSIONS;
RUN;
*/
*****
	PROCESS THE PRODUCTION FILE
	THIS PROGRAM READS IN THE BLANK SLATE IMPUTATIONS CREATED IN THE PRIOR STEP
	NOTE THE NAME CHANGE
*****;
***
	CREATE A COPY AND REMOVE THE BLANK SLATE VARIABLES
***;
DATA PROD2015(COMPRESS=YES);
SET EXTRACT.PROD2015_V1D;
DROP BUILDUP_LIFE BUILDUP_PENS_DB BUILDUP_PENS_DC GAINS_ON_HOME_SALE
     STEPUPINBASIS TEXINT ESHI_TAXPAYER ESHI_SPOUSE EDUCATIONAL_EXPENSE RENT_PAID;
RUN;
***
	CREATE FINAL FILE WITH MERGE STATEMENT
	NOTE NAME CHANGE
***;
DATA EXTRACT.PROD2015_V2E(COMPRESS=YES);
MERGE PROD2015 EXTRACT.ECPENSIONS;
RUN;
