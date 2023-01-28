import time
import micropython
import counters
import _thread
sLock = _thread.allocate_lock()
DEBUGCOUNTER = "debugCounter.txt"
LOGFILE = "debugLog.csv"

def resetCounter():
    sLock.acquire()
    counter = 0
    # Open the counter file for write (replace)
    fileHandle = open(DEBUGCOUNTER, "w")
    fileHandle.write(str(counter))
    fileHandle.close()
    sLock.release()


def debug(debugLevel, methodName, details, logToFile):

    sLock.acquire()  # Acquire exclusive use while outputing the debug info
    
    # Read the counter file
    fileHandle = open(DEBUGCOUNTER, "r")         # Open the file
    counterString=fileHandle.readline()          # Read the first line
    counter=int(counterString)
    fileHandle.close()                           # Close the file

    # Output the Heading
    if(counter==0):
        logText="Count\tLevel\tMethodName\t\tDetails"
        print(logText)
        if(logToFile):
            filelog(1, logText)
        logText="=================================================================================="
        print(logText)
        if(logToFile):
            filelog(1,logText)
    
    counter = counter + 1
    # Open the counter file for write (replace)
    fileHandle = open(DEBUGCOUNTER, "w")
    fileHandle.write(str(counter))
    fileHandle.close()
    
    logText=str(counter) + "\t" + str(debugLevel) + "\t" + methodName + "\t" + str(details)
    print(logText)
    if(logToFile):
        filelog(debugLevel,logText)
    if(debugLevel >=3):
        micropython.mem_info()
    sLock.release()

def filelog(debugLevel, logtext):
    file=open(LOGFILE,"a")                              # creation and opening of a CSV file in Write mode
    file.write((str(time.ticks_ms())+"~")+str(logtext)+"\n")  # Writing data in the opened file

    if(debugLevel >=3):
        micropython.mem_info()
    file.close()                                              # The file is closed

# debug(2,"test()","debug.py run directly",True)