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

try:
    import urllib.request as urlrequest
except:
    import urllib as urlrequest

from bs4 import BeautifulSoup
import subprocess
import sys
import webbrowser
import time
from datetime import datetime
import argparse

try:
    import lxml
    PARSER = 'lxml'
except ImportError:
    PARSER = 'html.parser'
    sys.stderr.write("lxml unavailable, using html.parser instead\n")

RED = "\033[1;31m"
END = "\033[1;00m"

# following variables are relevant information of the course
# format has to be exact for the program to find the result

# TERM = '16S'              # which quarter
# AREA = 'COM SCI'          # area in all caps, separated by space
# CRS = 'M51A'              # index of the course
# LEC_NUM = 1               # lecture number, appears before name of lecturer
# PERIOD = 30               # query will be made every PERIOD second(s)


# code after this line are for the program
# please do not modify if you don't know what you are doing


def course_info(soup):
    try:
        course = ' '.join(soup.find(id=COURSE_ID).contents[0].split())

        # instructors has duplicate HTML ID !!!
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
        print(RED + "*** cannot understand query ***" + END,
              file=sys.stderr)
        print("URL for this query:", URL, sep='\n', end='\n\n')
        raise RuntimeError("Not a valid query")


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


def main():
    print("Welcome to class scrapper\n")
    page = urlrequest.urlopen(URL)
    soup = BeautifulSoup(page, PARSER)

    print("=== Course Information ===")
    course_information = course_info_str(course_info(soup))
    print(course_information, end='\n\n')

    while True:
        try:
            page = urlrequest.urlopen(URL)
            soup = BeautifulSoup(page, PARSER)

            # waitlist is open
            if waitlist_detector(soup):
                break

            print("updated at {}\n".
                  format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        except urlrequest.URLError:
            print(RED + '*** NETWORK ERROR ***' + END, file=sys.stderr)
            if sys.platform == "darwin":
                subprocess.call(['say', 'network error'])

        except Exception as ex:
            print(RED + '*** UNKNOWN ERROR ***' + END, file=sys.stderr)
            print(ex, file=sys.stderr)

        time.sleep(PERIOD)

    # agressive notification
    print("\n\nWAITLIST OPEN !!!\n")
    try:
        webbrowser.open_new(URL)
    except Exception:
        pass
    while True:
        if sys.platform == "darwin":
            subprocess.call(['say', 'waitlist open'])
        print('\a' * 10, end='')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description="waitlist detecter "
                                     "tailored for UCLA registrar")
    parser.add_argument('--term', '-t', required=True,
                        help="which quarter")
    parser.add_argument('--area', '-a', required=True,
                        help="area of study/major")
    parser.add_argument('--crs', '-c', required=True,
                        help="course index")
    parser.add_argument('--num', '-n', type=int, default=1,
                        help="lecture number, appears before name "
                        "of the lecturer, defaults to %(default)s")
    parser.add_argument('--period', '-p', type=int, default=30,
                        help="query to be made every [period] "
                        "second(s), defaults to %(default)s")

    args = parser.parse_args()

    TERM = args.term
    AREA = args.area
    CRS = args.crs
    LEC_NUM = args.num
    PERIOD = args.period

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

    try:
        main()
    except KeyboardInterrupt:
        pass
