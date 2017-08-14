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
DATA EXTRACT.PROD2015_V1A(COMPRESS=YES);
SET EXTRACT.PROD2015_V1;
RETAIN ISEED1 21679 ISEED2 665533 ;
*****
	Adjust FILST Variable - Not Necessary Now
*****;
/*
IF( FILST EQ 0.) THEN
	DO;
		IF( WAS GT 0.0 )THEN
			DO;
				CALL RANUNI( ISEED1 , Z1 );
				IF( Z1 LE 0.9000 )THEN FILST = 1;
			END;
		ELSE
			DO;
				CALL RANUNI( ISEED2 , Z2 );
				IF( Z2 LE 0.6000 )THEN FILST = 1;
			END;
	END;
RUN;
*/
RUN;
PROC MEANS N SUMWGT MIN MAX SUM DATA=EXTRACT.PROD2015_V1A;
VAR FILST;
WEIGHT WT;
TITLE1 "Adjustment of Filing Status Variable to Match SOI Totals";
RUN;
