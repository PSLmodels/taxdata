*OPTIONS PAGESIZE=84 LINESIZE=111; /* PORTRAIT  */
OPTIONS COMPRESS=YES PAGESIZE=59 LINESIZE=160 CENTER ; /* LANDSCAPE */
/*
    =======================================
		 American Enterprise Institute

        STATISTICAL MATCHING PROJECT

    March 2014 CPS  <-> 2009 Public Use File (Aged to 2013)




    Program NonFilers:Converts NonFiler Tax Units
                      created from CPS-RETS 
                      into "SOI"-like records.
    =======================================
*/

LIBNAME EXTRACT   'C:\Users\anderson.frailey\Documents\';


DATA NONFILER;
SET  EXTRACT.CPSNONF2014;
*ARRAY C(*) C1-C42;
*ARRAY F(*) F1-F175;
ARRAY ICPS(*) ICPS01-ICPS50;
ARRAY JCPS(*) JCPS1-JCPS200;
***
	NONFILERS ONLY ON THIS FILE
***;
FILER = 0.;
SOISEQ = 0 ;
PRODSEQ = 0 ;
*****
	Taxpayer Exemptions
*****;
XFPT =0.;
XFST = 0.;
IF( IFDEPT = 0 )THEN
	DO;
		XFPT = 1.;
		IF( JS =2 )THEN XFST = 1.;
	END;
/* RENAME
    ICPS01='Age of Tax Unit Head'
	ICPS02='Age of Tax Unit Spouse'
	ICPS03='Age of Dependent #1'
	ICPS04='Age of Dependent #2'
	ICPS05='Age of Dependent #3'
	ICPS06='Age of Dependent #4'
	ICPS07='Age of Dependent #5'
	ICPS08='Age of Youngest Child'
	ICPS09='Age of Oldest Child'
; */
/*
	Set ICPS age variables
*/
DO I=1 TO 9;
    ICPS(I) = ICPS(I);
END;

/*
	1.)	SET THE C(*) ARRAY
*/
AGIR1	= 	0	;
DSI  	=   IFDEPT;
EFI  	=	0	;
EIC	    =   0	;
ELECT	=	0	;
FDED	=	0   ;
FLPDYR	=	2009;
FLPDMO	=	12	;
F2441	=   0	;
F3800	=   0	;
F6251	=	0	;
F8582	=	0	;
F8606	=	0	;
F8829	=	0	;
F8910	=	0	;
IE	    =	0	;
MARS	=   JS	;IF( MARS = 3 )THEN MARS = 4;	/*	HH has CODE = 4 FOR MARS	*/
MIDR	=	0	;
N20	    =	0	;
N24	    =	0	;
N25	    =   0	;
N30	    =	0	;
PREP	=	0	;
SCHB    =   0   ;
SCHCF	=	0	;
SCHE	=   0   ;
TFORM	=	0	;
TXST	=	0	;
XFPT    =   XFPT   ;
XFST    =   XFST   ;
XOCAH   =   XXOCAH ;
XOCAWH  =   XXOCAWH;
XOODEP  =   XXOODEP;
XOPAR   =   XXOPAR ;
XTOT    =   XFPT + XFST + XOCAH + XOCAWH + XOODEP + XOPAR   ;

/*
	2.)	SET THE F(*) ARRAY
*/
E00200 = WAS;
E00300 = INTST;
E00400 = 0;
E00600 = DBE;
E00650 = 0;
E00700 = ALIMONY;
E00800 = BIL;
E00900 = 0;
E01000 = 0;
E01100 = 0;
E01200 = 0;
E01400 = 0;
E01500 = 0;
E01700 = PENSIONS;
E02000 = RENTS;
E02100 = FIL;
E02300 = UCOMP;
E02400 = SOCSEC;
E03150 = 0;
E03210 = 0;
E03220 = 0;
E03230 = 0;
E03260 = 0;
E03270 = 0;
E03240 = 0;
E03290 = 0;
E03300 = 0;
E03400 = 0;
E03500 = 0;
E00100 = 0;
P04470 = 0;
E04250 = 0;
E04600 = 0;
E04800 = 0;
E05100 = 0;
E05200 = 0;
E05800 = 0;
E06000 = 0;
E06200 = 0;
E06300 = 0;
E09600 = 0;
E07180 = 0;
E07200 = 0;
E07220 = 0;
E07220 = 0;
E07230 = 0;
E07140 = 0;
E07260 = 0;
E07300 = 0;
E07400 = 0;
E07600 = 0;
P08000 = 0;
E07150 = 0;
E06500 = 0;
E08800 = 0;
E09400 = 0;
E09700 = 0;
E09800 = 0;
E09900 = 0;
E10300 = 0;
E10700 = 0;
E10900 = 0;
E10950 = 0;
E10960 = 0;
E59560 = 0;
E59680 = 0;
E59700 = 0;
E11550 = 0;
E11070 = 0;
E11100 = 0;
E11200 = 0;
E11300 = 0;
E11400 = 0;
E11570 = 0;
E11580 = 0;
E11582 = 0;
E11583 = 0;
E10605 = 0;
E11900 = 0;
E12000 = 0;
E12200 = 0;
E15100 = 0;
E15210 = 0;
E15250 = 0;
E15360 = 0;
E17500 = 0;
E18400 = 0;
E18500 = 0;
E18600 = 0;
E19200 = 0;
E19550 = 0;
E19800 = 0;
E20100 = 0;
E19700 = 0;
E20550 = 0;
E20600 = 0;
E20400 = 0;
E20800 = 0;
E20500 = 0;
E21040 = 0;
P22250 = 0;
E22320 = 0;
E22370 = 0;
P23250 = 0;
E24515 = 0;
E24516 = 0;
E24518 = 0;
E24560 = 0;
E24598 = 0;
E24615 = 0;
E24570 = 0;
P25350 = 0;
P25380 = 0;
P25470 = 0;
P25700 = 0;
E25820 = 0;
E25850 = 0;
E25860 = 0;
E25940 = 0;
E25980 = 0;
E25920 = 0;
E25960 = 0;
E26110 = 0;
E26170 = 0;
E26190 = 0;
E26160 = 0;
E26180 = 0;
E26270 = 0;
E26100 = 0;
E26390 = 0;
E26400 = 0;
E27200 = 0;
E30400 = 0;
E30500 = 0;
E32800 = 0;
E33000 = 0;
E53240 = 0;
E53280 = 0;
E53410 = 0;
E53300 = 0;
E53317 = 0;
E53458 = 0;
E58950 = 0;
E58990 = 0;
P60100 = 0;
P61850 = 0;
E60000 = 0;
E62100 = 0;
E62900 = 0;
E62720 = 0;
E62730 = 0;
E62740 = 0;
P65300 = 0;
P65400 = 0;
E68000 = 0;
E82200 = 0;
T27800 = 0;
S27860 = 0;
P27895 = 0;
P87482 = 0;
P87521 = 0;
E87530 = 0;
E87550 = 0;
P86421 = 0;
E52852 = 0;
E52872 = 0;
E87870 = 0;
E87875 = 0;
E87880 = 0;
RECID = 0;
S006 = WT;
S008 = 0;
S009 = 0;
WSAMP = 0;
TXRT = 0;


***
	WEIGHT
***;
MATCHWT = WT;
RUN;
PROC PRINT DATA=NONFILER (OBS=15);
RUN;
PROC MEANS DATA=NONFILER N MIN MAX MEAN SUM ;
TITLE1 'S t a t i s t i c a l  M a t c h i n g  P r o j e c t' ;
TITLE5 'Table 1. - CPS Tax Units' ;
TITLE6 'Source: March 2014 Current Population Survey' ;
TITLE7 '(*** Unweighted ***)' ;
TITLE8 'Non-Filers' ;
TITLE9 '----------' ;
RUN;
**************************************************************************************;
*****                        CREATE FINAL VERSION OF PRODUCTION FILE             *****;
**************************************************************************************;
DATA EXTRACT.PROD2009_V2;
SET EXTRACT.PROD2009_V2 NONFILER;
DROP ICPS10-ICPS50;
***
	FINAL SEQUENCE NUMBER
***;
FINALSEQ = _N_;
RUN;
PROC EXPORT DATA = EXTRACT.PROD2009_V2
	OUTFILE = "C:\Users\anderson.frailey\Documents\Matching Project\PROD2009_V2.CSV"
	DBMS = CSV
	REPLACE;
RUN;
