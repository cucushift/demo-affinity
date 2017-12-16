#!/usr/bin/env python
import time

def log(s):
    print "%s %s" % (time.asctime(time.gmtime()), s)

def main():
    while True:
        log("I'm a little VNF, short and stout, here is my ingress and here is my out")
        time.sleep(5)

if __name__ == "__main__":
    main()
