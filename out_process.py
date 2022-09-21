import sys
import os
import math

from os import listdir
from os.path import isfile, join

import argparse

"""
sample command
python tagCache.py sample.out 1 64 64 2
"""

parser = argparse.ArgumentParser(description='input file')
parser.add_argument('input_file', type=str, help='the trace file to use')
parser.add_argument('number', type=int, help='number to compare against')

args = parser.parse_args()
number = args.number

accesses = 0
hits = 0
misses = 0

""""Here do the main processing on the input file"""


with open(args.input_file) as infile:
    start = False
    for line in infile:
        #print(line.split()[-1])
        #print(int(line.split()[-1], 16))
        #print(line)
        if 'Dump stats at the end of the ROI!' in line:
            print('BREAK')
            break

        if '**' in line:
            start = True
            continue

        if start == False:
            continue

        if ',' in line:
            trigger_count = int(line.split(',')[-1])

            if trigger_count > number:
                #print(line)
                print(trigger_count)
                #print("\n")


print("Processing done!")
