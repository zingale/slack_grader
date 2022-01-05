[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

# slack-grader

A simple command-line tool for posting "+1" type grades to a slack
chat, keeping a log for each student  for end-of-semester grades.

# API token

you need to create a slack API token.  You create an App that is a
"bot" and then under "OAuth & Permissions" you give it access to your
workspace.


# setup

* install the `slackclient` package, e.g., as:
  ```
  pip3 install slackclient
  ```

* create an API token for your slack group.

* configure:

  ```
  ./slackgrade.py --setup
  ```

  This will ask you some questions (including the API token and where
  to log the grades).

  This will write a file in your home directory called `.slackgrader`


# use

The basic usage of this script is to post a comment on a slack channel
with a message (indicating the grade):

```
./slackgrade.py student comment [channel]
```

Each grade is assumed to have the same point value.

A record of this is stored in the logfile noted during the setup part
above.  Each record is given its own line in the log file.  This
allows you to keep it in version control and merge it across machines
without conflicts.

To get a summary of points by student, do:
```
./slackgrade.py --report
```

To DM each user a summary of their participation (only they will see
their records), do
```
./slackgrade.py --post_grades
```
This will show up in their _slackbot_ channel.


# todo

* add point values (so some comments can be worth more)

* cache the user list (add a --refresh option to reload it?)

* better support for multiple classes (setting a default class)

* we don't handle the case where comments have a "," in the report
