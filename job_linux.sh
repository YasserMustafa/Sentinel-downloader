#!/usr/bin/env bash


#This bash script use the PID method to prevent duplicate run of the main.py
#See the following link for more information about the PID method
#http://bencane.com/2015/09/22/preventing-duplicate-cron-job-executions/
#This bash script can be launched thanks to the crontable program.
#exemple: 0 20 * * * ~/job_linux.sh
#will run the joblinux.sh every day at 8pm and no more than one instance can run at a time thanks to this bash script.


pidfilename="/job_linux.pid"
mainScript="/main.py"
logger="/activity.log"

BASEDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $BASEDIR
PIDFILE=$BASEDIR$pidfilename
echo $PIDFILE

if [ -f $PIDFILE ]
then
  PID=$(cat $PIDFILE)
  ps -p $PID > /dev/null 2>&1
  if [ $? -eq 0 ]
  then
    echo "Process already running"
    exit 1
  else
    ## Process not found assume not running
    echo $$ > $PIDFILE
    if [ $? -ne 0 ]
    then
      echo "Could not create PID file"
      exit 1
    fi
  fi
else
  echo $$ > $PIDFILE
  if [ $? -ne 0 ]
  then
    echo "Could not create PID file"
    exit 1
  fi
fi

#Run the python script main.py
python $BASEDIR$mainScript

rm $PIDFILE

#mail -s “logger_Sentinel” n.debonnaire@gmail.com < $BASEDIR$logger
