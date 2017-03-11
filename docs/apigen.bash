#!/bin/bash
# script to automatically generate the psyplot api documentation using
# sphinx-apidoc and sed
sphinx-apidoc -f -M -e  -T -o api ../psy_simple/
# replace chapter title in psyplot.rst
sed -i -e 1,1s/.*/'API Reference'/ api/psy_simple.rst

# sphinx-autogen -o generated *.rst */*.rst
