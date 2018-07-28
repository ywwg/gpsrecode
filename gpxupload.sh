#!/bin/bash

if [ ! -f "$1" ] ; then	
	echo need a filename to send to gps
	exit 1
fi

# disable carrier detect as per:
# http://comments.gmane.org/gmane.comp.hardware.gps.gpsbabel.general/6232
# http://forum.nginx.org/read.php?30,135400,135554
stty -F /dev/ttyUSB0 clocal

filename="$1"
#waypoints=`xmlstarlet el "$filename" | grep name | wc -l`
#waypoint_count=0

sudo gpsbabel -D 5 -r -i gpx -f "$filename" -o garmin -F /dev/ttyUSB0

#(
#    for line in `sudo gpsbabel -D 5 -r -i gpx -f "$filename" -o garmin -F /dev/ttyUSB0 2&>1`; 
#    do
#        if [[ $line == *RTEWPT* ]] ; then
#            let percent=100*waypoint_count/waypoints
#            let waypoint_count=waypoint_count+1
#            echo "$percent"
#        fi
#    done
#) | 
#zenity --progress --title "Uploading to GPS"
