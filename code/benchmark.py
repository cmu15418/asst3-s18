#!/usr/bin/python

import subprocess
import sys
import os
import os.path
import getopt
import math
import datetime
import random

import grade

def usage(fname):
    
    ustring = "Usage: %s [-h] [-s SCALE] [-u UPDATELIST] [-t THREADLIMIT] [-f OUTFILE] [-c]" % fname
    print ustring
    print "(All lists given as colon-separated text.)"
    print "    -h            Print this message"
    print "    -s SCALE      Reduce number of steps in each benchmark by specified factor"
    print "    -u UPDATELIST Specify update modes(s):"
    print "       r: rat order"
    print "       s: synchronous"
    print "       b: batch"
    print "    -t THREADLIMIT Specify upper limit on number of OMP threads"
    print "       If > 1, will run crun-omp.  Else will run crun"
    print "    -f OUTFILE    Create output file recording measurements"
    print "         If file name contains field of form XX..X, will replace with ID having that many digits"
    print "    -c            Compare simulator output to recorded result"
    sys.exit(0)

# Enumerated type for update mode:
# synchronous:  First compute all next states for all rats, and then move them
# ratOrder:     For each rat: compute its next state and move it immediately
class UpdateMode:
    ratOrder, batch, synchronous = range(3)
    flags = ['r', 'b', 's']

# General information
simProg = "./crun"
ompSimProg = "./crun-omp"

dataDir = "./data/"
outFile = None
captureDirectory = "./capture"
doCheck = False

# How many mismatched lines warrant detailed report
mismatchLimit = 5

# Dictionary of geometric means, indexed by (mode, threads)
gmeanDict = {}



def outmsg(s, noreturn = False):
    if len(s) > 0 and s[-1] != '\n' and not noreturn:
        s += "\n"
    sys.stdout.write(s)
    sys.stdout.flush()
    if outFile is not None:
        outFile.write(s)


# Run such that only capture initial and final states
runFlags = ["-q"]
captureRunFlags = []

# For computing geometric mean
logSum = 0.0
bcount = 0

# For keeping track of speedups
# Mapping from runtime parameters to MRPS
resultCache = {}

# Marker that allows filtering via grep
marker = "+++\t"
nomarker = "\t"

def reset():
    global logSum, bcount
    logSum = 0.0
    bcount = 0

# Graph/rat combinations: (graphSize, graphType, ratType, loadFactor)
benchmarkList = [
    (25600, 't', 'u', 40),
    (25600, 't', 'd', 40),
    (25600, 't', 'r', 40),
    (25600, 'f', 'u', 40),
    (25600, 'f', 'd', 40),
    ]


# Tests
synchRunList = [(1, 800), (12, 800)]
otherRunList = [(1, 400), (12, 400)]

def captureFileName(graphSize, graphType, ratType, loadFactor, stepCount, updateFlag):
    params = (graphSize, graphType, ratType, loadFactor, stepCount, updateFlag)
    return captureDirectory + "/cap" + "-%.3d-%s-%s-%.3d-%.3d-%s.txt" % params

def openCaptureFile(graphSize, graphType, ratType, loadFactor, stepCount, updateFlag):
    if not doCheck:
        return None
    name = captureFileName(graphSize, graphType, ratType, loadFactor, stepCount, updateFlag)
    try:
        cfile = open(name, "r")
    except Exception as e:
        outmsg("Couldn't open captured result file '%s': %s" % (name, e))
        return None
    return cfile


def checkOutputs(captureFile, outputFile):
    if captureFile == None or outputFile == None:
        return True
    badLines = 0
    lineNumber = 0
    while True:
        rline = captureFile.readline()
        tline = outputFile.readline()
        lineNumber +=1
        if rline == "":
            if tline == "":
                break
            else:
                badLines += 1
                outmsg("Mismatch at line %d.  Reference file ended prematurely" % (lineNumber))
                break
        elif tline == "":
            badLines += 1
            outmsg("Mismatch at line %d.  Simulation output ended prematurely\n" % (lineNumber))
            break
        if rline[-1] == '\n':
            rline = rline[:-1]
        if tline[-1] == '\n':
            tline = tline[:-1]
        if rline != tline:
            badLines += 1
            if badLines <= mismatchLimit:
                outmsg("Mismatch at line %d.  Expected result:'%s'.  Simulation result:'%s'\n" % (lineNumber, rline, tline))
    captureFile.close()
    if badLines > 0:
        outmsg("%d total mismatches.\n" % (badLines))
    if badLines == 0:
        outmsg("Simulator output matches recorded results!")
    return badLines == 0

def cmd(graphSize, graphType, ratType, loadFactor, stepCount, updateType, threadCount, otherArgs):
    global bcount, logSum
    global cacheKey
    updateFlag = UpdateMode.flags[updateType]
    params = ["%5d" % graphSize, graphType, "%4d" % loadFactor, ratType, str(stepCount), updateFlag]
    cacheKey = ":".join(params)
    results = params + [str(threadCount)]
    sizeName = str(graphSize)
    graphFileName = dataDir + "g-" + graphType + sizeName + ".gph"
    ratFileName = dataDir + "r-" + sizeName + '-' + ratType + str(loadFactor) + ".rats"
    checkFile = openCaptureFile(graphSize, graphType, ratType, loadFactor, stepCount, updateFlag)
    recordOutput = checkFile is not None
    ok = True
    if recordOutput:
        clist = captureRunFlags + ["-g", graphFileName, "-r", ratFileName, "-u", updateFlag, "-n", str(stepCount), "-i", str(stepCount)] + otherArgs
    else:
        clist = runFlags + ["-g", graphFileName, "-r", ratFileName, "-u", updateFlag, "-n", str(stepCount), "-i", str(stepCount)] + otherArgs
    prog = simProg if threadCount == 1 else ompSimProg
    gcmd = [prog] + clist + ["-t", str(threadCount)]
    gcmdLine = " ".join(gcmd)
    retcode = 1
    tstart = datetime.datetime.now()
    try:
        # File number of standard output
        stdoutFileNumber = 1
        if recordOutput:
            simProcess = subprocess.Popen(gcmd, stderr = subprocess.PIPE, stdout = subprocess.PIPE)
            ok = ok and checkOutputs(checkFile, simProcess.stdout)
            # Echo any results printed by simulator on stderr onto stdout
            for line in simProcess.stderr:
                sys.stdout.write(line)
        else:
            simProcess = subprocess.Popen(gcmd, stderr = stdoutFileNumber)

        simProcess.wait()
        retcode = simProcess.returncode
    except Exception as e:
        print "Execution of command '%s' failed. %s" % (gcmdLine, e)
        return False
    if retcode == 0:
        delta = datetime.datetime.now() - tstart
        secs = delta.seconds + 24 * 3600 * delta.days + 1e-6 * delta.microseconds
        rops = int(graphSize * loadFactor) * stepCount
        ssecs = "%.2f" % secs 
        results.append(ssecs)
        mrps = 1e-6 * float(rops)/secs
        if mrps > 0:
            logSum += math.log(mrps)
            bcount += 1
        smrps = "%7.2f" % mrps
        results.append(smrps)
        if cacheKey in resultCache:
            speedup = mrps / resultCache[cacheKey] 
            sspeedup = "(%5.2fX)" % speedup
            results.append(sspeedup)
        if threadCount == 1:
            resultCache[cacheKey] = mrps
        pstring = marker + "\t".join(results)
        outmsg(pstring)
    else:
        print "Execution of command '%s' gave return code %d" % (gcmdLine, retcode)
        return False
    return ok

def sweep(updateType, threadLimit, scale, otherArgs):
    runList = synchRunList if updateType == UpdateMode.synchronous else otherRunList
    ok = True
    for rparams in runList:
        reset()
        (threadCount, stepCount) = rparams
        stepCount = stepCount / scale
        if threadCount > threadLimit:
            continue
        outmsg("\tNodes\tgtype\tlf\trtype\tsteps\tupdate\tthreads\tsecs\tMRPS")
        outmsg(nomarker + "---------" * 8)
        for bparams in benchmarkList:
            (graphSize, graphType, ratType, loadFactor) = bparams
            ok = ok and cmd(graphSize, graphType, ratType, loadFactor, stepCount, updateType, threadCount, otherArgs)
        if bcount > 0:
            gmean = math.exp(logSum/bcount)
            updateFlag = UpdateMode.flags[updateType]
            outmsg(marker + "Gmean\t\t\t\t\t%s\t%d\t\t%7.2f" % (updateFlag, threadCount, gmean))
            outmsg(marker + "---------" * 8)
            gmeanDict[(updateFlag, threadCount)] = gmean
    return ok

def generateFileName(template):
    n = len(template)
    ls = []
    for i in range(n):
        c = template[i]
        if c == 'X':
            c = chr(random.randint(ord('0'), ord('9')))
        ls.append(c)
    return "".join(ls)

def run(name, args):
    global outFile, doCheck
    scale = 1
    updateList = [UpdateMode.batch, UpdateMode.synchronous]
    threadLimit = 100
    optString = "hs:u:t:f:c"
    optlist, args = getopt.getopt(args, optString)
    otherArgs = []

    for (opt, val) in optlist:
        if opt == '-h':
            usage(name)
        elif opt == '-s':
            scale = float(val)
        elif opt == '-f':
            fname = generateFileName(val)
            try:
                outFile = open(fname, "w")
                outmsg("Writing to file '%s'" % fname)
            except Exception as e:
                outFile = None
                outmsg("Couldn't open output file '%s'" % fname)
        elif opt == '-u':
            ulist = val.split(":")
            updateList = []
            for c in ulist:
                if c == 's':
                    updateList.append(UpdateMode.synchronous)
                elif c == 'b':
                    updateList.append(UpdateMode.batch)
                elif c == 'r':
                    updateList.append(UpdateMode.ratOrder)
                else:
                    print "Invalid update mode '%s'" % c
                    usage(name)
        elif opt == '-c':
            doCheck = True
        elif opt == '-t':
            threadLimit = int(val)
        else:
            outmsg("Unknown option '%s'" % opt)
            usage(name)
    
    tstart = datetime.datetime.now()

    ok = True
    for u in updateList:
        ok = ok and sweep(u, threadLimit, scale, otherArgs)
    
    delta = datetime.datetime.now() - tstart
    secs = delta.seconds + 24 * 3600 * delta.days + 1e-6 * delta.microseconds
    print "Total test time = %.2f secs." % secs

    grade.grade(ok, gmeanDict, sys.stdout)

    if outFile:
        grade.grade(ok, gmeanDict, outFile)
        outFile.close()

if __name__ == "__main__":
    run(sys.argv[0], sys.argv[1:])
