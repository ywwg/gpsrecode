#!/usr/bin/python

#take a gpx xml file from http://www.marengo-ltd.com/map/ and recode it to fill out blanks
#and remove numbers from beginning.  Eventually use an sqlite db or something to check for dupes over all routes

import string
import pickle
import os,os.path,sys
import math

import xml.sax
from xml.sax.saxutils import XMLFilterBase,  XMLGenerator

waypoints = []

NAME=0
LAT=1
LON=2

class gpxfilter(XMLFilterBase):
    def __init__(self, In, Out):
        XMLFilterBase.__init__(self, In)
        self.element_stack = []
        self.Out = Out
        self.last_waypoint = None
        self.in_rtept = False

    def startElement(self, name, attrs):
        if name == "rtept":
            self.in_rtept = True
        self.Out.characters("\n" + "   " * len(self.element_stack))
        self.Out.startElement(name, attrs)
        if attrs.has_key('lat'):
            self.element_stack.append([name, attrs['lat'], attrs['lon']])
        else:
            self.element_stack.append([name, None, None])

    def characters(self, content):
        if len(content) == 0:
            return
        white = True
        for c in content:
            if not isWhitespace(c):
                white = False
                break
        if white:
            return

        if self.element_stack[-1][NAME] == "name":
            name = content

            if not self.in_rtept:
            #if '-' not in name: #the title of the route, for instance
                self.Out.characters(name)
            else:
                if name.isdigit():
                    name = self.last_waypoint

                split = name.split('-')
                if len(split) != 2:
                    name = split[0]
                if len(split) == 2 and split[0].isdigit() and len(split[1]) > 0: #get rid of 03-BLAH
                    name = split[1]
                elif len(split) == 2 and split[0].isdigit() and len(split[1]) == 0:
                    name = self.last_waypoint

                if len(name) > 6:
                    name = name[0:6]

                self.last_waypoint = name
                basename = name

                match_index = -1

                # First try original name
                # If name is unique, add it to cache and break
                # Else if coords are close, break (use dupe name)
                # Else loop (try new name)

                found = False
                for i in range(0, 9999):
                    if i > 0:
                        name = basename[0:6 - len(str(i))] + str(i)
                    try:
                        match_index = [n[NAME] for n in waypoints].index(name)
                    except: #didn't find a match
                        if self.element_stack[-2][LAT] is not None:
                            waypoints.append([name,
                                              self.element_stack[-2][LAT],
                                              self.element_stack[-2][LON]])
                        found = True
                        break

                    diff_lat = abs(float(self.element_stack[-2][LAT]) - float(waypoints[match_index][LAT]))
                    diff_lon = abs(float(self.element_stack[-2][LON]) - float(waypoints[match_index][LON]))
                    if diff_lat <= .0003 and diff_lon <= .0003:
                        found = True
                        break
                if not found:
                    print "ran out of tries??? (should never happen)"
                self.Out.characters(name)

    def endElement(self, name):
        if name == "rtept":
            self.in_rtept = False
        if name != self.element_stack[-1][NAME]:
            print "ERROR expected " + str(self.element_stack[-1])[0] + " got " + str(name)
        self.element_stack.pop(-1)
        self.Out.endElement(name)
        self.Out.characters("\n" + "   "*(len(self.element_stack) - 1))

def isWhitespace(s):
    """Is 's' a single character and whitespace?"""
    if s in string.whitespace:
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "need input file and output folder"
        print "waypoints are cached in ~/.gpswaypoints"
        sys.exit(1)
    try:
    #   #try to load waypoint cache
       f = open(os.getenv('HOME')+"/.gpswaypoints","r")
       contrib,waypoints = pickle.load(f)
    except:
        contrib = []
        waypoints = []

    in_name = sys.argv[1]
    out_name = os.path.basename(in_name)
    ext_place = out_name.rfind('.')
    out_name = os.path.join(sys.argv[2],out_name[0:ext_place]+"-recode"+out_name[ext_place:])
    try:
        print "output to", out_name
        out = open(out_name, "w")
    except Exception, e:
        print "couldn't open output file", out_name
        print str(e)
        sys.exit(1)

    In = xml.sax.make_parser()
    Out = XMLGenerator(out)
    filter_handler = gpxfilter(In, Out)
    try:
        filter_handler.parse(sys.argv[1])
    except IOError, e:
        print "couldn't open input file"
        sys.exit(1)

    f = open(os.getenv('HOME')+"/.gpswaypoints","w")
    #save the cache
    if os.path.split(sys.argv[1])[1] not in contrib:
       contrib = contrib+[os.path.split(sys.argv[1])[1]]
    pickle.dump([contrib,waypoints],f)
    out.close()
