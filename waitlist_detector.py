#! /usr/bin/env python3


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

try:
    import lxml
    PARSER = 'lxml'
except ImportError:
    PARSER = 'html.parser'
    sys.stderr.write("lxml unavailable, using html.parser instead\n")


# following variables are relevant information of the course
# format has to be exact for the program to find the result

TERM = '16S'              # which quarter
AREA = 'COM SCI'          # area in all caps, separated by space
CRS = 'M51A'              # index of the course
LEC_NUM = 1               # lecture number, appears before name of lecturer
PERIOD = 30               # query will be made every PERIOD second(s)


# code after this line are for the program
# please do not modify if you don't know what you are doing

TERM = TERM.upper()
AREA = ' '.join(AREA.split()).upper()
# course index require to be 4 digits, not including ending letter
# if 'M' exists, only add it to the end
CRS = CRS.upper()
CRS = CRS.rjust(4, '0') if not CRS[-1].isalpha() \
    else CRS[:-1].rjust(4, '0') + CRS[-1]
if 'M' in CRS:
    CRS = CRS.replace('M', '0') + ' M'

URL = "http://www.registrar.ucla.edu/schedule/detselect.aspx?" + \
      "termsel={term}&subareasel={area}&idxcrs={crs}".\
      format(term=TERM,
             # better leave AREA/CRS like this, HTML id requires AREA/CRS
             # to be sparated by space
             area='+'.join(AREA.split()),
             crs='+'.join(CRS.split()))

# ID refers to HTML id
COURSE_ID = "ctl00_BodyContentPlaceHolder_detselect_dgdCourseHeader" + \
            "{area}{crs}_ctl02_lblCourseHeader".\
            format(area=AREA,
                   crs=CRS)

INSTRUCTOR_ID = "ctl00_BodyContentPlaceHolder_detselect_dgdLectureHeader" + \
                "{area}{crs}_ctl02_lblGenericMessage2".\
                format(area=AREA,
                       crs=CRS)

ID_BASE = "ctl00_BodyContentPlaceHolder_detselect_ctl{lec:02d}_ctl02_{item}"

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


def waitlist_detector(soup):
    # print(soup.body.form.center.div.center.table.
    #       find_all('tr')[1].
    #       find_all('td')[1].prettify())

    try:
        course = soup.find(id=COURSE_ID).contents[0]
        course = ' '.join(course.split())

        instructor = soup.find(id=INSTRUCTOR_ID).contents[0].strip()

        days = soup.find(id=DAYS_ID).span.contents[0].strip()
        time_start = soup.find(id=TIMESTART_ID).span.contents[0].strip()
        time_end = soup.find(id=TIMEEND_ID).span.contents[0].strip()

        waitlist_total = int(soup.find(id=WAITLIST_TOTAL_ID).span.contents[0])
        waitlist_cap = int(soup.find(id=WAITLIST_CAP_ID).span.contents[0])
        status = soup.find(id=STATUS_ID).span.span.contents[0]

        print("=== {crs}  LEC {lec} ===".
              format(crs=course,
                     lec=LEC_NUM))
        print("=== {ins}  {time} ===".
              format(ins=instructor,
                     time=' '.join((days, time_start, time_end))))
        print("Total: {}  Capacity: {}  Status: {}".
              format(waitlist_total,
                     waitlist_cap,
                     status))

        return waitlist_cap > waitlist_total or status != 'Closed'

    except (ValueError, AttributeError):
        print("*** cannot understand query ***", file=sys.stderr)
        return False


def main():
    # print("Welcome to class scrapper")
    # page = urlrequest.urlopen(URL)
    # soup = BeautifulSoup(page, PARSER)

    # print("=== Class Information ===")
    # print("Course Title: {}".format())

    while True:
        try:
            page = urlrequest.urlopen(URL)
            soup = BeautifulSoup(page, PARSER)

            # waitlist is open
            if waitlist_detector(soup):
                break

            print("query made at {}\n".
                  format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        except urlrequest.URLError:
            print('*** NETWORK ERROR ***', file=sys.stderr)
            if sys.platform == "darwin":
                subprocess.call('say ' + 'network error', shell=True)

        except Exception as ex:
            print('*** UNKNOWN ERROR ***', file=sys.stderr)
            print(ex)

        time.sleep(PERIOD)

    # agressive notification
    print("\n\nWAITLIST OPEN !!!")
    webbrowser.open_new(URL)
    while True:
        if sys.platform == "darwin":
            subprocess.call('say ' + 'waitlist open', shell=True)
        print('\a' * 10, end='')


if __name__ == '__main__':
    main()
