#!/usr/bin/python

# Take a gpx xml file from RideWithGPS and convert the route points to something my ETrex can use.

import math
import os
import os.path
import pickle
import re
import string
import sys

import xml.sax
from xml.sax.saxutils import XMLFilterBase,  XMLGenerator

waypoints = []

NAME=0
LAT=1
LON=2

def shorten_rtept(rtept):
    """ETrex only supports 6 upper case characters"""
    return rtept.upper()[:6].strip()

def comment_to_rtept(comment):
    """Take a ridewithGPS comment and make a nice short routepoint out of it"""

    if comment == "Start of route":
        return "START"
    elif comment == "End of route":
        return "END"
    elif comment == "Turn right":
        return "RIGHT"
    elif comment == "Turn left":
        return "LEFT"

    ONTO_MATCHER = re.compile("onto (.*)$")
    STAY_MATCHER = re.compile("to stay on (.*)$")
    TOWARD_MATCHER = re.compile("toward (.*)$")
    TAKE_MATCHER = re.compile("Take the (.*)$")

    matchers = (ONTO_MATCHER, STAY_MATCHER, TOWARD_MATCHER, TAKE_MATCHER)

    for m in matchers:
        match = m.search(comment)
        if match is not None:
            return match.group(1)

    print "Warning, unhandled comment format:", comment
    return comment


class TurnFilter(XMLFilterBase):
    """A filter which reads the comments from a gpx file into a map for later processing"""

    def __init__(self, In):
        XMLFilterBase.__init__(self, In)
        self.TurnMap = {}
        self._in_rtept = ""
        self._in_cmt = False

    def startElement(self, name, attrs):
        if name == "rtept":
            self._in_rtept = "%s,%s" % (attrs['lat'], attrs['lon'])
        elif name == "cmt":
            self._in_cmt = True

    def endElement(self, name):
        if name == "rtept":
            self._in_rtept = ""
        elif name == "cmt":
            self._in_cmt = False

    def characters(self, content):
        if not self._in_cmt:
            return

        self.TurnMap[self._in_rtept] = shorten_rtept(comment_to_rtept(content))


class gpxfilter(XMLFilterBase):
    """A filter which mostly passes through the XML, but munges the route point names according
    to the comment map.
    """


    def __init__(self, In, Out, turn_map):
        XMLFilterBase.__init__(self, In)
        self._turn_map = turn_map
        self.element_stack = []
        self.Out = Out
        self.last_waypoint = None
        self.in_rtept = False
        self.in_name = False
        self.in_cmt = False

    def startElement(self, name, attrs):
        if name == "rtept":
            self.in_rtept = True
        elif name == "name":
            self.in_name = True
        elif name == "cmt":
            self.in_cmt = True
            return
        self.Out.characters("\n" + "   " * len(self.element_stack))
        self.Out.startElement(name, attrs)
        if attrs.has_key('lat'):
            self.element_stack.append([name, attrs['lat'], attrs['lon']])
        else:
            self.element_stack.append([name, None, None])

    def endElement(self, name):
        if name == "rtept":
            self.in_rtept = False
        elif name == "name":
            self.in_name = False
        elif name == "cmt":
            self.in_cmt = False
            return
        if name != self.element_stack[-1][NAME]:
            print "ERROR expected " + str(self.element_stack[-1])[0] + " got " + str(name)
        self.element_stack.pop(-1)
        self.Out.endElement(name)
        self.Out.characters("\n" + "   "*(len(self.element_stack) - 1))

    def characters(self, content):
        if self.in_cmt:
            return
        if not self.in_name or not self.in_rtept:
            self.Out.characters(content.strip())
            return

        # Let it blow up on key error
        name = self._turn_map["%s,%s" % (self.element_stack[-2][LAT], self.element_stack[-2][LON])]

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

    turn_mapper = TurnFilter(In)
    turn_mapper.parse(sys.argv[1])

    Out = XMLGenerator(out)
    filter_handler = gpxfilter(In, Out, turn_mapper.TurnMap)
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
