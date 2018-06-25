#!/bin/bash
CMD="python -u stage2.py"  # -u option forces unbuffered output
LOG=stage2.log
MSG="infeasible"  # possibly customize MSG when changing LP solver

# show time this script starts running
date

# start CMD running in background writing stdout and stderr to LOG
$CMD > $LOG 2>&1 &

# save process id of the background process
PID=$!

# periodically check LOG for MSG indicating background process needs to stop
while sleep 10
do
    if grep -q -i "$MSG" $LOG
    then
        kill $PID > /dev/null 2>&1
        echo "INFEASIBLE STOP: read $LOG file for details"
        date
        exit 0
    fi
    # also check if background process has finished execution
    if ! kill -0 $PID > /dev/null 2>&1
    then
        echo "FINISHED EXECUTION: read $LOG file for details"
        date
        exit 0
    fi
done
