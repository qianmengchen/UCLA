#! /usr/bin/env python3

"""
*** DEPRECATED as of fall 2016 ***
UCLA made its registrar dynamic with a lot of javascript,
and the query url format has changed.
A rework of this project is needed.

* NOTE: the old static site is still available as a lagacy feature,
this program still works as of now.


WaitList Detector

for usage, run program with '-h' flag
    python waitlist_detector.py -h

required python packages:
    BeautifulSoup4
    lxml (optional, for better performance)

supposed to work under both python2 and python3,
if not, please file an issue
"""


from __future__ import print_function

import traceback
try:
    import urllib.request as urlrequest
except:
    import urllib2 as urlrequest

from bs4 import BeautifulSoup
import subprocess
import sys
import webbrowser
import time
from datetime import datetime
import argparse
import json
import signal

try:
    import lxml
    PARSER = 'lxml'
except ImportError:
    PARSER = 'html.parser'
    sys.stderr.write("lxml unavailable, using html.parser instead\n")

RED_BOLD = "\033[1;31m"
END = "\033[1;00m"

MSG = """\
The waitlist for the following course is now open.

{course}
Available at: {time}
"""

ERR_MSG = """\
{error} occured, and the program might have been terminated.

{exception}
"""


def course_info(soup):
    try:
        course = ' '.join(soup.find(id=COURSE_ID).contents[0].split())

        # instructors have duplicate HTML ID !!!
        instructor = soup.findAll(id=INSTRUCTOR_ID)[LEC_NUM-1].\
            contents[0].strip()

        days = soup.find(id=DAYS_ID).span.contents[0].strip()
        time_start = soup.find(id=TIMESTART_ID).span.contents[0].strip()
        time_end = soup.find(id=TIMEEND_ID).span.contents[0].strip()

        waitlist_total = int(soup.find(id=WAITLIST_TOTAL_ID).span.contents[0])
        waitlist_cap = int(soup.find(id=WAITLIST_CAP_ID).span.contents[0])
        status = soup.find(id=STATUS_ID).span.span.contents[0]

        return {"course": course,
                "instructor": instructor,
                "days": days,
                "time_start": time_start,
                "time_end": time_end,
                "waitlist_total": waitlist_total,
                "waitlist_cap": waitlist_cap,
                "status": status}

    except (ValueError, AttributeError):
        raise ValueError("Not a valid query")


def course_info_str(info):
    return ("Course Title: {}\n"
            "Instructor:   {}\n"
            "Time:         {} {} {}").\
        format(info["course"],
               info["instructor"],
               info["days"], info["time_start"], info["time_end"])


def waitlist_detector(soup):
    info = course_info(soup)
    if info is None:
        return False

    print("=== {crs}  LEC {lec} ===".
          format(crs=info["course"],
                 lec=LEC_NUM))
    print("Total: {}  Capacity: {}  Status: {}".
          format(info["waitlist_total"],
                 info["waitlist_cap"],
                 info["status"]))

    return info["waitlist_total"] < info["waitlist_cap"] or \
        info["status"] != 'Closed' and info["status"] != "Cancelled"


def sendmail(msg, subject):
    mail = subprocess.Popen(["mail", "-s", subject, RECIPIENT],
                            stdin=subprocess.PIPE)
    mail.communicate(input=msg.encode())
    if mail.returncode != 0:
        print(RED_BOLD + "*** error sending email ***" + END, file=sys.stderr)
    else:
        print("The following email is sent to", RECIPIENT, end='\n\n')
        print(msg)

    return mail.returncode


def notify_success(info, status="Waitlist Open"):
    if RECIPIENT:
        return sendmail(
            MSG.format(course=info,
                       time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            subject=status)

    # local notification
    try:
        webbrowser.open_new(URL)
    except Exception:
        pass

    while True:                 # run until manually terminated?
        if sys.platform == "darwin":
            subprocess.call(['say', 'waitlist open'])
        print('\a' * 10, end='')
    return 0


def main():
    print("Welcome to class scrapper\n")

    nth = 1
    while True:
        try:
            page = urlrequest.urlopen(URL)
            soup = BeautifulSoup(page, PARSER)

            if nth == 1:
                print("=== Course Information ===")
                course_information = course_info_str(course_info(soup))
                print(course_information, end='\n\n')
            nth += 1

            # waitlist is open
            if waitlist_detector(soup):
                break

            print("updated at {}\n".
                  format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        # caused by invalid query
        except ValueError as ex:
            print(RED_BOLD + "*** cannot understand query ***" + END,
                  file=sys.stderr)
            exception = "Invalid URL for this query, check URL.\n" + \
                        "URL formed for this query: {}".format(URL)
            error_msg = ERR_MSG.format(error=type(ex).__name__,
                                       exception=exception)
            print(error_msg, file=sys.stderr)
            if RECIPIENT:
                sendmail(error_msg, "Invalid Query")
            else:
                if sys.platform == "darwin":
                    subprocess.call(['say',
                                     'invalid query, terminating program'])
            return 1

        except urlrequest.URLError as ex:
            print(RED_BOLD + '*** NETWORK ERROR ***' + END, file=sys.stderr)
            error_msg = ERR_MSG.format(error=type(ex).__name__,
                                       exception=traceback.format_exc())
            print(error_msg, file=sys.stderr)
            if RECIPIENT:
                sendmail(error_msg, "Network Error Occured")
            else:
                if sys.platform == "darwin":
                    subprocess.call(['say', 'network error'])

        except Exception as ex:
            print(RED_BOLD + '*** UNKNOWN ERROR ***' + END, file=sys.stderr)
            error_msg = ERR_MSG.format(error=type(ex).__name__,
                                       exception=traceback.format_exc())
            print(error_msg, sys.stderr)
            if RECIPIENT:
                sendmail(error_msg, "Unknown Error Occured")
            else:
                if sys.platform == "darwin":
                    subprocess.call(['say', 'unknown error'])

        sys.stdout.flush()
        sys.stderr.flush()
        time.sleep(PERIOD)

    # notification
    print("\n\nWAITLIST OPEN !!!\n")
    return notify_success(course_information)


def signal_handler(signal, frame):
    sendmail("caught signal {}, exiting".format(signal), subject="Error!")
    sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description="waitlist detecter "
                                     "tailored for UCLA registrar")
    parser.add_argument('--term', '-t',
                        help="which quarter")
    parser.add_argument('--area', '-a',
                        help="area of study/major")
    parser.add_argument('--crs', '-c',
                        help="course index")
    parser.add_argument('--num', '-n', type=int, default=1,
                        help="lecture number, appears before name "
                        "of the lecturer, defaults to %(default)s")
    parser.add_argument('--period', '-p', type=float, default=30,
                        help="query to be made every [period] "
                        "second(s), defaults to %(default)s")
    parser.add_argument('--email', nargs='+', default=[],
                        help="send notification email to recipient(s). "
                        "Assume `mail' is installed on your system")
    parser.add_argument('--file', '-f', help="input file for arguments")

    args = parser.parse_args()

    TERM = AREA = CRS = LEC_NUM = PERIOD = RECIPIENT = ''

    if args.file:
        with open(args.file, "r") as f:
            input_json = json.load(f)
        TERM = input_json["term"]
        AREA = input_json["area"]
        CRS = input_json["crs"]
        if "num" in input_json:
            LEC_NUM = input_json["num"]
        if "period" in input_json:
            PERIOD = input_json["period"]
        else:
            PERIOD = args.period
        if "email" in input_json:
            RECIPIENT = ','.join(input_json["email"])
    else:
        TERM = args.term
        AREA = args.area
        CRS = args.crs
        LEC_NUM = args.num
        PERIOD = args.period
        RECIPIENT = ','.join(args.email)

    TERM = TERM.upper()
    AREA = ' '.join(AREA.split()).upper()
    # course index require to be 4 digits, not including ending letter
    # if 'M' exists, only add it to the end
    CRS = CRS.upper()
    CRS = CRS.rjust(4, '0') if not CRS[-1].isalpha() \
        else CRS[:-1].rjust(4, '0') + CRS[-1]
    if 'CM' in CRS:
        CRS = '0' + CRS[2:] + "  CM"
    elif 'M' in CRS:
        CRS = CRS.replace('M', '0') + ' M'

    URL = "http://legacy.registrar.ucla.edu/schedule/detselect.aspx?" + \
          "termsel={term}&subareasel={area}&idxcrs={crs}".\
          format(term=TERM,
                 # better leave AREA/CRS like this, HTML id requires AREA/CRS
                 # to be sparated by space
                 area=AREA.replace(' ', '+'),
                 crs=CRS.replace(' ', '+'))

    # ID refers to HTML id
    COURSE_ID = "ctl00_BodyContentPlaceHolder_detselect_dgdCourseHeader" + \
        "{area}{crs}_ctl02_lblCourseHeader".\
        format(area=AREA,
               crs=CRS)

    # for instructor, registrar has the duplicate HTML ID
    INSTRUCTOR_ID = "ctl00_BodyContentPlaceHolder_detselect_" + \
        "dgdLectureHeader" + \
        "{area}{crs}_ctl02_lblGenericMessage2".\
        format(area=AREA,
               crs=CRS)

    ID_BASE = "ctl00_BodyContentPlaceHolder_" + \
              "detselect_ctl{lec:02d}_ctl02_{item}"
    # Days, e.g. MWF
    DAYS_ID = \
        ID_BASE.format(lec=LEC_NUM + 1,
                       item="lblDays")
    # time start, e.g. 10:00A
    TIMESTART_ID = \
        ID_BASE.format(lec=LEC_NUM + 1,
                       item="lblTimeStart")
    # time end, e.g. 11:50A
    TIMEEND_ID = \
        ID_BASE.format(lec=LEC_NUM + 1,
                       item="lblTimeEnd")
    # waitlist total
    WAITLIST_TOTAL_ID = \
        ID_BASE.format(lec=LEC_NUM + 1,
                       item="WaitListTotal")
    # waitlist capacity
    WAITLIST_CAP_ID = \
        ID_BASE.format(lec=LEC_NUM + 1,
                       item="WaitListCap")
    # waitlist status
    STATUS_ID = \
        ID_BASE.format(lec=LEC_NUM + 1,
                       item="Status")

    # print(URL)
    # print(TERM)
    # print(AREA)
    # print(CRS)
    # print(LEC_NUM)
    # print(COURSE_ID)
    # print(INSTRUCTOR_ID)
    # print(WAITLIST_TOTAL_ID)
    # print(WAITLIST_CAP_ID)
    # print(STATUS_ID)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)

    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
