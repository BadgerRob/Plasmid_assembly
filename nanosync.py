#!/usr/bin/env python3

##################################################################
# NanoSync, a python script for syncing fast5 files from a local HD to an external SSD during a sequencing reaction.
# Removes fast5 files from local HD once synced with SSD.

# Instructions for use:
# Modify 'path/to/external/SSD' in python script before use.
# Make file executable with 'chmod +x nanosync.py'.
# Place nanosync.py in minION output dir (set in minKNOW gui).
# Change to minION output dir containing nanosync.py in terminal.
# Start sequencing run in minKNOW.
# Run ./nanosync.py in terminal to sync fast5 with external SSD.
# Test before use.
##################################################################

import os
import time

print("")
print("NanoSync")
print("##############################################################")
print("")
print("Press 'ctrl + c' to quit")
print("")

tstr = input("Enter sync rate (sec): ")
t =int(tstr)

n = 1

while True:
        os.system('rsync -zvar --remove-source-files --include "*.fast5" --include "*/" --exclude "*" . /path/to/external/SSD')
        print("NanoSync iteration", n)
        time.sleep (t)
        n = n + 1
done


