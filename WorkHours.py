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

TIMEOUTS = 600
SHORT_SLEEP = 1
TIMEOUT_SECONDS = TIMEOUTS * SHORT_SLEEP

DATA_ROOT = 'Data/'
DATA_CACHE = DATA_ROOT + 'Cache/'
LAST_TIMESTAMPS = DATA_CACHE + 'LastTime.txt'  # Last time when work was done
ADDED_UP_UNTIL = DATA_CACHE + 'LastDaily.txt'  # Last Daily addup
CRASH_LOG = DATA_ROOT + 'CrashLog.txt'


def AppendLast(now):
    f = open(LAST_TIMESTAMPS, 'a+')
    f.write(now.isoformat() + '\n')
    f.close()
    return now

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
    os.rename(LAST_TIMESTAMPS, LAST_TIMESTAMPS + ".old")
    

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

    activity = None  # Unknown
    opos = None
    logged_activity, oldest_activity = GetLoggedActivity()
    print("First", oldest_activity, "Last", logged_activity)
    if logged_activity:
        EndSection(oldest_activity, logged_activity) 
        if (datetime.now() - logged_activity).total_seconds() < TIMEOUT_SECONDS:
            print("restarted within timeout, can't tell if by system or user")
            oldest_activity = logged_activity
            logged_activity = AppendLast(oldest_activity)
        else:
            print("restarted after timeout passed (or section already ended)")
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
        sys.stdout.write('W')
        sys.stdout.flush()
        logged_activity = AppendLast(activity)

        stopped = TIMEOUTS
        opos = mouse.position
        while stopped > 0:
            sleep(SHORT_SLEEP)
            npos = mouse.position
            stopped -= 1
            if opos != npos:
                # Continued activity, no writes
                sys.stdout.write('.')
                sys.stdout.flush()
                activity = datetime.now()  # last confirmed activity
                stopped = TIMEOUTS  # restart
                opos = npos
                seconds_since_last_log = (activity - logged_activity).total_seconds() if logged_activity else TIMEOUT_SECONDS
                if seconds_since_last_log > 2 * TIMEOUT_SECONDS:
                    # must have slept, end old section
                    sys.stdout.write('S+W\n')
                    EndSection(oldest_activity, logged_activity)
                    # activity OK
                    oldest_activity = activity  # not yet written
                    logged_activity = AppendLast(activity)
                elif seconds_since_last_log >= TIMEOUT_SECONDS:
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

