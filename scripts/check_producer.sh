#!/bin/bash

# Exit codes
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2
STATE_UNKNOWN=3

# Warning threshold
thresh_warn=70
# Critical threshold
thresh_crit=85

BASENAME=`which basename`
PROGNAME=`$BASENAME $0`

PRODUCER_HOME="/opt/producers"
BACK_OFF_INDICATOR="/var/run/reporting-producer/back-off"

function print_usage {
   # Print a short usage statement
   echo "Usage: $PROGNAME -w <limit> -c <limit> -d <home-dir>"
}

# Parse command line options
while [ "$1" ]; do
   case "$1" in
       -h | --help)
           print_usage
           exit $STATE_OK
           ;;
       -w | --warning | -c | --critical)
           if [[ -z "$2" || "$2" = -* ]]; then
               # Threshold not provided
               echo "$PROGNAME: Option '$1' requires an argument"
               print_usage
               exit $STATE_UNKNOWN
           elif [[ "$2" = +([0-9]) ]]; then
               # Threshold is a number (MB)
               thresh=$2
           elif [[ "$2" = +([0-9])% ]]; then
               # Threshold is a percentage
               thresh=$(( tot_mem * ${2%\%} / 100 ))
           else
               # Threshold is neither a number nor a percentage
               echo "$PROGNAME: Threshold must be integer or percentage"
               print_usage
               exit $STATE_UNKNOWN
           fi
           [[ "$1" = *-w* ]] && thresh_warn=$thresh || thresh_crit=$thresh
           shift 2
           ;;
       -d | --directory)
           PRODUCER_HOME=$2
           ;;
       -?)
           print_usage
           exit $STATE_OK
           ;;
       *)
           echo "$PROGNAME: Invalid option '$1'"
           print_usage
           exit $STATE_UNKNOWN
           ;;
   esac
done

parse_yaml() {
   local prefix=$2
   local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
   sed -ne "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
   awk -F$fs '{
      indent = length($1)/2;
      vname[indent] = $2;
      for (i in vname) {if (i > indent) {delete vname[i]}}
      if (length($3) > 0) {
         vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
         printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
      }
   }'
}

CONFIG_FILE="/etc/reporting-producer/config.yaml"
prog="producer.py"

has_pusher=0
if grep -q '^pusher:' $CONFIG_FILE; then
    has_pusher=1
fi

num_process=$(pgrep -fl $prog | grep -v grep | grep -v bash | wc -l)
if [ "$has_pusher" -eq 0 ] && [ "$num_process" -eq 1 ]; then
    echo "Producer OK: no pusher in config"
    exit $STATE_OK
elif [ "$has_pusher" -eq 1 ] && [ "$num_process" -eq 1 ]; then
    echo "Producer CRITICAL: main process or pusher process is dead"
    exit $STATE_CRITICAL
elif [ "$num_process" -eq 0 ]; then
    echo "Producer CRITICAL: producer is not running"
    exit $STATE_CRITICAL
fi

RESULT_MSG=`$PRODUCER_HOME/client.py check nagios`
RESULT=$?
if [ $RESULT -gt 0 ]; then
    echo $RESULT_MSG
    exit $RESULT
fi

if [ -f $BACK_OFF_INDICATOR ]; then
    echo "Producer CRITICAL: Remote server not accessible, backing off"
    exit $STATE_CRITICAL
fi

eval $(parse_yaml $CONFIG_FILE)

buffer_dir=$(echo $output__buffer__directory|tr -d '\n'|tr -d '\r')
buffer_size=$(echo $output__buffer__size|tr -d '\n'|tr -d '\r')

if [ ! -z "$buffer_dir" ] && [ ! -z "$buffer_size" ]; then
    dir_usage=$(du -sm $buffer_dir|cut -f1)
    if which bc 2>1 >/dev/null; then
        percentage=$(echo "${dir_usage} * 1024 * 100 / ${buffer_size}" | bc)
    else
        percentage=$((${dir_usage} * 1024 * 100 / ${buffer_size}))
    fi

    if [ $percentage -gt $thresh_warn ]; then
        echo "Producer WARNING: cache size reached $thresh_warn%"
        exit $STATE_WARNING
    elif [ $percentage -gt $thresh_crit ]; then
        echo "Producer CRITICAL: cache size reached $thresh_crit%"
        exit $STATE_CRITICAL
    fi

    echo "Producer OK: buffer usage is $percentage%"
    exit $STATE_OK
fi

echo "Producer WARNING: config file may be changed after producer is started"
exit $STATE_WARNING
