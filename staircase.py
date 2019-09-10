#!/usr/bin/python
import sys
h = int(sys.argv[1])
for i in range (0, h):
    print(' '*(h-i-1) + '#'*(i+1))
