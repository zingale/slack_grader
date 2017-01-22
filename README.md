# slack-grader

A simple command-line tool for posting "+1" type grades to a slack
chat, keeping a log for each student  for end-of-semester grades.


# setup

* create an _incoming webhook_ for your slack.

  - go to https://_slackname_.slack.com/apps
  - type "webhook" in the search box
  - select "incoming webhooks" and follow the instuctions
    (you can select an icon and label here)
	
  You should wind up with a URL that is the webhook you can post with


* configure:

  ```
  ./slackgrade.py --setup
  ```

  This will ask you some questions (including the URL for the webhook and
  where to log the grades).

  This will write a file in your home directory called `.slackgrader`


# use

The basic usage of this script is to post a comment on a slack channel
with a message (indicating the grade):

```
./slackgrade.py student comment [channel]
```

Each grade is assumed to have the 

A record of this is stored in the logfile noted during the setup part
above.  Each record is given its own line in the log file.  This
allows you to keep it in version control and merge it across machines
without conflicts.

To get a summary of points by student, do:
```
./slackgrade.py --report
```


# todo

* add point values (so some comments can be worth more)

* validate the users are actually on slack

* better support for multiple classes (setting a default class)

* we don't handle the case where comments have a "," in the report
