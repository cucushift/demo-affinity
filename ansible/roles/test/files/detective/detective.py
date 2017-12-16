#!/usr/bin/env python

import os, time, threading, urllib2, json
from threading import Lock

lock = Lock()

def log(s):
    print "%s %s" % (time.asctime(time.gmtime()), s)

def query_definitions():
    log("[info] pulling new hardware detection defintions")
    if os.getenv("DEFINITIONS_URL"):
       log("[info] Reading definitions from %s" % os.getenv("DEFINITIONS_URL"))
       with lock:
           try:
               defs = open('/tmp/definitions.txt', 'w+')
               request = urllib2.Request(os.getenv("DEFINITIONS_URL"))
               request.add_header('Pragma', 'no-cache')
               content = urllib2.build_opener().open(request).read()
               log(content)
               defs.write(content)
               defs.close()
           except Exception as e:
               log("[erro] Unable to read definition %s" % e)
    else:
        log("[info] No hardware definitions detection file specified")


    threading.Timer(int(os.getenv("DEFINITION_QUERY_PERIOD", 10)),
            query_definitions).start()

def detect():
    hostname = open('/parent/etc/hostname', 'r').read().strip()
    log("[info] hardware detection on %s" % hostname)
    with lock:
        try:
            if os.path.isfile('/tmp/definitions.txt'):
                with open('/tmp/definitions.txt') as defs:
                    for line in defs.readlines():
                        tuple = line.strip().split()
                        if tuple[0] == hostname:
                            try:
                                log("kubectl --kubeconfig=/etc/kubernetes/admin.conf -n onap label --overwrite node %s %s" % (hostname,
                                    tuple[1]))
                                os.system("kubectl --kubeconfig=/etc/kubernetes/admin.conf -n onap label --overwrite node %s %s" % (hostname,
                                    tuple[1]))
                            except:
                                pass
        except Exception as e:
            log("[erro] Unable to process definitions %s" % e)

    threading.Timer(int(os.getenv("DETECTION_QUERY_PERIOD", 5)),
            detect).start()

def main():
    for k in os.environ:
        print "%s : %s" % (k, os.getenv(k))
    log("[info] Starting the hardware detective")
    query_definitions()
    detect()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
