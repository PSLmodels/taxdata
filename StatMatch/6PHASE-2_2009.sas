/*
    =======================================

			American Enterprise Institute

        STATISTICAL MATCHING PROJECT

    March 2014 CPS  <-> 2009 Public Use File (Aged to 2013)


	Program PHASE-2 :Perform the Match
                     and Evaluate the CPS
                     Variables.
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

libname EXTRACT 'C:\Users\anderson.frailey\Documents';

/*
        -------------
        MACRO SECTION
        -------------
*/
%MACRO FILLAX ;
                AX(NRECA , 1)  = YHAT ;
                AX(NRECA , 2)  = SOISEQ ;
                AX(NRECA , 3)  = WT;
%MEND  FILLAX ;

%MACRO FILLBX ;
                BX(NRECB , 1)  = YHAT ;
                BX(NRECB , 2)  = CPSSEQ ;
                BX(NRECB , 3)  = WT;
%MEND  FILLBX ;

/*
        --------------------------------------------------------
        CREATE WORKING FILES
        --------------------------------------------------------
*/
DATA SOIFILE(KEEP=CELLID YHAT SOISEQ WT) ;
SET EXTRACT.SOIRETS2009;
RUN;

DATA CPSFILE(KEEP=CELLID YHAT CPSSEQ WT) ;
SET EXTRACT.CPSRETS14;
RUN;


/*
        --------------------------------------------------------
        PREDICTIVE MEAN MATCHING ALGORITHM

        This program performs a constrained statistical match
        using the predictive mean matching algorithm for each
        of the partitions defined for the run. The main file
        that is processed is a file of COUNTS for each of the
        partitions. Records are read into arrays AX() and BX()
        to hold record for the SOI and CPS, respectively.
        --------------------------------------------------------
*/
/*
                ------------------------------------------------
                NOTE: Sort Order - CELLID, OWNER, ZHAT1
                ------------------------------------------------
*/
PROC SORT DATA=SOIFILE;BY CELLID YHAT;
RUN;
PROC SORT DATA=CPSFILE;BY CELLID YHAT;
RUN;

DATA EXTRACT.MATCH(KEEP=SOISEQ CPSSEQ CWEIGHT);
SET EXTRACT.COUNTS;
RETAIN PTRA PTRB;
ARRAY AX(40000 , 3) _temporary_ ;
ARRAY BX(40000 , 3) _temporary_ ;
/*
        ------------------------------
        INITIALIZE POINTERS & WEIGHT TOTALS
        ------------------------------
*/
IF (_N_ = 1)THEN
        DO;
                PTRA = 0.0 ;
                PTRB = 0.0 ;
        END;
WTA = 0.0 ;
WTB = 0.0 ;
/*
        ------------------------------
        FILL UP AX() & BX() ARRAYS

        NOTE: SOI IS HOST  (FILE A)
              CPS IS DONOR (FILE B)
        ------------------------------
*/
        DO NRECA = 1 TO SOICOUNT;
                PTRA = PTRA + 1;
                SET SOIFILE POINT=PTRA ;
                %FILLAX
                WTA = WTA + AX(NRECA , 3) ;
        END;

        DO NRECB = 1 TO CPSCOUNT;
                PTRB = PTRB + 1;
                SET CPSFILE POINT=PTRB ;
                %FILLBX
                WTB = WTB + BX(NRECB , 3) ;
        END;

/*
        ------------------------------
        SCALE RECORDS ON FILE B
        ------------------------------
*/
FACTOR = 1.0 ;
IF( WTB GT 0.0 )THEN FACTOR = WTA / WTB ;
ELSE
        DO;
                PUT '*** ERROR: EMPTY CELL' ;
                STOP;
        END;

        DO NB = 1 TO CPSCOUNT ;
                BX(NB , 3) = BX(NB , 3) * FACTOR ;
        END;
/*
        -------------------------------
        PERFORM THE MATCH
        -------------------------------
*/
EPSILON = 0.001 ;
BPTR = 1.;
BWT = BX(BPTR , 3) ;
DO NRECA = 1 TO SOICOUNT ;
        AWT = AX(NRECA , 3) ;
        DO WHILE ( AWT GT EPSILON ) ;
                CWT = MIN(AWT , BWT) ;
                SOISEQ = AX(NRECA , 2) ;
                CPSSEQ = BX(BPTR , 2) ;
                CWEIGHT  = CWT ;
                OUTPUT;
                AWT = MAX(0. , AWT - CWT) ;
                BWT = MAX(0. , BWT - CWT) ;
                /*
                        -------------------------
                        CHECK IF DONOR WEIGHT > 0.0
                        -------------------------
                */
                IF( BWT LE EPSILON )THEN
                        DO;
                                IF( BPTR LT CPSCOUNT )THEN
                                        DO;
                                                BPTR = BPTR + 1. ;
                                                BWT = BX(BPTR , 3) ;
                                        END;
                        END;
        END;
END;
RUN;
/*
        -------------
        MATCH SUMMARY
        -------------
*/
PROC MEANS DATA=EXTRACT.MATCH N SUM MIN MAX;
TITLE1 'Statistical Matching Project' ;
TITLE2 'Final Matched File' ;
TITLE3 'Host  is: 2009 SOI Public Use File' ;
TITLE4 'Donor is: March 2014 CPS' ;
RUN;
/*
        --------------------------------------
        EVALUATION PHASE - LINK FILES
        --------------------------------------
*/
DATA CPSFILE(KEEP=CPSSEQ Z1-Z50 P1-P50 WT);
SET EXTRACT.CPSRETS14;
ARRAY Z(*) Z1-Z50 ;
ARRAY P(*) P1-P50 ;
ARRAY ICPS(*) ICPS01-ICPS50;
DO I = 1 TO 50 ;
        Z(I) = ICPS(I) ;
END;
/*
        Positive Values
*/
DO I = 1 TO 50 ;
        P(I) = Z(I) ;
        IF( P(I) = 0.0 )THEN P(I) = . ;
END;
/*
        Labels
*/
LABEL
Z1  = 'Age of Tax Unit Head'
Z2  = 'Age of Tax Unit Spouse'
Z3  = 'Age of Dependent #1'
Z4  = 'Age of Dependent #2'
Z5  = 'Age of Dependent #3'
Z6  = 'Age of Dependent #4'
Z7  = 'Age of Dependent #5'
Z8  = 'Age of Youngest Child'
Z9  = 'Age of Oldest Child'
Z10 = 'HI: Covered (HEAD)'
Z11 = 'HI: Employer-Provided (HEAD)'
Z12 = 'HI: Employer Pays (HEAD)'
Z13 = 'HI: Covered (SPOUSE)'
Z14 = 'HI: Employer-Provided (SPOUSE)'
Z15 = 'HI: Employer Pays (SPOUSE)'
Z16 = 'Pension: Offered (HEAD)'
Z17 = 'Pension: Included (HEAD)'
Z18 = 'Pension: Offered (SPOUSE)'
Z19 = 'Pension: Included (SPOUSE)'
Z20 = 'Health Status (HEAD)'
Z21 = 'Health Status (SPOUSE)'
Z22 = 'Supplemental Security Income'
Z23 = 'Public Assistance (TANF)'
Z24 = 'Workmans Compensation'
Z25 = 'Veterans Benefits'
Z26 = 'Child Support'
Z27 = 'Disability Income'
Z28 = 'Social Security Income'
Z29 = 'Home Ownership (TENURE)'
Z30 = 'Wage Share (Lesser Earner)'
Z31 = 'Energy Assistance'
Z32 = 'Food Stamps'
Z33 = 'School Lunches'
Z34 = 'Medicare (Head)'
Z35 = 'Medicaid (Head)'
Z36 = 'Champus (Head)'
Z37 = 'Country of Origin (Head)'
Z38 = 'Medicare (Spouse)'
Z39 = 'Medicaid (Spouse)'
Z40 = 'Champus (Spouse)'
Z41 = 'Country of Origin (Spouse)'
P1  = 'Age of Tax Unit Head'
P2  = 'Age of Tax Unit Spouse'
P3  = 'Age of Dependent #1'
P4  = 'Age of Dependent #2'
P5  = 'Age of Dependent #3'
P6  = 'Age of Dependent #4'
P7  = 'Age of Dependent #5'
P8  = 'Age of Youngest Child'
P9  = 'Age of Oldest Child'
P10 = 'HI: Covered (HEAD)'
P11 = 'HI: Employer-Provided (HEAD)'
P12 = 'HI: Employer Pays (HEAD)'
P13 = 'HI: Covered (SPOUSE)'
P14 = 'HI: Employer-Provided (SPOUSE)'
P15 = 'HI: Employer Pays (SPOUSE)'
P16 = 'Pension: Offered (HEAD)'
P17 = 'Pension: Included (HEAD)'
P18 = 'Pension: Offered (SPOUSE)'
P19 = 'Pension: Included (SPOUSE)'
P20 = 'Health Status (HEAD)'
P21 = 'Health Status (SPOUSE)'
P22 = 'Supplemental Security Income'
P23 = 'Public Assistance (TANF)'
P24 = 'Workmans Compensation'
P25 = 'Veterans Benefits'
P26 = 'Child Support'
P27 = 'Disability Income'
P28 = 'Social Security Income'
P29 = 'Home Ownership (TENURE)'
P30 = 'Wage Share (Lesser Earner)'
P31 = 'Energy Assistance'
P32 = 'Food Stamps'
P33 = 'School Lunches'
P34 = 'Medicare (Head)'
P35 = 'Medicaid (Head)'
P36 = 'Champus (Head)'
P37 = 'Country of Origin (Head)'
P38 = 'Medicare (Spouse)'
P39 = 'Medicaid (Spouse)'
P40 = 'Champus (Spouse)'
P41 = 'Country of Origin (Spouse)'
;
RUN;
/*
        Prepare Files for Linking
*/
PROC SORT DATA=CPSFILE;BY CPSSEQ;
PROC SORT DATA=EXTRACT.MATCH;BY CPSSEQ;
/*
        Create Analysis File
*/
DATA ANALYSIS;
MERGE EXTRACT.MATCH(IN=M) CPSFILE(IN=D) ;
BY CPSSEQ;
IF(M);
RUN;
/*
                Table 1. - Match Summary (Matched File)
*/
PROC MEANS DATA=ANALYSIS VARDEF=WEIGHT N SUMWGT MEAN STD;
WEIGHT CWEIGHT;
VAR Z1-Z41 P1-P41 ;
TITLE1 'Statistical Matching Project' ;
TITLE2 'Evaluation Phase' ;
TITLE3 'Table 1. - Match Summary (Matched File - Host is SOI)' ;
TITLE4 '***** (Weighted) *****' ;
RUN;
/*
                Table 2. - Match Summary (Donor File)
*/
PROC MEANS DATA=CPSFILE VARDEF=WEIGHT N SUMWGT MEAN STD;
WEIGHT WT;
VAR Z1-Z41 P1-P41 ;
TITLE1 'Statistical Matching Project' ;
TITLE2 'Evaluation Phase' ;
TITLE3 'Table 2. - Match Summary (Donor File is CPS)' ;
TITLE4 '***** (Weighted) *****' ;
RUN;
