#!/usr/bin/python

#take a tcx xml file from ridewithgps.com and recode it to gpx,
#using the notes to name the waypoints and filling out blanks

#build up a list of route points and comments
#go through points
#if corresponding comment, use comment.  otherwise use last comment with incremented number

import string
import pickle
import os,os.path,sys
import math

import xml.sax
from xml.sax.saxutils import XMLFilterBase,  XMLGenerator

class tcxfilter(XMLFilterBase):
    def __init__(self, In, Out):
        XMLFilterBase.__init__(self, In)
        self.Out = Out
        self.in_coursepoint = False
        self.current_coursepoint = {'lat':None, 'lon':None, 'name':None}
        self.element_type = ""
        self.value = None
        self.coursepoints = []
        self.process_chars = False
        self.route_name = None

    def startElement(self, name, attrs):
        if name == "Name" and self.route_name is None:
            self.element_type = "TEXT"
            self.process_chars = True
            return
        if name == "CoursePoint":
            self.in_coursepoint = True
        if not self.in_coursepoint:
            return
        if name == "LatitudeDegrees":
            if self.current_coursepoint['lat'] is not None:
                print "ERROR: current trackpoint already has latitude set", self.current_coursepoint['lat']
            self.element_type = "NUMBER"
        elif name == "LongitudeDegrees":
            if self.current_coursepoint['lon'] is not None:
                print "ERROR: current trackpoint already has longitude set", self.current_coursepoint['lon']
            self.element_type = "NUMBER"
        elif name == "Name":
            if self.current_coursepoint['name'] is not None:
                print "ERROR: current trackpoint already has name set", self.current_coursepoint['name']
            self.element_type = "TEXT"
        else:
            return
        self.process_chars = True
        self.value = None

    def endElement(self, name):
        if self.route_name is None:
            if name == "Name":
                self.route_name = self.value
                self.process_chars = False
                self.value = None
                return
        if name == "CoursePoint":
            self.in_coursepoint = False
            self.coursepoints.append(self.current_coursepoint)
            self.current_coursepoint = {'lat':None, 'lon':None, 'name':None}
            self.process_chars = False
        elif name == "Course":
            self.write_course()
        elif name == "LatitudeDegrees":
            self.current_coursepoint['lat'] = self.value
            self.process_chars = False
        elif name == "LongitudeDegrees":
            self.current_coursepoint['lon'] = self.value
            self.process_chars = False
        elif name == "Name":
            self.current_coursepoint['name'] = self.value
            self.process_chars = False

    def characters(self, content):
        if not self.process_chars:
            return

        if self.element_type == "NUMBER":
            self.value = float(content.strip())
        elif self.element_type == "TEXT":
            self.value = content.strip()

    def write_course(self):
        schema = {"xmlns:xsi":"http://www.w3.org/2001/XMLSchema-instance",
                  "xmlns": "http://www.topografix.com/GPX/1/1",
                  "version": "1.1",
                  "xsi:schemaLocation": "http://www.topografix.com/GPX/1/1    http://www.topografix.com/GPX/1/1/gpx.xsd",
                  "creator": "tcxrecode.py By Owen Williams"}
        self.Out.startElement("gpx", schema)
        self.Out.characters("\n    ")
        self.Out.startElement("rte", {})
        self.Out.characters("\n" + "    " * 2)
        self.Out.startElement("name", {})
        self.Out.characters(self.route_name)
        self.Out.endElement("name")
        last_name = "START"
        for i,r in enumerate(self.coursepoints):
            if r['name'] == "" or r['name'] is None:
                r['name'] = last_name
            r['name'] = self.rewrite_name(r)
            # rewrite this item in the list so the name will be correct.
            self.coursepoints[i] = r
            self.write_element(r)
            last_name = r['name']
        self.Out.characters("\n    ")
        self.Out.endElement("rte")
        self.Out.characters("\n")
        self.Out.endElement("gpx")

    def rewrite_name(self, coursepoint):
        # First try original name
        # If name is unique, hurray
        # (UNDONE: Else if coords are close, break (use dupe name))
        # Else loop (try new name)

        # names must be upper case and at most 6 chars for my garmin etrex
        basis = coursepoint['name'][0:6].upper().strip()
        name = basis
        for i in range(0, 9999):
            if i > 0:
                name = basis[0:6 - len(str(i))] + str(i)
            # horrific, but who cares.
            if name not in [n['name'] for n in self.coursepoints]:
                return name
        return "UNKNOWN"

    def write_element(self, coursepoint):
        attrs = {'lat':str(coursepoint['lat']), 'lon':str(coursepoint['lon'])}
        self.Out.characters("\n" + "    " * 2)
        self.Out.startElement("rtept", attrs)
        self.Out.characters("\n" + "    " * 3)
        self.Out.startElement("name", {})
        self.Out.characters(coursepoint['name'])
        self.Out.endElement("name")
        self.Out.characters("\n" + "    " * 2)
        self.Out.endElement("rtept")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "need input file and output folder"
        print "waypoints are cached in ~/.gpswaypoints (DISABLED AND UNSUPPORTED ANYWAY)"
        sys.exit(1)
    #try:
    ##   #try to load waypoint cache
    #   f = open(os.getenv('HOME')+"/.gpswaypoints","r")
    #   contrib,waypoints = pickle.load(f)
    #except:
    #    contrib = []
    #    waypoints = []

    in_name = sys.argv[1]
    ext_place = in_name.rfind('.')
    out_name = os.path.join(sys.argv[2],in_name[0:ext_place]+"-recode.gpx")
    try:
        out = open(out_name, "w")
    except Exception, e:
        print "couldn't open output file", out_name
        print str(e)
        sys.exit(1)

    In = xml.sax.make_parser()
    Out = XMLGenerator(out)
    filter_handler = tcxfilter(In, Out)
    try:
        filter_handler.parse(sys.argv[1])
    except IOError, e:
        print "couldn't open input file"
        sys.exit(1)

    #f = open(os.getenv('HOME')+"/.gpswaypoints","w")
    ##save the cache
    #if os.path.split(sys.argv[1])[1] not in contrib:
    #   contrib = contrib+[os.path.split(sys.argv[1])[1]]
    #pickle.dump([contrib,waypoints],f)
    #out.close()
