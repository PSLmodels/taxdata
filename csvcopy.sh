#!/bin/bash
# copies CSV files produced by csvmake.sh to the specified taxcalc directory

function usage {
    echo "USAGE: ./csvcopy.sh DATATYPE TAXCALCDIR [dryrun]"
    echo "       where DATATYPE can be puf or cps"
    echo "         and TAXCALCDIR is path to Tax-Calculator taxcalc directory"
    echo "             (TAXCALCDIR must end with a / character)"
    echo "         and dryrun is optional signal to skip the CSV copying"
    echo "       Note: run ./csvcopy.sh in top-level taxdata directory"
    exit 1
}

function copyifdiff {
    # FUNCTION ARGUMENTS: $1=FILENAME $2=SRCPATH $3=DSTPATH $4=DRYRUN
    if [ -f $3 ]; then
        diff --brief $2 $3 >/dev/null
        ISDIFF=$?
        if [ $ISDIFF -eq 0 ]; then
            echo "NO DIFFERENCES IN $1 ==> FILE COPY IS UNNECESSARY"
        else
            echo "SOME DIFFERNCES IN $1 ==> FILE COPY IS NECESSARY"
        fi
    else
        echo "TAXCALCDIR FILE $1 DOES NOT EXIST ==> COPY MAY BE INEFFECTIVE"
        ISDIFF=1
    fi
    if [ $ISDIFF -eq 1 ] && [ $4 -eq 0 ]; then
        cp $2 $3
        echo "COPIED $2 TO $3"
    fi
}

# process command-line arguments
if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    echo "ERROR: number of command-line arguments is not two or three"
    usage
fi
DTYPE=$1
if [ $DTYPE != "puf" ] && [ $DTYPE != "cps" ]; then
    echo "ERROR: DATATYPE is neither puf nor cps"
    usage
fi
TAXCALCDIR=$2
if [[ ! $TAXCALCDIR = */ ]]; then
    echo "ERROR: $TAXCALCDIR does not end in /"
    usage
fi
if [ ! -d $TAXCALCDIR ]; then
    echo "ERROR: $TAXCALCDIR is not a directory"
    usage
fi
if [ $# -eq 3 ]; then
    if [ $3 == "dryrun" ]; then
        DRYRUN=1
    else
        echo "ERROR: unknown option $3"
        usage
    fi
else
    DRYRUN=0
fi

# copy $DTYPE_data/$DTYPE CSV file if different
TAXDATADIR=$DTYPE"_data/"
if [ $DTYPE == "cps" ]; then
    # gzipped file is in TAXCALCDIR directory
    SRCFILENAME=$DTYPE".csv.gz"
    DSTFILENAME=$SRCFILENAME
else
    # ungzipped file is in parent directory of TAXCALCDIR
    SRCFILENAME=$DTYPE".csv"
    DSTFILENAME="../"$SRCFILENAME
fi
copyifdiff $SRCFILENAME $TAXDATADIR$SRCFILENAME $TAXCALCDIR$DSTFILENAME $DRYRUN

# copy puf_stage1/growfactors.csv file if different
TAXDATADIR="puf_stage1/"
FILENAME="growfactors.csv"
copyifdiff $FILENAME $TAXDATADIR$FILENAME $TAXCALCDIR$FILENAME $DRYRUN

# copy $DTYPE_stage2/$DTYPE_weights.csv.gz file if different
TAXDATADIR=$DTYPE"_stage2/"
FILENAME=$DTYPE"_weights.csv.gz"
copyifdiff $FILENAME $TAXDATADIR$FILENAME $TAXCALCDIR$FILENAME $DRYRUN

# copy $DTYPE_stage3/$DTYPE_ratios.csv file if different
TAXDATADIR=$DTYPE"_stage3/"
FILENAME=$DTYPE"_ratios.csv"
if [ $DTYPE == "puf" ]; then
    copyifdiff $FILENAME $TAXDATADIR$FILENAME $TAXCALCDIR$FILENAME $DRYRUN
fi

# copy $DTYPE_stage4/$DTYPE_benefits.csv.gz file if different
TAXDATADIR=$DTYPE"_stage4/"
FILENAME=$DTYPE"_benefits.csv.gz"
if [ $DTYPE == "cps" ]; then
    copyifdiff $FILENAME $TAXDATADIR$FILENAME $TAXCALCDIR$FILENAME $DRYRUN
fi

exit 0
