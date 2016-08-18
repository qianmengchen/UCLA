#!/bin/sh

set -e

if [ -z "$1" ]
then
    echo "Usage: $0 <username>"
    exit 1
fi

user="$1"
echo "==> creating user $user"
useradd "$user" -s /bin/bash
# echo "==> creating password for user $user"
# passwd $user

home=/home/"$user"
mkdir "$home"
[ -d /etc/skel ] && rsync -a /etc/skel/ "$home"
chown -R "$user":"$user" "$home"
