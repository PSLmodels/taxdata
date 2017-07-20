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
LIBNAME EXTRACT "C:\Users\anderson.frailey\Documents\State Database - 2015\CPS Tax Units\2015\EXTRACTS\";
*****
	PROCESS THE PRODUCTION FILE

	NOTE: WE USE A TEMPORARY DATA SET FIRST UNTIL
	 	  THE SOI CONTROL TOTAL IS REACHED.
	17-SEP-2015
*****;
DATA EXTRACT.CPSRETS2015(COMPRESS=YES);
SET EXTRACT.CPSRETS2015;
RETAIN ISEED1 21679 ISEED2 665533 ;
*****
	Adjust FILST Variable
*****;
IF( FILST EQ 0.) THEN
	DO;
		IF( WAS GT 0.0 )THEN
			DO;
				CALL RANUNI( ISEED1 , Z1 );
				IF( Z1 LE 0.8400 )THEN FILST = 1;
			END;
		ELSE
			DO;
				CALL RANUNI( ISEED2 , Z2 );
				IF( Z2 LE 0.5400 )THEN FILST = 1;
			END;
	END;
RUN;
PROC MEANS N SUMWGT MIN MAX SUM DATA=EXTRACT.CPSRETS2015;
VAR FILST;
WEIGHT WT;
TITLE1 "Adjustment of Filing Status Variable to Match SOI Totals";
RUN;
/*
*****
	CREATE FILER AND NON-FILER EXTRACTS
*****;
DATA EXTRACT.CPSRETS;
SET EXTRACT.CPSRETS2015;
IF( FILST EQ 1 );
RUN;
DATA EXTRACT.CPSNONF;
SET EXTRACT.CPSRETS2015;
IF( FILST EQ 0 );
RUN;
*/
