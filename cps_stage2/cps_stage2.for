      PROGRAM MPSFILE                                                   
      IMPLICIT REAL*8 (A-H,O-Z)                                         
C     ----------------------------------------------------              
C     PURPOSE - CONSTRUCT THE MATRIX TABLEAU FOR THE LINEAR             
C               PROGRAMMING PROBLEM.  OUTPUT AN MPS FILE FOR            
C               USE IN MINOS VERSION 5.4.                               
C                                                                       
C                   *  DEVELOPMENT LOG  *                               
C                                                                       
C     10-01-09 STARTED BY O'HARE.
C     ----------------------------------------------------              
      INCLUDE "/Users/jfo/Documents/State Modeling Project/Stage-II Extrapolation/MPS Generator/MPS Source/Segd"        
      INCLUDE "/Users/jfo/Documents/State Modeling Project/Stage-II Extrapolation/MPS Generator/MPS Source/SEGP"  
      LOGICAL CONNECTED
      CHARACTER*100 FILE_NAME      
      CHARACTER*40 INAME,TITLE,DUMMY1,DUMMY2
      CHARACTER*40 STNAME(51)
      CHARACTER*4 IFIPS(51)                                              
      CHARACTER*1 ITYPE,ILEVEL
      CHARACTER*1 LEVEL(18),LTYPE(18)
      INTEGER*4 NOBS(51)
      DATA CONTROL_TOTAL/0.D0/
C      INTEGER*4 IFIPS(51)                                          
      PARAMETER (IYEAR=2011 , INDXYR=IYEAR-2003)                        
      DIMENSION T(51) 
      REAL*8 TARGET(23,51),THIS_STATE                                              
      DATA NREC,NFAM,ICOUNT/3*0/                                        
      DATA IUNIT,JUNIT,KUNIT,LUNIT,MUNIT/10,11,12,20,22/
      DATA IOLDW/19/                                                    
1000  FORMAT('1',/                                                      
     .' ','***** END OF PROCESSING,',I10,' RECORDS READ',/              
     .' ','                        ',I10,' FAMILIES PROCESSED.')        
1001  FORMAT(A1, A1, 4X, A40)                                           
1002  FORMAT(7F10.1)                                                    
1003  FORMAT('1',///,' 2012 State Model File/Stage-II Extrapolation: September 2014',/              
     .      ' ',5X,'EXTRAPOLATION PROCEDURE',///                        
     .      ' ','INPUT PARAMETERS:',/                                   
     .      ' ','NUMBER OF RETURN AGGREGATES (IRAT)   :',I10,/          
     .      ' ','NUMBER OF AMOUNT AGGREGATES (IAAT)   :',I10,/          
     .      ' ','NUMBER OF RETURN BY CLASSES (IRBT)   :',I10,/          
     .      ' ','NUMBER OF AMOUNT BY CLASSES (IABT)   :',I10,/          
     .      ' ','TOTAL NUMBER OF ROWS IN MATRIX       :',I10)           
1004  FORMAT(////,                                                      
     .' ','YEAR OF EXTRAPOLATION = ',I4,///                             
     .' ','RIGHT-HAND SIDE (TARGET) VECTOR:',///)                       
1005  FORMAT(' ','RHS(',I4.4,') = ',F20.3)                              
4000  FORMAT(F20.6)                                                     
      DATA SCALE/1.D-03/ 
	DATA SCALE3/1.D-03/
C	---------------------
C	OPEN DATA FILES
C	---------------------
	OPEN(IUNIT, FILE="/Users/jfo/Documents/State Modeling Project/Stage-II Extrapolation/Data/PRODEXT2012.csv")
        OPEN(JUNIT, FILE="/Users/jfo/Documents/State Modeling Project/Stage-II Extrapolation/Data/TARGETS.TXT",FORM="FORMATTED")		                                               
        OPEN(KUNIT, FILE="/Users/jfo/Documents/State Modeling Project/Stage-II Extrapolation/Output/MINOS.MPS")		                                               
        OPEN(MUNIT,FILE="/Users/jfo/Documents/State Modeling Project/Stage-II Extrapolation/Output/Output.txt")

C     ---------------------                                             
C     INITIALIZE ARRAYS                                                 
C     ---------------------                                             
      CALL ZERO(RHS , NRHS)                                             
      CALL ZERO(DELTA , NRHS)
C     ---------------------                                             
C     INPUT TARGETS                                                     
C     ---------------------
        INQUIRE(UNIT=JUNIT,OPENED=CONNECTED,NAME=FILE_NAME,RECL=LENGTH)
        PRINT *,"UNIT = ", JUNIT
        PRINT *,"CONNECTED = ", CONNECTED
        PRINT *,"FILE NAME = ", FILE_NAME
        PRINT *,"RECORD LENGTH = ", LENGTH
        PRINT *,"BEGIN PROCESSING TARGET FILE"
        READ(JUNIT,FMT='(A40)',IOSTAT=IOPROB)TITLE
        PRINT *,"FIRST READ ATTEMPT"
        PRINT *,"TITLE IS: ",TITLE
        PRINT *,"IOSTAT IS: ", IOPROB
        READ(JUNIT, FMT=*)DUMMY1,DUMMY2,(STNAME(I),I=1,51) 
        PRINT *,DUMMY1,DUMMY2 
        PRINT *,(STNAME(I),I=1,6)
        READ(JUNIT,FMT=*)DUMMY1,DUMMY2,(IFIPS(I),I=1,51)
        PRINT *,DUMMY1,DUMMY2,(IFIPS(I),I=1,6)                                           
        READ(JUNIT,FMT=*)DUMMY1,DUMMY2,(NOBS(I),I=1,51)
        PRINT *,DUMMY1,DUMMY2,(NOBS(I),I=1,6)
C      ----------------------------------------
C      BEGIN READING THE STATE TARGETS (AGGREGATE)
C      ----------------------------------------
        DO NTARGETS=1,17           
                READ(JUNIT,FMT=*)DUMMY1,DUMMY2,(TARGET(NTARGETS,I),I=1,51)
                READ(DUMMY2,FMT='(A1)') LTYPE(NTARGETS)
                READ(DUMMY2,FMT='(1X,A1)') LEVEL(NTARGETS)
                PRINT *, DUMMY1,DUMMY2,TARGET(NTARGETS , 5)
        END DO
C     ------------------------------------------
C     BEGIN READING THE STATE TARGETS (INCOME CLASS)
C     ------------------------------------------
        NTARGETS = 18
        READ(JUNIT,FMT=*)DUMMY1,DUMMY2,(TARGET(NTARGETS,I),I=1,51)
        READ(DUMMY2,FMT='(A1)') LTYPE(18)
        READ(DUMMY2,FMT='(1X,A1)') LEVEL(18)
        PRINT *,"ITYPE IS: ",LTYPE(18)
        PRINT *,"ILEVEL IS:",LEVEL(18)
        PRINT *,DUMMY1,DUMMY2,TARGET(NTARGETS , 5)
        DO NC=2,6
                NTARGETS = 17 + NC
                READ(JUNIT,FMT=*)DUMMY1,DUMMY2,(TARGET(NTARGETS,I),I=1,51)
                PRINT *, DUMMY1,DUMMY2,TARGET(NTARGETS , 5)
        END DO
C        --------------------------------------
C        BEGIN PROCESSING EACH STATE
C        --------------------------------------                
C1     READ(JUNIT,FMT=*,END=5000)ITYPE,ILEVEL,INAME
        PRINT *,"NUMBER OF INCOME CLASSES IS: ",NCLASS
C        
        ISTATE = 19
C
        DO NTARGETS = 1,18
        ILEVEL = LEVEL(NTARGETS)
        ITYPE = LTYPE(NTARGETS)
C                                                                       
C     AGGREGATE TARGETS 
C                                                                       
      IF(ILEVEL  .EQ.  'A')THEN                                         
         IF(ITYPE  .EQ.  'R')THEN                                       
            IRAT = IRAT + 1                                             
         ELSE                                                           
            IAAT = IAAT + 1                                             
         ENDIF                                                          
C                                                                       
C         READ(JUNIT,*,END=5000)(T(I),I=1,NYEARS)                     
         ICOUNT = ICOUNT + 1                                            
         RHS(ICOUNT) = TARGET(NTARGETS , ISTATE)                                        
      ENDIF    
C                                                                       
C     INCOME CLASS TARGETS                                              
C 
      IF(ILEVEL  .EQ.  'B')THEN                                         
         IF(ITYPE  .EQ.  'R')THEN                                       
            IRBT = IRBT + 1                                             
         ELSE                                                           
            IABT = IABT + 1                                             
         ENDIF                                                          
C 
        PRINT *, "ICOUNT IS: ",ICOUNT
         DO 2 NC = 1,NCLASS
C         READ(JUNIT,*,END=5000)(T(I),I=1,NYEARS)                     
         ICOUNT = ICOUNT + 1
2        RHS(ICOUNT) = TARGET(17 + NC , ISTATE)
      ENDIF                                                             
      END DO                                                           
       IROWS = ICOUNT                                                    
C     -------------------------------                                   
C     PRINT SUMMARY                                                     
C     -------------------------------                                   
      WRITE(MUNIT, 1003)IRAT,IAAT,IRBT,IABT,ICOUNT                             
      WRITE(MUNIT, 1004)IYEAR                                                  
      WRITE(MUNIT, 1005)(I,RHS(I),I=1,ICOUNT)                                  
C     -------------------------------                                   
C     INITIALIZE ACCUMULATION ARRAYS.                                   
C     -------------------------------                                   
      CALL ZERO(RA , NRAT)                                              
      CALL ZERO(AA , NAAT)                                              
      CALL ZERO(RB , NRBT*NCLASS)                                       
      CALL ZERO(AB , NABT*NCLASS)                                       
C     ---------------------                                             
C     INITIALIZE MPS FILE.                                              
C     ---------------------                                             
      CALL MPS(1 , KUNIT , JY , NFAM)                                   
C     -------------------------------                                   
C     READ A RECORD.                                                    
C     -------------------------------
        READ(IFIPS(ISTATE),FMT='(F4.0)') THIS_STATE
 10    CALL RDFILE(IUNIT , *9000)
        IF( ( STATECODE .EQ. THIS_STATE ) .AND.  (FILST .EQ. 1. ) )THEN                                        
      NREC = NREC + 1
      CONTROL_TOTAL = CONTROL_TOTAL + FAGI*WT
C	-------------------------------
C	FAMILY IDENTIFIERS - NONE (SOI File)
C	-------------------------------
	TUNO = 1
	NTUF = 1
C     -------------------------------                                   
C     SCALE.                                                            
C     -------------------------------                                   
      WT = MAX(1.D0 , WT)                                               
      WT = WT * 1.D-03                                                  
C     -------------------------------                                   
C     INCOME CLASSIFIER                                                 
C     -------------------------------                                   
      CALL EIC(AGIX , IFLAG)                                          
      FACTOR = 1.D0                                             
      JY = INDXX(AGIX , STUBS , 7 , FACTOR)
C	-------------------------------
C	VARIABLE TRANSFORMATIONS
C	-------------------------------
C	CGAGIX = MAX( 0.D0 , CGNET ) + MAX( 0.D0 , CGD ) 
C                                                                       
C                                                                       
C        MAIN ACCUMULATION SECTION                                      
C                                                                       
C                                                                       
      IF(TUNO .EQ.  1)THEN                                             
          CALL ZERO(RA , NRAT)                                          
          CALL ZERO(AA , NAAT)                                          
          CALL ZERO(RB , NRBT*NCLASS)                                   
          CALL ZERO(AB , NABT*NCLASS)                                   
          NFAM = NFAM + 1                                               
C         WRITE(LUNIT)NFAM,JY,WT                                        
      ENDIF
C	-------------------------------
C	SECTION 00 - ALL RETURNS
C	-------------------------------
C	AA(01) = AA(01) + TOTPOP * SCALE3	                                                             
C	DELTA(01+IRAT) = DELTA(01+IRAT) + TOTPOP * SCALE3 * WT
        RA(01) = RA(01) + 1.D0
        DELTA(01) = DELTA(01) + WT
C     -------------------------------                                   
C     SECTION 01 - FILERS ONLY
C     -------------------------------
C
C	RETURN AGGREGATES
C
	IF( ( FILST .EQ. 1.D0 ) )THEN
		RA(02) = RA(02) + 1.D0
		DELTA(02) = DELTA(02) + WT
C
C	AMOUNT AGGREGATESEITC
C
                AA(01) = AA(01) + INTST *SCALE
		AA(02) = AA(02) + DBE * SCALE
		AA(03) = AA(03) + BIL* SCALE
		AA(04) = AA(04) + CGAGIX * SCALE
		AA(05) = AA(05) + RENTS* SCALE
		AA(06) = AA(06) + TIRAD * SCALE
		AA(07) = AA(07) + PENSIONS * SCALE
		AA(08) = AA(08) + SOCSECX * SCALE
		AA(09) = AA(09) + UCOMP * SCALE
		AA(10) = AA(10) + KEOGH * SCALE
                AA(11) = AA(11) + SEHEALTH*SCALE
		AA(12) = AA(12) + ADJIRA * SCALE
		AA(13) = AA(13) + SLINT* SCALE
		AA(14) = AA(14) + DPAD * SCALE
		AA(15) = AA(15) + EITC * SCALE
C
C		DELTA: NOTE OFFSET FOR ALIGNMENT WITH RHS
C
		DELTA(01+IRAT) = DELTA(01+IRAT) + INTST * SCALE * WT
		DELTA(02+IRAT) = DELTA(02+IRAT) + DBE * SCALE * WT
		DELTA(03+IRAT) = DELTA(03+IRAT) + BIL * SCALE * WT
		DELTA(04+IRAT) = DELTA(04+IRAT) + CGAGIX * SCALE * WT
		DELTA(05+IRAT) = DELTA(05+IRAT) + RENTS * SCALE * WT
		DELTA(06+IRAT) = DELTA(06+IRAT) + TIRAD * SCALE * WT
		DELTA(07+IRAT) = DELTA(07+IRAT) + PENSIONS * SCALE * WT
		DELTA(08+IRAT) = DELTA(08+IRAT) + SOCSECX * SCALE * WT
		DELTA(09+IRAT) = DELTA(09+IRAT) + UCOMP * SCALE * WT
		DELTA(10+IRAT) = DELTA(10+IRAT) + KEOGH * SCALE * WT
		DELTA(11+IRAT) = DELTA(11+IRAT) + SEHEALTH * SCALE * WT
		DELTA(12+IRAT) = DELTA(12+IRAT) + ADJIRA * SCALE * WT
		DELTA(13+IRAT) = DELTA(13+IRAT) + SLINT * SCALE * WT
		DELTA(14+IRAT) = DELTA(14+IRAT) + DPAD * SCALE * WT
		DELTA(15+IRAT) = DELTA(15+IRAT) + EITC * SCALE * WT
C                                        
C     RETURNS BY CLASS - NONE
C
		IDXRB = IRAT + IAAT
C
C                                   
C     AMOUNTS BY CLASS
C
	    IDXAB = IRAT + IAAT + IRBT*6
	    AB(JY , 1) = AB(JY , 1) + WAS * SCALE                             
	    DELTA(IDXAB + JY) = DELTA(IDXAB + JY) + WAS * SCALE * WT
	ENDIF               
C     -------------------------------                                   
C     MPS FILE - 2ND ENTRY (ARRAY)                                      
C     ------------------------------- 
      IORIG = INT( ORIGSEQ )                                  
      IF(TUNO .EQ.  NTUF)THEN                                          
         CALL MPS(2 , KUNIT , JY , IORIG)                                
      ENDIF                                                             
      ENDIF
      GO TO 10                                                          
C     -------------------------------                                   
C     MPS FILE - 3RD ENTRY (RHS)                                        
C     -------------------------------                                   
9000  CALL MPS(3 , KUNIT , JY , NFAM)                                   
C     -------------------------------                                   
C     MPS FILE - FINAL ENTRY (BOUNDS)                                   
C     -------------------------------                                   
      REWIND (IUNIT)                                                    
      CALL MPS(4 , KUNIT , JY , NFAM)                                   
      PRINT 1000,NREC,NFAM
      PRINT *, "Total Federal Adjusted Gross Income Is: ", CONTROL_TOTAL                                              
      STOP                                                              
      END                                                               
