*******************************************************************************************;
***                                                                                     ***;
***                                                                                     ***;
***                          State Modeling Project                                     ***;
***                                                                                     ***;
***                                                                                     ***;
*******************************************************************************************;
OPTIONS PAGESIZE=59 LINESIZE=160 CENTER COMPRESS=YES; /* LANDSCAPE */
*****
	PRODUCTION FILE
*****;
LIBNAME EXTRACT "C:\Users\anderson.frailey\Documents\State Database - 2015\Production File\Extracts\";
PROC FORMAT;
VALUE STATE (DEFAULT = 32)
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
*****
	PROCESS THE PRODUCTION FILE - 28-JAN-2015
	REVISED ON 28-OCT-2016 TO ADD ALL VARIABLES BACK.
*****;
DATA EXTRACT.ECPENSIONS(KEEP= SEQUENCE BUILDUP_LIFE BUILDUP_PENS_DB
                              BUILDUP_PENS_DC GAINS_ON_HOME_SALE STEPUPINBASIS
							  TEXINT ESHI_TAXPAYER ESHI_SPOUSE EDUCATIONAL_EXPENSE
							  RENT_PAID ECPENSIONS WT);
SET EXTRACT.PROD2015_V1D;
RETAIN ISEED1 561123 ISEED2 32415 ISEED3 55249;
*****
	INITIALIZE
*****;
SEQUENCE = _N_ ;
BUILDUP_LIFE = 0.0;
BUILDUP_PENS_DB = 0.0;
BUILDUP_PENS_DC = 0.0;
GAINS_ON_HOME_SALE = 0.0;
STEPUPINBASIS = 0.0;
TEXINT = 0.0;
ESHI_TAXPAYER = 0.0;
ESHI_SPOUSE = 0.0;
EDUCATIONAL_EXPENSE = 0.0;
RENT_PAID = 0.0;
IF( HOMEEQUITY EQ . )THEN HOMEEQUITY = 0.;
IF( CCE EQ . )THEN CCE = 0.;
*****
	RE-MAP SOME CPS FIELDS
*****;
ICPS10 = JCPS5;
ICPS11 = JCPS6;
ICPS12 = JCPS7;
ICPS13 = JCPS15;
ICPS14 = JCPS16;
ICPS15 = JCPS17;
*****
	CREATE SOME VARIABLES
*****;
IF( CGAGIX EQ . )THEN CGAGIX = 0.;
IF( TIRAD EQ . )THEN TIRAD = 0.;
MARRIED = 0.;
IF( JS = 2 )THEN MARRIED = 1.;
AGEP = ICPS01;
AGESQR = AGEP * AGEP;
AGEDE = 0.;
IF( ICPS01 GE 65. )THEN AGEDE = 1;
IF( ICPS02 GE 65. )THEN AGEDE = AGEDE + 1;
INCOME = WAS + INTST + DBE + ALIMONY + BIL + PENSIONS + RENTS + FIL + UCOMP + SOCSEC 
       + CGAGIX + TIRAD ;
INCOME = INCOME / 1000.;
INCOME2 = WAS + INTST + DBE + ALIMONY + BIL + PENSIONS + RENTS + FIL + UCOMP + SOCSEC 
       + CGAGIX + TIRAD ;
INCOME2 = MIN( 1000000. , INCOME2 ) / 1000.;
LNINCOME = LOG( 1. + MAX( 0. , INCOME ) );
LNINCOME2 = LOG( 1. + MAX( 0. , INCOME2 ) );
LNINTST = LOG( 1. + ( MAX( 0. , INTST )/1000. ) );
***
	228:	CASH VALUE LIFE INSURANCE
***;
XB = 0.;
XB = -4.939295
     + 0.341101*LNINCOME
     + 0.210042*MARRIED
     + 0.043812*AGEP
     - 0.000110*AGESQR ; 
PROB = EXP( XB ) / (1. + EXP( XB ) );
CALL RANUNI( ISEED1 , Z1 );
IF( Z1 LE PROB )THEN
	DO;
		XB = 2.93293
		     + 0.745429*LNINCOME
		     + 0.057145*MARRIED
		     + 0.073103*AGEP
		     - 0.000425*AGESQR ;
		BUILDUP_LIFE = EXP( XB ) * 0.040; 
	END;
***
	229:	DB PLANS
***;
XB = 0.;
XB = -5.523435
     + 0.455226*LNINCOME
     + 0.306575*MARRIED
     + 0.052442*AGEP
     - 0.000023*AGESQR ; 
PROB = EXP( XB ) / (1. + EXP( XB ) );
CALL RANUNI( ISEED1 , Z1 );
IF( Z1 LE PROB )THEN
	DO;
		XB = -1.182855
		     + 0.176279*LNINCOME
		     + 0.027678*MARRIED
		     + 0.032099*AGEP
		     - 0.000296*AGESQR ;
		BUILDUP_PENS_DB = EXP( XB )* 1000. * 0.040; 
	END;
***
	230:	DC PLANS
***;
XB = 0.;
XB = -7.628465
     + 1.178294*LNINCOME
     - 0.036142*MARRIED
     + 0.135468*AGEP
     - 0.001710*AGESQR ; 
PROB = EXP( XB ) / (1. + EXP( XB ) );
CALL RANUNI( ISEED1 , Z1 );
IF( Z1 LE PROB )THEN
	DO;
		XB = -5.382661
		     + 1.267289*LNINCOME
		     - 0.129236*MARRIED
		     + 0.115907*AGEP
		     - 0.000721*AGESQR ;
		BUILDUP_PENS_DC = EXP( XB )* 1000. * 0.040; 
	END;
***
	231:	HOME SALES
***;
PROB = 0.07;
LIMIT = 250000.;
IF( JS EQ 2 )THEN LIMIT = 500000.;
IF( ICPS29 EQ 1 )THEN
	DO;
		CALL RANUNI( ISEED1 , Z1 );
		IF( Z1 LE PROB )THEN
			DO;
				GAINS_ON_HOME_SALE = MIN( LIMIT , HOMEEQUITY*0.25 );
			END;
	END;
***
	232:	STEP UP IN BASIS (NET WORTH)
***;
XB = 0.;
IF( AGEP =	0	)THEN PROBD = 	0.00612	;
IF( AGEP =	1	)THEN PROBD = 	0.00042	;
IF( AGEP =	2	)THEN PROBD = 	0.00026	;
IF( AGEP =	3	)THEN PROBD = 	0.00020	;
IF( AGEP =	4	)THEN PROBD = 	0.00015	;
IF( AGEP =	5	)THEN PROBD = 	0.00014	;
IF( AGEP =	6	)THEN PROBD = 	0.00012	;
IF( AGEP =	7	)THEN PROBD = 	0.00012	;
IF( AGEP =	8	)THEN PROBD = 	0.00010	;
IF( AGEP =	9	)THEN PROBD = 	0.00009	;
IF( AGEP =	10	)THEN PROBD = 	0.00009	;
IF( AGEP =	11	)THEN PROBD = 	0.00009	;
IF( AGEP =	12	)THEN PROBD = 	0.00012	;
IF( AGEP =	13	)THEN PROBD = 	0.00017	;
IF( AGEP =	14	)THEN PROBD = 	0.00024	;
IF( AGEP =	15	)THEN PROBD = 	0.00032	;
IF( AGEP =	16	)THEN PROBD = 	0.00040	;
IF( AGEP =	17	)THEN PROBD = 	0.00049	;
IF( AGEP =	18	)THEN PROBD = 	0.00057	;
IF( AGEP =	19	)THEN PROBD = 	0.00065	;
IF( AGEP =	20	)THEN PROBD = 	0.00074	;
IF( AGEP =	21	)THEN PROBD = 	0.00082	;
IF( AGEP =	22	)THEN PROBD = 	0.00088	;
IF( AGEP =	23	)THEN PROBD = 	0.00091	;
IF( AGEP =	24	)THEN PROBD = 	0.00092	;
IF( AGEP =	25	)THEN PROBD = 	0.00093	;
IF( AGEP =	26	)THEN PROBD = 	0.00094	;
IF( AGEP =	27	)THEN PROBD = 	0.00095	;
IF( AGEP =	28	)THEN PROBD = 	0.00097	;
IF( AGEP =	29	)THEN PROBD = 	0.00099	;
IF( AGEP =	30	)THEN PROBD = 	0.00102	;
IF( AGEP =	31	)THEN PROBD = 	0.00106	;
IF( AGEP =	32	)THEN PROBD = 	0.00109	;
IF( AGEP =	33	)THEN PROBD = 	0.00113	;
IF( AGEP =	34	)THEN PROBD = 	0.00118	;
IF( AGEP =	35	)THEN PROBD = 	0.00124	;
IF( AGEP =	36	)THEN PROBD = 	0.00130	;
IF( AGEP =	37	)THEN PROBD = 	0.00138	;
IF( AGEP =	38	)THEN PROBD = 	0.00147	;
IF( AGEP =	39	)THEN PROBD = 	0.00157	;
IF( AGEP =	40	)THEN PROBD = 	0.00168	;
IF( AGEP =	41	)THEN PROBD = 	0.00181	;
IF( AGEP =	42	)THEN PROBD = 	0.00198	;
IF( AGEP =	43	)THEN PROBD = 	0.00218	;
IF( AGEP =	44	)THEN PROBD = 	0.00242	;
IF( AGEP =	45	)THEN PROBD = 	0.00268	;
IF( AGEP =	46	)THEN PROBD = 	0.00295	;
IF( AGEP =	47	)THEN PROBD = 	0.00324	;
IF( AGEP =	48	)THEN PROBD = 	0.00354	;
IF( AGEP =	49	)THEN PROBD = 	0.00385	;
IF( AGEP =	50	)THEN PROBD = 	0.00418	;
IF( AGEP =	51	)THEN PROBD = 	0.00454	;
IF( AGEP =	52	)THEN PROBD = 	0.00491	;
IF( AGEP =	53	)THEN PROBD = 	0.00530	;
IF( AGEP =	54	)THEN PROBD = 	0.00571	;
IF( AGEP =	55	)THEN PROBD = 	0.00616	;
IF( AGEP =	56	)THEN PROBD = 	0.00665	;
IF( AGEP =	57	)THEN PROBD = 	0.00714	;
IF( AGEP =	58	)THEN PROBD = 	0.00762	;
IF( AGEP =	59	)THEN PROBD = 	0.00812	;
IF( AGEP =	60	)THEN PROBD = 	0.00868	;
IF( AGEP =	61	)THEN PROBD = 	0.00932	;
IF( AGEP =	62	)THEN PROBD = 	0.01007	;
IF( AGEP =	63	)THEN PROBD = 	0.01094	;
IF( AGEP =	64	)THEN PROBD = 	0.01193	;
IF( AGEP =	65	)THEN PROBD = 	0.01306	;
IF( AGEP =	66	)THEN PROBD = 	0.01431	;
IF( AGEP =	67	)THEN PROBD = 	0.01563	;
IF( AGEP =	68	)THEN PROBD = 	0.01701	;
IF( AGEP =	69	)THEN PROBD = 	0.01849	;
IF( AGEP =	70	)THEN PROBD = 	0.02019	;
IF( AGEP =	71	)THEN PROBD = 	0.02212	;
IF( AGEP =	72	)THEN PROBD = 	0.02425	;
IF( AGEP =	73	)THEN PROBD = 	0.02658	;
IF( AGEP =	74	)THEN PROBD = 	0.02915	;
IF( AGEP =	75	)THEN PROBD = 	0.03215	;
IF( AGEP =	76	)THEN PROBD = 	0.03555	;
IF( AGEP =	77	)THEN PROBD = 	0.03923	;
IF( AGEP =	78	)THEN PROBD = 	0.04317	;
IF( AGEP =	79	)THEN PROBD = 	0.04751	;
IF( AGEP =	80	)THEN PROBD = 	0.05250	;
IF( AGEP =	81	)THEN PROBD = 	0.05825	;
IF( AGEP =	82	)THEN PROBD = 	0.06468	;
IF( AGEP =	83	)THEN PROBD = 	0.07183	;
IF( AGEP =	84	)THEN PROBD = 	0.07981	;
IF( AGEP =	85	)THEN PROBD = 	0.08875	;
IF( AGEP =	86	)THEN PROBD = 	0.09877	;
IF( AGEP =	87	)THEN PROBD = 	0.10994	;
IF( AGEP =	88	)THEN PROBD = 	0.12233	;
IF( AGEP =	89	)THEN PROBD = 	0.13594	;
IF( AGEP =	90	)THEN PROBD = 	0.15079	;
IF( AGEP =	91	)THEN PROBD = 	0.16686	;
IF( AGEP =	92	)THEN PROBD = 	0.18414	;
IF( AGEP =	93	)THEN PROBD = 	0.20259	;
IF( AGEP =	94	)THEN PROBD = 	0.22218	;
IF( AGEP =	95	)THEN PROBD = 	0.24179	;
IF( AGEP =	96	)THEN PROBD = 	0.26109	;
IF( AGEP =	97	)THEN PROBD = 	0.27974	;
IF( AGEP =	98	)THEN PROBD = 	0.29735	;
IF( AGEP =	99	)THEN PROBD = 	0.31358	;
IF( AGEP =	100	)THEN PROBD = 	0.33069	;
IF( AGEP =	101	)THEN PROBD = 	0.34875	;
IF( AGEP =	102	)THEN PROBD = 	0.36780	;
IF( AGEP =	103	)THEN PROBD = 	0.38790	;
IF( AGEP =	104	)THEN PROBD = 	0.40910	;
IF( AGEP =	105	)THEN PROBD = 	0.43148	;
IF( AGEP =	106	)THEN PROBD = 	0.45509	;
IF( AGEP =	107	)THEN PROBD = 	0.48001	;
IF( AGEP =	108	)THEN PROBD = 	0.50629	;
IF( AGEP =	109	)THEN PROBD = 	0.53404	;
IF( AGEP =	110	)THEN PROBD = 	0.56331	;
IF( AGEP =	111	)THEN PROBD = 	0.59420	;
IF( AGEP =	112	)THEN PROBD = 	0.62680	;
IF( AGEP =	113	)THEN PROBD = 	0.66120	;
IF( AGEP =	114	)THEN PROBD = 	0.69751	;
IF( AGEP =	115	)THEN PROBD = 	0.73582	;
IF( AGEP =	116	)THEN PROBD = 	0.77626	;
IF( AGEP =	117	)THEN PROBD = 	0.81818	;
IF( AGEP =	118	)THEN PROBD = 	0.85909	;
IF( AGEP =	119	)THEN PROBD = 	0.90205	;

CALL RANUNI( ISEED1 , Z1 );
IF( Z1 LE PROBD )THEN
	DO;
		XB = -3.940298
		     + 1.387882*LNINCOME	/*	NOTE CHANGE IN INCOME CONCEPT	*/
		     + 0.164254*MARRIED
		     + 0.0450189*AGEP
		     + 0.000056*AGESQR  ;
		STEPUPINBASIS = EXP( XB )* 1000. * 0.5 ; 
	END;
***
	233:	TEXINT
***;
XB = 0.;
XB = -7.206106
     + 0.539793*LNINCOME
     - 0.442224*MARRIED
     + 0.463489*AGEDE
     + 0.4170335*LNINTST ; 
PROB = EXP( XB ) / (1. + EXP( XB ) );
CALL RANUNI( ISEED1 , Z1 );
IF( Z1 LE PROB )THEN
	DO;
		XB = 4.02137   
		     + 0.226618*LNINCOME
		     - 0.525778*MARRIED
		     + 0.713761*AGEDE
		     - 0.295498*LNINTST ;
		TEXINT = EXP( XB )* 1000.; 
	END;
***
	234 AND 235:	ESHI
***;
***
	SET VALUES FOR PREMIUMS: AVERAGE AND STANDARD DEVIATION (FAMILY AND SINGLE COVERAGE)
	Note: Values are for 2004.
***;
AVEPREM_F = 10006.;
STDPREM_F = 28.25;
AVEPREM_S = 3705.;
STDPREM_S = 16.42;
***
	SET VALUES FOR EMPLOYEE SHARE: AVERAGE AND STANDARD DEVIATION (FAMILY AND SINGLE COVERAGE)
***;
AVESHARE_F = 0.2440;
STDSHARE_F = 0.0041;
AVESHARE_S = 0.1810;
STDSHARE_S = 0.0023;
***
	SET VALUES FOR LIFE INSURANCE CONTRIBUTIONS (FROM BLS EMPLOYEE COMPENSATION SURVEY)
***;
PROBLIFE = 0.6200;
WAGESHARE = 0.0025;
***
	INCOME
***;
WAGES = WAS;
***
	INITIALIZE
***;
HIPREMIUM_P = 0.0;;
EMPLOYERSHARE_P = 0.0;
HIPREMIUM_S = 0.0;
EMPLOYERSHARE_S = 0.0;
TOTALEMPLOYERH = 0.0;
ECLIFE_P = 0.0;
ECLIFE_S = 0.0;
TOTALEMPLOYERL = 0.0;
PLANTYPE_P = 0;
PLANTYPE_S = 0;
***
	IMPUTE TOTAL PREMIUM: (PRINCIPAL TAXPAYER), NON-DEPENDENT RETURNS ONLY
***;
IF( ( ICPS10 EQ 1 ) AND ( ICPS11 EQ 1 ) AND ( IFDEPT EQ 0 ) )THEN
	DO;
		IF( ( DEPNE GT 0 ) OR ( ICPS13 EQ 2 ) )THEN
			DO;
				AVEPRM = AVEPREM_F;
				STDPRM = STDPREM_F;
				AVESHR = AVESHARE_F;
				STDSHR = STDSHARE_F;
				PLANTYPE_P = 2;
			END;
		ELSE
			DO;
				AVEPRM = AVEPREM_S;
				STDPRM = STDPREM_S;
				AVESHR = AVESHARE_S;
				STDSHR = STDSHARE_S;
				PLANTYPE_P = 1;
			END;
		***
			TOTAL PREMIUM AMOUNT
		***;
		CALL RANNOR( ISEED1 , Z );
		HIPREMIUM_P = MAX( 0. , AVEPRM + STDPRM*Z );
		***
			EMPLOYER SHARE: WE USE THE CPS VARIABLE
		***;
		IF( ICPS12 EQ 1 )THEN EMPLOYERSHARE_P = HIPREMIUM_P; /*	EMPLOYER PAYS ALL	*/
		IF( ICPS12 EQ 3 )THEN EMPLOYERSHARE_P = 0.;			 /* EMPLOYER PAYS NONE	*/
		IF( ICPS12 EQ 2 )THEN	/*	EMPLOYER PAYS PART	*/
			DO;
				CALL RANNOR( ISEED2 , Z );
				EMPLOYEESHARE = MAX( 0. , AVESHR + STDSHR*Z ) * HIPREMIUM_P;
				EMPLOYERSHARE_P = MAX( 0. , HIPREMIUM_P - EMPLOYEESHARE );
			END;	 
	END;
***
	IMPUTE TOTAL PREMIUM: (SECONDARY TAXPAYER), NON-DEPENDENT RETURNS ONLY
***;
IF( ( ICPS13 EQ 1 ) AND ( ICPS14 EQ 1 ) AND ( IFDEPT EQ 0 ) )THEN
	DO;
		IF( ( DEPNE GT 0 ) AND ( ICPS10 EQ 2 ) )THEN
			DO;
				AVEPRM = AVEPREM_F;
				STDPRM = STDPREM_F;
				AVESHR = AVESHARE_F;
				STDSHR = STDSHARE_F;
				PLANTYPE_S = 2;
			END;
		ELSE
			DO;
				AVEPRM = AVEPREM_S;
				STDPRM = STDPREM_S;
				AVESHR = AVESHARE_S;
				STDSHR = STDSHARE_S;
				PLANTYPE_S = 1;
			END;
		***
			TOTAL PREMIUM AMOUNT
		***;
		CALL RANNOR( ISEED1 , Z );
		HIPREMIUM_S = MAX( 0. , AVEPRM + STDPRM*Z );
		***
			EMPLOYER SHARE: WE USE THE CPS VARIABLE
		***;
		IF( ICPS15 EQ 1 )THEN EMPLOYERSHARE_S = HIPREMIUM_S; /*	EMPLOYER PAYS ALL	*/
		IF( ICPS15 EQ 3 )THEN EMPLOYERSHARE_S = 0.;			 /* EMPLOYER PAYS NONE	*/
		IF( ICPS15 EQ 2 )THEN	/*	EMPLOYER PAYS PART	*/
			DO;
				CALL RANNOR( ISEED2 , Z );
				EMPLOYEESHARE = MAX( 0. , AVESHR + STDSHR*Z ) * HIPREMIUM_S;
				EMPLOYERSHARE_S = MAX( 0. , HIPREMIUM_S - EMPLOYEESHARE );
			END;	 
	END;
ESHI_TAXPAYER = EMPLOYERSHARE_P * 1.65;
ESHI_SPOUSE = EMPLOYERSHARE_S * 1.65;
***
	237:	RENT
***;
RENT_PAID = 0.0;
IF( ICPS29 NE 1 )THEN 
	DO;
		RENT_PAID = .15 * MAX( 0. , (WAS + INTST + DBE + ALIMONY + BIL) ) ;
	END;
***
	FIX CHILD AND DEPENDENT CARE EXPENSES - STILL NOT SURE WHAT'S GOING ON HERE
***;
CCER = CCE * 3.0 ;
***
	EMPLOYER CONTRIBUTIONS TO PENSIONS
	NOTE: DATA FROM THE NATIONAL COMPENSATION SURVEY (BLS)
***;
ECPENSIONS = 0.0;
IF(  ( BUILDUP_PENS_DB GT 0. ) )THEN
	DO;
		ECPENSIONS = ECPENSIONS + .0480 * WAS ;
	END;
IF(  ( BUILDUP_PENS_DC GT 0. ) )THEN
	DO;
		ECPENSIONS = ECPENSIONS + .0277 * WAS ;
	END;

RUN;
PROC MEANS N SUMWGT MEAN MIN MAX SUM DATA=EXTRACT.ECPENSIONS;
WEIGHT WT;
TITLE1 "BLANK SLATE IMPUTATIONS - EMPLOYER CONTRIBUTIONS TO PENSIONS";
RUN;
*****
	DROP THE WEIGHT SO AS NOT TO SCREW UP THE MERGE
*****;
DATA EXTRACT.ECPENSIONS(COMPRESS=YES);
SET EXTRACT.ECPENSIONS;
DROP WT;
RUN;
