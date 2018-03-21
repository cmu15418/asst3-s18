#!/usr/bin/python

# Perform simulator regression test, comparing outputs of different simulators

import subprocess
import sys
import math
import os
import os.path
import getopt

def usage(fname):
    print "Usage: %s [-h] [-c] [-t THD] [-p PCS]" % fname
    print "    -h       Print this message"
    print "    -c       Clear expected result cache"
    print "    -t THD   Specify number of OMP threads"
    print "       If > 1, will run crun-omp.  Else will run crun"
    print "    -a       Run ALL tests, including for big graphs"
    sys.exit(0)


# General information

# Gold-standard reference program
standardProg = "./grun.py"

# Simulator being tested
testProg = "./crun"
ompTestProg = "./crun-omp"
mpiTestProg = "./crun-mpi"

# Directories
# graph and rat files
dataDir = "./data/"
# cache for holding reference simulation results
cacheDir = "./regression-cache/"

# Limit on how many mismatches get reported
mismatchLimit = 5

# Series of tests to perform.
# Each defined by:
#  number of nodes
#  Graph type (u, f)
#  Rat distribution type (u, d, r)
#  Load factor
#  Number of steps
#  Update mode (s, b, r)
#  Seed (0-99)
regressionList = [
    (4, 'u', 'u', 1, 10, 'r', 15),
    (4, 'u', 'u', 1, 11, 'b', 16),
    (4, 'u', 'u', 1, 12, 's', 17),
    (64, 'u', 'u', 5, 10, 'r', 18),
    (64, 'u', 'd', 5, 11, 'b', 19),
    (64, 'u', 'r', 5, 12, 's', 20),
    (64, 'f', 'u', 5, 10, 'r', 21),
    (64, 'f', 'd', 5, 11, 'b', 22),
    (64, 'f', 'r', 5, 12, 's', 23),
    (1024, 'u', 'u', 10, 3, 'r', 24),
    (1024, 'u', 'u', 10, 6, 's', 25),
    (1024, 'u', 'd', 10, 4, 'b', 26),
    (1024, 'f', 'u', 10, 4, 'b', 27),
    (1024, 'f', 'r', 10, 6, 's', 28),
    ]

extraRegressionList = [
    (25600, 'u', 'u', 40, 2, 's', 29),
    (25600, 't', 'd', 40, 2, 's', 30)
]


def regressionName(params, standard = True):
    return ("ref" if standard else "tst") +  "-%.3d-%s-%s-%.3d-%.3d-%s-%.2d.txt" % params

def regressionCommand(params, standard = True, threadCount = 1):    
    graphSize, graphType, ratType, ratLoad, stepCount, updateFlag, seed = params

    sizeName = str(graphSize)

    graphFileName = dataDir + "g-" + graphType + sizeName + ".gph"

    ratFileName = dataDir + "r-" + sizeName + '-' + ratType + str(ratLoad) + ".rats"

    prog = ''
    prelist = []

    if standard:
        prog = standardProg
    elif threadCount > 1:
        prog = ompTestProg
    else:
        prog = testProg

    cmd = prelist + [prog, "-g", graphFileName, "-r", ratFileName, "-u", updateFlag, "-n", str(stepCount), "-s", str(seed)]

    if standard:
        cmd += ["-m", "d"]
    elif threadCount > 1:
        cmd += ["-t", str(threadCount)]
    return cmd



def runSim(params, standard = True, threadCount = 1):
    cmd = regressionCommand(params, standard, threadCount)
    cmdLine = " ".join(cmd)

    pname = cacheDir + regressionName(params, standard)
    try:
        outFile = open(pname, 'w')
    except Exception as e:
        sys.stderr.write("Couldn't open file '%s' to write.  %s\n" % (pname, e))
        return False
    try:
        sys.stderr.write("Executing " + cmdLine + " > " + regressionName(params, standard) + "\n")
        simProcess = subprocess.Popen(cmd, stdout = outFile)
        simProcess.wait()
        outFile.close()
    except Exception as e:
        sys.stderr.write("Couldn't execute " + cmdLine + " > " + regressionName(params, standard) + " " + str(e) + "\n")
        outFile.close()
        return False
    return True

def checkFiles(refPath, testPath):
    badLines = 0
    lineNumber = 0
    try:
        rf = open(refPath, 'r')
    except:
        sys.sterr.write("Couldn't open reference file '%s'\n" % refPath);
        return False
    try:
        tf = open(testPath, 'r')
    except:
        sys.stderr.write("Couldn't open test file '%s'\n" % testPath);
        return False
    while True:
        rline = rf.readline()
        tline = tf.readline()
        lineNumber +=1
        if rline == "":
            if tline == "":
                break
            else:
                badLines += 1
                sys.stderr.write("Mismatch at line %d.  File %s ended prematurely\n" % (lineNumber, refPath))
                break
        elif tline == "":
            badLines += 1
            sys.stderr.write("Mismatch at line %d.  File %s ended prematurely\n" % (lineNumber, testPath))
            break
        if rline[-1] == '\n':
            rline = rline[:-1]
        if tline[-1] == '\n':
            tline = tline[:-1]
        if rline != tline:
            badLines += 1
            if badLines <= mismatchLimit:
                sys.stderr.write("Mismatch at line %d.  File %s:'%s'.  File %s:'%s'\n" % (lineNumber, refPath, rline, testPath, tline))
    rf.close()
    tf.close()
    if badLines > 0:
        sys.stderr.write("%d total mismatches.  Files %s, %s\n" % (badLines, refPath, testPath))
    return badLines == 0
            
def regress(params, threadCount):
    refPath = cacheDir + regressionName(params, standard = True)
    if not os.path.exists(refPath):
        if not runSim(params, standard = True):
            sys.stderr.write("Failed to run simulation with reference simulator\n")
            return False

    if not runSim(params, standard = False, threadCount = threadCount):
        sys.stderr.write("Failed to run simulation with test simulator\n")
        return False
        
    testPath = cacheDir + regressionName(params, standard = False)

    return checkFiles(refPath, testPath)

def run(flushCache, threadCount, doAll):

    if flushCache and os.path.exists(cacheDir):
        try:
            simProcess = subprocess.Popen(["rm", "-rf", cacheDir])
            simProcess.wait()
        except Exception as e:
            sys.stderr.write("Could not flush old result cache: %s" % str(e))
    if not os.path.exists(cacheDir):
        try:
            os.mkdir(cacheDir)
        except Exception as e:
            sys.stderr.write("Couldn't create directory '%s'" % cacheDir)
            sys.exit(1)
    goodCount = 0
    allCount = 0
    rlist = regressionList + (extraRegressionList if doAll else [])
    for p in rlist:
        allCount += 1
        if regress(p, threadCount):
            sys.stderr.write("Regression %s passed\n" % regressionName(p, standard = False))
            goodCount += 1
    totalCount = len(rlist)
    message = "SUCCESS" if goodCount == totalCount else "FAILED"
    sys.stderr.write("Regression set size %d.  %d/%d tests successful. %s\n" % (totalCount, goodCount, allCount, message))


if __name__ == "__main__":
    doAll = False
    threadCount = 1
    flushCache = False
    
    optlist, args = getopt.getopt(sys.argv[1:], "hct:a")


    for (opt, val) in optlist:
        if opt == '-h':
            usage(sys.argv[0])
        if opt == '-c':
            flushCache = True
        elif opt == '-t':
            threadCount = int(val)
        elif opt == '-a':
            doAll = True
    run(flushCache, threadCount, doAll)
