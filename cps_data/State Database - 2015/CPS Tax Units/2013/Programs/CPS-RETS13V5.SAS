*****
	SHANE:	THIS IS THE PROGRAM I MODIFIED TO ADD THE NEW VARIABLES YOU SUGGESTED. TO SEE
			WHERE I MADE THE MODIFICATIONS, JUST SEARCH FOR "SHANE:". I ADDED 10 NEW
			PERSON-LEVEL VARIABLES, BUT THIS TRANSLATED INTO 20 NEW TAX UNIT VARIABLES:
			ONE FOR THE PRIMARY TAXPAYER AND ONE FOR THE SPOUSE. THE VARIABLES ARE FROM
			YOUR EARLIER E-MAIL, PLUS I ADDED A COUPLE OF CENSUS IMPUTED TAX FIELDS. I
			DON'T HAVE MUCH EXPERIENCE WITH THESE IMPUTED AMOUNTS.

			1.	A_AGE	(ALREADY ON THE ORIGINAL TAX UNIT EXTRACT)
			2.	CARE
			3.	CAID
			4.	OTH
			5.	HI
			6.	PRIV
			7.	PAID
			8.	FILESTAT (APPEARS TO BE ZERO ON THE CPS)
			9.	AGI	     (APPEARS TO BE ZERO ON THE CPS)
			10.	CAP_GAIN (APPEARS TO BE ZERO ON THE CPS)

			BASICALLY, THESE 10 VARIABLES ARE STORED IN A NEW ARRAY (JCPS()) IN LOCATIONS
			151-170. THE FIRST 10 LOCATIONS (151-160) STORE THE VALUE OF THESE VARIABLES FOR THE
			PRIMARY TAXPAYER WHILE THE REMAINING (161-170) STORE THE VALUE FOR THE SPOUSE.
*****;


*******************************************************************************************;
***                                                                                     ***;
***                                                                                     ***;
***                          IBM/IRS CPS Tax Unit Project                               ***;
***                                                                                     ***;
***                                                                                     ***;
*******************************************************************************************;
***                                                                                     ***;
***	Program:		CPS-RETS.SAS                                                        ***;
***                                                                                     ***;
***	Type:			SAS Program                                                         ***;
***                                                                                     ***;
*** Function:		This program reads a person-level extract from the March CPS        ***;
***					created from an earlier SAS program (CPSMARXX.SAS, where 'XX'       ***;
***                 refers to the year of the extract). The program creates tax units   ***;
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
***	History:		Program begun on 01-FEB-2010.                                       ***;
***                 Revised on 20-FEB-2010 to automate the selection of tax years and   ***;
***                 CPS years. Also, added dataset of tax law parameters.               ***;
*******************************************************************************************;
*OPTIONS PAGESIZE=84 LINESIZE=111; /* PORTRAIT  */
OPTIONS PAGESIZE=59 LINESIZE=160 CENTER ; /* LANDSCAPE */

%LET TAXYEAR=2012;
%LET CPSYEAR=2013;

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
/*
        -------------------------------------------------------------------
        MACRO Section - The following MACROS are defined in this section:

                %CREATE       = Create a CPS Tax Unit and store it in
                                in the TREC(,) array.
                %SEARCH       = The inner loop of the processing algorithm.
                                Searches all household members except
                                reference person & spouse to determine
                                if there are dependents.
                %ADDEPT       = Adds a dependent to a Tax Unit. Arguments
                                are the person number of the (new) dependent
                                and the Tax Unit number.
                %OUTPUT       = After all CPS Tax Units have been created,
                                output all records.
                %IFDEPT       = Determines dependency status.
                %FILST        = Determines whether or not a CPS Tax Unit
                                actually files a return.
                %GROSS        = Computes Gross Income (for determining
                                filing requirements) for the Tax Unit.
                %SETPARMS     = Initializes income threshold amounts for
                                determining filing status.
                %FILLREC      = Fills Up Person Array for each individual
                                in the household.
                %HHSTATUS     = Determines whether a single individual with
                                dependents can or will file as a head of
                                household return.

        -------------------------------------------------------------------
*/

%MACRO CREATE ( PERSON ) ;
/*
        -----------------------------
        Create CPS Tax Units
        -----------------------------

*/

NUNITS = NUNITS + 1 ;
/*
        Flag this Person
*/
PREC(&PERSON , 55) = 1.0 ;
/*
        Income Items
*/
WAS = PREC(&PERSON , 20) ;
WASP = WAS ;
INTST = PREC(&PERSON , 26) ;
DBE = PREC(&PERSON , 27) ;
ALIMONY = PREC(&PERSON , 29) ;
BIL = PREC(&PERSON , 21) ;
PENSIONS = PREC(&PERSON , 25) ;
RENTS = PREC(&PERSON , 28) ;
FIL = PREC(&PERSON , 22) ;
UCOMP = PREC(&PERSON , 23) ;
SOCSEC = PREC(&PERSON , 24) ;
/*
        Weight & Flags
*/
WT = PREC(&PERSON , 10) ;
IFDEPT = PREC(&PERSON , 32) ;
PREC(&PERSON , 30) = 1.0 ;
/*
        CPS Identifiers
*/
XHID = PREC(&PERSON ,  1) ;
XFID = PREC(&PERSON ,  2) ;
XPID = PREC(&PERSON , 11) ;
XSTATE = GESTFIPS ;
XREGION = GEREG ;

/*
        CPS Evaluation Criteria (HEAD)
*/
ZIFDEP = PREC(&PERSON , 32) ;
ZNTDEP = 0;
ZHHINC = HHINC ;
ZAGEPT = PREC(&PERSON , 12) ;
ZAGESP = 0;
ZOLDES = 0;
ZYOUNG = 0;
ZWORKC = PREC(&PERSON , 40) ;
ZSOCSE = PREC(&PERSON , 24) ;
ZSSINC = PREC(&PERSON , 51) ;
ZPUBAS = PREC(&PERSON , 41) ;
ZVETBE = PREC(&PERSON , 52) ;
ZCHSUP = PREC(&PERSON , 53) ;
ZFINAS = PREC(&PERSON , 54) ;
ZDEPIN = 0;
ZOWNER = 0;
ZWASPT = PREC(&PERSON , 20) ;
ZWASSP = 0;
/* Blindness indicators */
BLIND_HEAD = 0;
BLIND_SPOUSE = 0;
IF (PREC(&PERSON , 119) = 1) THEN BLIND_HEAD = 1;
/*
        Home Ownership Flag
*/
IF( NUNITS = 1 )THEN
        DO;
                IF( H_TENURE = 1 )THEN ZOWNER = 1;
        END;

/*
        Marital Status
*/
MS = PREC(&PERSON , 36);
TYPE = 1.;
IF( (MS = 1) OR (MS = 2) OR (MS = 3) )THEN TYPE=2.;
SP_PTR = PREC(&PERSON , 9);
RELCODE = PREC(&PERSON , 38);
FTYPE = PREC(&PERSON ,  4) ;
SELECT;
        WHEN( TYPE = 1 )
                DO;
                        JS = 1;
                        AGEH = PREC(&PERSON , 12) ;
                        AGEDE = 0. ;IF( AGEH GE 65. )THEN AGEDE = 1.;
                        AGES = .;
                        DEPNE = 0.0 ;
/*
                        -----------------------------------------
                        Certain single & separated individuals
                        living alone are allowed to file as head
                        of household.
                        -----------------------------------------
*/
                        IF( ( (H_TYPE = 6) OR (H_TYPE = 7) ) AND (H_NUMPER = 1) )THEN
                                DO;
                                        IF( MS = 6 )THEN JS = 1;
                                END;

                END;
        WHEN( TYPE = 2 )
                DO;
                        JS = 2 ;
                        AGEH = PREC(&PERSON , 12) ;
                        AGEDE = 0. ;IF( AGEH GE 65. )THEN AGEDE = 1.;
                        DEPNE = 0.0 ;
                        IF( SP_PTR NE 0 )THEN   /* May be absent     */
                                DO;
                                        AGES= PREC(SP_PTR , 12) ;
                                        IF( AGES GE 65. )THEN AGEDE = AGEDE + 1.;
                                        WASS = PREC(SP_PTR , 20) ;
                                        WAS = WAS + WASS ;
                                        INTST = INTST + PREC(SP_PTR , 26) ;
                                        DBE = DBE + PREC(SP_PTR , 27) ;
                                        ALIMONY = ALIMONY + PREC(SP_PTR , 29) ;
                                        BIL = BIL + PREC(SP_PTR , 21) ;
                                        PENSIONS = PENSIONS + PREC(SP_PTR , 25) ;
                                        RENTS = RENTS + PREC(SP_PTR , 28) ;
                                        FIL = FIL + PREC(SP_PTR , 22) ;
                                        UCOMP = UCOMP + PREC(SP_PTR , 23) ;
                                        SOCSEC = SOCSEC + PREC(SP_PTR , 24) ;
                                        PREC(SP_PTR , 31) = 1.0 ;
                                        /*
                                                CPS Evaluation Criteria (SPOUSE)
                                        */
                                        ZAGESP = PREC(SP_PTR , 12) ;
                                        ZWORKC = ZWORKC + PREC(SP_PTR , 40) ;
                                        ZSOCSE = ZSOCSE + PREC(SP_PTR , 24) ;
                                        ZSSINC = ZSSINC + PREC(SP_PTR , 51) ;
                                        ZPUBAS = ZPUBAS + PREC(SP_PTR , 41) ;
                                        ZVETBE = ZVETBE + PREC(SP_PTR , 52) ;
                                        ZCHSUP = ZCHSUP + PREC(SP_PTR , 53) ;
                                        ZFINAS = ZFINAS + PREC(SP_PTR , 54) ;
                                        ZWASSP = PREC(SP_PTR , 20) ;

										/* Blindness indicator */
										IF (PREC(SP_PTR , 119) = 1) THEN BLIND_SPOUSE = 1;
                                END;
                END;
        OTHERWISE ;
END;
/*
        Construct the Tax Unit
*/
        TREC(NUNITS  , 01) = JS ;
        TREC(NUNITS  , 02) = IFDEPT ;
        TREC(NUNITS  , 03) = AGEDE ;
        TREC(NUNITS  , 04) = DEPNE ;
        TREC(NUNITS  , 05) = CAHE ;
        TREC(NUNITS  , 06) = AGEH ;
        TREC(NUNITS  , 07) = AGES ;
        TREC(NUNITS  , 08) = WAS ;
        TREC(NUNITS  , 09) = INTST ;
        TREC(NUNITS  , 10) = DBE ;
        TREC(NUNITS  , 11) = ALIMONY ;
        TREC(NUNITS  , 12) = BIL ;
        TREC(NUNITS  , 13) = PENSIONS ;
        TREC(NUNITS  , 14) = RENTS ;
        TREC(NUNITS  , 15) = FIL ;
        TREC(NUNITS  , 16) = UCOMP ;
        TREC(NUNITS  , 17) = SOCSEC ;
        TREC(NUNITS  , 18) = INCOME ;
        TREC(NUNITS  , 19) = 1.0 ;
        TREC(NUNITS  , 20) = WT ;
        DO NDP = 21 TO 36 ;
                TREC(NUNITS , NDP) = 0.0 ;
        END;
        TREC(NUNITS  , 37) = &PERSON ;
        TREC(NUNITS  , 38) = SP_PTR ;
        TREC(NUNITS  , 39) = RELCODE ;
        TREC(NUNITS  , 40) = FTYPE ;
        TREC(NUNITS  , 41) = ZIFDEP ;
        TREC(NUNITS  , 42) = ZNTDEP ;
        TREC(NUNITS  , 43) = ZHHINC ;
        TREC(NUNITS  , 44) = ZAGEPT ;
        TREC(NUNITS  , 45) = ZAGESP ;
        TREC(NUNITS  , 46) = ZOLDES ;
        TREC(NUNITS  , 47) = ZYOUNG ;
        TREC(NUNITS  , 48) = ZWORKC ;
        TREC(NUNITS  , 49) = ZSOCSE ;
        TREC(NUNITS  , 50) = ZSSINC ;
        TREC(NUNITS  , 51) = ZPUBAS ;
        TREC(NUNITS  , 52) = ZVETBE ;
        TREC(NUNITS  , 53) = ZCHSUP ;
        TREC(NUNITS  , 54) = ZFINAS ;
        TREC(NUNITS  , 55) = ZDEPIN ;
        TREC(NUNITS  , 56) = ZOWNER ;
        TREC(NUNITS  , 57) = ZWASPT ;
        TREC(NUNITS  , 58) = ZWASSP ;
        TREC(NUNITS  , 59) = 0 ;
        TREC(NUNITS  , 60) = 0 ;
        TREC(NUNITS  , 61) = 0 ;
        TREC(NUNITS  , 62) = 0 ;
        TREC(NUNITS  , 63) = 0 ;
        TREC(NUNITS  , 64) = 0 ;
        TREC(NUNITS  , 65) = WASP ;
        TREC(NUNITS  , 66) = WASS ;
        DO NDP = 67 TO 82 ;
                TREC(NUNITS , NDP) = 0.0 ;
        END;
/*
        --------------------------------------
        New Fields. Mostly for Non-filers.
        --------------------------------------
*/
        XSCHB = 0.0 ;IF( INTST GT 400. )THEN XSCHB = 1;
        XSCHF = 0.0 ;IF( FIL NE 0.0    )THEN XSCHF = 1;
        XSCHE = 0.0 ;IF( RENTS NE 0.0  )THEN XSCHE = 1;
        XSCHC = 0.0 ;IF( BIL NE 0.0    )THEN XSCHC = 1;
/*
        --------------------------------------
        We'll count dependents later, after
        all relationships have been set.
        --------------------------------------
*/
        TREC(NUNITS  , 83) = 0.0 ;      /*      XXOODEP */
        TREC(NUNITS  , 84) = 0.0 ;      /*      XXOPAR  */
        TREC(NUNITS  , 85) = 0.0 ;      /*      XXTOT   */
        TREC(NUNITS  , 86) = AGEDE ;    /*      XAGEX   */
        TREC(NUNITS  , 87) = XSTATE ;   /*      XSTATE  */
        TREC(NUNITS  , 88) = XREGION ;  /*      XREGION */
        TREC(NUNITS  , 89) = XSCHB ;    /*      XSCHB   */
        TREC(NUNITS  , 90) = XSCHF ;    /*      XSCHF   */
        TREC(NUNITS  , 91) = XSCHE ;    /*      XSCHE   */
        TREC(NUNITS  , 92) = XSCHC ;    /*      XSCHC   */
        TREC(NUNITS  , 93) = XHID ;     /*      XHID    */
        TREC(NUNITS  , 94) = XFID ;     /*      XFID    */
        TREC(NUNITS  , 95) = XPID ;     /*      XPID    */

/*
        ---------------------------------------
        NEW CPS VARIABLES: Added JULY 2009 in
                locations 101-150.

        NOTE: Lot's of duplication here, but
              this is probably easier than
              taking the time to modify the
              whole program. Also, note that
              for the most part, we're pulling
              these variables from the Person
              array PREC(*,*).
        ---------------------------------------
*/
        /*
                First, We'll Zero-out the ICPS(*) Array
                and the corresponding elements in TREC(*).
        */
        DO I = 1 TO 50;
                ICPS(I) = 0;
                TREC(NUNITS , 100 + I) = 0;
        END;
		*****
			SHANE:	HERE, I ZERO OUT THE JCPS() ARRAY AND
					THE CORRESPONDING SLOTS IN THE TREC() ARRAY.
					NOTE: JCPS ARRAY HAS BEEN EXPANDED (24-MAY-2016).
		*****;
		DO I = 1 TO 200;
				JCPS(I) = 0.0;
		END;
		DO I = 1 TO 100;
				TREC(NUNITS , 150 + I) = 0;
		END;
        /*
                Age of HEAD & SPOUSE (if present)
        */
        TREC(NUNITS , 101) = PREC(&PERSON , 12) ;
        IF( SP_PTR NE 0 )THEN TREC(NUNITS , 102) = PREC(SP_PTR  , 12) ;
/*
        ========
        DEBUG
        ========
*/
/*
        IF( (SP_PTR NE 0) AND (TYPE = 1) )THEN
                DO;
                        PUT "****ERROR IN SPOUSE POINTER";
                        PUT "SPOUSE POINTER = " SP_PTR;
                        PUT "TYPE           = " TYPE;
                        PUT "AGE OF HEAD    = " AGEH;
                        PUT "AGE OF SPOUSE  = " AGES;
                        PUT "HOUSEHOLD ID   = " HHID;
                        STOP;
                END;
*/
/*
        =========
        END DEBUG
        =========
*/

/*
        We'll fill up the dependent ages later, once we
        know who they are.
*/
        /*
                Health Insurance Coverage
        */
        TREC(NUNITS , 110) = PREC(&PERSON , 43) ;
        TREC(NUNITS , 111) = PREC(&PERSON , 45) ;
        TREC(NUNITS , 112) = PREC(&PERSON , 46) ;
        IF( SP_PTR NE 0 )THEN
                DO;
                        TREC(NUNITS , 113) = PREC(SP_PTR , 43) ;
                        TREC(NUNITS , 114) = PREC(SP_PTR , 45) ;
                        TREC(NUNITS , 115) = PREC(SP_PTR , 46) ;

                END;
        /*
                Pension Coverage
        */
        TREC(NUNITS , 116) = PREC(&PERSON , 47) ;
        TREC(NUNITS , 117) = PREC(&PERSON , 48) ;
        IF( SP_PTR NE 0 )THEN
                DO;
                        TREC(NUNITS , 118) = PREC(SP_PTR , 47) ;
                        TREC(NUNITS , 119) = PREC(SP_PTR , 48) ;
                END;
        /*
                Health Status
        */
        TREC(NUNITS , 120) = PREC(&PERSON , 49) ;
        IF( SP_PTR NE 0 )THEN TREC(NUNITS , 121) = PREC(SP_PTR  , 49) ;
        /*
                Miscellaneous Income Amounts
        */
        TREC(NUNITS , 122) = PREC(&PERSON , 51) ; /* SSI                      */
        TREC(NUNITS , 123) = PREC(&PERSON , 41) ; /* Public Assistance (TANF) */
        TREC(NUNITS , 124) = PREC(&PERSON , 40) ; /* Workman's Compensation   */
        TREC(NUNITS , 125) = PREC(&PERSON , 52) ; /* Veteran's Benefits       */
        TREC(NUNITS , 126) = PREC(&PERSON , 53) ; /* Child Support            */
        TREC(NUNITS , 127) = PREC(&PERSON , 42) ; /* Disability Income        */
        TREC(NUNITS , 128) = PREC(&PERSON , 24) ; /* Social Security Income   */
        TREC(NUNITS , 129) = ZOWNER ;             /* Home Ownership Flag      */
        TREC(NUNITS , 130) = 0.0 ;                /* Wage Share               */
        IF( SP_PTR NE 0 )THEN
                DO;
                        TREC(NUNITS , 122) = TREC(NUNITS , 122) + PREC(SP_PTR , 51) ;
                        TREC(NUNITS , 123) = TREC(NUNITS , 123) + PREC(SP_PTR , 41) ;
                        TREC(NUNITS , 124) = TREC(NUNITS , 124) + PREC(SP_PTR , 40) ;
                        TREC(NUNITS , 125) = TREC(NUNITS , 125) + PREC(SP_PTR , 52) ;
                        TREC(NUNITS , 126) = TREC(NUNITS , 126) + PREC(SP_PTR , 53) ;
                        TREC(NUNITS , 127) = TREC(NUNITS , 127) + PREC(SP_PTR , 42) ;
                        TREC(NUNITS , 128) = TREC(NUNITS , 128) + PREC(SP_PTR , 24) ;
                        TOTALWAS = PREC(&PERSON , 20 ) + PREC( SP_PTR , 20 ) ;
                        IF( TOTALWAS GT 0.0 )THEN
                                DO;
                                TREC(NUNITS , 130) = MIN(PREC(&PERSON , 20) , PREC(SP_PTR , 20))
                                                   / TOTALWAS ;
                                END;
                END;

		/*
				NEW CPS VARIABLES ADDED JULY 2009
		*/
		***
			ENERGY ASSISTANCE, FOOD STAMPS, SCHOOL LUNCH
			ONLY GET PUT ON THE RETURN OF THE PRIMARY TAXPAYER
		***;
		IF( NUNITS EQ 1 )THEN
			DO;
				TREC(NUNITS , 131) = PREC(&PERSON , 56) ;
				TREC(NUNITS , 132) = PREC(&PERSON , 57) ;
				TREC(NUNITS , 133) = PREC(&PERSON , 58) ;
			END;
		***
			ADDITIONAL HEALTH-RELATED VARIABLES, ETC:
			MEDICARE, MEDICAID, CHAMPUS AND COUNTRY OF ORIGIN
		***;
        TREC(NUNITS , 134) = PREC(&PERSON , 59) ;
        TREC(NUNITS , 135) = PREC(&PERSON , 60) ;
        TREC(NUNITS , 136) = PREC(&PERSON , 61) ;
		TREC(NUNITS , 137) = PREC(&PERSON , 62) ;
        IF( SP_PTR NE 0 )THEN
                DO;
                        TREC(NUNITS , 138) = PREC(SP_PTR , 59) ;
                        TREC(NUNITS , 139) = PREC(SP_PTR , 60) ;
                        TREC(NUNITS , 140) = PREC(SP_PTR , 61) ;
                        TREC(NUNITS , 141) = PREC(SP_PTR , 62) ;
                END;
		***
			(1)	EDUCATIONAL ATTAINMENT (HEAD AND SPOUSE)
			(2)	GENDER (HEAD AND SPOUSE)
				NOTE: ADDED FEBRUARY, 2010 FOR IBM/IRS WORK.
		***;
		TREC(NUNITS , 142) = PREC(&PERSON , 39) ;
		TREC(NUNITS , 143) = PREC(&PERSON , 13) ;
		IF( SP_PTR NE 0 )THEN
				DO;
					TREC(NUNITS , 144) = PREC(SP_PTR , 39) ;
					TREC(NUNITS , 145) = PREC(SP_PTR , 13) ;
				END;
		***
			(1)	SELF-EMPLOYED INDUSTRY - HEAD AND SPOUSE
		***;
		CLASSOFWORKER = PREC( &PERSON , 60 );
		MAJORINDUSTRY = 0.0;
		SENONFARM = 0.0;
		SEFARM = 0.0;
		IF( CLASSOFWORKER EQ 6. )THEN
			DO;
				SENONFARM = PREC( &PERSON , 21 );
				SEFARM = PREC( &PERSON , 22 );
				MAJORINDUSTRY = PREC( &PERSON , 61 );
			END;

		IF( SP_PTR NE 0 )THEN
				DO;
					CLASSOFWORKER = PREC( SP_PTR , 60 );
					IF( CLASSOFWORKER EQ 6. )THEN
						DO;
							SENONFARM_SP = PREC( SP_PTR , 21 );
							SEFARM_SP = PREC( SP_PTR , 22 );
							IF( ABS( SENONFARM_SP ) GT ABS( SENONFARM ) )THEN MAJORINDUSTRY = PREC( SP_PTR , 61 );
							SENONFARM = SENONFARM + SENONFARM_SP;
							SEFARM = SEFARM + SEFARM_SP;
						END;
				END;
		TREC( NUNITS , 146 ) = MAJORINDUSTRY;
		TREC( NUNITS , 147 ) = SENONFARM;
		TREC( NUNITS , 148 ) = SEFARM;
		*****
			SHANE:	HERE I FILL UP THE TREC() ARRAY WITH THE NEW VARIABLES.
					THERE WILL BE 20 NEW VARIABLES, ONE FOR THE PRIMARY TAXPAYER
					AND ONE FOR THE SPOUSE. WE USE THE SPOUSE POINTER (SP_PTR) TO
					DO THIS. SLOTS 151-160 ARE FOR THE PRIMARY TAXPAYER, WHILE
					SLOTS 161-170 ARE FOR THE SPOUSE, IF PRESENT.
		*****;
		TREC( NUNITS , 151 ) = PREC(&PERSON , 63) ;
		TREC( NUNITS , 152 ) = PREC(&PERSON , 64) ;
		TREC( NUNITS , 153 ) = PREC(&PERSON , 65) ;
		TREC( NUNITS , 154 ) = PREC(&PERSON , 66) ;
		TREC( NUNITS , 155 ) = PREC(&PERSON , 67) ;
		TREC( NUNITS , 156 ) = PREC(&PERSON , 68) ;
		TREC( NUNITS , 157 ) = PREC(&PERSON , 69) ;
		TREC( NUNITS , 158 ) = PREC(&PERSON , 70) ;
		TREC( NUNITS , 159 ) = PREC(&PERSON , 71) ;
		TREC( NUNITS , 160 ) = PREC(&PERSON , 72) ;
		IF( SP_PTR NE 0 )THEN
			DO;
				TREC( NUNITS , 161 ) = PREC( SP_PTR , 63) ;
				TREC( NUNITS , 162 ) = PREC( SP_PTR , 64) ;
				TREC( NUNITS , 163 ) = PREC( SP_PTR , 65) ;
				TREC( NUNITS , 164 ) = PREC( SP_PTR , 66) ;
				TREC( NUNITS , 165 ) = PREC( SP_PTR , 67) ;
				TREC( NUNITS , 166 ) = PREC( SP_PTR , 68) ;
				TREC( NUNITS , 167 ) = PREC( SP_PTR , 69) ;
				TREC( NUNITS , 168 ) = PREC( SP_PTR , 70) ;
				TREC( NUNITS , 169 ) = PREC( SP_PTR , 71) ;
				TREC( NUNITS , 170 ) = PREC( SP_PTR , 72) ;
			END;
*****
	NEW VARIABLES FOR PEW DATABASE - VERSION 3.0
	STORED IN LOCATIONS: JCPS(021) - JCPS(030):	TAXPAYER
						 JCPS(031) - JCPS(040): SPOUSE
*****;
		TREC( NUNITS , 171 ) = PREC(&PERSON , 20) ;
		TREC( NUNITS , 172 ) = PREC(&PERSON , 26) ;
		TREC( NUNITS , 173 ) = PREC(&PERSON , 27) ;
		TREC( NUNITS , 174 ) = PREC(&PERSON , 29) ;
		TREC( NUNITS , 175 ) = PREC(&PERSON , 21) ;
		TREC( NUNITS , 176 ) = PREC(&PERSON , 25) ;
		TREC( NUNITS , 177 ) = PREC(&PERSON , 28) ;
		TREC( NUNITS , 178 ) = PREC(&PERSON , 22) ;
		TREC( NUNITS , 179 ) = PREC(&PERSON , 23) ;
		TREC( NUNITS , 180 ) = PREC(&PERSON , 24) ;
		IF( SP_PTR NE 0 )THEN
			DO;
				TREC( NUNITS , 181 ) = PREC( SP_PTR , 20) ;
				TREC( NUNITS , 182 ) = PREC( SP_PTR , 26) ;
				TREC( NUNITS , 183 ) = PREC( SP_PTR , 27) ;
				TREC( NUNITS , 184 ) = PREC( SP_PTR , 29) ;
				TREC( NUNITS , 185 ) = PREC( SP_PTR , 21) ;
				TREC( NUNITS , 186 ) = PREC( SP_PTR , 25) ;
				TREC( NUNITS , 187 ) = PREC( SP_PTR , 28) ;
				TREC( NUNITS , 188 ) = PREC( SP_PTR , 22) ;
				TREC( NUNITS , 189 ) = PREC( SP_PTR , 23) ;
				TREC( NUNITS , 190 ) = PREC( SP_PTR , 24) ;
			END;
*****
	NEW VARIABLES FOR PEW DATABASE - VERSION 4.0
*****;
*****
	RETIREMENT INCOME
*****;
		TREC( NUNITS , 191 ) = PREC(&PERSON , 73) ;
		TREC( NUNITS , 192 ) = PREC(&PERSON , 74) ;
		TREC( NUNITS , 193 ) = PREC(&PERSON , 75) ;
		TREC( NUNITS , 194 ) = PREC(&PERSON , 76) ;
		IF( SP_PTR NE 0 )THEN
			DO;
				TREC( NUNITS , 195 ) = PREC( SP_PTR , 73) ;
				TREC( NUNITS , 196 ) = PREC( SP_PTR , 74) ;
				TREC( NUNITS , 197 ) = PREC( SP_PTR , 75) ;
				TREC( NUNITS , 198 ) = PREC( SP_PTR , 76) ;
			END;
*****
	DISABILITY INCOME
*****;
		TREC( NUNITS , 199 ) = PREC(&PERSON , 77) ;
		TREC( NUNITS , 200 ) = PREC(&PERSON , 78) ;
		TREC( NUNITS , 201 ) = PREC(&PERSON , 79) ;
		TREC( NUNITS , 202 ) = PREC(&PERSON , 80) ;
		IF( SP_PTR NE 0 )THEN
			DO;
				TREC( NUNITS , 203 ) = PREC( SP_PTR , 77) ;
				TREC( NUNITS , 204 ) = PREC( SP_PTR , 78) ;
				TREC( NUNITS , 205 ) = PREC( SP_PTR , 79) ;
				TREC( NUNITS , 206 ) = PREC( SP_PTR , 80) ;
			END;
*****
	SURVIVOR INCOME
*****;
		TREC( NUNITS , 207 ) = PREC(&PERSON , 81) ;
		TREC( NUNITS , 208 ) = PREC(&PERSON , 82) ;
		TREC( NUNITS , 209 ) = PREC(&PERSON , 83) ;
		TREC( NUNITS , 210 ) = PREC(&PERSON , 84) ;
		IF( SP_PTR NE 0 )THEN
			DO;
				TREC( NUNITS , 211 ) = PREC( SP_PTR , 81) ;
				TREC( NUNITS , 212 ) = PREC( SP_PTR , 82) ;
				TREC( NUNITS , 213 ) = PREC( SP_PTR , 83) ;
				TREC( NUNITS , 214 ) = PREC( SP_PTR , 84) ;
			END;
*****
	VETERANS INCOME
*****;
		TREC( NUNITS , 215 ) = PREC(&PERSON , 85) ;
		TREC( NUNITS , 216 ) = PREC(&PERSON , 86) ;
		TREC( NUNITS , 217 ) = PREC(&PERSON , 87) ;
		TREC( NUNITS , 218 ) = PREC(&PERSON , 88) ;
		TREC( NUNITS , 219 ) = PREC(&PERSON , 89) ;
		TREC( NUNITS , 220 ) = PREC(&PERSON , 90) ;
		IF( SP_PTR NE 0 )THEN
			DO;
				TREC( NUNITS , 221 ) = PREC( SP_PTR , 85) ;
				TREC( NUNITS , 222 ) = PREC( SP_PTR , 86) ;
				TREC( NUNITS , 223 ) = PREC( SP_PTR , 87) ;
				TREC( NUNITS , 224 ) = PREC( SP_PTR , 88) ;
				TREC( NUNITS , 225 ) = PREC( SP_PTR , 89) ;
				TREC( NUNITS , 226 ) = PREC( SP_PTR , 90) ;
			END;
*****
	NEED TO SAVE SPOUSE POINTER LATER USE.
	ADDED ON 24-MAY-2016 BY OHARE.
*****;
		TREC( NUNITS , 227 ) = SP_PTR;
*****
		ANDERSON: NEW TAX RECORD VARIABLES
*****;
		/*	HOUSEHOLD	*/
		TREC( NUNITS , 228 ) = PREC(&PERSON , 111);
		TREC( NUNITS , 229 ) = PREC(&PERSON , 112);
		TREC( NUNITS , 230 ) = PREC(&PERSON , 113);
		TREC( NUNITS , 231 ) = PREC(&PERSON , 114);
		TREC( NUNITS , 232 ) = PREC(&PERSON , 115);
		TREC( NUNITS , 233 ) = PREC(&PERSON , 116);
		TREC( NUNITS , 234 ) = PREC(&PERSON , 117);
		TREC( NUNITS , 235 ) = PREC(&PERSON , 118);
		/*	TAXPAYER	*/
		TREC( NUNITS , 236 ) = PREC(&PERSON , 91);
		TREC( NUNITS , 237 ) = PREC(&PERSON , 92);
		TREC( NUNITS , 238 ) = PREC(&PERSON , 93);
		TREC( NUNITS , 239 ) = PREC(&PERSON , 94);
		TREC( NUNITS , 240 ) = PREC(&PERSON , 95);
		TREC( NUNITS , 241 ) = PREC(&PERSON , 96);
		TREC( NUNITS , 242 ) = PREC(&PERSON , 97);
		TREC( NUNITS , 243 ) = PREC(&PERSON , 98);
		TREC( NUNITS , 244 ) = PREC(&PERSON , 99);
		TREC( NUNITS , 245 ) = PREC(&PERSON , 100);
		TREC( NUNITS , 246 ) = PREC(&PERSON , 101);
		TREC( NUNITS , 247 ) = PREC(&PERSON , 102);
		TREC( NUNITS , 248 ) = PREC(&PERSON , 103);
		TREC( NUNITS , 249 ) = PREC(&PERSON , 104);
		TREC( NUNITS , 250 ) = PREC(&PERSON , 105);
		TREC( NUNITS , 251 ) = PREC(&PERSON , 106);
		TREC( NUNITS , 252 ) = PREC(&PERSON , 107);
		TREC( NUNITS , 253 ) = PREC(&PERSON , 108);
		TREC( NUNITS , 254 ) = PREC(&PERSON , 109);
		TREC( NUNITS , 255 ) = PREC(&PERSON , 110);
		/*	SPOUSE, IF PRESENT	*/
		IF( SP_PTR NE 0 )THEN
		DO;
			TREC( NUNITS , 256 ) = PREC(SP_PTR , 91);
			TREC( NUNITS , 257 ) = PREC(SP_PTR , 92);
			TREC( NUNITS , 258 ) = PREC(SP_PTR , 93);
			TREC( NUNITS , 259 ) = PREC(SP_PTR , 94);
			TREC( NUNITS , 260 ) = PREC(SP_PTR , 95);
			TREC( NUNITS , 261 ) = PREC(SP_PTR , 96);
			TREC( NUNITS , 262 ) = PREC(SP_PTR , 97);
			TREC( NUNITS , 263 ) = PREC(SP_PTR , 98);
			TREC( NUNITS , 264 ) = PREC(SP_PTR , 99);
			TREC( NUNITS , 265 ) = PREC(SP_PTR , 100);
			TREC( NUNITS , 266 ) = PREC(SP_PTR , 101);
			TREC( NUNITS , 267 ) = PREC(SP_PTR , 102);
			TREC( NUNITS , 268 ) = PREC(SP_PTR , 103);
			TREC( NUNITS , 269 ) = PREC(SP_PTR , 104);
			TREC( NUNITS , 270 ) = PREC(SP_PTR , 105);
			TREC( NUNITS , 271 ) = PREC(SP_PTR , 106);
			TREC( NUNITS , 272 ) = PREC(SP_PTR , 107);
			TREC( NUNITS , 273 ) = PREC(SP_PTR , 108);
			TREC( NUNITS , 274 ) = PREC(SP_PTR , 109);
			TREC( NUNITS , 275 ) = PREC(SP_PTR , 110);
		END;

		/* Add age variables - Anderson */
		TREC( NUNITS , 276 ) = 0; /* Under 18 */
		TREC( NUNITS , 277 ) = 0; /* 18 - 21 */
		TREC( NUNITS , 278 ) = 0; /* Over 21 */

		IF (PREC(&PERSON, 12) < 18 AND PREC(&PERSON, 12) > 0) THEN
		    TREC(NUNITS, 276) = TREC(NUNITS, 276) + 1;
		ELSE IF (PREC(&PERSON, 12) >= 18 AND PREC(&PERSON, 12) < 21) THEN
		    TREC(NUNITS, 277) = TREC(NUNITS, 277) + 1;
		ELSE IF (PREC(&PERSON, 12) >= 21) THEN
		    TREC(NUNITS, 278) = TREC(NUNITS, 278) + 1;

		IF ( SP_PTR NE 0 ) THEN
		    DO;
			    IF (PREC(SP_PTR, 12) < 18 AND PREC(SP_PTR, 12) > 0) THEN
				    TREC(NUNITS, 276) = TREC(NUNITS, 276) + 1;
				ELSE IF (PREC(SP_PTR, 12) >= 18 AND PREC(SP_PTR, 12) < 21) THEN
				    TREC(NUNITS, 277) = TREC(NUNITS, 277) + 1;
				ELSE IF (PREC(SP_PTR, 12) >= 21) THEN
				    TREC(NUNITS, 278) = TREC(NUNITS, 278) + 1;
			END;
/* Add imputed variable data */
		DO NDP = 279 TO 586;
			TREC(NUNITS, NDP) = 0.0;
		END;
		TREC(NUNITS, 309) = PREC(&PERSON, 120); * Total SSI;
		TREC(NUNITS, 279) = PREC(&PERSON, 120); * SSI Imputation Value;
		TREC(NUNITS, 294) = PREC(&PERSON, 121); * SSI participation probability;
		TREC(NUNITS, 310) = PREC(&PERSON, 122); * Total VB Imputations;
	    TREC(NUNITS, 311) = PREC(&PERSON, 123); * Total SNAP Imputations;
		TREC(NUNITS, 312) = PREC(&PERSON, 124); * Total Medicare Imputations;
		TREC(NUNITS, 313) = PREC(&PERSON, 125); * Total Medicaid Imputations;
		TREC(NUNITS, 314) = PREC(&PERSON, 126); * Total Social Security Imputations;
		TREC(NUNITS, 315) = PREC(&PERSON, 128); * SNAP probability for head of unit;
		TREC(NUNITS, 330) = PREC(&PERSON, 123); * SNAP imputation value;
		TREC(NUNITS, 345) = PREC(&PERSON, 127); * SS Probability for head of unit;
		TREC(NUNITS, 360) = PREC(&PERSON, 126); * SS imputation value for head of unit;
		TREC(NUNITS, 375) = PREC(&PERSON, 129); * VB Probability for head of unit;
		TREC(NUNITS, 390) = PREC(&PERSON, 122); * VB imputation for head of unit;
		TREC(NUNITS, 405) = PREC(&PERSON, 130); * Medicare probability for head of unit;
		TREC(NUNITS, 420) = PREC(&PERSON, 124); * Medicare benefit for head of unit;
		TREC(NUNITS, 435) = PREC(&PERSON, 131); * Meidcaid probability for head of unit;
		TREC(NUNITS, 450) = PREC(&PERSON, 125); * Medicaid benefit for head of unit;

		TREC(NUNITS, 467) = PREC(&PERSON, 133); * TANF benefit for head of unit;
		TREC(NUNITS, 482) = PREC(&PERSON, 133); * TANF total benefits;
		TREC(NUNITS, 483) = PREC(&PERSON, 134); * TANF probability - head;
		TREC(NUNITS, 498) = PREC(&PERSON, 135); * UI benefit for head of unit;
		TREC(NUNITS, 513) = PREC(&PERSON, 135); * UI total benefits;
		TREC(NUNITS, 514) = PREC(&PERSON, 136); * UI probability - head;
		TREC(NUNITS, 529) = PREC(&PERSON, 137); * Housing benefit - head of unit;
		TREC(NUNITS, 544) = PREC(&PERSON, 137); * Housing total benefits;
		TREC(NUNITS, 545) = PREC(&PERSON, 138); * Housing benefit probability - head;
		TREC(NUNITS, 560) = PREC(&PERSON, 139); * WIC benefits for head of unit;
		TREC(NUNITS, 575) = PREC(&PERSON, 139); * WIC benefits total;
		TREC(NUNITS, 576) = PREC(&PERSON, 140); * WIC probability - head;

		IF (SP_PTR NE 0) THEN
			DO;
				TREC(NUNITS, 280) = PREC(SP_PTR, 120); *SSI Imputataion value;
				TREC(NUNITS, 295) = PREC(SP_PTR, 121); * SSI participation probability;
				TREC(NUNITS, 309) = TREC(NUNITS, 309) + PREC(SP_PTR, 120);
				TREC(NUNITS, 310) = TREC(NUNITS, 310) + PREC(SP_PTR, 122);
				TREC(NUNITS, 312) = TREC(NUNITS, 312) + PREC(SP_PTR, 124);
				TREC(NUNITS, 313) = TREC(NUNITS, 313) + PREC(SP_PTR, 125);
				TREC(NUNITS, 314) = TREC(NUNITS, 314) + PREC(SP_PTR, 126);
				TREC(NUNITS, 316) = PREC(SP_PTR, 128); * SNAP probability for spouse;
				TREC(NUNITS, 331) = PREC(SP_PTR, 123); * SNAP value for spouse;
				TREC(NUNITS, 346) = PREC(SP_PTR, 127); * SS probability for spouse;
				TREC(NUNITS, 361) = PREC(SP_PTR, 126); * SS value for spouse;
				TREC(NUNITS, 376) = PREC(SP_PTR, 129); * VB probability for spouse;
				TREC(NUNITS, 391) = PREC(SP_PTR, 122); * VB benefit for spouse;
				TREC(NUNITS, 406) = PREC(SP_PTR, 130); * Medicare probability for spouse;
				TREC(NUNITS, 421) = PREC(SP_PTR, 124); * Meidcare benefit for spouse;
				TREC(NUNITS, 436) = PREC(SP_PTR, 131); * Medicaid probability for spouse;
				TREC(NUNITS, 451) = PREC(SP_PTR, 125); * Medicaid benefit for spouse;
				TREC(NUNITS, 468) = PREC(SP_PTR, 133); * TANF benefit for spouse;
				TREC(NUNITS, 482) = TREC(NUNITS, 482) + PREC(SP_PTR, 133);
				TREC(NUNITS, 484) = PREC(SP_PTR, 134); * TANF probability - spouse;
				TREC(NUNITS, 499) = PREC(SP_PTR, 135); * UI benefit - spouse;
				TREC(NUNITS, 513) = TREC(NUNITS, 513) + PREC(SP_PTR, 135);
				TREC(NUNITS, 515) = PREC(SP_PTR, 136); * UI probability - spouse;
				TREC(NUNITS, 530) = PREC(SP_PTR, 137); * Housing benefit - spouse;
				TREC(NUNITS, 544) = TREC(NUNITS, 544) + PREC(SP_PTR, 137);
				TREC(NUNITS, 546) = PREC(SP_PTR, 138); * Housing probability - spouse;
				TREC(NUNITS, 561) = PREC(SP_PTR, 139); * WIC benefit - spouse;
				TREC(NUNITS, 575) = TREC(NUNITS, 575) + PREC(SP_PTR, 139);
				TREC(NUNITS, 577) = PREC(SP_PTR, 140); * WIC probability - spouse;

			END;

		* add head id to TREC array;
		TREC(NUNITS, 465) = PREC(&PERSON, 6);
		* add a_lineno to TREC array;
		TREC(NUNITS, 466) = PREC(&PERSON, 132);




/*
        ---------------------------------------
        Dependents can't have dependents, so
        limit this search to non-dependent
        filers.
        ---------------------------------------
*/
        IF( IFDEPT NE 1 )THEN
                DO;
                        %SEARCH1
                END;

/*
        ---------------------------------------
        Certain variables are for spouses only.
        Let's reset some of these to missing so
        not to cause any confusion.
        ---------------------------------------
*/
        AGES = . ;
        WASS = . ;
        SP_PTR = 0 ;
        ZWASSP = . ;

%MEND CREATE ;

%MACRO SEARCH1 ;
/*
        ---------------------------------------
        PHASE I Search:
        Search for Dependents Among Other
        Members of the Family Who are not
        Already Claimed on Another Return. In
        order to determine which records to
        search, we make a few assumptions:

        1. A Person can't search for himself;
        2. Searches are confined in Phase I to
           immediate family members;
        3. Can't already be a HEAD of a tax unit;
        4. Can't already be a SPOUSE of a tax unit;
        5. Can't already be a DEPENDENT of a tax unit.
        ---------------------------------------
*/
DO JX = 1 TO H_NUMPER;
idxFID = PREC(JX ,  2) ;
idxHEA = PREC(JX , 30) ;
idxSPO = PREC(JX , 31) ;
idxDEP = PREC(JX , 32) ;
idxREL = PREC(JX , 38) ;
IF( (JX NE IX) AND (idxFID = refFID) AND (idxDEP = 0) AND (idxSPO = 0)
AND (idxHEA = 0) )THEN
        DO;
                %IFDEPT( JX , DFLAG )
                /*
                        -----------------------
                        Add this Person to the
                        Return as a Dependent
                        -----------------------
                */
                IF( DFLAG = 1 )THEN
                        DO;
                                %ADDEPT( JX , NUNITS )
                        END;
        END;
END;
%MEND SEARCH1 ;

%MACRO SEARCH2 ;
/*
        ---------------------------------------
        PHASE II Search:

        PURPOSE - Search for Dependencies Among
        Tax Units. As a first approximation,
        attach the dependents to the tax unit
        with the highest income in the household.
        ---------------------------------------
*/
HIGHEST = -9.9E32 ;
idxHIGH = 0 ;
DO IX = 1 TO NUNITS;
        %TOTINCX( IX )
        INCOME = TOTINCX ;
        IF( INCOME GE HIGHEST )THEN
                DO;
                        HIGHEST = INCOME ;
                        idxHIGH = IX ;
                END;
END;
/*
        --------------------------------------
        Check non-dependent tax units other than
        the highest income return and check for
        dependencies. It's possible that the
        highest income return could be a dependent
        filer. In that case, just skip this
        step.

        At this stage, let's not allow joint
        returns to become dependent filers since
        we seem to be OK here.
        --------------------------------------
*/
IF( TREC(idxHIGH , 2) NE 1)THEN
DO IX = 1 TO NUNITS;
        idxJS   = TREC(IX ,  1) ;
        idxDEPF = TREC(IX ,  2) ;
        idxRELC = TREC(IX , 39) ;
        idxFAMT = TREC(IX , 40) ;
        IF( (IX NE idxHIGH) AND (idxDEPF NE 1) AND (HIGHEST GT 0.0)
            AND (idxJS NE 2) )THEN
                DO;
                SELECT;
                        WHEN( (idxFAMT = 1) OR (idxFAMT = 3) OR (idxFAMT =5) )
                                DO;
                                        %TOTINCX( IX )
                                        INCOME = TOTINCX ;
                                        IF( INCOME LE 0.0 )THEN
                                                DO;
                                                        %COMBINE( IX , idxHIGH )
                                                END;
                                        IF( (INCOME GT 0.0) AND (INCOME LE 3000.) )THEN
                                                DO;
                                                        %CONVERT( IX , idxHIGH )
                                                END;
                                END;
                        WHEN( idxRELC = 11 )
                                DO;
                                        %COMBINE( IX , idxHIGH )
                                END;
                        OTHERWISE;
                END;
                END;
END;
%MEND SEARCH2 ;

%MACRO CONVERT(IX , IY) ;
/*
        -----------------------------------------
        PURPOSE - Convert an existing tax unit (IX)
        to a dependent filer and add the dependent
        information to the target return (IY).
        -----------------------------------------
*/
TREC(&IX , 2) = 1 ;
IXDEPS = TREC(&IX , 4) ;
IYDEPS = TREC(&IY , 4) ;
TREC(&IX , 4) = 0;         /* Dependents can't have dependents. */
IXJS = TREC(&IX , 1) ;
IYBEGIN = 20 + IYDEPS ;
IF( IXJS = 2 )THEN
        DO;
                TREC(&IY , 4) = TREC(&IY , 4) + IXDEPS + 2 ;
                TREC(&IY , IYBEGIN + 1) = TREC(&IX , 37) ;
                TREC(&IY , IYBEGIN + 2) = TREC(&IX , 38) ;
                IYBEGIN = 20 + IYDEPS + 2 ;
        END;
ELSE
        DO;
                TREC(&IY , 4) = TREC(&IY , 4) + IXDEPS + 1 ;
                TREC(&IY , IYBEGIN + 1) = TREC(&IX , 37) ;
                IYBEGIN = 20 + IYDEPS + 1 ;
        END;
IF( IXDEPS GT 0 )THEN
        DO NDEPS = 1 TO IXDEPS ;
                TREC(&IY , IYBEGIN + NDEPS) = TREC(&IX , 20 + NDEPS) ;
                TREC(&IX , 20 + NDEPS) = 0.0 ;
        END;

/* Add age info */
TREC(&IY, 276) = TREC(&IY, 276) + TREC(&IX, 276);
TREC(&IY, 277) = TREC(&IY, 277) + TREC(&IX, 277);
TREC(&IY, 278) = TREC(&IY, 278) + TREC(&IX, 278);
%MEND CONVERT ;

%MACRO COMBINE(IX , IY) ;
/*
        -----------------------------------------
        PURPOSE - Combine an existing tax unit (IX)
        with another return (IY) making all members
        of IX dependents of IY.
        -----------------------------------------
*/

TREC(&IX , 19) = 0.0 ;  /* No Longer a Tax Unit */
%CONVERT(&IX , &IY)

%MEND COMBINE ;

%MACRO IFDEPT( PERSON , DFLAG ) ;
/*
        --------------------------------------
        Purpose: Determine if Individual is a
                 Dependent of the reference
                 person.

        In general, five tests must be met in
        order for an individual to a dependent.
        They are:

                1. Relationship
                2. Marital Status
                3. Citizenship
                4. Income
                5. Support

        To the extent supported by CPS data,
        all five tests must be passed for an
        individual to be a dependent.
        --------------------------------------
*/
/*
        Initialize: All Tests FALSE
*/
TEST1 = 0.0 ;
TEST2 = 0.0 ;
TEST3 = 0.0 ;
TEST4 = 0.0 ;
TEST5 = 0.0 ;
&DFLAG = 0.0 ;
AGE = PREC(&PERSON , 12) ;
INCOME = PREC(&PERSON , 20) + PREC(&PERSON , 21) + PREC(&PERSON , 22)
       + PREC(&PERSON , 23) + PREC(&PERSON , 24) + PREC(&PERSON , 25)
       + PREC(&PERSON , 26) + PREC(&PERSON , 27) + PREC(&PERSON , 28)
       + PREC(&PERSON , 29) ;
/*
        ----------------------------------------------------------
        Test #1: Relationship Test. Since at this
                 phase of the program, we are only
                 looking within families (or related
                 subfamilies) this test is passed.
        ----------------------------------------------------------
*/
TEST1 = 1.0 ;
/*
        ----------------------------------------------------------
        Test #2: Marital Status. In general, married individuals
                 filing a joint return cannot be dependents unless
                 they file a return to receive a refund. Again,
                 since we are looking at families, no married
                 couples will be tested.
        ----------------------------------------------------------
*/
TEST2 = 1.0 ;
/*
        ----------------------------------------------------------
        Test #3. Citizen Test. Assume this is always met.
        ----------------------------------------------------------
*/
TEST3 = 1.0 ;
/*
        ----------------------------------------------------------
        Test #4. Income Test. In general, a person's income must
                 be less than $2,500 to be eligible to be a
                 dependent. But there are exceptions for children.
        ----------------------------------------------------------
*/
IF( INCOME LE 2500. )THEN TEST4 = 1.0 ;
%RELATION( RELATED )
IF( (RELCODE = 5) OR (RELATED = -1) )THEN
        DO;
                IF( (AGE LE 18) )THEN TEST4 = 1.0 ;
                IF( (AGE LE 23) AND (A_ENRLW GT 0.0) )THEN TEST4 = 1.0 ;
        END;
/*
        -----------------------------------------------------------
        Test #5. Support Test. General rule is that you must provide
                 more than half of the support of the individual in
                 order to qualify as a dependent.
        -----------------------------------------------------------
*/
%TOTINCX( NUNITS )
IF( ( (TOTINCX+INCOME) GT 0.0) )THEN
        DO;
                IF( (INCOME / (TOTINCX+INCOME) ) LT .50 )THEN TEST5 = 1.0 ;
        END;
ELSE
        TEST5 = 1.0;
DTEST = TEST1 + TEST2 + TEST3 + TEST4 + TEST5 ;
IF( DTEST = 5.0 )THEN &DFLAG = 1.0 ;

%MEND IFDEPT ;

%MACRO RELATION( RELATED ) ;
/*
        -------------------------------------------
        Relationship among related subfamilies
        -------------------------------------------
*/
&RELATED = 99;
RELIX = PREC(IX , 38);
RELJX = PREC(JX , 38);
/*
        Offset for Reference Person
*/
SELECT;
        WHEN( RELIX = 5 )GENIX = -1;
        WHEN( RELIX = 7 )GENIX = -2;
        WHEN( RELIX = 8 )GENIX =  1;
        WHEN( RELIX = 9 )GENIX =  0;
        WHEN( RELIX = 11)GENIX = -1;
        OTHERWISE GENIX = 99;
END;
/*
        Offset for Index Person
*/
SELECT;
        WHEN( RELJX = 5 )GENJX = -1;
        WHEN( RELJX = 7 )GENJX = -2;
        WHEN( RELJX = 8 )GENJX =  1;
        WHEN( RELJX = 9 )GENJX =  0;
        WHEN( RELJX = 11)GENJX = -1;
        OTHERWISE GENJX = 99;
END;
/*
        Child Flag
*/
IF( (GENIX NE 99) AND (GENJX NE 99) )THEN
        DO;
                &RELATED = GENJX - GENIX ;
        END;

%MEND RELATION ;

%MACRO MUSTFILE( PERSON , DEPFILE ) ;

/*
        -------------------------------------------
        Determine if a Dependent Must File a Return

        Note that since we are processing families,
        we only need to check reference person and
        not a spouse.
        -------------------------------------------
*/
&DEPFILE = 0.0 ;
WAGES = PREC(&PERSON , 20) ;
INCOME = PREC(&PERSON , 20) + PREC(&PERSON , 21) + PREC(&PERSON , 22)
       + PREC(&PERSON , 23) + PREC(&PERSON , 24) + PREC(&PERSON , 25)
       + PREC(&PERSON , 26) + PREC(&PERSON , 27) + PREC(&PERSON , 28)
       + PREC(&PERSON , 29) ;
IF( (WAGES  GT DEPWAGES) )THEN &DEPFILE = 1.0 ;
IF( (INCOME GT DEPTOTAL) )THEN &DEPFILE = 1.0 ;

%MEND MUSTFILE ;

%MACRO ADDEPT( PERSON , RETURN ) ;
/*
        ---------------------------------------
        Adds a dependent to the current Tax Unit
        ---------------------------------------
*/
PREC(&PERSON , 32) = 1.0 ;
TREC(&RETURN ,  4) = TREC(&RETURN ,  4) + 1.0 ;
DEPNE = TREC(&RETURN , 4) ;
DAGE = PREC(&PERSON , 12) ;
TREC(&RETURN , 20 + DEPNE) = &PERSON ;
TREC(&RETURN , 66 + DEPNE) = DAGE ;
TREC(&RETURN , 280 + DEPNE) = PREC(&PERSON , 120); * SSI Imputed value;
TREC(&RETURN , 295 + DEPNE) = PREC(&PERSON , 121); * SSI participation probability;
TREC(&RETURN , 309) = TREC(&RETURN , 309) + PREC(&PERSON , 120); * Total SSI;
TREC(&RETURN , 310) = TREC(&RETURN , 310) + PREC(&PERSON , 122); * Total VB;
TREC(&RETURN , 312) = TREC(&RETURN , 312) + PREC(&PERSON , 124); * Total Medicare;
TREC(&RETURN , 313) = TREC(&RETURN , 313) + PREC(&PERSON , 125); * Total Medicaid;
TREC(&RETURN , 314) = TREC(&RETURN , 314) + PREC(&PERSON , 126); * Total Social Security;
TREC(&RETURN , 316 + DEPNE) = PREC(&PERSON, 128); * SNAP probability;
* TREC(&RETURN , 331 + DEPNE) = PREC(&PERSON, 123); * SNAP value;
TREC(&RETURN , 346 + DEPNE) = PREC(&PERSON, 127); * SS probability;
TREC(&RETURN , 361 + DEPNE) = PREC(&PERSON, 126); * SS value;
TREC(&RETURN , 376 + DEPNE) = PREC(&PERSON, 129); * VB probability;
TREC(&RETURN , 391 + DEPNE) = PREC(&PERSON, 122); * VB imputed value;
TREC(&RETURN , 406 + DEPNE) = PREC(&PERSON, 130); * Medicare probability;
TREC(&RETURN , 421 + DEPNE) = PREC(&PERSON, 124); * Medicare imputed value;
TREC(&RETURN , 436 + DEPNE) = PREC(&PERSON, 131); * Medicaid probability;
TREC(&RETURN , 451 + DEPNE) = PREC(&PERSON, 125); * Medicadi imputed value;

TREC(&RETURN , 468 + DEPNE) = PREC(&PERSON, 133); * TANF value;
TREC(&RETURN , 482) = TREC(&RETURN , 482) + PREC(&PERSON, 133);
TREC(&RETURN , 484 + DEPNE) = PREC(&PERSON, 134); * TANF probability;
TREC(&RETURN , 499 + DEPNE) = PREC(&PERSON, 135); * UI value;
TREC(&RETURN , 513) = TREC(&RETURN , 513) + PREC(&PERSON, 135);
TREC(&RETURN , 515 + DEPNE) = PREC(&PERSON, 136); * UI probability;
* comment out because housing is by family;
* TREC(&RETURN , 530 + DEPNE) = PREC(&PERSON, 137); * Housing value;
* TREC(&RETURN , 544) = TREC(&RETURN , 544) + PREC(&PERSON, 137);
TREC(&RETURN , 546 + DEPNE) = PREC(&PERSON, 138); * Housing probability;
TREC(&RETURN , 561 + DEPNE) = PREC(&PERSON, 139); * WIC value;
TREC(&RETURN , 575) = TREC(&RETURN , 575) + PREC(&PERSON , 139);
TREC(&RETURN , 577 + DEPNE) = PREC(&PERSON, 140); * WIC probability;

/* Add dependent age info */
IF (PREC(&PERSON, 12) < 18 AND PREC(&PERSON, 12) > 0) THEN
    TREC(&RETURN, 276) = TREC(&RETURN, 276) + 1;
ELSE IF (PREC(&PERSON, 12) >= 18 AND PREC(&PERSON, 12) < 21) THEN
    TREC(&RETURN, 277) = TREC(&RETURN, 277) + 1;
ELSE IF (PREC(&PERSON, 12) >= 21) THEN
    TREC(&RETURN, 278) = TREC(&RETURN, 278) + 1;
%MEND ADDEPT ;

%MACRO OUTPUT ;
/*
        ---------------------------------------
        Output CPS Tax Units for This Household
        ---------------------------------------
*/
DO N = 1 TO NUNITS ;
        IF( (TREC(N , 19) = 1.0) )THEN
                DO;
                        JS = TREC(N ,  1) ;
                    IFDEPT = TREC(N ,  2) ;
                     AGEDE = TREC(N ,  3) ;
                     DEPNE = TREC(N ,  4) ;
                      CAHE = TREC(N ,  5) ;
                      AGEH = TREC(N ,  6) ;
                      AGES = TREC(N ,  7) ;
                       WAS = TREC(N ,  8) ;
                     INTST = TREC(N ,  9) ;
                       DBE = TREC(N , 10) ;
                   ALIMONY = TREC(N , 11) ;
                       BIL = TREC(N , 12) ;
                  PENSIONS = TREC(N , 13) ;
                     RENTS = TREC(N , 14) ;
                       FIL = TREC(N , 15) ;
                     UCOMP = TREC(N , 16) ;
                    SOCSEC = TREC(N , 17) ;
                             %TOTINCX( N )
                    INCOME = TOTINCX ;
                   RETURNS = TREC(N , 19) ;
                        WT = TREC(N , 20) ;
                    ZIFDEP = TREC(N ,  2) ;
                    ZNTDEP = TREC(N , 42) ;
                    ZHHINC = TREC(N , 43) ;
                    ZAGEPT = TREC(N , 44) ;
                    ZAGESP = TREC(N , 45) ;
                    ZOLDES = TREC(N , 46) ;
                    ZYOUNG = TREC(N , 47) ;
                    ZWORKC = TREC(N , 48) ;
                    ZSOCSE = TREC(N , 49) ;
                    ZSSINC = TREC(N , 50) ;
                    ZPUBAS = TREC(N , 51) ;
                    ZVETBE = TREC(N , 52) ;
                    ZCHSUP = TREC(N , 53) ;
                    ZFINAS = TREC(N , 54) ;
                    ZDEPIN = TREC(N , 55) ;
                    ZOWNER = TREC(N , 56) ;
                    ZWASPT = TREC(N , 57) ;
                    ZWASSP = TREC(N , 58) ;
                      WASP = TREC(N , 65) ;
                      WASS = TREC(N , 66) ;
					  /* Age fields */
					  NU18 = TREC(N , 276);
					 N1821 = TREC(N , 277);
					   N21 = TREC(N , 278);
					   /* SSI imputation variables*/
					   SSI_VAL1 = TREC(N , 279);
					   SSI_VAL2 = TREC(N , 280);
					   SSI_VAL3 = TREC(N , 281);
					   SSI_VAL4 = TREC(N , 282);
					   SSI_VAL5 = TREC(N , 283);
					   SSI_VAL6 = TREC(N , 284);
					   SSI_VAL7 = TREC(N , 285);
					   SSI_VAL8 = TREC(N , 286);
					   SSI_VAL9 = TREC(N , 287);
					  SSI_VAL10 = TREC(N , 288);
					  SSI_VAL11 = TREC(N , 289);
					  SSI_VAL12 = TREC(N , 290);
					  SSI_VAL13 = TREC(N , 291);
					  SSI_VAL14 = TREC(N , 292);
					  SSI_VAL15 = TREC(N , 293);
					  SSI_PROB1 = TREC(N , 294);
					  SSI_PROB2 = TREC(N , 295);
					  SSI_PROB3 = TREC(N , 296);
					  SSI_PROB4 = TREC(N , 297);
					  SSI_PROB5 = TREC(N , 298);
					  SSI_PROB6 = TREC(N , 299);
					  SSI_PROB7 = TREC(N , 300);
					  SSI_PROB8 = TREC(N , 301);
					  SSI_PROB9 = TREC(N , 302);
					 SSI_PROB10 = TREC(N , 303);
					 SSI_PROB11 = TREC(N , 304);
					 SSI_PROB12 = TREC(N , 305);
					 SSI_PROB13 = TREC(N , 306);
					 SSI_PROB14 = TREC(N , 307);
					 SSI_PROB15 = TREC(N , 308);
					 SSI = TREC(N , 309);
					 VB = TREC(N , 310);
					 SNAP = TREC(N , 311);
					 MEDICARE = TREC(N , 312);
					 MEDICAID = TREC(N , 313);
					 SS = TREC(N , 314);
					 SNAP_PROB1 = TREC(N, 315);
					 SNAP_PROB2 = TREC(N, 316);
					 SNAP_PROB3 = TREC(N, 317);
					 SNAP_PROB4 = TREC(N, 318);
					 SNAP_PROB5 = TREC(N, 319);
					 SNAP_PROB6 = TREC(N, 320);
					 SNAP_PROB7 = TREC(N, 321);
					 SNAP_PROB8 = TREC(N, 322);
					 SNAP_PROB9 = TREC(N, 323);
					SNAP_PROB10 = TREC(N, 324);
					SNAP_PROB11 = TREC(N, 325);
					SNAP_PROB12 = TREC(N, 326);
					SNAP_PROB13 = TREC(N, 327);
					SNAP_PROB14 = TREC(N, 328);
					SNAP_PROB15 = TREC(N, 329);
					  SNAP_VAL1 = TREC(N, 330);
					  SNAP_VAL2 = TREC(N, 331);
					  SNAP_VAL3 = TREC(N, 332);
					  SNAP_VAL4 = TREC(N, 333);
					  SNAP_VAL5 = TREC(N, 334);
					  SNAP_VAL6 = TREC(N, 335);
					  SNAP_VAL7 = TREC(N, 336);
					  SNAP_VAL8 = TREC(N, 337);
					  SNAP_VAL9 = TREC(N, 338);
				     SNAP_VAL10 = TREC(N, 339);
					 SNAP_VAL11 = TREC(N, 340);
					 SNAP_VAL12 = TREC(N, 341);
					 SNAP_VAL13 = TREC(N, 342);
					 SNAP_VAL14 = TREC(N, 343);
					 SNAP_VAL15 = TREC(N, 344);
					   SS_PROB1 = TREC(N, 345);
					   SS_PROB2 = TREC(N, 346);
					   SS_PROB3 = TREC(N, 347);
					   SS_PROB4 = TREC(N, 348);
					   SS_PROB5 = TREC(N, 349);
					   SS_PROB6 = TREC(N, 350);
					   SS_PROB7 = TREC(N, 351);
					   SS_PROB8 = TREC(N, 352);
					   SS_PROB9 = TREC(N, 353);
					  SS_PROB10 = TREC(N, 354);
					  SS_PROB11 = TREC(N, 355);
					  SS_PROB12 = TREC(N, 356);
					  SS_PROB13 = TREC(N, 357);
					  SS_PROB14 = TREC(N, 358);
					  SS_PROB15 = TREC(N, 359);
					    SS_VAL1 = TREC(N, 360);
						SS_VAL2 = TREC(N, 361);
						SS_VAL3 = TREC(N, 362);
						SS_VAL4 = TREC(N, 363);
						SS_VAL5 = TREC(N, 364);
						SS_VAL6 = TREC(N, 365);
						SS_VAL7 = TREC(N, 366);
						SS_VAL8 = TREC(N, 367);
						SS_VAL9 = TREC(N, 368);
					   SS_VAL10 = TREC(N, 369);
					   SS_VAL11 = TREC(N, 370);
					   SS_VAL12 = TREC(N, 371);
					   SS_VAL13 = TREC(N, 372);
					   SS_VAL14 = TREC(N, 373);
					   SS_VAL15 = TREC(N, 374);

					   VB_PROB1 = TREC(N, 375);
 					   VB_PROB2 = TREC(N, 376);
 					   VB_PROB3 = TREC(N, 377);
 					   VB_PROB4 = TREC(N, 378);
 					   VB_PROB5 = TREC(N, 379);
 					   VB_PROB6 = TREC(N, 380);
 					   VB_PROB7 = TREC(N, 381);
 					   VB_PROB8 = TREC(N, 382);
 					   VB_PROB9 = TREC(N, 383);
 					  VB_PROB10 = TREC(N, 384);
 					  VB_PROB11 = TREC(N, 385);
 					  VB_PROB12 = TREC(N, 386);
 					  VB_PROB13 = TREC(N, 387);
 					  VB_PROB14 = TREC(N, 388);
 					  VB_PROB15 = TREC(N, 389);
 					    VB_VAL1 = TREC(N, 390);
 						VB_VAL2 = TREC(N, 391);
 						VB_VAL3 = TREC(N, 392);
 						VB_VAL4 = TREC(N, 393);
 						VB_VAL5 = TREC(N, 394);
 						VB_VAL6 = TREC(N, 395);
 						VB_VAL7 = TREC(N, 396);
 						VB_VAL8 = TREC(N, 397);
 						VB_VAL9 = TREC(N, 398);
 					   VB_VAL10 = TREC(N, 399);
 					   VB_VAL11 = TREC(N, 400);
 					   VB_VAL12 = TREC(N, 401);
 					   VB_VAL13 = TREC(N, 402);
 					   VB_VAL14 = TREC(N, 403);
 					   VB_VAL15 = TREC(N, 404);

					   MCARE_PROB1 = TREC(N, 405);
 					   MCARE_PROB2 = TREC(N, 406);
 					   MCARE_PROB3 = TREC(N, 407);
 					   MCARE_PROB4 = TREC(N, 408);
 					   MCARE_PROB5 = TREC(N, 409);
 					   MCARE_PROB6 = TREC(N, 410);
 					   MCARE_PROB7 = TREC(N, 411);
 					   MCARE_PROB8 = TREC(N, 412);
 					   MCARE_PROB9 = TREC(N, 413);
 					  MCARE_PROB10 = TREC(N, 414);
 					  MCARE_PROB11 = TREC(N, 415);
 					  MCARE_PROB12 = TREC(N, 416);
 					  MCARE_PROB13 = TREC(N, 417);
 					  MCARE_PROB14 = TREC(N, 418);
 					  MCARE_PROB15 = TREC(N, 419);
 					    MCARE_VAL1 = TREC(N, 420);
 						MCARE_VAL2 = TREC(N, 421);
 						MCARE_VAL3 = TREC(N, 422);
 						MCARE_VAL4 = TREC(N, 423);
 						MCARE_VAL5 = TREC(N, 424);
 						MCARE_VAL6 = TREC(N, 425);
 						MCARE_VAL7 = TREC(N, 426);
 						MCARE_VAL8 = TREC(N, 427);
 						MCARE_VAL9 = TREC(N, 428);
 					   MCARE_VAL10 = TREC(N, 429);
 					   MCARE_VAL11 = TREC(N, 430);
 					   MCARE_VAL12 = TREC(N, 431);
 					   MCARE_VAL13 = TREC(N, 432);
 					   MCARE_VAL14 = TREC(N, 433);
 					   MCARE_VAL15 = TREC(N, 434);

					   MCAID_PROB1 = TREC(N, 435);
 					   MCAID_PROB2 = TREC(N, 436);
 					   MCAID_PROB3 = TREC(N, 437);
 					   MCAID_PROB4 = TREC(N, 438);
 					   MCAID_PROB5 = TREC(N, 439);
 					   MCAID_PROB6 = TREC(N, 440);
 					   MCAID_PROB7 = TREC(N, 441);
 					   MCAID_PROB8 = TREC(N, 442);
 					   MCAID_PROB9 = TREC(N, 443);
 					  MCAID_PROB10 = TREC(N, 444);
 					  MCAID_PROB11 = TREC(N, 445);
 					  MCAID_PROB12 = TREC(N, 446);
 					  MCAID_PROB13 = TREC(N, 447);
 					  MCAID_PROB14 = TREC(N, 448);
 					  MCAID_PROB15 = TREC(N, 449);
 					    MCAID_VAL1 = TREC(N, 450);
 						MCAID_VAL2 = TREC(N, 451);
 						MCAID_VAL3 = TREC(N, 452);
 						MCAID_VAL4 = TREC(N, 453);
 						MCAID_VAL5 = TREC(N, 454);
 						MCAID_VAL6 = TREC(N, 455);
 						MCAID_VAL7 = TREC(N, 456);
 						MCAID_VAL8 = TREC(N, 457);
 						MCAID_VAL9 = TREC(N, 458);
 					   MCAID_VAL10 = TREC(N, 459);
 					   MCAID_VAL11 = TREC(N, 460);
 					   MCAID_VAL12 = TREC(N, 461);
 					   MCAID_VAL13 = TREC(N, 462);
 					   MCAID_VAL14 = TREC(N, 463);
 					   MCAID_VAL15 = TREC(N, 464);

					   TANF = TREC(N, 482);
					   TANF_VAL1 = TREC(N, 467);
					   TANF_VAL2 = TREC(N, 468);
					   TANF_VAL3 = TREC(N, 469);
					   TANF_VAL4 = TREC(N, 470);
					   TANF_VAL5 = TREC(N, 471);
					   TANF_VAL6 = TREC(N, 472);
					   TANF_VAL7 = TREC(N, 473);
					   TANF_VAL8 = TREC(N, 474);
					   TANF_VAL9 = TREC(N, 475);
					   TANF_VAL10 = TREC(N, 476);
					   TANF_VAL11 = TREC(N, 477);
					   TANF_VAL12 = TREC(N, 478);
					   TANF_VAL13 = TREC(N, 479);
					   TANF_VAL14 = TREC(N, 480);
					   TANF_VAL15 = TREC(N, 481);
					   TANF_PROB1 = TREC(N, 483);
					   TANF_PROB2 = TREC(N, 484);
					   TANF_PROB3 = TREC(N, 485);
					   TANF_PROB4 = TREC(N, 486);
					   TANF_PROB5 = TREC(N, 487);
					   TANF_PROB6 = TREC(N, 488);
					   TANF_PROB7 = TREC(N, 489);
					   TANF_PROB8 = TREC(N ,490);
					   TANF_PROB9 = TREC(N, 491);
					   TANF_PROB10 = TREC(N, 492);
					   TANF_PROB11 = TREC(N, 493);
					   TANF_PROB12 = TREC(N, 494);
					   TANF_PROB13 = TREC(N, 495);
					   TANF_PROB14 = TREC(N, 496);
					   TANF_PROB15 = TREC(N, 497);

					   UI = TREC(N, 513);
					   UI_VAL1 = TREC(N, 498);
					   UI_VAL2 = TREC(N, 499);
					   UI_VAL3 = TREC(N, 500);
					   UI_VAL4 = TREC(N, 501);
					   UI_VAL5 = TREC(N, 502);
					   UI_VAL6 = TREC(N, 503);
					   UI_VAL7 = TREC(N, 504);
					   UI_VAL8 = TREC(N, 505);
					   UI_VAL9 = TREC(N, 506);
					   UI_VAL10 = TREC(N, 507);
					   UI_VAL11 = TREC(N, 508);
					   UI_VAL12 = TREC(N, 509);
					   UI_VAL13 = TREC(N, 510);
					   UI_VAL14 = TREC(N, 511);
					   UI_VAL15 = TREC(N, 512);
					   UI_PROB1 = TREC(N, 514);
					   UI_PROB2 = TREC(N, 515);
					   UI_PROB3 = TREC(N, 516);
					   UI_PROB4 = TREC(N, 517);
					   UI_PROB5 = TREC(N, 518);
					   UI_PROB6 = TREC(N, 519);
					   UI_PROB7 = TREC(N, 520);
					   UI_PROB8 = TREC(N, 521);
					   UI_PROB9 = TREC(N, 522);
					   UI_PROB10 = TREC(N, 523);
					   UI_PROB11 = TREC(N, 524);
					   UI_PROB12 = TREC(N, 525);
					   UI_PROB13 = TREC(N, 526);
					   UI_PROB14 = TREC(N, 527);
					   UI_PROB15 = TREC(N, 528);

					   HOUSING = TREC(N, 544);
					   HOUSING_VAL1 = TREC(N, 529);
					   HOUSING_VAL2 = TREC(N, 530);
					   HOUSING_VAL3 = TREC(N, 531);
					   HOUSING_VAL4 = TREC(N, 532);
					   HOUSING_VAL5 = TREC(N, 533);
					   HOUSING_VAL6 = TREC(N, 534);
					   HOUSING_VAL7 = TREC(N, 535);
					   HOUSING_VAL8 = TREC(N, 536);
					   HOUSING_VAL9 = TREC(N, 537);
					   HOUSING_VAL10 = TREC(N, 538);
					   HOUSING_VAL11 = TREC(N, 539);
					   HOUSING_VAL12 = TREC(N, 540);
					   HOUSING_VAL13 = TREC(N, 541);
					   HOUSING_VAL14 = TREC(N, 542);
					   HOUSING_VAL15 = TREC(N, 543);
					   HOUSING_PROB1 = TREC(N, 545);
					   HOUSING_PROB2 = TREC(N, 546);
					   HOUSING_PROB3 = TREC(N, 547);
					   HOUSING_PROB4 = TREC(N, 548);
					   HOUSING_PROB5 = TREC(N, 549);
					   HOUSING_PROB6 = TREC(N, 550);
					   HOUSING_PROB7 = TREC(N, 551);
					   HOUSING_PROB8 = TREC(N, 552);
					   HOUSING_PROB9 = TREC(N, 553);
					   HOUSING_PROB10 = TREC(N, 554);
					   HOUSING_PROB11 = TREC(N, 555);
					   HOUSING_PROB12 = TREC(N, 556);
					   HOUSING_PROB13 = TREC(N, 557);
					   HOUSING_PROB14 = TREC(N, 558);
					   HOUSING_PROB15 = TREC(N, 559);

					   WIC = TREC(N, 575);
					   WIC_VAL1 = TREC(N, 560);
					   WIC_VAL2 = TREC(N, 561);
					   WIC_VAL3 = TREC(N, 562);
					   WIC_VAL4 = TREC(N, 563);
					   WIC_VAL5 = TREC(N, 564);
					   WIC_VAL6 = TREC(N, 565);
					   WIC_VAL7 = TREC(N, 566);
					   WIC_VAL8 = TREC(N, 567);
					   WIC_VAL9 = TREC(N, 568);
					   WIC_VAL10 = TREC(N, 569);
					   WIC_VAL11 = TREC(N, 570);
					   WIC_VAL12 = TREC(N, 571);
					   WIC_VAL13 = TREC(N, 572);
					   WIC_VAL14 = TREC(N, 573);
					   WIC_VAL15 = TREC(N, 574);
					   WIC_PROB1 = TREC(N, 576);
					   WIC_PROB2 = TREC(N, 577);
					   WIC_PROB3 = TREC(N, 578);
					   WIC_PROB4 = TREC(N, 579);
					   WIC_PROB5 = TREC(N, 580);
					   WIC_PROB6 = TREC(N, 581);
					   WIC_PROB7 = TREC(N, 582);
					   WIC_PROB8 = TREC(N, 583);
					   WIC_PROB9 = TREC(N, 584);
					   WIC_PROB10 = TREC(N, 585);
					   WIC_PROB11 = TREC(N, 586);
					   WIC_PROB12 = TREC(N, 587);
					   WIC_PROB13 = TREC(N, 588);
					   WIC_PROB14 = TREC(N, 589);
					   WIC_PROB15 = TREC(N, 590);

					   A_LINENO = TREC(N, 466);
/*
                   Additional Fields for Non-Filers
                   NOTE: Locations 83, 84 & 85 will
                         be set now.
*/
                   TXPYE = 1;IF( JS = 2 )THEN TXPYE = 2;
                   XXTOT   = TXPYE + DEPNE;
				   /* verify XTOT equals the sum of the UBI age variables */
				   EFLAG = 0;
				   NSUMS = NU18 + N1821 + N21;
				   IF (XXTOT NE NSUMS)THEN EFLAG = 1;
				   /* Reset variables if there is an error */
				   IF (EFLAG EQ 1)THEN
				       DO;
				           XXTOT = 1;
					       NU18 = 0;
					       N1821 = 0;
					       N21 = 0;
						   IF (AGEH < 18)THEN
                               NU18 = NU18 + 1;
                           ELSE IF (AGEH >= 18 AND AGEH < 21)THEN
                               N1821 = N1821 + 1;
                           ELSE IF (AGEH >= 21)THEN
                               N21 = N21 + 1;
						   /* Check spouse age */
						   IF (JS EQ 2)THEN
						       DO;
									XXTOT = XXTOT + 1;
									IF (AGES < 18)THEN
										NU18 = NU18 + 1;
									ELSE IF (AGES >= 18 AND AGES < 21)THEN
										N1821 = N1821 + 1;
									ELSE IF (AGES >= 21)THEN
										N21 = N21 + 1;
								END;
						END; 

/*
                   Check relationship codes among dependents
*/
                   XXOODEP = 0.0 ;
                   XXOPAR = 0.0 ;
                   XXOCAH = 0.0 ;
                   XXOCAWH = 0.0 ;
                   IF( (DEPNE) GT 0.0 )THEN
                        DO I = 1 TO DEPNE ;
                                PPTR = 20 + I ;
                                DINDEX = TREC(N , PPTR) ;
                                DREL = PREC(DINDEX , 38) ;
                                DAGE = PREC(DINDEX , 12) ;
                                IF( DREL = 8 )THEN XXOPAR = XXOPAR + 1;
                                IF( (DREL GE 9) AND (DAGE GE 18) )THEN XXOODEP = XXOODEP + 1;
                                IF( (DAGE LT 18) )THEN XXOCAH = XXOCAH + 1;
								/* Check ages for UBI */
								IF (EFLAG EQ 1)THEN
									DO;
										XXTOT = XXTOT + 1;
										IF (DAGE < 18)THEN
											NU18 = NU18 + 1;
										ELSE IF (DAGE >= 18 AND DAGE < 21)THEN
											N1821 = N1821 + 1;
										ELSE IF (DAGE >= 21)THEN
											N21 = N21 + 1;
									END;
                        END;
					/* XTOT and UBI age variable error check*/
					AGESUMS = NU18 + N1821 + N21;
					XTOTDIFF = XXTOT - AGESUMS;

                   XAGEX   = TREC(N , 86) ;
                   XSTATE  = TREC(N , 87) ;
                   XREGION = TREC(N , 88) ;
                   XSCHB   = TREC(N , 89) ;
                   XSCHF   = TREC(N , 90) ;
                   XSCHE   = TREC(N , 91) ;
                   XSCHC   = TREC(N , 92) ;
                   XHID    = TREC(N , 93) ;
                   XFID    = TREC(N , 94) ;
                   XPID    = TREC(N , 95) ;
				   XFHEADIDX = TREC(N, 465);
/*
                    Oldest & Youngest Dependents
*/
OLDEST = 0 ;
YOUNGEST = 0 ;
IF( (DEPNE) GT 0.0 )THEN
        DO;
                OLDEST = -9.9E16 ;
                YOUNGEST = 9.9E16 ;
                DO I = 1 TO DEPNE ;
                        DINDEX = 66 + I ;
                        DAGE = TREC(N , DINDEX) ;
                        IF( (DAGE GT OLDEST) )THEN OLDEST = DAGE;
                        IF( (DAGE LT YOUNGEST) )THEN YOUNGEST = DAGE;
                END;
                ZOLDES = OLDEST;
                ZYOUNG = YOUNGEST;
        END;
/*
        New CPS Variables: Added Feb-03.
*/
        ICPS01 = TREC(N , 101) ;
        ICPS02 = TREC(N , 102) ;
        D5 = MIN(DEPNE , 5) ;
        IF( D5 GT 0 )THEN
                DO I = 1 TO D5 ;
                        DINDEX = 66 + I ;
                        DAGE = TREC(N , DINDEX) ;
                        CINDEX = 102 + I ;
                        TREC(N , CINDEX) = DAGE ;
                        ICPS(2 + I) = DAGE ;
                END;
        ICPS08 = YOUNGEST;
        ICPS09 = OLDEST;
        ICPS10 = TREC(N , 110) ;
        ICPS11 = TREC(N , 111) ;
        ICPS12 = TREC(N , 112) ;
        ICPS13 = TREC(N , 113) ;
        ICPS14 = TREC(N , 114) ;
        ICPS15 = TREC(N , 115) ;
        ICPS16 = TREC(N , 116) ;
        ICPS17 = TREC(N , 117) ;
        ICPS18 = TREC(N , 118) ;
        ICPS19 = TREC(N , 119) ;
        ICPS20 = TREC(N , 120) ;
        ICPS21 = TREC(N , 121) ;
        ICPS22 = TREC(N , 122) ;
        ICPS23 = TREC(N , 123) ;
        ICPS24 = TREC(N , 124) ;
        ICPS25 = TREC(N , 125) ;
        ICPS26 = TREC(N , 126) ;
        ICPS27 = TREC(N , 127) ;
        ICPS28 = TREC(N , 128) ;
        ICPS29 = TREC(N , 129) ;
        ICPS30 = TREC(N , 130) ;
/*
		NEW CPS VARIABLES ADDED JULY 2009
*/
		ICPS31 = TREC(N , 131) ;
		ICPS32 = TREC(N , 132) ;
		ICPS33 = TREC(N , 133) ;
		ICPS34 = TREC(N , 134) ;
		ICPS35 = TREC(N , 135) ;
		ICPS36 = TREC(N , 136) ;
		ICPS37 = TREC(N , 137) ;
		ICPS38 = TREC(N , 138) ;
		ICPS39 = TREC(N , 139) ;
		ICPS40 = TREC(N , 140) ;
		ICPS41 = TREC(N , 141) ;
		ICPS42 = TREC(N , 142) ;
		ICPS43 = TREC(N , 143) ;
		ICPS44 = TREC(N , 144) ;
		ICPS45 = TREC(N , 145) ;
		ICPS46 = TREC(N , 146) ;
		ICPS47 = TREC(N , 147) ;
		ICPS48 = TREC(N , 148) ;
*****
		SHANE:	HERE I FILL-UP THE JCPS() ARRAY. THIS IS THE NEW
				ARRAY I CREATED TO STORE THE VARIABLES AND GIVE THEM NAMES.
				I NEED TO DO THIS BECAUSE I USE THE SAS KEEP STATEMENT
				TO SAVE THE VARIABLES I REALLY WANT. THIS IS JUST A CONVENIENT(?)
				DEVICE TO SAVE ME THE TROUBLE OF NAMING EVERYTHING. JFO.
*****;
		/*	PRIMARY TAXPAYER	*/
		JCPS1	=	TREC(N , 151);
		JCPS2	=	TREC(N , 152);
		JCPS3	=	TREC(N , 153);
		JCPS4	=	TREC(N , 154);
		JCPS5	=	TREC(N , 155);
		JCPS6	=	TREC(N , 156);
		JCPS7	=	TREC(N , 157);
		JCPS8	=	TREC(N , 158);
		JCPS9	=	TREC(N , 159);
		JCPS10	=	TREC(N , 160);
		/*	SPOUSE				*/
		JCPS11	=	TREC(N , 161);
		JCPS12	=	TREC(N , 162);
		JCPS13	=	TREC(N , 163);
		JCPS14	=	TREC(N , 164);
		JCPS15	=	TREC(N , 165);
		JCPS16	=	TREC(N , 166);
		JCPS17	=	TREC(N , 167);
		JCPS18	=	TREC(N , 168);
		JCPS19	=	TREC(N , 169);
		JCPS20	=	TREC(N , 170);
*****
		PEW DATABASE: VERSION 3.0
*****;
		/*	PRIMARY TAXPAYER	*/
		JCPS21	=	TREC(N , 171);
		JCPS22	=	TREC(N , 172);
		JCPS23	=	TREC(N , 173);
		JCPS24	=	TREC(N , 174);
		JCPS25	=	TREC(N , 175);
		JCPS26	=	TREC(N , 176);
		JCPS27	=	TREC(N , 177);
		JCPS28	=	TREC(N , 178);
		JCPS29	=	TREC(N , 179);
		JCPS30	=	TREC(N , 180);
		/*	SPOUSE				*/
		JCPS31	=	TREC(N , 181);
		JCPS32	=	TREC(N , 182);
		JCPS33	=	TREC(N , 183);
		JCPS34	=	TREC(N , 184);
		JCPS35	=	TREC(N , 185);
		JCPS36	=	TREC(N , 186);
		JCPS37	=	TREC(N , 187);
		JCPS38	=	TREC(N , 188);
		JCPS39	=	TREC(N , 189);
		JCPS40	=	TREC(N , 190);
*****
		PEW DATABASE: VERSION 4.0
*****;
		JCPS41	=	TREC(N , 191);
		JCPS42	=	TREC(N , 192);
		JCPS43	=	TREC(N , 193);
		JCPS44	=	TREC(N , 194);
		JCPS45	=	TREC(N , 195);
		JCPS46	=	TREC(N , 196);
		JCPS47	=	TREC(N , 197);
		JCPS48	=	TREC(N , 198);
		JCPS49	=	TREC(N , 199);
		JCPS50	=	TREC(N , 200);
		JCPS51	=	TREC(N , 201);
		JCPS52	=	TREC(N , 202);
		JCPS53	=	TREC(N , 203);
		JCPS54	=	TREC(N , 204);
		JCPS55	=	TREC(N , 205);
		JCPS56	=	TREC(N , 206);
		JCPS57	=	TREC(N , 207);
		JCPS58	=	TREC(N , 208);
		JCPS59	=	TREC(N , 209);
		JCPS60	=	TREC(N , 210);
		JCPS61	=	TREC(N , 211);
		JCPS62	=	TREC(N , 212);
		JCPS63	=	TREC(N , 213);
		JCPS64	=	TREC(N , 214);
		JCPS65	=	TREC(N , 215);
		JCPS66	=	TREC(N , 216);
		JCPS67	=	TREC(N , 217);
		JCPS68	=	TREC(N , 218);
		JCPS69	=	TREC(N , 216);
		JCPS70	=	TREC(N , 220);
		JCPS71	=	TREC(N , 221);
		JCPS72	=	TREC(N , 222);
		JCPS73	=	TREC(N , 223);
		JCPS74	=	TREC(N , 224);
		JCPS75	=	TREC(N , 225);
		JCPS76	=	TREC(N , 226);
*****
		NEW HEALTH INSURANCE VARIABLES ADDED 09-MAR-2016
		ADDITIONAL MEANS TESTED VARIABLES ADDED 24-MAY-2016
*****;
*****
	ANDERSON: SET UP THE JCPS(*) ARRAY
*****;
		IF( ( N = 1 ) AND ( IFDEPT = 0 ) )THEN
			DO;
				JCPS77 = TREC(N , 228);
				JCPS78 = TREC(N , 229);
				JCPS79 = TREC(N , 230);
				JCPS80 = TREC(N , 231);
				JCPS81 = TREC(N , 232);
				JCPS82 = TREC(N , 233);
				JCPS83 = TREC(N , 234);
				JCPS84 = TREC(N , 235);
			END;
*****
		NEW MEANS TESTED VARIABLES (PRINCIPLE TAXPAYER)
		ADDED 24-MAY-2016.
*****;
		JCPS85 = TREC(N , 236) ;
		JCPS86 = TREC(N , 237) ;
		JCPS87 = TREC(N , 238) ;
		JCPS88 = TREC(N , 239) ;
		JCPS89 = TREC(N , 240) ;
		*****
			NEW HEALTH INSURANCE VARIABLES
		*****;
		JCPS90 = TREC(N , 241);
		JCPS91 = TREC(N , 242);
		JCPS92 = TREC(N , 243);
		JCPS93 = TREC(N , 244);
		JCPS94 = TREC(N , 245);
		JCPS95 = TREC(N , 246);
		JCPS96 = TREC(N , 247);
		JCPS97 = TREC(N , 248);
		JCPS98 = TREC(N , 249);
		JCPS99 = TREC(N , 250);
		*****
			OTHER VARIABLES
		*****;
		JCPS100 = TREC(N , 251);
		JCPS101 = TREC(N , 252);
		JCPS102 = TREC(N , 253);
		JCPS103 = TREC(N , 254);
		JCPS104 = TREC(N , 255);
*****
		NEW MEANS TESTED VARIABLES (SPOUSE)
		ADDED 24-MAY-2016.
*****;
		JCPS105 = TREC(N , 256) ;
		JCPS106 = TREC(N , 257) ;
		JCPS107 = TREC(N , 258) ;
		JCPS108 = TREC(N , 259) ;
		JCPS109 = TREC(N , 260) ;
		*****
			NEW HEALTH INSURANCE VARIABLES
		*****;
		JCPS110 = TREC(N , 261);
		JCPS111 = TREC(N , 262);
		JCPS112 = TREC(N , 263);
		JCPS113 = TREC(N , 264);
		JCPS114 = TREC(N , 265);
		JCPS115 = TREC(N , 266);
		JCPS116 = TREC(N , 267);
		JCPS117 = TREC(N , 268);
		JCPS118 = TREC(N , 269);
		JCPS119 = TREC(N , 270);
		*****
			OTHER VARIABLES
		*****;
		JCPS120 = TREC(N , 271);
		JCPS121 = TREC(N , 272);
		JCPS122 = TREC(N , 273);
		JCPS123 = TREC(N , 274);
		JCPS124 = TREC(N , 275);
/*
        Dependent Income
*/
ZDEPIN = 0.0 ;
IF( DEPNE GT 0.0 )THEN
        DO I = 1 TO DEPNE;
                PPTR = 20 + I ;
                DINDEX = TREC(N , PPTR) ;
                IF( PREC(DINDEX , 55) = 0.0 )THEN
                        DO;
                                ZDEPIN = ZDEPIN +
                                PREC(DINDEX , 20) + PREC(DINDEX , 21) + PREC(DINDEX , 22)
                              + PREC(DINDEX , 23) + PREC(DINDEX , 24) + PREC(DINDEX , 25)
                              + PREC(DINDEX , 26) + PREC(DINDEX , 27) + PREC(DINDEX , 28)
                              + PREC(DINDEX , 29) ;
                        END;
        END;
                        %FILST

						/*	MARRIED, JOINT RETURNS. 	*/

						IF( JS EQ 2 )THEN
							DO;
								OUTPUT EXTRACT.CPSRETS&CPSYEAR;
							END;

						/*	SINGLE RETURNS.				*/

						IF( JS EQ 1 )THEN
							DO;
								OUTPUT EXTRACT.CPSRETS&CPSYEAR;
							END;

						/*	HEAD OF HOUSEHOLD RETURNS.	*/

							IF( JS EQ 3 )THEN
							DO;
								OUTPUT EXTRACT.CPSRETS&CPSYEAR;
							END;
        END;
END;
%MEND OUTPUT ;


%MACRO TOTINCX( RETURN ) ;
/*
        -------------------------
        Total Income for Tax Unit
        -------------------------
*/
TOTINCX = TREC(&RETURN ,  8) + TREC(&RETURN ,  9) + TREC(&RETURN , 10)
        + TREC(&RETURN , 11) + TREC(&RETURN , 12) + TREC(&RETURN , 13)
        + TREC(&RETURN , 14) + TREC(&RETURN , 15) + TREC(&RETURN , 16)
        + TREC(&RETURN , 17) ;

%MEND TOTINCX ;

%MACRO FILST ;
/*
        -----------------------------------------------------------------------
        Filer/Non-Filer Test -  This macro checks to see whether a CPS tax unit
                                actually files a tax return, since this is the
                                population we are trying to create in order to
                                align with the SOI. If we decide that that a
                                CPS tax unit will actually file a return, then
                                a tax return is flagged to appear in the output
                                dataset (FILST = 1). Otherwise, the unit is
                                omitted from the final file.

                                Three tests are performed to determine if a CPS
                                tax unit files a return:

                                        (1) Wage test. If anyone in the tax unit
                                            (head or spouse) has wage and salary
                                            income, the unit is deemed to have
                                            file a return. While this is not a
                                            technically accurate representation
                                            of the law, experience has shown that
                                            it works quite well in the CPS world.

                                        (2) Gross Income Test. The income thresh-
                                            olds in the "Filing Requirements"
                                            section of the Form 1040 Instructions
                                            are used to determine if a CPS tax
                                            unit is required to file a tax return.
                                            Due to underreporting of income, it is
                                            likely that this will be too stringent
                                            a test (but mitigated somewhat by the
                                            Wage test). To assist in the targetting
                                            of SOI return totals, an adjustment
                                            (DELTA) is allowed to the gross income
                                            test thresholds for each filing status.

                                        (3) Dependent Filer Test. Individuals who are
                                            claimed a dependents on another tax
                                            return but who are required to file a
                                            return.

                                        (4) Random selection. If necessary, CPS
                                            tax units can be randomly selected to
                                            file a tax return. (Not enforced at
                                            this time.)
        -----------------------------------------------------------------------
*/
FILST = 0.0 ;
/*
        Test 1. - Wage Test
*/
SELECT;
        WHEN ( JS = 1 )
                DO;
                        IF( WAS GE WAGE1 )THEN FILST = 1 ;
                END;
        WHEN ( JS = 2 )	/*	Note: Different Test for Dependents	*/
                DO;
					IF( DEPNE GT 0.) THEN
						DO;
                        	IF( WAS GE WAGE2 )THEN FILST = 1 ;
						END;
					ELSE
						DO;
							IF( WAS GE WAGE2NK )THEN FILST = 1;
						END;
                END;
        WHEN ( JS = 3 )
                DO;
                        IF( WAS GE WAGE3 )THEN FILST = 1 ;
                END;
END;
/*
        Test 2. - Gross Income Test
*/
INCOME = WAS + INTST + DBE + ALIMONY + BIL + PENSIONS
       + RENTS + FIL + UCOMP  ;
SELECT;
        WHEN ( JS = 1 ) /* Single Returns    */
                DO;
                        AMOUNT = (GROSS1N + DELTA1N - DEPEX1 * DEPNE) ;
                        IF( AGEDE NE 0 )THEN AMOUNT = (GROSS1A + DELTA1A - DEPEX1 * DEPNE) ;
                        IF( INCOME GE AMOUNT )THEN FILST = 1 ;
                END;
        WHEN ( JS = 2 ) /* Joint Returns     */
                DO;
                        AMOUNT = (GROSS2N0 + DELTA2N0 - DEPEX2 * DEPNE) ;
                        IF( AGEDE = 1 )THEN AMOUNT = (GROSS2A1 + DELTA2A1 - DEPEX2 * DEPNE) ;
                        IF( AGEDE = 2 )THEN AMOUNT = (GROSS2A2 + DELTA2A2 - DEPEX2 * DEPNE) ;
                        IF( INCOME GE AMOUNT )THEN FILST = 1 ;
                END;
        WHEN ( JS = 3 ) /* Head of Household */
                DO;
                        AMOUNT = (GROSS3N + DELTA3N) ;
                        IF( AGEDE NE 0 )THEN AMOUNT = (GROSS3A + DELTA3A - DEPEX3 * DEPNE) ;
                        IF( INCOME GE AMOUNT )THEN FILST = 1 ;
                END;
        OTHERWISE
                DO;
                        PUT '*** ERROR IN FILING STATUS FLAG' ;
                        STOP;
                END;
END;
/*
        Test 3. - Dependent Filers
*/
IF( IFDEPT = 1 )THEN FILST = 1;
/*
        Test 4. - Random Selection
*/
IF(  (JS = 3) AND (AGEDE GT 0) AND (INCOME LT 6500.)
              AND (DEPNE GT 0) )THEN FILST = 0. ;
/*
		Test 5. - Negative Income
*/
IF( BIL LT 0.0 )THEN FILST = 1.;
IF( FIL LT 0.0 )THEN FILST = 1.;
IF( RENTS LT 0.0 )THEN FILST = 1.;
%MEND  FILST ;

%MACRO SETPARMS ;
/*
        ----------------------------
        2014 Filing Thresholds, Etc.

		NOTE: From 1040 Instructions
			  relating to "Who Has To
			  File?"
        ----------------------------
*/
/*
        Gross Income Test - Single
*/
GROSS1N = 10150. ; DELTA1N = 0.;
GROSS1A = 11700. ; DELTA1A = 0.;
/*
        Gross Income Test - Head of Household
*/
GROSS3N = 13050. ; DELTA3N = 0.;
GROSS3A = 14600. ; DELTA3A = 0.;
/*
        Gross Income Test - Joint
*/
GROSS2N0 = 20300. ; DELTA2N0 = 0.;
GROSS2A1 = 21500. ; DELTA2A1 = 0.;
GROSS2A2 = 22700. ; DELTA2A2 = 0.;
/*
        Gross Income Test - Qualifying Widow(er) w/ Dependent Child
*/
GROSS4N = 16350.  ; DELTA4N = 0.;
GROSS4A = 17550. ; DELTA4A = 0.;
/*
        Income Thresholds for Dependent Filers
*/
DEPWAGES = 0.0 ;
DEPTOTAL = 1000. ;
/*
        Wage Thresholds for Non-Dependent Filers
*/
WAGE1 = 1000. ;  	/* Single */
WAGE2 = 250. ;  	/* Joint, With Kids  */
WAGE2NK = 10000.;	/* Joint, No Kids */
WAGE3 = 1. ;  		/* Head   */
/*
        Dependent Exemption
*/
DEPEX1 = 3950. ;
DEPEX2 = 3950. ;
DEPEX3 = 3950. ;

%MEND  SETPARMS ;

%MACRO FILLREC ;
                PREC(NPER , 1)  = H_SEQ ;
                PREC(NPER , 2)  = FFPOS ;
                PREC(NPER , 3)  = FKIND;
                PREC(NPER , 4)  = FTYPE;
                PREC(NPER , 5)  = FPERSONS;
                PREC(NPER , 6)  = FHEADIDX;
                PREC(NPER , 7)  = FWIFEIDX;
                PREC(NPER , 8)  = FHUSBIDX;
                PREC(NPER , 9)  = A_SPOUSE;     /* NOTE: Change from previous matches! */
				IF( A_SPOUSE GT H_NUMPER )THEN PREC(NPER , 9) = 0;
                PREC(NPER , 10) = FSUP_WGT;
                PREC(NPER , 11) = PH_SEQ;
                PREC(NPER , 12) = A_AGE;
                PREC(NPER , 13) = A_SEX;
                PREC(NPER , 14) = A_FAMREL;
                PREC(NPER , 15) = A_PFREL;
                PREC(NPER , 16) = HHDREL;
                PREC(NPER , 17) = FAMREL;
                PREC(NPER , 18) = HHDFMX;
                PREC(NPER , 19) = MARSUPWT;
                PREC(NPER , 20) = WSAL_VAL;
                PREC(NPER , 21) = SEMP_VAL;
                PREC(NPER , 22) = FRSE_VAL;
                PREC(NPER , 23) = UC_VAL;
                PREC(NPER , 24) = SS_VAL_X;
                PREC(NPER , 25) = RTM_VAL;
                PREC(NPER , 26) = INT_VAL;
                PREC(NPER , 27) = DIV_VAL;
                PREC(NPER , 28) = RNT_VAL;
				*****
					ALIMONY NOW COMBINED IN OTHER INCOME FIELD
					9-MAR-2016 BY OHARE.
				*****;
				ALM_VAL = 0.;
				IF( OI_OFF = 20 )THEN ALM_VAL = OI_VAL;
                PREC(NPER , 29) = ALM_VAL;
                PREC(NPER , 30) = 0.0;
                PREC(NPER , 31) = 0.0;
                PREC(NPER , 32) = 0.0;
                PREC(NPER , 33) = P_STAT;
                PREC(NPER , 34) = A_FAMNUM;
                PREC(NPER , 35) = A_FAMTYP;
                PREC(NPER , 36) = A_MARITL;
                PREC(NPER , 37) = A_ENRLW;
                PREC(NPER , 38) = A_EXPRRP;
                PREC(NPER , 39) = A_HGA;
                PREC(NPER , 40) = WC_VAL;
                PREC(NPER , 41) = PAW_VAL;
                PREC(NPER , 42) = DSAB_VAL;
                PREC(NPER , 43) = 0.0;
                PREC(NPER , 44) = 0.0;
                PREC(NPER , 45) = 0.0;
                PREC(NPER , 46) = 0.0;
                PREC(NPER , 47) = 0.0;
                PREC(NPER , 48) = 0.0;
                PREC(NPER , 49) = 0.0;
                PREC(NPER , 50) = 0.0;
                PREC(NPER , 51) = SSI_VAL;
                PREC(NPER , 52) = VET_VAL;
                PREC(NPER , 53) = 0.0;
                PREC(NPER , 54) = 0.0;
                PREC(NPER , 55) = 0.0 ;
				PREC(NPER , 56) = 0.0;
				PREC(NPER , 57) = 0.0;
				PREC(NPER , 58) = 0.0;
				PREC(NPER , 59) = 0.0;
				PREC(NPER , 60) = LJCW;
				PREC(NPER , 61) = WEMIND;
				PREC(NPER , 62) = PENATVTY;
				*****
					SHANE:	HERE I ADD THE PERSON-LEVEL VARIABLES FROM THE CPS
							NOTE THAT THESE MAY NEED TO BE COMBINED FOR SPOUSES WHEN
							THE TAX UNIT IS CREATED.

							YOU WILL SEE THAT HERE I ADD 10 VARIABLES, IN LOCATIONS
							63-72. JFO.
				*****;
				PREC(NPER , 63) = A_AGE;
				PREC(NPER , 64) = CARE;
				PREC(NPER , 65) = CAID;
				PREC(NPER , 66) = OTH;
				PREC(NPER , 67) = HI;
				PREC(NPER , 68) = PRIV;
				PREC(NPER , 69) = PAID;
				PREC(NPER , 70) = FILESTAT;
				PREC(NPER , 71) = AGI;
				PREC(NPER , 72) = 0.;	/*	CAPITAL GAINS NO LONGER ON FILE	*/
				*****
					NEW VARIABLES FOR VERSION 4
				*****;
				PREC(NPER , 73) = RET_VAL1;
				PREC(NPER , 74) = RET_SC1;
				PREC(NPER , 75) = RET_VAL2;
				PREC(NPER , 76) = RET_SC2;
				PREC(NPER , 77) = DIS_VAL1;
				PREC(NPER , 78) = DIS_SC1;
				PREC(NPER , 79) = DIS_VAL2;
				PREC(NPER , 80) = DIS_SC2;
				PREC(NPER , 81) = SUR_VAL1;
				PREC(NPER , 82) = SUR_SC1;
				PREC(NPER , 83) = SUR_VAL2;
				PREC(NPER , 84) = SUR_SC2;
				PREC(NPER , 85) = VET_TYP1;
				PREC(NPER , 86) = VET_TYP2;
				PREC(NPER , 87) = VET_TYP3;
				PREC(NPER , 88) = VET_TYP4;
				PREC(NPER , 89) = VET_TYP5;
				PREC(NPER , 90) = VET_VAL;
				*****
					NEW MEANS TESTED VARIABLES
				*****;
				PREC(NPER , 91) = PAW_VAL;
				PREC(NPER , 92) = MCAID;
				PREC(NPER , 93) = PCHIP;
				PREC(NPER , 94) = WICYN;
				PREC(NPER , 95) = SSI_VAL;
				PREC(NPER , 96) = HI_YN;
				PREC(NPER , 97) = HIOWN;
				PREC(NPER , 98) = HIEMP;
				PREC(NPER , 99) = HIPAID;
				PREC(NPER , 100) = EMCONTRB;
				PREC(NPER , 101) = HI;
				PREC(NPER , 102) = HITYP;
				PREC(NPER , 103) = PAID;
				PREC(NPER , 104) = PRIV;
				PREC(NPER , 105) = PRITYP;
				PREC(NPER , 106) = SS_VAL_X;
				PREC(NPER , 107) = UC_VAL;
				PREC(NPER , 108) = MCARE;
				PREC(NPER , 109) = WC_VAL;
				PREC(NPER , 110) = VET_VAL;
*****
	ANDERSON: ADDITIONAL HOUSEHOLD LEVEL VARIABLES
*****;
				PREC(NPER , 111) = FHIP_VAL;
				PREC(NPER , 112) = FMOOP;
				PREC(NPER , 113) = FOTC_VAL;
				PREC(NPER , 114) = FMED_VAL;
				PREC(NPER , 115) = HMCAID;
				PREC(NPER , 116) = HRWICYN;
				PREC(NPER , 117) = HFDVAL;
				PREC(NPER , 118) = CARE_VAL;
				PREC(NPER , 119) = PEDISEYE;
*****
   Variables from imputations
*****;
				PREC(NPER , 120) = SSI_IMPUTE;
				PREC(NPER , 121) = SSI_PROBS;
				PREC(NPER , 122) = VB_IMPUTE;
				PREC(NPER , 123) = SNAP_IMPUTE;
				PREC(NPER , 124) = MEDICAREX;
				PREC(NPER , 125) = MEDICAIDX;
				PREC(NPER , 126) = SS_VAL_Y;
				PREC(NPER , 127) = SS_PROBS;
				PREC(NPER , 128) = SNAP_PROBS;
				PREC(NPER , 129) = VB_PROBS;
				PREC(NPER , 130) = MCARE_PROBS;
				PREC(NPER , 131) = MCAID_PROBS;
				PREC(NPER , 133) = TANF_IMPUTE;
				PREC(NPER , 134) = TANF_PROBS;
				PREC(NPER , 135) = UI_IMPUTE;
				PREC(NPER , 136) = UI_PROBS;
				PREC(NPER , 137) = HOUSING_IMPUTE;
				PREC(NPER , 138) = HOUSING_PROBS;
				PREC(NPER , 139) = WIC_IMPUTE;
				PREC(NPER , 140) = WIC_PROBS;
*****
				person line number
*****;
				PREC(NPER , 132) = A_LINENO;
%MEND FILLREC ;

%MACRO HHSTATUS( INDEX ) ;
/*
        ----------------------------------------
        Determine Head of Household Status
        ----------------------------------------
*/
        INCOME = 0.0 ;
        DO IUNIT = 1 TO NUNITS ;
                %TOTINCX( IUNIT )
                INCOME = INCOME + TOTINCX;
        END;
        IF( INCOME GT 0.0 )THEN
                DO;
                        %TOTINCX( &INDEX )
                        indJS = TREC(&INDEX , 1);       /* Filing Status:     1=Single    */
                        indIF = TREC(&INDEX , 2);       /* Dependency Status: 1=Dependent */
                        indDX = TREC(&INDEX , 4);       /* Number of Dependent Exemptions */
                        indAE = TREC(&INDEX , 3);       /* Number of Aged Exempions       */
                        IF( (indJS = 1) AND ( (TOTINCX/INCOME) GT 0.99) )THEN
                                DO;
                                        IF( (indIF NE 1) AND (indDX GT 0.) )THEN
                                                DO;
                                                        TREC(&INDEX , 1) = 3;
                                                END;
                                END;
                END;
%MEND HHSTATUS ;

LIBNAME EXTRACT "C:\Users\anderson.frailey\Documents\State Database - 2015\CPS Tax Units\2013\Extracts\";

*****
	CREATE A TEMPORY SAS DATASET OF HOUSEHOLDS W/ NUMBER OF PERSONS TO
	FACILITATE PROCESSING.

	NOTE: 	THE ORIGINAL CPS IS NOT IS THE CORRECT SORT ORDER SO WE GIVE EACH
			RECORD A UNIQUE SEQUENCE NUMBER.
*****;
DATA TEMPORARY(KEEP=H_SEQ SORT_ORDER H_NUMPER);
* SET EXTRACT.CPSMAR&CPSYEAR;
* SET EXTRACT.CPSMARBEN13;
* SET EXTRACT.CPSMAR2013_BEN;
SET EXTRACT.CPSMAR2013_BEN_FULL;
SORT_ORDER = _N_;
RUN;
PROC SORT DATA=TEMPORARY;BY H_SEQ;
RUN;
DATA HOUSEHOLDS(KEEP=SEQUENCE SORT_ORDER H_NUMPER);
SET TEMPORARY;
BY H_SEQ;
RETAIN SEQUENCE;
IF( _N_ EQ 1 )THEN
	DO;
		SEQUENCE = 0.;
	END;
IF( LAST.H_SEQ )THEN
	DO;
		SEQUENCE = SEQUENCE + 1;
		OUTPUT;
		END;
RUN;
*****
	NOW PUT THE FILE BACK IN THE ORIGINAL SORT ORDER
*****;
PROC SORT DATA=HOUSEHOLDS;BY SORT_ORDER;
RUN;

*******************************************************************************************;
*****        MAIN PROGRAM                                                             *****;
*****                                                                                 *****;
*****        Purpose - Create Extract of CPS Tax Units                                *****;
*******************************************************************************************;
DATA EXTRACT.CPSRETS&CPSYEAR(KEEP=JS IFDEPT AGEDE DEPNE CAHE AGEH AGES
                          WAS INTST DBE ALIMONY BIL PENSIONS
                          RENTS FIL UCOMP SOCSEC INCOME RETURNS WT FILST HHID
                          ZIFDEP ZNTDEP ZHHINC ZAGEPT ZAGESP ZOLDES
                          ZYOUNG ZWORKC ZSOCSE ZSSINC ZPUBAS ZVETBE
                          ZCHSUP ZFINAS ZDEPIN ZOWNER ZWASPT ZWASSP
                          WASP WASS OLDEST YOUNGEST
                          XXOCAH XXOCAWH
                          XXOODEP XXOPAR XXTOT XAGEX XSTATE XREGION
                          XSCHB XSCHF XSCHE XSCHC XHID XFID XPID
						  NU18 N1821 N21
						  BLIND_HEAD BLIND_SPOUSE
						  SSI_VAL1-SSI_VAL15 SSI_PROB1-SSI_PROB15 SSI
						  VB SNAP MEDICARE MEDICAID SS
						  SNAP_PROB1-SNAP_PROB15 SNAP_VAL1-SNAP_VAL15
						  SS_PROB1-SS_PROB15 SS_VAL1-SS_VAL15
						  MCARE_VAL1-MCARE_VAL15 MCARE_PROB1-MCARE_PROB15
						  MCAID_VAL1-MCAID_VAL15 MCAID_PROB1-MCAID_PROB15
						  VB_VAL1-VB_VAL15 VB_PROB1-VB_PROB15 XFHEADIDX XTOTDIFF
						  A_LINENO TANF TANF_VAL1-TANF_VAL15 TANF_PROB1-TANF_PROB15
						  UI UI_VAL1-UI_VAL15 WIC WIC_VAL1-WIC_VAL15 WIC_PROB1-WIC_PROB15
						  HOUSING HOUSING_VAL1-HOUSING_VAL15 HOUSING_PROB1-HOUSING_PROB15
                          /*
                                        New CPS Variables
                          */
                          ICPS01-ICPS50
						  /*
						  				Expanded Set of CPS Variables (ADDED 14-OCT-2010)
						  				Expanded Again on 24-MAY-2016 for Means Tested Programs
						  */
						  JCPS1-JCPS200)

;
SET HOUSEHOLDS;
RETAIN PTR;
RETAIN ISEED1 87421 ISEED2 73445 ISEED3 12339;
*****
	SHANE:	HERE I INCREASE THE SIZE OF THE PERSON (PREC) AND TAX UNIT (TREC)
			ARRAYS BY 100.

			I ALSO SET UP A NEW CPS-ARRAY (JCPS) TO STORE THE NEW VARIABLES, BUT
			THIS ISNT REALLY NECESSARY. JFO.
*****;
ARRAY PREC(16 , 162) _temporary_ ;	/*	NEW CPS FIELDS	*/
*****
	ANDERSON: NEED TO INCREASE SIZE TREC(*) ARRAY
*****;
ARRAY TREC(16 , 595) _temporary_ ;
ARRAY ICPS(*) ICPS01-ICPS50 ;
ARRAY JCPS(*) JCPS1-JCPS200 ;
IF (_N_ = 1)THEN PTR = 0;
RETURNS = 1.0;
NUNITS = 0.0 ;
HHID = H_SEQ ;

%SETPARMS

******************************************************************************;
*****     I.) INITIALIZATION PHASE: FILL-UP PERSON ARRAY PREC()          *****;
******************************************************************************;
DO NPER = 1 TO H_NUMPER;
	* SET EXTRACT.CPSMAR&CPSYEAR ;
	* SET EXTRACT.CPSMARBEN13;
    * SET EXTRCT.CPSMAR2013_BEN_FULL;
	SET EXTRACT.CPSMAR2013_BEN_FULL;
   	%FILLREC
END;
******************************************************************************;
*****           II.) MAIN COMPUTATIONAL PHASE: CONSTRUCT TAX UNITS       *****;
******************************************************************************;
***
====> For two types of households, constructing tax units
      is pretty straightforward:

                (1) Single persons living alone are one tax unit.
                (2) Individuals living in group quarters get one
                    tax unit per individual.

        So let's take care of these cases first.
***;
        SELECT;

                *************************************************;
                *** CASE #1: Single Persons Living Alone      ***;
                *************************************************;

                WHEN( ( (H_TYPE = 6) OR (H_TYPE = 7) ) AND (H_NUMPER = 1) )
                        DO;
                                %CREATE( 1 )
                        END;

                *************************************************;
                *** CASE #2: Persons Living in Group Quarters ***;
                *************************************************;

				WHEN(  (H_TYPE = 9)  )
                        DO IPER = 1 TO H_NUMPER;
                                %CREATE( IPER )
                        END;

                *************************************************;
                *** CASE #3: All Other Family Structures      ***;
                *************************************************;

                OTHERWISE
                        DO;
                                DO IX = 1 TO H_NUMPER ;
                                /*
                                -----------------------------
                                OUTER LOOP - Reference Person
                                -----------------------------
                                */
                                refFID   = PREC(IX ,  2) ;
                                refFKIND = PREC(IX ,  3) ;
                                refFTYPE = PREC(IX ,  4) ;
                                refHHREL = PREC(IX , 16) ;
                                refFFREL = PREC(IX , 17) ;
                                refHFREL = PREC(IX , 18) ;
                                refHFLAG = PREC(IX , 30) ; /* Tax Unit Head Flag      */
                                refSFLAG = PREC(IX , 31) ; /* Tax Unit Spouse Flag    */
                                refDFLAG = PREC(IX , 32) ; /* Tax Unit Dependent Flag */
                                refREL   = PREC(IX , 38) ; /* Relationship Code       */
                                /*
                                ---------------------------------------------
                                Check if this Person has already been taken
                                ---------------------------------------------
                                */
                                IF( (refHFLAG = 0) AND (refSFLAG = 0) AND (refDFLAG = 0) )THEN
                                        DO;
                                                %CREATE( IX )
                                        END;
                                /*
                                        ---------------------------------------------
                                        If this Person is a dependent, check to see if
                                        they must file a return.
                                        ---------------------------------------------
                                */
                                IF( (refSFLAG = 0) AND (refDFLAG = 1) )THEN
                                        DO;
                                                %MUSTFILE( IX , DEPFILE )
                                                IF( DEPFILE = 1 )THEN
                                                        DO;
                                                                %CREATE( IX )
                                                        END;
                                        END;
                                END;
                                /*
                                ------------------------------------------
                                Now check tentative returns for dependency
                                if household has more than one tax unit.
                                ------------------------------------------
                                */
                                IF( NUNITS GT 1 )THEN
                                        DO;
                                                %SEARCH2
                                        END;
                        END;
        END;

                *******************************************************;
                *** III.) FINAL ALIGNMENT CHECK                     ***;
                *******************************************************;

                DO NRET = 1 TO NUNITS ;
                        %HHSTATUS( NRET );
                END;


                ********************************************************;
                *** IV.) OUTPUT RETURNS                              ***;
                ********************************************************;

%OUTPUT

LABEL JS = 'Filing Status'
    AGEH = 'Age of Head'
  INCOME = 'Income Class'
   AGEDE = 'Aged Status'
  IFDEPT = 'Dependency Status'
   DEPNE = 'Presence of Dependents' ;
RUN;
***
        Make one last pass through both FILER and NON-FILER extracts to
        assign unique IDs.
***;
DATA EXTRACT.CPSRETS&CPSYEAR;
SET EXTRACT.CPSRETS&CPSYEAR;
CPSSEQ = _N_;
TAXYEAR = &TAXYEAR;
RUN;
/*
                Table 2a. - First Blocking Partitions: Filing Status, Age & Income
                                (Unweighted) - Filers Only
*/
PROC TABULATE DATA=EXTRACT.CPSRETS&CPSYEAR FORMAT=COMMA12. ;
CLASS JS AGEDE IFDEPT DEPNE ;
VAR RETURNS ;
FORMAT JS JS. IFDEPT IFDEPT. DEPNE DEPNE. AGEDE AGEDE.
FILST FILST.;
KEYLABEL SUM='AMOUNT' PCTSUM='PERCENT' ALL='Total, All Returns'
MEAN='AVERAGE' N='Unweighted' PCTN='PERCENT' SUMWGT='Weighted' ;
TABLE ( (IFDEPT ALL)*(AGEDE ALL) ) , RETURNS*( ((JS*DEPNE ALL) )*(N)  )
/ PRINTMISS MISSTEXT='n.a.' ;
TITLE1 'S t a t i s t i c a l  M a t c h i n g  P r o j e c t' ;
TITLE3 'Preliminary File Alignment' ;
TITLE5 'Table 2a. - First Blocking Partition: Filing Status, Age & Dependency Status' ;
TITLE6 'Source: MARCH 2013 Current Population Survey' ;
TITLE7 '(*** Unweighted ***)' ;
TITLE8 'Filers' ;
TITLE9 '------' ;
RUN;
/*
                Table 2b. - First Blocking Partitions: Filing Status, Age & Income
                                (Weighted) - Filers Only
*/
PROC TABULATE DATA=EXTRACT.CPSRETS&CPSYEAR FORMAT=COMMA12. ;
WHERE( FILST EQ 1. );
WEIGHT WT;
CLASS JS AGEDE IFDEPT DEPNE ;
VAR RETURNS ;
FORMAT JS JS. IFDEPT IFDEPT. DEPNE DEPNE. AGEDE AGEDE.
FILST FILST.;
KEYLABEL SUM='AMOUNT' PCTSUM='PERCENT' ALL='Total, All Returns'
MEAN='AVERAGE' N='Unweighted' PCTN='PERCENT' SUMWGT='Weighted' ;
TABLE ( (IFDEPT ALL)*(AGEDE ALL) ) , RETURNS*( ((JS*DEPNE ALL) )*(SUMWGT)  )
/ PRINTMISS MISSTEXT='n.a.' ;
TITLE1 'S t a t i s t i c a l  M a t c h i n g  P r o j e c t' ;
TITLE3 'Preliminary File Alignment' ;
TITLE5 'Table 2b. - First Blocking Partition: Filing Status, Age & Dependency Status' ;
TITLE6 'Source: MARCH 2013 Current Population Survey' ;
TITLE7 '(*** Weighted ***)' ;
TITLE8 'Filers' ;
TITLE9 '------' ;
RUN;
*****
	SUMMARIZE THE TAX UNIT EXTRACT
*****;
PROC MEANS N MIN MAX MEAN SUM DATA=EXTRACT.CPSRETS&CPSYEAR;
TITLE1 'TAX YEAR 2012 - CPS YEAR 2013 TAX UNIT EXTRACT';
RUN;
PROC MEANS N MIN MAX MEAN SUM DATA=EXTRACT.CPSRETS&CPSYEAR;
WEIGHT WT;
VAR FILST;
TITLE1 'TAX YEAR 2012 - CPS YEAR 2013 TAX UNIT EXTRACT';
RUN;
