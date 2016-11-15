#!/bin/sh

if [ -z "$1" ]
then
    echo "Usage: $0 <hostname>"
    exit 1
fi

request=$(cat <<EOF
GET / HTTP/1.1
Host: $1
Connection: keep-alive
Cache-Control: max-age=0
User-Agent: Mozilla/5.0 AppleWebKit/537.36 Chrome/52.0.2743.116 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8

EOF
)

# echo "$request"
{ echo "$request"; cat /dev/stdin; } |
     ncat --ssl "$1" 443
# somehow ncat would terminate connection when stdin is closed
# keep connection open by catting stdin
