These are some really bad utilities for creating GPX files that will
work with my old-ass 2005 Garmin ETrex.  The ETrex has some great
properties:

 * No maps
 * Very basic breadcrumb support
 * max 127 points per route
 * max 6 uppercase letters per point
 * built like a tank and has survived multiple drops
 * takes AA batteries
 * simple serial cable track upload

This device is very endearing even though it's objectively bad.

== Use ==

Currently tcxrecode.py is the better-supported converter.  I use it
to take TCX files from ridewithgps and convert them to GCX.  Then
I use gpxupload.sh to upload the files to my etrex.
