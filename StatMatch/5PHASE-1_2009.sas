*OPTIONS PAGESIZE=84 LINESIZE=111; /* PORTRAIT  */
OPTIONS PAGESIZE=59 LINESIZE=160 CENTER ; /* LANDSCAPE */
/*
    =======================================
         American Enterprise Institute

        STATISTICAL MATCHING PROJECT

    March 2014 CPS  <-> 2009 Public Use File (Aged to 2013)



    Program PHASE-1 :File Partitioning and
                     and Predictive Mean
                     Estimation.
    =======================================
*/

PROC FORMAT;
        VALUE IJS 1 = 'Single Returns'
                  2 = 'Joint Returns'
                  3 = 'Head of Household' ;
        VALUE IAGEDE 1 = 'Non-Aged Return'
                     2 = 'Aged Return' ;
        VALUE IDEPT 1 = 'Non-Dependent Filer'
                    2 = 'Dependent Filer' ;
        VALUE IDEPNE 0 = 'No Dependents'
                     1 = '1 Dependent'
                     2 = '2 Dependents'
                     3 = '3 Dependents'
                     4 = '4 Dependents'
                     5 = '5+ Dependents' ;
        VALUE FILST          0 = 'Non-Filers'
                             1 = 'Filers' ;
        VALUE IKIDS 1 = 'One Dependent '
                    2 = 'Two Dependents'
                    3 = 'Three or More Dependents' ;
        VALUE ISELF 1 = 'Only Wage Income (or no earnings)'
                    2 = 'Only Self-Employment Income'
                    3 = 'Both Wage and Self-Employment' ;
RUN;

LIBNAME EXTRACT 'C:\Users\anderson.frailey\Documents';

/*
        Create CPSFILE

*/
RUN;
DATA CPSFILE;
SET EXTRACT.CPSRETS14;
/*
        ----------------------------------------------------
        BEGIN PARTITIONING PHASE
        ----------------------------------------------------
*/
IDEPT = 9 ;
IJS   = 9 ;
IAGEDE= 9 ;
IDEPNE= 9 ;
IKIDS = 9 ;
ISELF = 9 ;
/*
        ---------------------
        SELF-EMPLOYMENT
        ---------------------
*/
SELFEMPL = 1.;
WAGEFLAG = 0.;IF( WAS NE 0. )THEN WAGEFLAG = 1.;
SELFFLAG = 0.;IF( (BIL + FIL) NE 0. )THEN SELFFLAG = 1.;
IF( (WAGEFLAG = 1) AND (SELFFLAG = 0) )THEN SELFEMPL = 1.;
IF( (WAGEFLAG = 0) AND (SELFFLAG = 1) )THEN SELFEMPL = 2.;
IF( (WAGEFLAG = 1) AND (SELFFLAG = 1) )THEN SELFEMPL = 3.;
/*
        ---------------------
        POPULATION CHECK
        ---------------------
*/
PEOPLE = 1.;
IF( JS = 2 )THEN PEOPLE = 2.;
PEOPLE = PEOPLE + DEPNE ;
IF( IFDEPT = 1 )THEN PEOPLE = . ;
/*
        ----------------------------
        (1)     DEPENDENT FILERS
        ----------------------------
*/
IDEPT  = 1. ;IF( IFDEPT = 1 )THEN IDEPT = 2.;
/*
        ----------------------------
        (2)     NON-DEPENDENT FILERS
        ----------------------------
*/
IF( IDEPT = 1. )THEN
        DO;
                IJS    = JS ;
                IAGEDE = 1. ;IF( AGEDE GT 0 )THEN IAGEDE = 2.;
                IF( AGEDE = 0 )THEN
                        DO;
                                IF( JS NE 2 )THEN
                                        IDEPNE = MIN(DEPNE , 3) ;
                                ELSE
                                        IDEPNE = MIN(DEPNE , 5) ;
                        END;
        END;
/*
        -----------------------------
        (3)     Independent Variables
        -----------------------------
*/
SCHE = RENTS;
UCAGIX = UCOMP ;
SSINC = SOCSEC ;
TEXINT = 0.0;
TPI = WAS + INTST + TEXINT + DBE + MAX(0., SCHE) + MAX(0., BIL)
    + MAX(0., FIL) + SSINC + PENSIONS + ALIMONY + UCAGIX ;
WAGESHR = 0.0 ;
CAPSHR = 0.0 ;
IF( TPI NE 0.0 )THEN
        DO;
                WAGESHR = WAS / TPI ;
                CAPSHR  = (INTST + TEXINT + DBE) / TPI ;
        END;
RUN;
/*
        Create SOIFILE
*/
DATA SOIFILE;
SET EXTRACT.SOIRETS2009;
/*
        ----------------------------------------------------
        BEGIN PARTITIONING PHASE
        ----------------------------------------------------
*/
IDEPT = 9 ;
IJS   = 9 ;
IAGEDE= 9 ;
IDEPNE= 9 ;
IKIDS = 9 ;
ISELF = 9 ;
/*
        ---------------------
        SELF-EMPLOYMENT
        ---------------------
*/
SELFEMPL = 1.;
WAGEFLAG = 0.;IF( WAS NE 0. )THEN WAGEFLAG = 1.;
SELFFLAG = 0.;IF( (BIL + FIL) NE 0. )THEN SELFFLAG = 1.;
IF( (WAGEFLAG = 1) AND (SELFFLAG = 0) )THEN SELFEMPL = 1.;
IF( (WAGEFLAG = 0) AND (SELFFLAG = 1) )THEN SELFEMPL = 2.;
IF( (WAGEFLAG = 1) AND (SELFFLAG = 1) )THEN SELFEMPL = 3.;
/*
        ---------------------
        POPULATION CHECK
        ---------------------
*/
PEOPLE = 1.;
IF( JS = 2 )THEN PEOPLE = 2.;
PEOPLE = PEOPLE + DEPNE ;
IF( IFDEPT = 1 )THEN PEOPLE = . ;
/*
        ----------------------------
        (1)     DEPENDENT FILERS
        ----------------------------
*/
IDEPT  = 1. ;IF( IFDEPT = 1 )THEN IDEPT = 2.;
/*
        ----------------------------
        (2)     NON-DEPENDENT FILERS
        ----------------------------
*/
IF( IDEPT = 1. )THEN
        DO;
                IJS    = JS ;
                IAGEDE = 1. ;IF( AGEDE GT 0 )THEN IAGEDE = 2.;
                IF( AGEDE = 0 )THEN
                        DO;
                                IF( JS NE 2 )THEN
                                        IDEPNE = MIN(DEPNE , 3)  ;
                                ELSE
                                        IDEPNE = MIN(DEPNE , 5)  ;
                        END;
        END;
*****
		In the 2008 PUF, there are 481 Head of Household records that report
		no dependents. We'll give them one dependent.
*****;
IF( ( JS = 3 ) AND ( IDEPNE = 0 ) )THEN IDEPNE = 1; 
/*
        -----------------------------
        (3)     Independent Variables
        -----------------------------
*/
TPI = WAS + INTST + TEXINT + DBE + MAX(0., SCHE) + MAX(0., BIL)
    + MAX(0., FIL) + SSINC + PENSIONS + ALIMONY + UCAGIX ;
WAGESHR = 0.0 ;
CAPSHR = 0.0 ;
IF( TPI NE 0.0 )THEN
        DO;
                WAGESHR = WAS / TPI ;
                CAPSHR  = (INTST + TEXINT + DBE) / TPI ;
        END;
RUN;
/*
        ----------------------
        DATA FILE SUMMARY
        ----------------------
*/
PROC MEANS DATA=SOIFILE N SUM SUMWGT;
WEIGHT WT;
VAR PEOPLE;
Title1 'Statistical Matching Project' ;
Title2 'Partitioning & Predictive Mean Estimation' ;
Title3 'Population Count - SOI' ;
RUN;
PROC MEANS DATA=CPSFILE N SUM SUMWGT;
WEIGHT WT;
VAR PEOPLE;
Title1 'Statistical Matching Project' ;
Title2 'Partitioning & Predictive Mean Estimation' ;
Title3 'Population Count - CPS' ;
RUN;

/*
        SORT BOTH FILES
*/
PROC SORT DATA=CPSFILE;BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
PROC SORT DATA=SOIFILE;BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
/*
        ----------------------
        FILE SUMMARY - UNWEIGHTED
        ----------------------
*/
PROC FREQ DATA=SOIFILE;
TABLES IDEPT*IJS*IAGEDE*IDEPNE*IKIDS*ISELF /OUT=SOICOUNT NOPRINT SPARSE;
FORMAT IDEPT IDEPT. IJS IJS. IAGEDE IAGEDE. IDEPNE IDEPNE.
IKIDS IKIDS. ISELF ISELF.;
Title1 'Statistical Matching Project' ;
Title2 'Partitioning & Predictive Mean Estimation' ;
Title3 'Host File is SOI' ;
RUN;
PROC FREQ DATA=CPSFILE;
TABLES IDEPT*IJS*IAGEDE*IDEPNE*IKIDS*ISELF /OUT=CPSCOUNT NOPRINT SPARSE;
FORMAT IDEPT IDEPT. IJS IJS. IAGEDE IAGEDE. IDEPNE IDEPNE.
IKIDS IKIDS. ISELF ISELF. ;
Title1 'Statistical Matching Project' ;
Title2 'Partitioning & Predictive Mean Estimation' ;
Title3 'Donor File is CPS' ;
RUN;
/*
        ----------------------
        FILE SUMMARY - WEIGHTED
        ----------------------
*/
PROC FREQ DATA=SOIFILE;
WEIGHT WT;
TABLES IDEPT*IJS*IAGEDE*IDEPNE*IKIDS*ISELF /OUT=SOIWGT NOPRINT SPARSE;
FORMAT IDEPT IDEPT. IJS IJS. IAGEDE IAGEDE. IDEPNE IDEPNE.
IKIDS IKIDS. ISELF ISELF.;
Title1 'Statistical Matching Project' ;
Title2 'Partitioning & Predictive Mean Estimation' ;
Title3 'Host File is SOI' ;
RUN;
PROC FREQ DATA=CPSFILE;
WEIGHT WT;
TABLES IDEPT*IJS*IAGEDE*IDEPNE*IKIDS*ISELF /OUT=CPSWGT NOPRINT SPARSE;
FORMAT IDEPT IDEPT. IJS IJS. IAGEDE IAGEDE. IDEPNE IDEPNE.
IKIDS IKIDS. ISELF ISELF. ;
Title1 'Statistical Matching Project' ;
Title2 'Partitioning & Predictive Mean Estimation' ;
Title3 'Donor File is CPS' ;
RUN;
/*
        ----------------------
        MERGE THE FREQUENCIES
        ----------------------
*/
PROC SORT DATA=SOICOUNT;BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
PROC SORT DATA=CPSCOUNT;BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
PROC SORT DATA=SOIWGT;BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
PROC SORT DATA=CPSWGT;BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
DATA EXTRACT.COUNTS;
MERGE SOICOUNT(RENAME=(COUNT=SOICOUNT))
      CPSCOUNT(RENAME=(COUNT=CPSCOUNT))
      SOIWGT(RENAME=(COUNT=SOIWGT))
      CPSWGT(RENAME=(COUNT=CPSWGT)) ;
BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
IF( (SOICOUNT GT 0.0) AND (CPSCOUNT GT 0.0) );
FACTOR = 0.0 ;
IF( CPSWGT GT 0.0 )THEN FACTOR = SOIWGT / CPSWGT ;
DROP PERCENT;
RUN;
/*
                -----------------------
                ATTACH CELLID TO COUNTS
                -----------------------
*/
DATA EXTRACT.COUNTS;
SET EXTRACT.COUNTS;
CELLID = _N_;
RUN;
PROC PRINT DATA=EXTRACT.COUNTS;
Title1 'Statistical Matching Project' ;
Title2 'Partitioning & Predictive Mean Estimation' ;
Title3 'Donor File is CPS' ;
Title4 'First Partitioning Scheme' ;
RUN;
/*
        ----------------------
        PREDICTION
        ----------------------
*/
PROC REG DATA = SOIFILE OUTEST=EXTRACT.BETA;
WEIGHT WT;
BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
MODEL TINCX = AGEDE WAS INTST DBE
              BIL FIL SCHE PENSIONS SSINC UCAGIX
              ALIMONY WAGESHR CAPSHR
              WAGEFLAG SELFFLAG ;
TITLE1 'Statistical Matching Project' ;
TITLE2 'Predictive Mean Matching - Estimation' ;
TITLE3 '2009 Statistics of Income - Public Use File' ;
QUIT;
RUN;
/*
        ----------------------
        PRINT RESULTS
        ----------------------
*/
PROC PRINT DATA=EXTRACT.BETA;
TITLE1 'Statistical Matching Project' ;
TITLE2 'Predictive Mean Matching - Estimation' ;
TITLE3 '2009 Statistics of Income - Public Use File' ;
RUN;
/*
        ----------------------
        COEFFICIENT FILE
        ----------------------
*/
DATA BETA(KEEP=B00 B01 B02 B03 B04 B05
               B06 B07 B08 B09 B10 B11
               B12 B13 B14 B15
               IDEPT IJS IAGEDE IDEPNE IKIDS ISELF) ;
SET EXTRACT.BETA;
B00 = INTERCEPT ;
B01 = AGEDE ;
B02 = WAS ;
B03 = INTST ;
B04 = DBE ;
B05 = BIL ;
B06 = FIL ;
B07 = SCHE ;
B08 = PENSIONS ;
B09 = SSINC ;
B10 = UCAGIX ;
B11 = ALIMONY ;
B12 = WAGESHR ;
B13 = CAPSHR ;
B14 = WAGEFLAG ;
B15 = SELFFLAG ;
RUN;


PROC SORT DATA=BETA;BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
PROC SORT DATA=EXTRACT.COUNTS;BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
/*
        ----------------------
        MERGE
        ----------------------
*/
DATA SOIFILE(KEEP=SOISEQ YHAT CELLID);
MERGE SOIFILE BETA EXTRACT.COUNTS;
BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
/*
        ----------------------
        Predicted Mean
        ----------------------
*/
YHAT    = B00
        + B01 * AGEDE
        + B02 * WAS
        + B03 * INTST
        + B04 * DBE
        + B05 * BIL
        + B06 * FIL
        + B07 * SCHE
        + B08 * PENSIONS
        + B09 * SSINC
        + B10 * UCAGIX
        + B11 * ALIMONY
        + B12 * WAGESHR
        + B13 * CAPSHR
        + B14 * WAGEFLAG
        + B15 * SELFFLAG ;

LABEL YHAT = 'Predicted Value (TINCX)' ;
RUN;
DATA CPSFILE(KEEP=CPSSEQ YHAT CELLID);
MERGE CPSFILE BETA EXTRACT.COUNTS;
BY IDEPT IJS IAGEDE IDEPNE IKIDS ISELF;
/*
        ----------------------
        Predicted Mean
        ----------------------
*/
YHAT    = B00
        + B01 * AGEDE
        + B02 * WAS
        + B03 * INTST
        + B04 * DBE
        + B05 * BIL
        + B06 * FIL
        + B07 * SCHE
        + B08 * PENSIONS
        + B09 * SSINC
        + B10 * UCAGIX
        + B11 * ALIMONY
        + B12 * WAGESHR
        + B13 * CAPSHR
        + B14 * WAGEFLAG
        + B15 * SELFFLAG ;

LABEL YHAT = 'Predicted Value (TINCX)' ;
RUN;
/*
        --------------------------------------------
        MERGE Predicted Value & CELLID
                Back to Original Files
        --------------------------------------------
*/
PROC SORT DATA=EXTRACT.CPSRETS14;BY CPSSEQ;
PROC SORT DATA=CPSFILE;BY CPSSEQ;
PROC SORT DATA=EXTRACT.SOIRETS2009;BY SOISEQ;
PROC SORT DATA=SOIFILE;BY SOISEQ;
/*
        CPSFILE
*/
DATA EXTRACT.CPSRETS14;
MERGE EXTRACT.CPSRETS14 CPSFILE;
BY CPSSEQ;
RUN;
/*
        SOIFILE
*/


DATA EXTRACT.SOIRETS2009;
MERGE EXTRACT.SOIRETS2009 SOIFILE;
BY SOISEQ;
RUN;

/*
        ----------------------
        DATA FILE SUMMARY
        ----------------------
*/

PROC MEANS DATA=EXTRACT.SOIRETS2009 N SUM SUMWGT;
WEIGHT WT;
Title1 'Statistical Matching Project' ;
Title2 'Partitioning & Predictive Mean Estimation' ;
Title3 '2009 SOI Public Use File Extract' ;
RUN;
PROC MEANS DATA=EXTRACT.CPSRETS14 N SUM SUMWGT;
WEIGHT WT;
Title1 'Statistical Matching Project' ;
Title2 'Partitioning & Predictive Mean Estimation' ;
Title3 'March 2014 CPS Tax Unit Extract: FILERS Only' ;
RUN;
