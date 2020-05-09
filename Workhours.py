#!/usr/bin/python3
from datetime import datetime,timedelta
import errno
import dateutil.parser

from pynput.mouse import Button, Controller
from time import sleep
from math import sin
import traceback
import os
import sys

import locale
locale.setlocale(locale.LC_ALL, '')  # Sets things like first day of week, weekday names

mouse = Controller()

TIMEOUT = 600


DATA_ROOT = 'Data/'
DATA_CACHE = DATA_ROOT + 'Cache/'
LAST_TIMESTAMPS = DATA_CACHE + 'LastTime.txt'  # Last time when work was done
ADDED_UP_UNTIL = DATA_CACHE + 'LastDaily.txt'  # Last Daily addup
CRASH_LOG = DATA_ROOT + 'CrashLog.txt'


def AppendLast(Now):
    f = open(LAST_TIMESTAMPS, 'a+')
    f.write(Now.isoformat() + '\n')
    f.close()
    return Now

def GetLoggedActivity():
    try:
        with open(LAST_TIMESTAMPS, 'r') as f:
            timestamps = f.readlines()
            f.close()
    except FileNotFoundError:
        return None, None

    if len(timestamps) == 0:
        return None, None
    return dateutil.parser.parse(timestamps[-1]), dateutil.parser.parse(timestamps[0])

def EndSection(started, ended):
    if not started or not ended:
        print(f"Section can't be ended started={started} ended={ended}")
        return
    worked = ended - started
    hours = worked.total_seconds() / 60 / 60
    message = f'{started.isoformat(" ", "minutes")} till {ended.strftime("%H:%M")} = {hours} timmar'
    print(message)
   
    Addtext(started, message)

    # added worktime section to output, restart section
    f = open(LAST_TIMESTAMPS, 'w')
    f.write('')
    f.close()

   

def Addtext(started, text):
    current_week = datetime.isocalendar(started)[1]

    week_dir = f'v{current_week}'
    if not week_dir in os.listdir(DATA_ROOT):
        os.mkdir(DATA_ROOT + week_dir)

    p = f"{DATA_ROOT}{week_dir}/{started.strftime('%Y-%m-%d')}.txt"

    f = open(p, 'a+')
    f.write(text+'\n')
    f.close()


def mkdir(dirname):
    try:
        os.mkdir(dirname)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise

# Main program
try:
    mkdir(DATA_ROOT)
    mkdir(DATA_CACHE)

    logged_activity, oldest_activity = GetLoggedActivity()
    print("First", oldest_activity, "Last", logged_activity)
    if logged_activity and (datetime.now() - logged_activity).total_seconds() < TIMEOUT:
        print("restarted within timeout, can't tell if by system or user")
        opos = None
    else:
        print("restarted after timeout passed (or section already ended)")
        EndSection(oldest_activity, logged_activity)
        oldest_activity = None
        logged_activity = None
        opos = mouse.position
           
    while True:
        # Wait for activity (skipped if restarted within timeout)
        while opos == mouse.position:
            sleep(1)

        # Activity!
        activity = datetime.now()
        if not oldest_activity:
            oldest_activity = activity
        logged_activity = AppendLast(activity)

        stopped = TIMEOUT
        opos = mouse.position
        while stopped > 0:
            sleep(1)
            npos = mouse.position
            stopped -= 1
            if opos != npos:
                # Continued activity, no writes
                sys.stdout.write('.')
                sys.stdout.flush()
                activity = datetime.now()  # last confirmed activity
                stopped = TIMEOUT  # restart
                opos = npos
                if not logged_activity or (activity - logged_activity).total_seconds() >= TIMEOUT:
                        sys.stdout.write('w')
                        sys.stdout.flush()
                        logged_activity = AppendLast(activity)
            elif stopped == 0:
                # No longer active, will write
                sys.stdout.write('s\n')
                EndSection(oldest_activity, activity)
                activity = None
                oldest_activity = None
                logged_activity = None

except Exception:
    # os.rename(CRASH_LOG, CRASH_LOG + ".old")
    log = open(CRASH_LOG, 'w')
   
    traceback.print_exc(file=log)
   
    log.close()
    print("Crashlog written\n")
