#/bin/sh

if [ -z "$3" ];
then
    echo "Usage: $0 <file1> <file2> <outfile>"
    exit 1
fi

# ghostscript
gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile="$3" "$1" "$2"

# or try convert from imagemagick
# convert file1.pdf file2.pdf output.pdf
