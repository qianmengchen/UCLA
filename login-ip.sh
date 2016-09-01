#!/bin/sh

# check login ip for $1
# also checkout commands `lastb', `lastlog'

user=${1:-$(whoami)}

# parsing from last output
# supply -i to last if only ip is desired
last -w | awk '$1 == "'"$user"'" { print $3 }' |
    sort | uniq
    # sort | uniq -c | sort -n
