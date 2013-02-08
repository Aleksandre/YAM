#!/bin/sh

#This script is intented to be run before a push

#Clean up the code
python ext/pythontidy.py yam/clientapp.py 
python ext/pythontidy.py yam/devices.py
#http://pypi.python.org/pypi/PythonTidy

#Analyze code
pylint yam/clientapp.py --reports=y --include-ids=y  --disable=R0903,R0913 > pylint.txt
#Requires PyLint
#http://www.logilab.org/857

#Generate class diagram
#pyreverse  yam/clientapp.py -o png -f ALL -m y -p diagram
pyreverse  yam/devices.py -o png -f ALL -m y -p diagram

#Generate pydoc
pydoc yam/*.py > pydoc.txt

