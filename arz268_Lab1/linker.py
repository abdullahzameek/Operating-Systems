import sys

#function to read from standard input. Once user has typed in input, hit enter and Ctrl+D to indicate end of input
#Take the input and put the entire thing into a list
def readStdIn():
    file = []
    final = []
    for line in sys.stdin:
        file.append(line.strip("\n"))
    for wordblock in file:
            wordList = wordblock.split()
            for word in wordList:
                try:
                    final.append(int(word))
                except:
                    final.append(word)
    return final
        


def firstParse(initialInput):
    numModules = initialInput[0]
    cur = 1 #we dont need the 0th element since thats just the number of modules
    symbolTable = {} #Final Symbol Table
    instructions = [] #Final list of list of instructions
    offset = 0
    offsets = [0] #keep track of offsets 
    symbolErrors = {} #log errors 
    symbolModule = {} #log which symbols belong to which module

    for i in range(numModules):
        #first step is to get the definitions sorted out
       numDefs = initialInput[cur]
       cur+=1
       #loop through all the definitions and record their values in a dictionary 
       for j in range(numDefs):
           if initialInput[cur] not in symbolTable:
               symbolTable[initialInput[cur]] =  initialInput[cur+1] + offset 
               symbolModule[initialInput[cur]] = i
               cur+=2
               
           else:
               #Handle the case where the symbol already exists in the dictionary 
               symbolErrors[initialInput[cur]] = "Error: The symbol " + str(initialInput[cur]) + " has already been defined! The first value was used"
               cur+=2
       
       #in the first parse, we are not too concerned with the usage list, so we just skip it 
       cur = cur + 2*initialInput[cur]+1
       #get the number of instructions that are in the current module
       numInstructions = initialInput[cur]
       offset+=numInstructions
       offsets.append(offset)
       cur+=1
       instructions.append(initialInput[cur:cur+numInstructions])
       cur = cur + numInstructions
       
       #Handle the case where the value of a symbol is out of scope of 
       for symbol, value in symbolTable.items():
            if symbolModule[symbol] == i:
                if value-offsets[i] > numInstructions-1:
                    symbolTable[symbol] = offsets[i]
                    symbolErrors[symbol] = "Error: The symbol " + str(symbol) + " lies out of scope of its module. The current address of this has been set to zero (relative)"           

    offsets.pop(-1)
    return symbolTable, instructions , offsets, symbolErrors, symbolModule

def secondParse(initialInput, symbolTable, instructions, offsets):

    numModules = initialInput[0]
    cur = 1 #we dont need the 0th element since thats just the number of modules
    useList = [] #keep track of the useList of each module
    memoryErrors = {} #keep track of all the memory errors that occue
    usedSymbols = [] #to be used when checking which symbols were used
    
    for i in range(numModules):
        useList = []
        #this will be used to see if multiple symbols reference the same address
        visited = [False]*len(instructions[i])

        #we are not concerned with the definition list, so we skip it like how we did with the use list above. 
        cur = cur + initialInput[cur]*2+1
        #now, we're at the number of uses in the module, so we note that down and add one
        numUses = initialInput[cur]
        

        cur+=1
        offset = 0


        for j in range(numUses):
            #Now we need to check the following with regards to each symbol
            #if they are defined and used
            #if they are defined but not used
            #if they are used but not defined
            #if multiple symbols are used at the same place
            curSymbol = initialInput[cur]

            #check if symbol exists or not 
            if curSymbol not in symbolTable:
                notDefined = True
                external = 0
            else:
                notDefined = False
                external = symbolTable[curSymbol]
                usedSymbols.append(curSymbol)

            curIndex = initialInput[cur+1]
            curNum = instructions[i][curIndex]    
            trueIndex = int(str(curNum)[1:4])

            #traverse through the addresses until you hit 777
            while(trueIndex != 777):
                #error check to see if a type 1 appeared on the list
                if(int(str(curNum)[4]) == 1):
                    memoryErrors[offsets[i]+curIndex] = "Error: Type 1 address appeared on use list. Treated as Type 4"
                    instructions[i][curIndex] = curNum-1+4
                #error check to see if a symbol has been defined or not
                if(notDefined):
                    memoryErrors[offsets[i]+curIndex] = "Error: Symbol " + str(curSymbol) + " has not been defined but used in module " + str(i) +". It has been assigned the value 0" 
                    external = 0
                visited[curIndex] = True
                temp = int(str(int(str(curNum)[:4]) - int(str(curNum)[1:4]) + external) + '4') 
                instructions[i][curIndex] = temp
                curIndex = trueIndex
                curNum = instructions[i][curIndex]
                trueIndex = int(str(curNum)[1:4])

            # check if multiple symbols have attempted to be used at the same locations
            if(visited[curIndex] is not False):
                memoryErrors[offsets[i]+curIndex] = "Error: Multiple symbols attempted to be used at module "+str(i) + ".All but the last usage have been ignored"
            #check if symbol was defined or not
            if(notDefined):
                memoryErrors[offsets[i]+curIndex] = "Error: Symbol " + str(curSymbol) + " has not been defined but used in module " + str(i) +". It has been assigned the value 0"
                external = 0
            visited[curIndex] = "Done"
            temp = int(str(int(str(curNum)[:4]) - int(str(curNum)[1:4]) + external) + '4')
            instructions[i][curIndex] = temp

            useList.append(initialInput[cur+1])
            cur+=2

        
        numInstructions = initialInput[cur] #number of instructions
        insts = list(instructions[i]) #get the instructions from the instructions list from parse 1 
        for k in range(0,numInstructions):
            lastDigit = int(str(instructions[i][k])[-1]) #get the last digit
            inst = int(str(instructions[i][k])[1:4]) #get the middle three
            #handle case where a type 4 was not in the uselist
            if lastDigit == 4:
                if k not in useList and visited[k] == False:
                    memoryErrors[i+k] = "Error: Type 4 address did not appear on use list. Treated as Type 1"
                    instructions[i][k] = instructions[i][k] -4 +1
            #handle cases for immediate and absolute address out of scope
            if(lastDigit == 2):
                if(inst % 1000 > 200):
                    memoryErrors[offsets[i]+k] = "Error: Absolute address exceeds size of machine, 199 used (max 200)"
                    instructions[i][k] = instructions[i][k] - (inst % 1000)
                    instructions[i][k] += 199
            elif(lastDigit == 3):
                instructions[i][k] = int(str(int(str(int(str(instructions[i][k])[:4])+offsets[i]))) + '3') 
                if(inst % 1000 > 200):
                    memoryErrors[offsets[i]+k] = "Error: Absolute address exceeds size of machine, 199 used (max 200)"
                    instructions[i][k] = instructions[i][k] - (inst % 1000)
                    instructions[i][k] += 199
        cur += numInstructions+1

    return memoryErrors,usedSymbols

def printEverything(symbolTable, instructions, symbolErrors, memErrors, used, syms):
    print()
    #first print the symbol table
    print("Symbol Table: ")
    for key, value in symbolTable.items():
        if key in symbolErrors:
            error = symbolErrors[key]
        else:
            error = ""
        print(str(key) + ": " + str(value)+"   " +error)

    print()
    tempList = []
    for inst in instructions:
        for i in inst:
            tempList.append(i)
    print("Memory Map: ")
    for i in range(len(tempList)):
        if i in memErrors:
            error = memErrors[i]
        else:
            error = ""
        print(str(i)+": "+str(tempList[i])[:4]+"  "+error)

    for key in symbolTable:
        if key not in used:
            print("Warning: "+key+" was defined in module "+ str(syms[key]) + " but was not used")
    print()
    
        
def main():
    final = readStdIn()
    symbolTable, instructions, offsets, symbolErrors, syms = firstParse(final)
    memErrors, used = secondParse(final, symbolTable, instructions, offsets)

    printEverything(symbolTable, instructions, symbolErrors, memErrors, used, syms)

if __name__ == "__main__":
    main()
