'''
Abdullah Zameek - Scheduling Lab (simulate FCFS, SJF, RR and HRPN)

'''
import sys

########
#These are global flags that are going to be used over the course of the code. 
global VERBOSE, SHOW_RANDOM, OPEN, randomFile, RR, IOUtilisation
IOUtilisation = 0
RR = False
VERBOSE = False
SHOW_RANDOM = False
OPEN = True
#################### HELPER FUNCTIONS/CLASSES START HERE ###############################

def processInput():
    '''Returns a list of lists of all process blocks and the number of processes.'''
    with open(sys.argv[-1], 'r') as f:
        contents = f.read()
    contents = contents.split()
    contents = [int(i) for i in contents]
    numProcesses = contents.pop(0)
    return [contents[i:i + 4] for i in range(0, len(contents), 4)], numProcesses

def randomOS(U):
    '''Returns the value 1 + X mod U '''
    randomNo = int(randomFile.readline().strip())
    return 1 + randomNo % U

class Timer:
    def __init__(self):
        self.timer = 0

    def getTime(self):
        return self.timer
    
    def update(self):
        self.timer+=1

################## END OF HELPER FUNCTIONS/CLASSES #####################################

class Process:  
    def __init__(self,A,B,C,M,i):
        self.A = A
        self.B = B
        self.C = C
        self.M  = M
        self.i = i
        self.state = "unstarted" # There are five possible states -> unstarted, ready, running, blocked, terminated
        self.readyTime = 0
        self.burst = 0
        self.previousBurst = 0 
        self.remainingTime = C
        self.finishTime = 0
        self.runningTime = 0
        self.blockedTime = 0
        self.waitingTime = 0
        self.turnaroundTime = 0

        ### JUST FOR RR ######
        self.quantum = 2
        ### JUST FOR RR ######


    def updateState(self):
        curTime = sysClock.getTime()
        if self.state == "unstarted":
            if curTime == self.A:
                self.setReady()

        if self.state == "blocked":
            if self.burst == 0:
                self.setReady()

        if self.state == "running":
            if self.remainingTime == 0:
                self.state = "terminated"
                self.finishTime = curTime
                self.burst = 0
            elif self.burst == 0:
                self.setBlocked()
            elif RR:
                if self.quantum == 0:
                    self.setReady()
        return

    def getCPUBurst(self):
        self.previousBurst = randomOS(self.B)
        self.burst = self.previousBurst
        return

    def getIOBurst(self):
        self.burst = self.previousBurst * self.M
        return 

    def setBlocked(self):
        self.getIOBurst()
        self.state = "blocked"
        return
    
    def setReady(self):
        curTime = sysClock.getTime()
        self.state = "ready"
        self.readyTime = curTime
        return

    def setRunning(self):
        self.state = "running"
        if RR:
            self.quantum = 2
        if self.burst == 0:
            self.getCPUBurst()
        return

    def getRatio(self):
        return self.turnaroundTime/max(1,self.runningTime)

    def updateTimes(self):
        if self.state not in ["unstarted", "terminated"]: #Nothing to do in these two cases 
            self.turnaroundTime+=1
            if self.state == "ready":
                self.waitingTime+=1
            elif self.state == "running":
                self.runningTime += 1
                self.remainingTime -= 1
                if RR:
                    self.quantum -=1
                if (self.burst):
                    self.burst -=1
            elif self.state == "blocked":
                self.blockedTime +=1
                if self.burst > 0:
                    self.burst -=1
        return 

    def printProcessAttr(self):
        print("({} {} {} {})  ".format(self.A, self.B, self.C, self.M), end='')

    def printProcess(self):
        print("\t(A, B, C, M) = ({}, {}, {}, {})\n\tFinishing Time: {}\n\tTurnaround Time: {}\n\tI/O Time: {}\n\tWaiting Time: {}\n\t".format(self.A, self.B, self.C, self.M, self.finishTime, self.finishTime-self.A, self.blockedTime, self.waitingTime))


######################## MANIPULATE THE PROCESSLIST #############################################

def orderByArrivalTime(processList):
     processList.sort(key=lambda process: process.A)
     return processList

def orderByInput(processList):
    processList.sort(key=lambda process: process.i)
    return processList

def orderByReadyState(processList):
    processList.sort(key=lambda process: process.readyTime)
    return processList

def orderByShortestJob(processList):
    processList.sort(key=lambda process: process.C - process.runningTime)
    return processList

def orderByHPRN(processList):
    processList.sort(key=lambda process: -process.getRatio())
    return processList  

def checkComplete(processList):
    global finishTime
    for process in processList:
        if process.state != "terminated":
            return False
    finishTime = sysClock.getTime() - 1
    return True
        
def getProcessesByState(processList, state):
    newList = []
    for process in processList:
        if process.state == state:
            newList.append(process)
    return newList

def updateProcessTimers(processList):
   global IOUtilisation
   if getProcessesByState(processList, "blocked"):
        IOUtilisation += 1
   for process in processList:
        process.updateTimes()
   return 

def updateProcessStates(processList):
    for process in processList:
        process.updateState()
    return

def printListSummary(processList):
    cpuUtil = sum(list([process.runningTime for process in processList])) / finishTime
    ioUtil = (IOUtilisation / finishTime)
    throughput = 100*len(processList) / finishTime
    turnaround = sum(list([process.turnaroundTime for process in processList])) / len(processList)
    waitingTime = sum(list([process.waitingTime for process in processList])) / len(processList)
    print("Summary Data :\n\tFinishing Time: {}\n\tCPU Utilisation: {:.6f}\n\tI/O Utilisation: {:.6f}\n\tThroughput: {:.6f} processes per hundred cycles\n\tAverage turnaround time: {:.6f}\n\tAverage Waiting Time: {:.6f}".format(finishTime,cpuUtil,ioUtil, throughput, turnaround, waitingTime))


####################### END OF PROCESS LIST MANIPULATION ##########################################


########################## SCHEDULING ALGORITHM ##################################################

def schedulingAlgorithm(processList, schedulingMethod, RndR=False):
    global RR 
    RR = RndR
    i = 0
    while not checkComplete(processList):
        if VERBOSE:
            verboseLine= ""
            print("Before Cycle {}       ".format(str(i)),end='')
            for process in processList:
                verboseLine += process.state + "  : " + str(process.burst) + "     "
            print(verboseLine)
            i+=1
        updateProcessTimers(processList)
        updateProcessStates(processList)
        if not(getProcessesByState(processList, "running")):
            readyProcesses = orderByArrivalTime(orderByInput(getProcessesByState(processList,"ready")))
            if schedulingMethod == "First Come First Served":
                readyProcesses = orderByReadyState(readyProcesses) #this only works for first come first served 
            if schedulingMethod == "Round Robin":
                readyProcesses = orderByReadyState(readyProcesses)
            if schedulingMethod == "Shortest Job First":
                readyProcesses = orderByShortestJob(readyProcesses)
            if schedulingMethod == "Highest Penalty Ratio Next":
                readyProcesses = orderByHPRN(readyProcesses)
            if readyProcesses:
                readyProcesses.pop(0).setRunning()
        sysClock.update()
    print()
    print("The scheduling algorithm used was "+schedulingMethod)
    print()
    return processList

########################## MAIN  ##################################################
def main():
    global VERBOSE, SHOW_RANDOM
    global sysClock
    global finishTime 
    global IOUtilisation
    global randomFile
    randomFile = open("random-numbers.txt", 'r')
    IOUtilisation =0 
    finishTime = 0

    if "--verbose" in sys.argv:
        VERBOSE = True
    if "--show-random" in sys.argv:
        SHOW_RANDOM = True
   
   ################################# FIRST COME FIRST SERVED ################################

    #First, we take the input files and read the inputs into a list of lists and return it.
    processes, numProcesses = processInput()
    sysClock = Timer()
    processList = []
    #Then, we take this list of lists of processes and then create each list into a "Process"
    for i in range(len(processes)):
        processList.append(Process(*processes[i],i)) 
    print("The original input was : "+str(numProcesses)+" ", end='')
    for process in processList:
        process.printProcessAttr()
    print()
    #Then, we take each of these processes and then append it to a process list.
    processList = orderByArrivalTime(processList)
    
    print("The sorted input was :   "+str(numProcesses)+" ", end='')
    for process in processList:
        process.printProcessAttr()
    print("\n")
    processList = schedulingAlgorithm(processList, "First Come First Served")
    for i in range(len(processList)):
        print("Process {}:\t".format(str(i)))
        processList[i].printProcess()
    #Then we manipulate the process list until all the processes have a state of terminated and then we're done. 
    printListSummary(processList)
    print("---------------------------------------------------------------------------------")
    ########################### ROUND ROBIN  #################################################
    IOUtilisation =0 
    finishTime = 0
    randomFile.seek(0)
    #First, we take the input files and read the inputs into a list of lists and return it.
    processes, numProcesses = processInput()
    sysClock = Timer()
    processList = []
    #Then, we take this list of lists of processes and then create each list into a "Process"
    for i in range(len(processes)):
        processList.append(Process(*processes[i],i)) 
    print("The original input was : "+str(numProcesses)+" ", end='')
    for process in processList:
        process.printProcessAttr()
    print()
    #Then, we take each of these processes and then append it to a process list.
    processList = orderByArrivalTime(processList)
    
    print("The sorted input was :   "+str(numProcesses)+" ", end='')
    for process in processList:
        process.printProcessAttr()
    print("\n")
    processList = schedulingAlgorithm(processList, "Round Robin", True)
    for i in range(len(processList)):
        print("Process {}:\t".format(str(i)))
        processList[i].printProcess()
    #Then we manipulate the process list until all the processes have a state of terminated and then we're done. 
    printListSummary(processList)
    print("---------------------------------------------------------------------------------")
    ########################### SHORTEST JOB FIRST #################################################
    IOUtilisation =0 
    finishTime = 0
    randomFile.seek(0)
    #First, we take the input files and read the inputs into a list of lists and return it.
    processes, numProcesses = processInput()
    sysClock = Timer()
    processList = []
    #Then, we take this list of lists of processes and then create each list into a "Process"
    for i in range(len(processes)):
        processList.append(Process(*processes[i],i)) 
    print("The original input was : "+str(numProcesses)+" ", end='')
    for process in processList:
        process.printProcessAttr()
    print()
    #Then, we take each of these processes and then append it to a process list.
    processList = orderByArrivalTime(processList)
    
    print("The sorted input was :   "+str(numProcesses)+" ", end='')
    for process in processList:
        process.printProcessAttr()
    print("\n")
    processList = schedulingAlgorithm(processList, "Shortest Job First")
    for i in range(len(processList)):
        print("Process {}:\t".format(str(i)))
        processList[i].printProcess()
    #Then we manipulate the process list until all the processes have a state of terminated and then we're done. 
    printListSummary(processList)
    print("---------------------------------------------------------------------------------")
    ########################### HIGHEST PENALTY RATIO NEXT #################################################
    IOUtilisation =0 
    finishTime = 0
    randomFile.seek(0)
    #First, we take the input files and read the inputs into a list of lists and return it.
    processes, numProcesses = processInput()
    sysClock = Timer()
    processList = []
    #Then, we take this list of lists of processes and then create each list into a "Process"
    for i in range(len(processes)):
        processList.append(Process(*processes[i],i)) 
    print("The original input was : "+str(numProcesses)+" ", end='')
    for process in processList:
        process.printProcessAttr()
    print()
    #Then, we take each of these processes and then append it to a process list.
    processList = orderByArrivalTime(processList)
    
    print("The sorted input was :   "+str(numProcesses)+" ", end='')
    for process in processList:
        process.printProcessAttr()
    print("\n")
    processList = schedulingAlgorithm(processList, "Highest Penalty Ratio Next")
    for i in range(len(processList)):
        print("Process {}:\t".format(str(i)))
        processList[i].printProcess()
    #Then we manipulate the process list until all the processes have a state of terminated and then we're done. 
    printListSummary(processList)
    print("---------------------------------------------------------------------------------")


    
if __name__ == "__main__":
    main()