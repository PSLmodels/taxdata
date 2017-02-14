*OPTIONS PAGESIZE=84 LINESIZE=111; /* PORTRAIT  */
OPTIONS PAGESIZE=59 LINESIZE=160 CENTER ; /* LANDSCAPE */
/*
    =======================================

        American Enterprise Institute

        STATISTICAL MATCHING PROJECT

        March 2014 CPS  <-> 2009 Public Use File (Aged to 2013)




    Program SOIRETS: Create a Composite Extract
                     from the SOI 2009 PUBLIC
                     USE FILE.
    =======================================

*/

PROC FORMAT;
        VALUE JS 1 = 'Single Returns'
                 2 = 'Joint Returns'
                 3 = 'Head of Household' ;
        VALUE AGEP LOW  -  24 = 'Under 25'
                    25  -  34 = '25 lt 35'
                    35  -  44 = '35 lt 45'
                    45  -  54 = '45 lt 55'
                    55  -  64 = '55 lt 65'
                    65  - HIGH = '65 and Over' ;
        VALUE JY LOW        -       10000 =  'LESS THAN $10,000'
                 10000      -       20000 =  '$10,000 TO $20,000'
                 20000      -       30000 =  '$20,000 TO $30,000'
                 30000      -       40000 =  '$30,000 TO $40,000'
                 40000      -       50000 =  '$40,000 TO $50,000'
                 50000      -       75000 =  '$50,000 TO $75,000'
                 75000      -      100000 =  '$75,000 TO $100,000'
                100000      -      200000 =  '$100,000 TO $200,000'
                200000      -        HIGH =  '$200,000 AND OVER' ;
        VALUE AGEDE LOW -    0 = 'Non-Aged Return'
                      1 - HIGH = 'Aged Return' ;
        VALUE IFDEPT         0 = 'Non-Dependent Filer'
                             1 = 'Dependent Filer' ;
        VALUE DEPNE LOW -    0 = 'No Dependents'
                      1 - HIGH = 'With Dependents' ;

LIBNAME  EXTRACT 'C:\Users\anderson.frailey\Documents';

* Changed EXTRACT.SOIRETS to EXTRACT.SOIRETS2009;
DATA EXTRACT.SOIRETS2009(KEEP=JS AGEDEP1 AGEDEP2 AGEDEP3 PARENTS IFDEPT CAHE CAFHE OTHDEP DEPNE
                          AGEP AGES AGEDE WAS WASP WASS
                          INTST TEXINT DBE ALIMONY BIL PENSIONS
                          PTPEN SCHE FIL UCAGIX SSINC SSINCP SSINCS
                          SSAGIX TOTINCX AGIX TINCX RETURNS ZAGEPT
                          OLDEST YOUNGEST AGEPSQR XAGEDE XIFDEPT XDEPNE
                          INCOME RETID SEQUENCE SOISEQ WT FILER) ;
SET EXTRACT.PUF2009;
IF (RECID = 999999) THEN DELETE;
/*
ARRAY C(*) C1-C35 ;
ARRAY F(*) F1-F177 ;
*/
/*
        CREATE VARIABLES FROM INPUT FILE
*/
/*
        1.)     Filing Status
*/
FILER = 1 ;
DMFS = 1.0 ;
JS = 2;
IF( MARS = 1 )THEN JS = 1 ;
IF( (MARS = 4) )THEN JS = 3 ;
IF( (MARS = 3) OR (MARS = 6) )THEN DMFS = 0.5 ;
/*
        2.)     Return ID
*/
        RETID = RECID ;
		SEQUENCE = _N_ ;
		SOISEQ = _N_ ;
/*
        3.)     Exemptions
*/
CAHE = XOCAH;
CAFHE = XOCAWH;
OTHDEP = XOODEP;
IFDEPT = DSI ;
DEPNE = XOCAH + XOCAWH + XOODEP + XOPAR ;
AGEP = . ;
AGES = . ;
/* Add number of dependents under 13 from input file and parents */
/*CHILDREN = 0;
IF( AGEDP1 = 1 ) OR ( AGEDP1 = 2) THEN CHILDREN = CHILDREN + 1;
IF( AGEDP2 = 1 ) OR ( AGEDP2 = 2) THEN CHILDREN = CHILDREN + 1;
IF( AGEDP3 = 1 ) OR ( AGEDP3 = 3) THEN CHILDREN = CHILDREN + 1;
PARENTS = XOPAR ; */
AGEDEP1 = AGEDP1 ;
AGEDEP2 = AGEDP2 ;
AGEDEP3 = AGEDP3 ;
PARENTS = XOPAR ;
/*
      ---------------------
       CALCULATE AGED EXEMPTIONS

	   FOR THE 2009 PUF, USE THE AGE RANGE CODE
      ---------------------
*/
AGEX = 0 ;
IF( E02400 GT 0.0 )THEN AGEX = 1.;
AGEDE = AGEX ;
/*
        4.)     Income Items
*/
WAS = E00200 ;
WASP = . ;
WASS = . ;
INTST = E00300 ;
TEXINT = E00400 ;
DBE = E00600 ;
IF( E00800 = . )THEN E00800 = 0.0;
ALIMONY = E00800 ;
BIL = E00900 ;
PENSIONS = E01500 ;
PTPEN = E01700 ;
SCHE = E02000 ;
FIL = E02100 ;
UCAGIX = E02300 ;
SSINC = E02400 ;
SSINCP = . ;
SSINCS = . ;
SSAGIX = E02500 ;
AGIX = E00100 ;
TINCX = E04800 ;
RETURNS = 1.0 ;
OLDEST = . ;
YOUNGEST = . ;
AGEPSQR = . ;
IF( E03500 EQ . )THEN E03500 = 0.0;
ADJUST = E03150 + E03210 + E03220 + E03230
       + E03260 + E03270 + E03240 + E03290 + E03300 + E03400 + E03500 ;
TOTINCX = AGIX + ADJUST ;
XIFDEPT = IFDEPT ;
XDEPNE = DEPNE ;
XAGEDE = AGEDE ;
INCOME = TOTINCX ;
WT = S006 / 100. ;
*****
	ADJUST WEIGHT TO HIT 2013 TOTAL
*****;
WT = WT * 1.03 ;	/*	GO BACK AND CHECK THIS	*/
LABEL JS = 'Filing Status'
    AGEP = 'Age of Head'
 TOTINCX = 'Total Income'
  INCOME = 'Income Class'
   TINCX = 'Taxable Income'
  OLDEST = 'Age of Oldest Child'
YOUNGEST = 'Age of Youngest Child'
 XIFDEPT = 'Dependency Status'
  XDEPNE = 'Presence of Dependents'
  XAGEDE = 'Aged Status' ;
RUN;
/*
                Table 1a. - First Blocking Partitions: Filing Status, Age & Income
                                (Unweighted) - Filers Only
*/
PROC TABULATE DATA=EXTRACT.SOIRETS2009 FORMAT=COMMA12. ;
WEIGHT WT;
CLASS JS XAGEDE XIFDEPT XDEPNE ;
VAR RETURNS ;
FORMAT JS JS. XIFDEPT IFDEPT. XDEPNE DEPNE. XAGEDE AGEDE. ;
KEYLABEL SUM='AMOUNT' PCTSUM='PERCENT' ALL='Total, All Returns'
MEAN='AVERAGE' N='Unweighted' PCTN='PERCENT' SUMWGT='Weighted' ;
TABLE ( (XIFDEPT ALL)*(XAGEDE ALL) ) , RETURNS*( ((JS*XDEPNE ALL) )*(N)  )
/ PRINTMISS MISSTEXT='n.a.' ;
TITLE1 'S t a t i s t i c a l  M a t c h i n g  P r o j e c t' ;
TITLE3 'Preliminary File Alignment' ;
TITLE5 'Table 1a. - First Blocking Partition: Filing Status, Age & Dependency Status' ;
TITLE6 'Source: 2009 Individual Statistics of Income - Public Use File' ;
TITLE7 '(*** Unweighted ***)' ;
TITLE8 'Filers' ;
TITLE9 '------' ;
RUN;
/*
                Table 1b. - First Blocking Partitions: Filing Status, Age & Income
                                (Weighted) - Filers Only
*/
PROC TABULATE DATA=EXTRACT.SOIRETS2009 FORMAT=COMMA12. ;
WEIGHT WT;
CLASS JS XAGEDE XIFDEPT XDEPNE ;
VAR RETURNS ;
FORMAT JS JS. XIFDEPT IFDEPT. XDEPNE DEPNE. XAGEDE AGEDE. ;
KEYLABEL SUM='AMOUNT' PCTSUM='PERCENT' ALL='Total, All Returns'
MEAN='AVERAGE' N='Unweighted' PCTN='PERCENT' SUMWGT='Weighted' ;
TABLE ( (XIFDEPT ALL)*(XAGEDE ALL) ) , RETURNS*( ((JS*XDEPNE ALL) )*(SUMWGT)  )
/ PRINTMISS MISSTEXT='n.a.' ;
TITLE1 'S t a t i s t i c a l  M a t c h i n g  P r o j e c t' ;
TITLE3 'Preliminary File Alignment' ;
TITLE5 'Table 1b. - First Blocking Partition: Filing Status, Age & Dependency Status' ;
TITLE6 'Source: 2009 Individual Statistics of Income - Public Use File' ;
TITLE7 '(*** Weighted ***)' ;
TITLE8 'Filers' ;
TITLE9 '------' ;
RUN;
