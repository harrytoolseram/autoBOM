#! /usr/bin/python
from tinydb import TinyDB, Query
import yaml
import pprint, os.path

#Simulate User Requirement Inputs
req100GE=0
req40GE=0
req10GE=88
depth=3

#Internal workspace
tmp=[]
final=[]
listpos=-1
count=0

#Place user requirements in a list called MainReq (Main Requirements)
MainReq=[]
MainReq.append(req100GE)
MainReq.append(req40GE)
MainReq.append(req10GE)

#Initialize selected SKUs list. SKUs will be populated here from TinyDB based on user criteria
SKUlist=[]

#######################

def ComboRecursive():

        global tmp,depth,listpos,final,count,SKUlist

        if (listpos < (depth-1)):
                listpos+=1
                for i in range(0,len(SKUlist)):
                        tmp[listpos]=i
                        if listpos == (depth-1):
                                final.append(tmp[:])
                                count+=1
                        ComboRecursive()
                listpos-=1

########################

def loadTinyDB():

	global db

        # Check if DB is up to date
	if os.path.getmtime('data.json') > os.path.getmtime('data.yml'):
		print "DB up to date."
                print
		return(1) # return, nothing to do
	pp = pprint.PrettyPrinter(indent=2)
	db = TinyDB('data.json')
	# Clear tinyDB
	db.purge()

	# Open the YAML source files
	f = open('data.yml')
	d = yaml.load_all(f)
	print "Inserting into Database"
	for i in d:
  		pp.pprint(i)
  		db.insert(i)

	print "Dump DB"
	db.all()

########################

def RetrieveSKUfromDB():

	global SKUlist

	db=TinyDB('data.json')
	BOM=Query()
	print '######################################################################################'
	print 'User requirement placed in list...and indexed & in sequence of et100, et, xe (topdown)'
	print
	#Retrieve corresponding SKUs based on user requirement of 100G, 40G, 10G
	for index, item in enumerate(MainReq):
		Prodata=[]
		print index, item
		if index==0:
			sindex='et100'
		elif index==1:
			sindex='et'
		elif index==2:
			sindex='xe'
		if item != 0:
			Prodata=db.search((BOM.Type == 'MPC') & (BOM.Provides[0][sindex] != 0))
			if len(Prodata)>0:
				for x in range(0, len(Prodata)):
					SKUlist.append(Prodata[x])

	#Remove duplicate SKUs from list
	tempSKUlist=SKUlist
	SKUlist=[]
	for x in range(0, len(tempSKUlist)):
		if tempSKUlist[x] not in SKUlist:
			SKUlist.append(tempSKUlist[x])
	for i in range(0,3):
		print
    #Result of this process
	print '#########################################################################################'
        print "RESULT:  RetrieveSKUfromDB. Filter and retrieve appropriate SKU based on user requirement"
	print
	print "Number of SKUs: " + str(len(SKUlist))
        for i in range(0,len(SKUlist)):
                print SKUlist[i]
        for j in range(0,3):
                print

########################

def SKUconditioning():

	global SKUlist,SKUdata

	SKUdata=[]
	for i in range(0,len(SKUlist)):
		temp=[]
		temp.append(SKUlist[i]['SKU'])
		for j in range(0,len(MainReq)):
                	if j==0:
				sindex='et100'
                	elif j==1:
				sindex='et'
                	elif j==2:
				sindex='xe'
			try:
				if SKUlist[i]['Provides'][0][sindex] != 0:
					temp.append(SKUlist[i]['Provides'][0][sindex])
			except:
				temp.append(0)
		temp.append(SKUlist[i]['MPCBW'])
		temp.append(SKUlist[i]['Price'])
		SKUdata.append(temp[:])

	print '##########################################################################'
	#Result of this process
	print "RESULT:  SKUconditioning. Create temp list of SKUs for processing purposes"
	print
	for i in range(0,len(SKUdata)):
        	print SKUdata[i]
	for j in range(0,3):
        	print

########################

def SKUnReqMapping():

    global SKUdata,final,lowest,PortBalance,MainReq

    print '##################################################################################################'
    #Result of this process
    print "RESULT:  ComboRecursive. Create full matrix of SKU combinations based on number of slots defined"
    print
    for i in range(0,len(final)):
        print final[i]
    for j in range(0,3):
        print

########################

    lowest=[]
    lowest.append("You are FUCKED! Can't meet requirements! Need more slots!")
    highest=[]
    highest.append("You are FUCKED! Can't meet requirements! Need more slots!")

    matchfound=0
    empty=1
    print "HT1"
    for i in range(0,len(final)):
        PortBalance=MainReq[:]
        ProcessMPC=[]
        y=final[i]
        TotalCost=0
        print "HT2"
        for j in range(0,len(y)):
            BW=0
            useMPC=0
            print "HT3",len(final),len(y)
            for h in range(0,len(PortBalance)):
                count=0
                print "HT4",h
                print PortBalance
                if PortBalance[h] > 0:
                    while (BW < SKUdata[(y[j])][4]) & (count < SKUdata[(y[j])][h+1]) & (PortBalance[h]>0):
                        print "Inside"
                        if h==0:
                            xmultiply=100
                        elif h==1:
                            xmultiply=40
                        elif h==2:
                            xmultiply=10
                        count+=1
                        BW+=xmultiply
                        PortBalance[h]-=1
                        useMPC=1
            if useMPC==1:
                print "useMPC"
                ProcessMPC.append(SKUdata[(y[j])])
                print ProcessMPC
                TotalCost=TotalCost+SKUdata[(y[j])][5]
                print TotalCost
        if (PortBalance[0]<=0) & (PortBalance[1]<=0) & (PortBalance[2]<=0):
            matchfound=1
            if empty==1:
                lowest=ProcessMPC[:]
                lowest.append(TotalCost)
                highest=lowest[:]
                empty=0
            elif TotalCost < lowest[len(lowest)-1]:
                lowest=ProcessMPC[:]
                lowest.append(TotalCost)
            elif TotalCost > highest[len(highest)-1]:
                highest=ProcessMPC[:]
                highest.append(TotalCost)
    print
    print '##############################'
    print "USER REQUIREMENTS:"
    print
    for i in range(0,len(MainReq)):
        if i==0:
            print "et100:       " + str(MainReq[i])
        if i==1:
            print "et:          " + str(MainReq[i])
        if i==2:
            print "xe:          " + str(MainReq[i])
    print "Max Slots:   " + str(depth)
    print
    print '##############################'
    print "RESULTS: CHEAPEST OPTION"
    print
    if matchfound==1:
        for i in range(0,len(lowest)):
            if i==(len(lowest)-1):
                print ('Total:   ' + 'USD ${:,.2f}'.format(lowest[i]))
            else:
                print lowest[i]
    else:
        print lowest
    print
    print '##############################'
    print "RESULTS: MOST EXPENSIVE OPTION"
    print
    if matchfound==1:
        for i in range(0,len(highest)):
            if i==(len(highest)-1):
                print ('Total:   ' + 'USD ${:,.2f}'.format(highest[i]))
            else:
                print highest[i]
    else:
        print highest

########################
# MAIN PROGRAM #

loadTinyDB()
counterSKU=[]
db=TinyDB('data.json')
BOM=Query()
PortType=0
flag100GE=0
flag40GE=0
flag10GE=0
slot=[]
Intcon=0
for z in range(0,depth):
        tmp.append(999)
RetrieveSKUfromDB()
SKUconditioning()
ComboRecursive()
SKUnReqMapping()

########################
