#!/usr/bin/env python3
#

from MLogger import MLogger
import sys

def main():
    branch = Branch(sys.argv[1], sys.argv[2])
    branch.process()

if __name__=="__main__":
    main()
