#!/usr/bin/env python3

"""
this is a simple grading tool for slack.  We post a simple
"+1"-style grade for a student to a slack channel using an incoming
webhook.
"""

from __future__ import print_function

import argparse
import datetime
import json
import os
import shlex
import subprocess
import sys

import configparser
import validators

def run(string):
    """ run a UNIX command """

    # shlex.split will preserve inner quotes
    prog = shlex.split(string)
    p0 = subprocess.Popen(prog, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)

    stdout0, stderr0 = p0.communicate()
    rc = p0.returncode
    p0.stdout.close()

    return stdout0, stderr0, rc

class Grade(object):
    """ a new grade entry that we will be adding to slack and our records """

    def __init__(self, student, remark=None, channel="#general"):
        """ a Grade keeps track of a single entry in our grade records """
        if student.startswith("@"):
            student = student.split("@")[1]
        self.student = student

        self.remark = remark

        if not channel.startswith("#"):
            channel = "#" + channel
        self.channel = channel

        # record the data / time
        self.date = "{}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def slack_post(self, params):
        """ post our grade to slack """
        webhook = params["web-hook"]

        payload = {}
        payload["channel"] = self.channel
        payload["text"] = "<@{}> : {}".format(self.student, self.remark)
        payload["link_names"] = 1
        cmd = "curl -X POST --data-urlencode 'payload={}' {}".format(json.dumps(payload), webhook)
        so = run(cmd)

    def update_grades(self, params):
        """ update the grade log """
        log_file = params["grade-log"]

        with open(log_file, "a") as lf:
            lf.write("{}\n".format(self.__str__()))

    def __str__(self):
        return "{}, {:20}, {:12}, {}".format(self.date, self.student, self.channel, self.remark)

class Record(object):
    """ a recorded grade from our logs """

    def __init__(self, student, date, remark, channel):
        self.student = student
        self.date = date
        self.remark = remark
        self.channel = channel

    def __lt__(self, other):
        """ compare on student name for sorting """
        return self.student < other.student


def main(student=None, remark=None, channel=None,
         class_name=None,
         just_summary=False):
    """ the main driver """
    params = get_defaults(class_name)

    # if we just want a summary, do it
    if just_summary:
        report(params)
    else:
        # create the grade object
        g = Grade(student, remark=remark, channel=channel)

        # post the +1 to slack
        g.slack_post(params)

        # update the grade log
        g.update_grades(params)


def report(params):
    """ generate a simple report of the form 'student, grade' """
    records = []

    # open up the log file and create a list of records
    with open(params["grade-log"]) as lf:
        for line in lf:
            if line.startswith("#") or line.strip() == "":
                continue
            date, student, channel, remark = line.split(",")
            records.append(Record(student, date, remark, channel))

    # find unique student names
    names = sorted(set([q.student for q in records]))

    for name in names:
        points = len([q for q in records if q.student == name])
        print("{:20}, {}".format(name, points))



def get_args():
    """ parse commandline arguments """

    parser = argparse.ArgumentParser()

    parser.add_argument("--setup", help="define or modify the settings for your class",
                        action="store_true")
    parser.add_argument("--report", help="write out a summary of points by student",
                        action="store_true")
    parser.add_argument("--class_name", type=str, help="name of class to grade",
                        default=None)
    parser.add_argument("student", type=str, nargs="?",
                        help="name of student to grade",
                        default="")
    parser.add_argument("comment", type=str, nargs="?",
                        help="comment to use as grade", default="")
    parser.add_argument("channel", type=str, nargs="?",
                        help="channel to post to",
                        default="#general")
    args = parser.parse_args()

    if not args.setup and not args.report:
        # in this case, we require the user name and comment
        if args.student == "" or args.comment == "":
            parser.print_help()
            sys.exit("\nstudent and comment are required")

    return args

def get_defaults(class_name):
    """ we store our default settings in a ~/.slackgrader file """
    home_path = os.getenv("HOME")
    defaults_file = os.path.join(home_path, ".slackgrader")

    try:
        cf = configparser.ConfigParser()
        cf.read(defaults_file)
    except:
        sys.exit("Error: unable to read ~/.slackgrader")

    # if no class name was defined, then we use the first
    if class_name is None:
        class_name = cf.sections()[0]

    defaults = {}
    defaults["web-hook"] = cf.get(class_name, "web-hook")
    defaults["grade-log"] = cf.get(class_name, "grade-log")

    return defaults

def log_name(log_path, class_name):
    """ return the name of the log file we'll use """
    return os.path.join(log_path, "{}-slackgrades.log".format(class_name.strip()))

def setup_params():
    """ query the user to get the default parameters for this grade session """

    # ask for the name of this class
    class_name = input("Enter the name of the class: ")
    if class_name == "":
        sys.exit("Error: class name cannot be empty")

    # ask for the slack api webhook
    web_hook = input("Enter the full URL for your slack webhook: ")
    if not validators.url(web_hook):
        sys.exit("Error: slack webhook does not seem to be a valid URL")

    # ask for the path to the grade log
    home_path = os.getenv("HOME")

    log_path = input("Enter the full path to the grade log [{}]: ".format(home_path))
    if log_path == "":
        log_path = home_path

    grade_log = log_name(log_path, class_name)

    if os.path.isfile(grade_log):
        # if it exists, say we'll append.
        print("Grade log already exists.  We'll append")
        print("using logfile: {}".format(grade_log))
    else:
        # create a stub
        try:
            lf = open(grade_log, "w")
        except IOError:
            sys.exit("Error: unable to create the log file")
        else:
            lf.write("# slack grade log log for class: {}\n".format(class_name))
            lf.close()

    # write defaults file -- it's an ini-style file
    defaults_file = os.path.join(home_path, ".slackgrader")

    # if it exists, read its contents
    if os.path.isfile(defaults_file):
        try:
            cf = configparser.ConfigParser()
            cf.read(defaults_file)
        except:
            sys.exit("Error: default file exists but is unreadable")
    else:
        cf = configparser.ConfigParser({})

    # delete our class section if it is already there
    cf.remove_section(class_name)

    # now add it to start clean
    cf.add_section(class_name)

    # add the options
    cf.set(class_name, "web-hook", web_hook)
    cf.set(class_name, "grade-log", grade_log)

    # write it out
    with open(defaults_file, "w") as f:
        cf.write(f)


if __name__ == "__main__":
    args = get_args()

    if args.setup:
        setup_params()

    elif args.report:
        main(just_summary=True)

    else:
        main(args.student, args.comment, args.channel, class_name=args.class_name)
