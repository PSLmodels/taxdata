*******************************************************************************************;
***                                                                                     ***;
***                                                                                     ***;
***                          State Modeling Project                                     ***;
***                                                                                     ***;
***                                                                                     ***;
*******************************************************************************************;
***                                                                                     ***;
***	Program:		CreateProductionFile2015.SAS                                        ***;
***                                                                                     ***;
***	Type:			SAS Program                                                         ***;
***                                                                                     ***;
*** Function:		This program combines CPS Tax Units from the three most recently    ***;
***					available CPS years. In this version, we use CPS years from the     ***;
***                 March 2013, 2014 and 2015 extracts. The program creates tax units   ***;
***					from the CPS that will be used to create state-level summary        ***;
***                 statistics for the filing and non-filing population.                ***;
***                                                                                     ***;
***                 The basic logic of the program is as follows:                       ***;
***                                                                                     ***;
***                 * For each household on the CPS extract, determine how many tax     ***;
***                   filing units there are likely to be in the household (each        ***;
***                   household is assmed to have at least one tax-filing unit).        ***;
***                 * Construct a person-level array that stores income and demographic ***;
***                   information for each member of the household.                     ***;
***                 * Construct a tax unit array of tax variables for every potential   ***;
***                   tax unit in the household.                                        ***;
***                 * Determine which members of the household are dependents of other  ***;
***                   household members and add their information to that tax unit.     ***:
***                 * Repeat this process for each household member until all members   ***;
***                   of the household are represented in a tax unit record. A house-   ***;
***                   hold member can only be represented on one tax unit record.       ***;
***                 * After all CPS tax units have been constructed, determine if the   ***; 
***                   unit is required to actually file a tax return as determined by   ***;
***                   filing threshholds in place for that tax year.                    ***;
***                 * Repeat this process for every household in the CPS until a SAS    ***;
***                   dataset is created representing all tax units for that year.      ***;
***                 * Tabulate weighted and unweighted record counts by filing type.    ***;
***                                                                                     ***;
***	Input:      	CPS person-level extract from the raw CPS file for a particular     ***;
***                 year.                                                               ***; 
***                                                                                     ***;
***	Output:			SAS dataset containing CPS tax units. This dataset will form the    ***;
***                 basis of an aggregate summary, by state and filer type that is      ***;
***                 suitable for use in an aggregate econometric analysis.              ***;
***                                                                                     ***;
***	Author:			John F. O'Hare                                                      ***;
***                                                                                     ***;
***	History:		Program begun on 08-AUG-2016.                                       ***;
***                                                                                     ***;
***                                                                                     ***; 
*******************************************************************************************;
*OPTIONS PAGESIZE=84 LINESIZE=111; /* PORTRAIT  */
OPTIONS PAGESIZE=59 LINESIZE=160 CENTER ; /* LANDSCAPE */
*****
	PRODUCTION FILE
*****;
LIBNAME EXTRACT "C:\Users\anderson.frailey\Documents\State Database - 2015\Production File\EXTRACTS\";
*****
	COMPONENT CPS FILES: NOTE THAT WE ARE IDENTIFYING FILES BY THEIR CPS YEAR
*****;
LIBNAME YR2015 "C:\Users\anderson.frailey\Documents\State Database - 2015\CPS Tax Units\2015\EXTRACTS\";
LIBNAME YR2014 "C:\Users\anderson.frailey\Documents\State Database - 2015\CPS Tax Units\2014\EXTRACTS\";
LIBNAME YR2013 "C:\Users\anderson.frailey\Documents\State Database - 2015\CPS Tax Units\2013\EXTRACTS\";
*****
	FORMATS
*****;
PROC FORMAT;
        VALUE JS 1 = 'Single Returns'
                 2 = 'Joint Returns'
                 3 = 'Head of Household' ;
        VALUE AGEH LOW  -  24 = 'Under 25'
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
        VALUE FILST          0 = 'Non-Filers'
                             1 = 'Filers' ;
VALUE gestfips	(default=32)
	1         =  "Alabama"                       
	2         =  "Alaska"                        
	4         =  "Arizona"                       
	5         =  "Arkansas"                      
	6         =  "California"                    
	8         =  "Colorado"                      
	9         =  "Connecticut"                   
	10        =  "Delaware"                      
	11        =  "District of Columbia"          
	12        =  "Florida"                       
	13        =  "Georgia"                       
	15        =  "Hawaii"                        
	16        =  "Idaho"                         
	17        =  "Illinois"                      
	18        =  "Indiana"                       
	19        =  "Iowa"                          
	20        =  "Kansas"                        
	21        =  "Kentucky"                      
	22        =  "Louisiana"                     
	23        =  "Maine"                         
	24        =  "Maryland"                      
	25        =  "Massachusetts"                 
	26        =  "Michigan"                      
	27        =  "Minnesota"                     
	28        =  "Mississippi"                   
	29        =  "Missouri"                      
	30        =  "Montana"                       
	31        =  "Nebraska"                      
	32        =  "Nevada"                        
	33        =  "New Hampshire"                 
	34        =  "New Jersey"                    
	35        =  "New Mexico"                    
	36        =  "New York"                      
	37        =  "North Carolina"                
	38        =  "North Dakota"                  
	39        =  "Ohio"                          
	40        =  "Oklahoma"                      
	41        =  "Oregon"                        
	42        =  "Pennsylvania"                  
	44        =  "Rhode Island"                  
	45        =  "South Carolina"                
	46        =  "South Dakota"                  
	47        =  "Tennessee"                     
	48        =  "Texas"                         
	49        =  "Utah"                          
	50        =  "Vermont"                       
	51        =  "Virginia"                      
	53        =  "Washington"                    
	54        =  "West Virginia"                 
	55        =  "Wisconsin"                     
	56        =  "Wyoming"                       
;
RUN;
********************************************************************************************;
*****                         MAIN DATA SECTION                                        *****;
********************************************************************************************;
*****
	CREATE MARCH CPS INDICATOR ON EACH COMPONENT FILE
*****;
DATA CPSRETS15;
SET YR2015.CPSRETS2015;
MARCHCPS = 2015;
RUN;
DATA CPSRETS14;
SET YR2014.CPSRETS2014;
MARCHCPS = 2014;
RUN;
DATA CPSRETS13;
SET YR2013.CPSRETS2013;
MARCHCPS = 2013;
RUN;
DATA EXTRACT.PROD2015_V1A(COMPRESS=YES);
SET CPSRETS15
    CPSRETS14
	CPSRETS13 ;
*****
	ADJUST THE SAMPLE WEIGHTS
*****;
WT = WT / 3.0000 ;

*****
	CHANGE MISSING DATA TO ZEROS FOR STATA
*****;
ARRAY D(*) _NUMERIC_ ;
DO I = 1 TO DIM( D );
	IF( D( I ) = . )THEN D( I ) = 0.0 ;
END;
RUN;
/*
                Table 2a. - First Blocking Partitions: Filing Status, Age & Income
                                (Unweighted) - Filers Only
*/
PROC TABULATE DATA=EXTRACT.PROD2015_V1A FORMAT=COMMA12. ;
CLASS JS AGEDE IFDEPT DEPNE ;
VAR RETURNS ;
FORMAT JS JS. IFDEPT IFDEPT. DEPNE DEPNE. AGEDE AGEDE.
FILST FILST.;
KEYLABEL SUM='AMOUNT' PCTSUM='PERCENT' ALL='Total, All Returns'
MEAN='AVERAGE' N='Unweighted' PCTN='PERCENT' SUMWGT='Weighted' ;
TABLE ( (IFDEPT ALL)*(AGEDE ALL) ) , RETURNS*( ((JS*DEPNE ALL) )*(N)  )
/ PRINTMISS MISSTEXT='n.a.' ;
TITLE1 'S t a t e   M o d e l i n g  P r o j e c t' ;
TITLE3 'Creation of Production File: August 2016' ;
TITLE5 'Table 1. - First Blocking Partition: Filing Status, Age & Dependency Status' ;
TITLE6 'Source: March CPS Files for 2015, 2014 and 2013' ;
TITLE7 '(*** Unweighted ***)' ;
TITLE8 'All CPS Tax Units' ;
TITLE9 '-----------------' ;
RUN;
/*
                Table 2b. - First Blocking Partitions: Filing Status, Age & Income
                                (Weighted) - Filers Only
*/
PROC TABULATE DATA=EXTRACT.PROD2015_V1A FORMAT=COMMA12. ;
WEIGHT WT;
CLASS JS AGEDE IFDEPT DEPNE ;
VAR RETURNS ;
FORMAT JS JS. IFDEPT IFDEPT. DEPNE DEPNE. AGEDE AGEDE.
FILST FILST.;
KEYLABEL SUM='AMOUNT' PCTSUM='PERCENT' ALL='Total, All Returns'
MEAN='AVERAGE' N='Unweighted' PCTN='PERCENT' SUMWGT='Weighted' ;
TABLE ( (IFDEPT ALL)*(AGEDE ALL) ) , RETURNS*( ((JS*DEPNE ALL) )*(SUMWGT)  )
/ PRINTMISS MISSTEXT='n.a.' ;
TITLE1 'S t a t e   M o d e l i n g  P r o j e c t' ;
TITLE3 'Creation of Production File: August 2015' ;
TITLE5 'Table 1. - First Blocking Partition: Filing Status, Age & Dependency Status' ;
TITLE6 'Source: March CPS Files for 2015, 2014 and 2013' ;
TITLE7 '(*** Weighted ***)' ;
TITLE8 'All CPS Tax Units' ;
TITLE9 '-----------------' ;
RUN;
*****
	SUMMARIZE THE TAX UNIT EXTRACT BY STATE
*****;
PROC FREQ DATA=EXTRACT.PROD2015_V1A;
TABLES XSTATE;
FORMAT XSTATE GESTFIPS.;
TITLE1 '2015 Production File - By State';
TITLE2 'Unweighted Record Counts';
RUN;
PROC FREQ DATA=EXTRACT.PROD2015_V1A;
WEIGHT WT;
TABLES XSTATE;
FORMAT XSTATE GESTFIPS.;
TITLE1 '2015 Production File - By State';
TITLE2 'Weighted Record Counts';
RUN;
PROC FREQ DATA=EXTRACT.PROD2015_V1;
TABLES MARCHCPS;
RUN;
PROC MEANS N MIN MAX SUM DATA=EXTRACT.PROD2015_V1A;
WEIGHT WT;
VAR FILST;
TITLE1 '2015 Production File - By State';
TITLE2 'Weighted Record Counts';
RUN;
