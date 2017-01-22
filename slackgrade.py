#!/usr/bin/env python3

from __future__ import print_function

import argparse
import datetime

class Grade(object):
    def __init__(self, student, remark=None, channel="#general"):
        self.student = student
        self.remark = remark
        self.channel = channel

        # record the data / time
        self.date = "{}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def slack_post(self, params):


    def update_grades(self, params):
        """ update the grade log """



def main(student=None, remark=None, channel=None,
         just_summary=False):

    params = get_defaults()

    # if we just want a summary, do it
    if just_summary:
        export_csv()
    else:
        # create the grade object
        g = Grade(student, remark=remark, channel=channel)

        # post the +1 to slack
        g.slack_post(params)

        # update the grade log
        g.update_grades(params)


def get_args():
    """ parse commandline arguments """

def get_defaults():
    """ we store our default settings in a ~/.slackgrader file """

def export_csv():
    """ export a CSV file containing student and score columns """

def setup_params():
    """ query the user to get the default parameters for this grade session """

    # ask for the name of this class

    # ask for the slack api token

    # ask for the path to the grade log

    # ask for the name of the "grader" that will make the posts in slack


if __name__ == "__main__":
    args = get_args()

    if args.just_summary:
        main(just_summary=True)
    else:

    main(args.student, args.remark, args.channel)

