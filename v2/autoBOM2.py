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
# This function will recursively create relevant SKU combinations based
# on number of line card slots (eg. depth) specified in user requirement

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
# Convert YAML based SKUs to JSON format and populate TinyDB

def loadTinyDB():

	global db

        # Check if DB is up to date
	if os.path.getmtime('data2.json') > os.path.getmtime('data2.yml'):
		print "DB up to date."
                print
		return(1) # return, nothing to do
	pp = pprint.PrettyPrinter(indent=2)
	db = TinyDB('data2.json')
	# Clear tinyDB
	db.purge()

	# Open the YAML source files
	f = open('data2.yml')
	d = yaml.load_all(f)
	print "Inserting into Database"
	for i in d:
  		pp.pprint(i)
  		db.insert(i)

	print "Dump DB"
	db.all()

########################
# Based on user requirements, retrieve relevant SKUs from TinyDB.

def RetrieveSKUfromDB():

	global SKUlist

	db=TinyDB('data2.json')
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
# Process relevant SKUs by:
# - removing duplicate SKUs
# - creating an internally defined SKU list for program processing

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
	        if SKUlist[i]['Provides'][1]['ports'] != 'NA':
     			temp.append(SKUlist[i]['Provides'][1]['ports'])
        	else:
            		temp.append(0)
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
# Run thru the various SKU combinations. Process the SKUs by identifying which ones are
# used in meeting the user requirement of et100, et and xe ports.

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
    portdeduct=0.0
    for i in range(0,len(final)):

        # iterating thru the SKU combination list. "final" represents the
        # 2-dimensional list of all SKU combinations. This loops thru the line
        # item

        PortBalance=MainReq[:]
        ProcessMPC=[]
        y=final[i]
        TotalCost=0
        print "HT2"
        for j in range(0,len(y)):

            # Loops thru the individual SKUs within the line item

            BW=0
            useMPC=0
            portcount=0.0
            maxportcount=0
            print "HT3",len(final),len(y)
            for h in range(0,len(PortBalance)):

                # Processing port count (et100, et, xe) against each SKU

                count=0
                print "HT4",h
                print PortBalance
                if PortBalance[h] > 0:

                    # Proceed if specific port type (et100, et, xe) balance > 0

                    while (BW < SKUdata[(y[j])][4]) & (count < SKUdata[(y[j])][h+1]) & (PortBalance[h]>0) & (maxportcount == 0):
                        print "Inside",BW,count,PortBalance[h],h,portdeduct,SKUdata[(y[j])],SKUdata[(y[j])][4],SKUdata[(y[j])][6]

                        # MPC bandwidth tracking. incrementing bandwidth based on port type
                        # "portdeduct" is specific for MRATE cards to ensure physical port limits
                        # are enforced

                        if h==0:
                            xmultiply=100
			    portdeduct=1.0
                        elif h==1:
                            xmultiply=40
                            portdeduct=1.0
                        elif h==2:
                            xmultiply=10
			    if SKUdata[(y[j])][6] != 0:
			        portdeduct = (SKUdata[(y[j])][6]*1.0) / SKUdata[(y[j])][3]
                                print "portdeduct:", portdeduct
		            else:
                                portdeduct=1.0
                        print SKUdata[(y[j])][6], portdeduct,maxportcount,portcount
                        if SKUdata[(y[j])][6] != 0:
                            print SKUdata[(y[j])][6], portdeduct
                            if (portcount+portdeduct) > SKUdata[(y[j])][6]:
			        maxportcount=1
                                print "PORTS FULL!"
                        if ((BW + xmultiply) <= SKUdata[(y[j])][4]) & (maxportcount==0):
                            print "BW:",BW
                            count+=1
                            portcount+=portdeduct
                            BW+=xmultiply
                            PortBalance[h]-=1
                            useMPC=1
			else:
			    maxportcount=1
            if useMPC==1:
                print "useMPC"
                ProcessMPC.append(SKUdata[(y[j])])
                print ProcessMPC
                TotalCost=TotalCost+SKUdata[(y[j])][5]
                print TotalCost
        if (PortBalance[0]<=0) & (PortBalance[1]<=0) & (PortBalance[2]<=0):

            # Calculating lowest and highest cost BOM

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
