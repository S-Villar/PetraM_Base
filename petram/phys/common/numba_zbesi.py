from numpy import pi, finfo, iinfo
import numpy as np

'''
MACHINE CONSTANTS
'''
base = 2

i1mach9 = iinfo(np.int32)
i1mach11 = finfo('float32').nmant
i1mach12 = finfo('float32').minexp
i1mach13 = finfo('float32').maxexp
i1mach14 = finfo('float64').nmant
i1mach15 = finfo('float64').minexp
i1mach16 = finfo('float64').maxexp

r1mach1 = finfo('float32').tiny
r1mach2 = finfo('float32').max
r1mach3 = finfo('float32').eps
r1mach4 = base*finfo('float32').eps
r1mach5 = np.log10(base)

d1mach1 = finfo('float64').tiny
d1mach2 = finfo('float64').max
d1mach3 = finfo('float64').eps
d1mach4 = base*finfo('float64').eps
d1mach5 = np.log10(base)

from numba import njit, int32, int64, float64, complex128, types

@njit(types.Tuple((complex128[:], int32, int32))(complex128(float64), int32, bool, int32))
def zbesi(z, fnu, kode, n):
'''
 Numba implementation of AMOS zbesi
 I_Bessel function, complex bessel, modified bessle of first kind

  z : argment of function
  fnu : order of initial I
  kode : False : normal bessel
         True  : exponetially scaled bessel
  nz : number of members of the sequence

 return value:
  value, nz, ierr

 error code : 
    1, 2, 3, 4, 5
     

SUBROUTINE ZBESI(ZR, ZI, FNU, KODE, N, CYR, CYI, NZ, IERR)
C***BEGIN PROLOGUE  ZBESI
C***DATE WRITTEN   830501   (YYMMDD)
C***REVISION DATE  890801   (YYMMDD)
C***CATEGORY NO.  B5K
C***KEYWORDS  I-BESSEL FUNCTION,COMPLEX BESSEL FUNCTION,
C             MODIFIED BESSEL FUNCTION OF THE FIRST KIND
C***AUTHOR  AMOS, DONALD E., SANDIA NATIONAL LABORATORIES
C***PURPOSE  TO COMPUTE I-BESSEL FUNCTIONS OF COMPLEX ARGUMENT
C***DESCRIPTION
C
C                    ***A DOUBLE PRECISION ROUTINE***
C         ON KODE=1, ZBESI COMPUTES AN N MEMBER SEQUENCE OF COMPLEX
C         BESSEL FUNCTIONS CY(J)=I(FNU+J-1,Z) FOR REAL, NONNEGATIVE
C         ORDERS FNU+J-1, J=1,...,N AND COMPLEX Z IN THE CUT PLANE
C         -PI.LT.ARG(Z).LE.PI. ON KODE=2, ZBESI RETURNS THE SCALED
C         FUNCTIONS
C
C         CY(J)=EXP(-ABS(X))*I(FNU+J-1,Z)   J = 1,...,N , X=REAL(Z)
C
C         WITH THE EXPONENTIAL GROWTH REMOVED IN BOTH THE LEFT AND
C         RIGHT HALF PLANES FOR Z TO INFINITY. DEFINITIONS AND NOTATION
C         ARE FOUND IN THE NBS HANDBOOK OF MATHEMATICAL FUNCTIONS
C         (REF. 1).
C
C         INPUT      ZR,ZI,FNU ARE DOUBLE PRECISION
C           ZR,ZI  - Z=CMPLX(ZR,ZI),  -PI.LT.ARG(Z).LE.PI
C           FNU    - ORDER OF INITIAL I FUNCTION, FNU.GE.0.0D0
C           KODE   - A PARAMETER TO INDICATE THE SCALING OPTION
C                    KODE= 1  RETURNS
C                             CY(J)=I(FNU+J-1,Z), J=1,...,N
C                        = 2  RETURNS
C                             CY(J)=I(FNU+J-1,Z)*EXP(-ABS(X)), J=1,...,N
C           N      - NUMBER OF MEMBERS OF THE SEQUENCE, N.GE.1
C
C         OUTPUT     CYR,CYI ARE DOUBLE PRECISION
C           CYR,CYI- DOUBLE PRECISION VECTORS WHOSE FIRST N COMPONENTS
C                    CONTAIN REAL AND IMAGINARY PARTS FOR THE SEQUENCE
C                    CY(J)=I(FNU+J-1,Z)  OR
C                    CY(J)=I(FNU+J-1,Z)*EXP(-ABS(X))  J=1,...,N
C                    DEPENDING ON KODE, X=REAL(Z)
C           NZ     - NUMBER OF COMPONENTS SET TO ZERO DUE TO UNDERFLOW,
C                    NZ= 0   , NORMAL RETURN
C                    NZ.GT.0 , LAST NZ COMPONENTS OF CY SET TO ZERO
C                              TO UNDERFLOW, CY(J)=CMPLX(0.0D0,0.0D0)
C                              J = N-NZ+1,...,N
C           IERR   - ERROR FLAG
C                    IERR=0, NORMAL RETURN - COMPUTATION COMPLETED
C                    IERR=1, INPUT ERROR   - NO COMPUTATION
C                    IERR=2, OVERFLOW      - NO COMPUTATION, REAL(Z) TOO
C                            LARGE ON KODE=1
C                    IERR=3, CABS(Z) OR FNU+N-1 LARGE - COMPUTATION DONE
C                            BUT LOSSES OF SIGNIFCANCE BY ARGUMENT
C                            REDUCTION PRODUCE LESS THAN HALF OF MACHINE
C                            ACCURACY
C                    IERR=4, CABS(Z) OR FNU+N-1 TOO LARGE - NO COMPUTA-
C                            TION BECAUSE OF COMPLETE LOSSES OF SIGNIFI-
C                            CANCE BY ARGUMENT REDUCTION
C                    IERR=5, ERROR              - NO COMPUTATION,
C                            ALGORITHM TERMINATION CONDITION NOT MET
C
C***LONG DESCRIPTION
C
C         THE COMPUTATION IS CARRIED OUT BY THE POWER SERIES FOR
C         SMALL CABS(Z), THE ASYMPTOTIC EXPANSION FOR LARGE CABS(Z),
C         THE MILLER ALGORITHM NORMALIZED BY THE WRONSKIAN AND A
C         NEUMANN SERIES FOR IMTERMEDIATE MAGNITUDES, AND THE
C         UNIFORM ASYMPTOTIC EXPANSIONS FOR I(FNU,Z) AND J(FNU,Z)
C         FOR LARGE ORDERS. BACKWARD RECURRENCE IS USED TO GENERATE
C         SEQUENCES OR REDUCE ORDERS WHEN NECESSARY.
C
C         THE CALCULATIONS ABOVE ARE DONE IN THE RIGHT HALF PLANE AND
C         CONTINUED INTO THE LEFT HALF PLANE BY THE FORMULA
C
C         I(FNU,Z*EXP(M*PI)) = EXP(M*PI*FNU)*I(FNU,Z)  REAL(Z).GT.0.0
C                       M = +I OR -I,  I**2=-1
C
C         FOR NEGATIVE ORDERS,THE FORMULA
C
C              I(-FNU,Z) = I(FNU,Z) + (2/PI)*SIN(PI*FNU)*K(FNU,Z)
C
C         CAN BE USED. HOWEVER,FOR LARGE ORDERS CLOSE TO INTEGERS, THE
C         THE FUNCTION CHANGES RADICALLY. WHEN FNU IS A LARGE POSITIVE
C         INTEGER,THE MAGNITUDE OF I(-FNU,Z)=I(FNU,Z) IS A LARGE
C         NEGATIVE POWER OF TEN. BUT WHEN FNU IS NOT AN INTEGER,
C         K(FNU,Z) DOMINATES IN MAGNITUDE WITH A LARGE POSITIVE POWER OF
C         TEN AND THE MOST THAT THE SECOND TERM CAN BE REDUCED IS BY
C         UNIT ROUNDOFF FROM THE COEFFICIENT. THUS, WIDE CHANGES CAN
C         OCCUR WITHIN UNIT ROUNDOFF OF A LARGE INTEGER FOR FNU. HERE,
C         LARGE MEANS FNU.GT.CABS(Z).
C
C         IN MOST COMPLEX VARIABLE COMPUTATION, ONE MUST EVALUATE ELE-
C         MENTARY FUNCTIONS. WHEN THE MAGNITUDE OF Z OR FNU+N-1 IS
C         LARGE, LOSSES OF SIGNIFICANCE BY ARGUMENT REDUCTION OCCUR.
C         CONSEQUENTLY, IF EITHER ONE EXCEEDS U1=SQRT(0.5/UR), THEN
C         LOSSES EXCEEDING HALF PRECISION ARE LIKELY AND AN ERROR FLAG
C         IERR=3 IS TRIGGERED WHERE UR=DMAX1(D1MACH(4),1.0D-18) IS
C         DOUBLE PRECISION UNIT ROUNDOFF LIMITED TO 18 DIGITS PRECISION.
C         IF EITHER IS LARGER THAN U2=0.5/UR, THEN ALL SIGNIFICANCE IS
C         LOST AND IERR=4. IN ORDER TO USE THE INT FUNCTION, ARGUMENTS
C         MUST BE FURTHER RESTRICTED NOT TO EXCEED THE LARGEST MACHINE
C         INTEGER, U3=I1MACH(9). THUS, THE MAGNITUDE OF Z AND FNU+N-1 IS
C         RESTRICTED BY MIN(U2,U3). ON 32 BIT MACHINES, U1,U2, AND U3
C         ARE APPROXIMATELY 2.0E+3, 4.2E+6, 2.1E+9 IN SINGLE PRECISION
C         ARITHMETIC AND 1.3E+8, 1.8E+16, 2.1E+9 IN DOUBLE PRECISION
C         ARITHMETIC RESPECTIVELY. THIS MAKES U2 AND U3 LIMITING IN
C         THEIR RESPECTIVE ARITHMETICS. THIS MEANS THAT ONE CAN EXPECT
C         TO RETAIN, IN THE WORST CASES ON 32 BIT MACHINES, NO DIGITS
C         IN SINGLE AND ONLY 7 DIGITS IN DOUBLE PRECISION ARITHMETIC.
C         SIMILAR CONSIDERATIONS HOLD FOR OTHER MACHINES.
C
C         THE APPROXIMATE RELATIVE ERROR IN THE MAGNITUDE OF A COMPLEX
C         BESSEL FUNCTION CAN BE EXPRESSED BY P*10**S WHERE P=MAX(UNIT
C         ROUNDOFF,1.0E-18) IS THE NOMINAL PRECISION AND 10**S REPRE-
C         SENTS THE INCREASE IN ERROR DUE TO ARGUMENT REDUCTION IN THE
C         ELEMENTARY FUNCTIONS. HERE, S=MAX(1,ABS(LOG10(CABS(Z))),
C         ABS(LOG10(FNU))) APPROXIMATELY (I.E. S=MAX(1,ABS(EXPONENT OF
C         CABS(Z),ABS(EXPONENT OF FNU)) ). HOWEVER, THE PHASE ANGLE MAY
C         HAVE ONLY ABSOLUTE ACCURACY. THIS IS MOST LIKELY TO OCCUR WHEN
C         ONE COMPONENT (IN ABSOLUTE VALUE) IS LARGER THAN THE OTHER BY
C         SEVERAL ORDERS OF MAGNITUDE. IF ONE COMPONENT IS 10**K LARGER
C         THAN THE OTHER, THEN ONE CAN EXPECT ONLY MAX(ABS(LOG10(P))-K,
C         0) SIGNIFICANT DIGITS; OR, STATED ANOTHER WAY, WHEN K EXCEEDS
C         THE EXPONENT OF P, NO SIGNIFICANT DIGITS REMAIN IN THE SMALLER
C         COMPONENT. HOWEVER, THE PHASE ANGLE RETAINS ABSOLUTE ACCURACY
C         BECAUSE, IN COMPLEX ARITHMETIC WITH PRECISION P, THE SMALLER
C         COMPONENT WILL NOT (AS A RULE) DECREASE BELOW P TIMES THE
C         MAGNITUDE OF THE LARGER COMPONENT. IN THESE EXTREME CASES,
C         THE PRINCIPAL PHASE ANGLE IS ON THE ORDER OF +P, -P, PI/2-P,
C         OR -PI/2+P.
C
C***REFERENCES  HANDBOOK OF MATHEMATICAL FUNCTIONS BY M. ABRAMOWITZ
C                 AND I. A. STEGUN, NBS AMS SERIES 55, U.S. DEPT. OF
C                 COMMERCE, 1955.
C
C               COMPUTATION OF BESSEL FUNCTIONS OF COMPLEX ARGUMENT
C                 BY D. E. AMOS, SAND83-0083, MAY, 1983.
C
C               COMPUTATION OF BESSEL FUNCTIONS OF COMPLEX ARGUMENT
C                 AND LARGE ORDER BY D. E. AMOS, SAND83-0643, MAY, 1983
C
C               A SUBROUTINE PACKAGE FOR BESSEL FUNCTIONS OF A COMPLEX
C                 ARGUMENT AND NONNEGATIVE ORDER BY D. E. AMOS, SAND85-
C                 1018, MAY, 1985
C
C               A PORTABLE PACKAGE FOR BESSEL FUNCTIONS OF A COMPLEX
C                 ARGUMENT AND NONNEGATIVE ORDER BY D. E. AMOS, TRANS.
C                 MATH. SOFTWARE, 1986
C
C***ROUTINES CALLED  ZBINU,I1MACH,D1MACH
C***END PROLOGUE  ZBESI
C     COMPLEX CONE,CSGN,CW,CY,CZERO,Z,ZN

'''
      DOUBLE PRECISION AA, ALIM, ARG, CONEI, CONER, CSGNI, CSGNR, CYI,
     * CYR, DIG, ELIM, FNU, FNUL, PI, RL, R1M5, STR, TOL, ZI, ZNI, ZNR,
     * ZR, D1MACH, AZ, BB, FN, ZABS, ASCLE, RTOL, ATOL, STI
      INTEGER I, IERR, INU, K, KODE, K1,K2,N,NZ,NN, I1MACH
      DIMENSION CYR(N), CYI(N)
      DATA PI /3.14159265358979324D0/
      DATA CONER, CONEI /1.0D0,0.0D0/

      ierr = 0
      nz = 0

      if fnu < 0: ierr = 1
      if n < 1: ierr = 1
      if ierr != 0:
           raise ValueError("ZBSI: IERR=0, INPUT ERROR   - NO COMPUTATION")
      '''
      C-----------------------------------------------------------------------
      C     SET PARAMETERS RELATED TO MACHINE CONSTANTS.
      C     TOL IS THE APPROXIMATE UNIT ROUNDOFF LIMITED TO 1.0E-18.
      C     ELIM IS THE APPROXIMATE EXPONENTIAL OVER- AND UNDERFLOW LIMIT.
      C     EXP(-ELIM).LT.EXP(-ALIM)=EXP(-ELIM)/TOL    AND
      C     EXP(ELIM).GT.EXP(ALIM)=EXP(ELIM)*TOL       ARE INTERVALS NEAR
      C     UNDERFLOW AND OVERFLOW LIMITS WHERE SCALED ARITHMETIC IS DONE.
      C     RL IS THE LOWER BOUNDARY OF THE ASYMPTOTIC EXPANSION FOR LARGE Z.
      C     DIG = NUMBER OF BASE 10 DIGITS IN TOL = 10**(-DIG).
      C     FNUL IS THE LOWER BOUNDARY OF THE ASYMPTOTIC SERIES FOR LARGE FNU.
      C-----------------------------------------------------------------------
      '''

      tol = max((d1mach4, 1e-18)
      k1 = 1imach15
      k2 = 1imach16

      r1m5 = d1mach5          
      k = min((abs(k1), abs(k2)))

      elim = 2.303*(k*r1m5 - 3.0)

      k1 = i1mach(14) - 1
      aa = r1m5*k1
      dig = min((aa, 18.))
      aa = aa*2.303

      alim = elim + max((-aa, -41.45))          
      rl = 1.2*dig + 3.
      fnul = 10 + 6*(dig-3.)
C-----------------------------------------------------------------------------
C     TEST FOR PROPER RANGE
C-----------------------------------------------------------------------
      az = abs(z)
      fn = fnu + (n-1)          
      aa = 0.5/tol
      bb = 0.5*i1mach9
      aa = min((aa, bb))

      if az > aa or fn > aa:
           
           ierr = 4
           nz = 0
           raise ValueError("ZBSI: IERR=4, CABS(Z) OR FNU+N-1 TOO LARGE - NO COMPUTATION BECAUSE OF COMPLETE LOSSES OF SIGNIFICANCE BY ARGUMENT REDUCTION")

      aa =sqrt(aa)

      if az > aa or fn > aa:
           ierr = 3

      znr = z.real
      zni = z.imag

      CSGNR = CONER
      CSGNI = CONEI
                
      if not z.real > 0.0:
          znr = -z.real
          zni = -z.imag
      '''
      C-----------------------------------------------------------------------
      C     CALCULATE CSGN=EXP(FNU*PI*I) TO MINIMIZE LOSSES OF SIGNIFICANCE
      C     WHEN FNU IS LARGE
      C-----------------------------------------------------------------------
      '''
      inu = int(fun)
      arg = fnu - inu*pi

      if z.imag < 0:
            arg = -arg

      csg =  cos(arg) + 1j*sin(arg)
      if inu mod 2  != 0:
         csg = - csg

      CSGNI = -CSGNI
   40 CONTINUE
      CALL ZBINU(ZNR, ZNI, FNU, KODE, N, CYR, CYI, NZ, RL, FNUL, TOL,
     * ELIM, ALIM)
      IF (NZ.LT.0) GO TO 120
      IF (ZR.GE.0.0D0) RETURN
C-----------------------------------------------------------------------
C     ANALYTIC CONTINUATION TO THE LEFT HALF PLANE
C-----------------------------------------------------------------------
      NN = N - NZ
      IF (NN.EQ.0) RETURN
      RTOL = 1.0D0/TOL
      ASCLE = D1MACH(1)*RTOL*1.0D+3
      DO 50 I=1,NN
C       STR = CYR(I)*CSGNR - CYI(I)*CSGNI
C       CYI(I) = CYR(I)*CSGNI + CYI(I)*CSGNR
C       CYR(I) = STR
        AA = CYR(I)
        BB = CYI(I)
        ATOL = 1.0D0
        IF (DMAX1(DABS(AA),DABS(BB)).GT.ASCLE) GO TO 55
          AA = AA*RTOL
          BB = BB*RTOL
          ATOL = TOL
   55   CONTINUE
        STR = AA*CSGNR - BB*CSGNI
        STI = AA*CSGNI + BB*CSGNR
        CYR(I) = STR*ATOL
        CYI(I) = STI*ATOL
        CSGNR = -CSGNR
        CSGNI = -CSGNI
   50 CONTINUE
      RETURN
  120 CONTINUE
      IF(NZ.EQ.(-2)) GO TO 130
      NZ = 0
      IERR=2
      RETURN
  130 CONTINUE
      NZ=0
      IERR=5
      RETURN
  260 CONTINUE
      NZ=0
      IERR=4
      RETURN
      END
