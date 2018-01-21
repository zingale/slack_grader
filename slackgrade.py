#!/usr/bin/env python3

"""
this is a simple grading tool for slack.  We post a simple
"+1"-style grade for a student to a slack channel the slack API.
"""

from __future__ import print_function

import argparse
import datetime
import os
import sys

import configparser

from slackclient import SlackClient

class SlackUser(object):
    """an object that holds the information about slack users, to allow
    for mapping between user name and id"""

    def __init__(self, name, slack_id):
        self.name = name
        self.slack_id = slack_id
        self.im_channel = None

    def add_im(self, im_channel):
        self.im_channel = im_channel

    def post_str(self):
        return r"<@{}>".format(self.slack_id)

    def __str__(self):
        return self.name

def get_post_id_from_name(name, users):
    for u in users:
        if name in u.name:
            return u.post_str()

class Grade(object):
    """ a new grade event that we will be adding to slack and our records """

    def __init__(self, student, remark=None, channel="#general", users=None):
        """ a Grade keeps track of a single grading event in our grade records
        note: we can have multiple students with a single remark """
        self.student = []
        for s in student:
            if s.startswith("@"):
                snew = s.split("@")[1]
                self.student.append(snew)
            else:
                self.student.append(s)

        # translate the names to IDs
        if users is not None:
            sids = []
            for s in self.student:
                slack_id = get_post_id_from_name(s, users)
                if slack_id is not None:
                    sids.append(slack_id)
                else:
                    sys.exit("student {} does not exist".format(s))

            self.sids = sids
        else:
            self.sids = [""]

        self.remark = remark

        if not channel.startswith("#"):
            channel = "#" + channel
        self.channel = channel

        # record the data / time
        self.date = "{}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def slack_post(self, params):
        """ post our grade to slack """

        sc = SlackClient(params["token"])

        stext = ""
        for s in self.sids:
            stext += "{} ".format(s)

        message = "{} : {}".format(stext, self.remark)

        sc.api_call(
            "chat.postMessage",
            channel=self.channel,
            as_user=False,
            username="grader",
            icon_emoji=":farnsworth:",
            text=message)

    def update_grades(self, params):
        """ update the grade log """
        log_file = params["grade-log"]

        with open(log_file, "a") as lf:
            lf.write("{}\n".format(self.__str__()))

    def __str__(self):
        sstring = ""
        for s in self.student:
            sstring += "{}, {:20}, {:12}, {}\n".format(self.date, s, self.channel, self.remark)
        return sstring


class Record(object):
    """ a recorded grade from our logs """

    def __init__(self, student, date, remark, channel):
        self.student = student.strip()
        self.date = date.strip()
        self.remark = remark.strip()
        self.channel = channel.strip()

    def __lt__(self, other):
        """ compare on student name for sorting """
        return self.student < other.student

    def __str__(self):
        rstr = "{}: ({}; {}) {}".format(self.student, self.date, self.channel, self.remark)
        return rstr


class Student(object):
    """ a collection of all the records for a particular student """

    def __init__(self, student, users):
        self.student = student
        self.records = []

        # get the user ID and IM channel from the user list
        for u in users:
            if self.student in u.name:
                self.im_channel = u.im_channel
                self.slack_id = u.slack_id

    def direct_message(self, params):
        """send a direct message to the student's slack DM channel
        summarizing the grades"""

        text = """Here is your class participation summary ({}):\n""".format(self.student)
        for r in self.records:
            tmp = "{}".format(r)
            tmp = tmp.replace("{}:".format(r.student), "")
            text += "{}\n".format(tmp)

        sc = SlackClient(params["token"])

        sc.api_call(
            "chat.postMessage",
            channel=self.im_channel,
            as_user=False,
            username="grader",
            icon_emoji=":farnsworth:",
            text=text)

def get_users(params):

    # first get user Ids
    sc = SlackClient(params["token"])

    # note: we may run up against a limit here
    # eventually need to support pagination
    user_info = sc.api_call(
        "users.list",
        limit=100)

    users = []
    for rec in user_info["members"]:
        name = rec["name"]
        slack_id = rec["id"]
        users.append(SlackUser(name, slack_id))

    # now add the IM channel -- note: an IM channel will only exist if the 
    # user has already interacted 
    # https://stackoverflow.com/questions/37598354/slack-dm-to-a-user-not-in-im-list
    im_info = sc.api_call(
        "im.list",
        limit=100)

    print(im_info)

    for rec in im_info["ims"]:
        user_id = rec["user"]
        im = rec["id"]

        found = False
        for u in users:
            if u.slack_id == user_id:
                u.add_im(im)
                found = True
                break

        if not found:
            sys.exit("Error: couldn't match id {} to user".format(user_id))

    return users

def main(student=None, remark=None, channel=None,
         class_name=None, just_summary=False, post_grades=False):
    """ the main driver """

    params = get_defaults(class_name)

    users = get_users(params)

    for u in users:
        print(u.name, u.slack_id, u.im_channel)

    # if we just want a summary, do it
    if just_summary:
        report(params)

    elif post_grades:
        records = get_records(params)
        names = set([q.student for q in records])

        for n in names:
            student = Student(n, users)
            student.records = [q for q in records if q.student == n]
            student.direct_message(params)

    else:
        # create the grade object
        g = Grade(student, remark=remark, channel=channel, users=users)

        # post the +1 to slack
        g.slack_post(params)

        # update the grade log
        g.update_grades(params)


def get_records(params):
    records = []

    # open up the log file and create a list of records
    with open(params["grade-log"]) as lf:
        for line in lf:
            if line.startswith("#") or line.strip() == "":
                continue
            date, student, channel, remark = line.split(",")
            records.append(Record(student, date, remark, channel))

    return records

def report(params):
    """ generate a simple report of the form 'student, grade' """

    records = get_records(params)

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
    parser.add_argument("--post_grades", help="post grade summaries to the student's DM channel",
                        action="store_true")
    parser.add_argument("--class_name", type=str, help="name of class to grade",
                        default=None)
    parser.add_argument("student", type=str, nargs="?",
                        help="name of student to grade.  For multiple students, use space separate string",
                        default="")
    parser.add_argument("comment", type=str, nargs="?",
                        help="comment to use as grade", default="")
    parser.add_argument("channel", type=str, nargs="?",
                        help="channel to post to",
                        default="#general")
    args = parser.parse_args()

    if not args.setup and not (args.report or args.post_grades):
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
    defaults["grade-log"] = cf.get(class_name, "grade-log")
    defaults["token"] = cf.get(class_name, "token")

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

    # ask for the slack api token
    token = input("Enter your slack token:: ")

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
    cf.set(class_name, "token", token)
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

    elif args.post_grades:
        main(post_grades=True)

    else:
        # we might have multiple students
        students = args.student.split()
        main(students, args.comment, args.channel, class_name=args.class_name)
