*OPTIONS PAGESIZE=84 LINESIZE=111; /* PORTRAIT  */
OPTIONS COMPRESS=YES PAGESIZE=59 LINESIZE=160 CENTER ; /* LANDSCAPE */
/*
    =============================================
		  American Enterprise Institute

        STATISTICAL MATCHING PROJECT

    March 2014 CPS  <-> 2009 Public Use File (Aged to 2013)



    Program AssembleFile :Put together the 
						  final Production File.

					NOTE:	FILERS ONLY
=================================================
*/

LIBNAME  EXTRACT  'C:\Users\anderson.frailey\Documents';


/*
        --------------------------------------
        CPS EXTRACT W/ ICPS() VARIABLES ONLY
        --------------------------------------
*/
DATA CPSFILE(KEEP=CPSSEQ ICPS01-ICPS09 JCPS1-JCPS100);
SET EXTRACT.CPSRETS14;
ARRAY ICPS(*) ICPS01-ICPS50;
ARRAY JCPS(*) JCPS1-JCPS100;
RUN;
/*
        PREPARE THE FILES FOR LINKING
*/
PROC SORT DATA=CPSFILE;BY CPSSEQ;
RUN;
PROC SORT DATA=EXTRACT.MATCH;BY CPSSEQ;
RUN;

/*
        CREATE THE ICPS() EXTRACT

		NOTE: FILE WILL CONTAIN
		      CPSSEQ
              SOISEQ
              CWEIGHT (NEW WEIGHT FROM THE MATCH)
              ICPS1-ICPS50 (CPS VARIABLES)
*/
DATA ICPS;
MERGE EXTRACT.MATCH(IN=M) CPSFILE(IN=D) ;
BY CPSSEQ;
IF(M);
RUN;

/*
                Table 1. - Match Summary (Matched File)
*/
PROC MEANS DATA=ICPS N MEAN STD MIN MAX;
TITLE1 'Statistical Matching Project' ;
TITLE2 'Evaluation Phase' ;
TITLE3 'Table 1. - Match Summary (Matched File - Host is SOI)' ;
TITLE4 '***** (Weighted) *****' ;
RUN;
/*
                Table 2. - Match Summary (Donor File)
*/
PROC MEANS DATA=CPSFILE N MEAN STD MIN MAX;
TITLE1 'Statistical Matching Project' ;
TITLE2 'Evaluation Phase' ;
TITLE3 'Table 2. - Match Summary (Donor File is CPS)' ;
TITLE4 '***** (Weighted) *****' ;
RUN;
/*
	==============================================
	2009 SOI PUBLIC USE FILE
	==============================================
*/
DATA SOI;
SET EXTRACT.PUF2009 ;
IF (RECID = 999999) THEN DELETE;
***
	FILER
***;
FILER = 1;
***
	WEIGHT
***;
WT = S006 / 100.;
/*
	SET THE SOI SEQUENCE NUMBER
*/
SOISEQ = _N_;
RUN;

/*
	==============================================
	CREATE THE NEW PRODUCTION FILE (FILERS ONLY)
	==============================================
*/
PROC SORT DATA=SOI;BY SOISEQ;
RUN;
PROC SORT DATA=ICPS;BY SOISEQ;
RUN;
DATA EXTRACT.PROD2009_V2;
MERGE ICPS(IN=INA) SOI(IN=INB);
BY SOISEQ;
IF( INA );
***
	NEW SEQUENCE NUMBER
***;
PRODSEQ = _N_ ;
***
	NEW WEIGHT
***;
MATCHWT = CWEIGHT ;
RUN;
PROC MEANS DATA=EXTRACT.PROD2009_V2 N MEAN MIN MAX SUM;
TITLE1 'S T A T I S T I C A L   M A T C H I N G   P R O J E C T';
TITLE2 '2009 SOI PUBLIC USE FILE: PRODUCTION VERSION 1';
TITLE4 'Summary Statistics';
RUN;
PROC EXPORT DATA=EXTRACT.PROD2009_V2
    OUTFILE = "C:\Users\anderson.frailey\Documents\Matching Project\CPSRETS.csv"
	DBMS = CSV
	REPLACE;
RUN;
