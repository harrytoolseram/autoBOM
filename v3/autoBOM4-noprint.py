#! /usr/bin/python
from tinydb import TinyDB, Query
import yaml
import pprint, os.path

#Simulate User Requirement Inputs
req100GE=12
req40GE=15
req10GE=60
depth=7
#scbe settings: 0 - redundant (2+1), 1 - active (3+0)
scbe=1
#if scbe=0, the MPCBW for MPC7 is reset to bwMPC value specified below.
bwMPC=340

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
		return(1) # return, nothing to do
	pp = pprint.PrettyPrinter(indent=2)
	db = TinyDB('data2.json')
	# Clear tinyDB
	db.purge()

	# Open the YAML source files
	f = open('data2.yml')
	d = yaml.load_all(f)
	for i in d:
  		pp.pprint(i)
  		db.insert(i)
	db.all()

########################

def PortTypeMap(x):

	if x==0:
        	sindex='et100'
        elif x==1:
        	sindex='et'
        elif x==2:
        	sindex='xe'
	return sindex

########################
# Based on user requirements, retrieve relevant SKUs from TinyDB.

def RetrieveSKUfromDB():

	global SKUlist

	db=TinyDB('data2.json')
	BOM=Query()
	#Retrieve corresponding SKUs based on user requirement of 100G, 40G, 10G
	for index, item in enumerate(MainReq):
		Prodata=[]
		sindex=PortTypeMap(index)
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

########################
# Process relevant SKUs by:
# - removing duplicate SKUs
# - creating an internally defined SKU list for program processing

def SKUconditioning():

	global SKUlist,SKUdata,scbe,bwMPC

	SKUdata=[]
	for i in range(0,len(SKUlist)):
		temp=[]
		temp.append(SKUlist[i]['SKU'])
		for j in range(0,len(MainReq)):
			sindex=PortTypeMap(j)
			try:
				if SKUlist[i]['Provides'][0][sindex] != 0:
					temp.append(SKUlist[i]['Provides'][0][sindex])
			except:
				temp.append(0)
		if (scbe==0) & (SKUlist[i]['SKU'][:4]=='MPC7'):
			temp.append(bwMPC)
		else:
			temp.append(SKUlist[i]['MPCBW'])
		temp.append(SKUlist[i]['Price'])
	        if SKUlist[i]['Provides'][1]['ports'] != 'NA':
     			temp.append(SKUlist[i]['Provides'][1]['ports'])
        	else:
            		temp.append(0)
		SKUdata.append(temp[:])

########################
# Run thru the various SKU combinations. Process the SKUs by identifying which ones are
# used in meeting the user requirement of et100, et and xe ports.

def SKUnReqMapping():

    global SKUdata,final,lowest,PortBalance,MainReq

    lowest=[]
    lowest.append("You are FUCKED! Can't meet requirements! Need more slots!")
    highest=[]
    highest.append("You are FUCKED! Can't meet requirements! Need more slots!")

    matchfound=0
    empty=1
    for i in range(0,len(final)):

        # iterating thru the SKU combination list. "final" represents the
        # 2-dimensional list of all SKU combinations. This loops thru the line
        # item

        PortBalance=MainReq[:]
        ProcessMPC=[]
        y=final[i]
        TotalCost=0
	PortTracking=[]
        for j in range(0,len(y)):

            # Loops thru the individual SKUs within the line item

            BW=0
            useMPC=0
            portcount=0
            maxportcount=0

            for h in range(0,len(PortBalance)):

                # Processing port count (et100, et, xe) against each SKU

                count=0
		maxBW=0

                # MPC bandwidth tracking. incrementing bandwidth based on port type
                # "portdeduct" is specific for MRATE cards to ensure physical port limits
                # are enforced

		portdeduct=1
                if h==0:
                    xmultiply=100
                elif h==1:
                    xmultiply=40
		elif h==2:
		    xmultiply=10
		    if SKUdata[(y[j])][6] != 0:
                        portdeduct = (SKUdata[(y[j])][6]*1.0) / SKUdata[(y[j])][3]
           	
          	while (PortBalance[h]>0) & (maxportcount == 0) & (maxBW==0):

           	    if SKUdata[(y[j])][6] != 0:
                        if (portcount+portdeduct) > SKUdata[(y[j])][6]:
                            maxportcount=1
                    if (count + 1) > SKUdata[(y[j])][h+1]:
			maxBW=1
		    if ((BW + xmultiply) > SKUdata[(y[j])][4]):
			maxBW=1
		    if (maxportcount==0) & (maxBW==0):
                        count+=1
                        portcount+=portdeduct
                        BW+=xmultiply
                        PortBalance[h]=PortBalance[h]-1
                        useMPC=1
            if useMPC==1:
		PortTracking.append(PortBalance[:])
                ProcessMPC.append(SKUdata[(y[j])])
                TotalCost=TotalCost+SKUdata[(y[j])][5]
        if (PortBalance[0]<=0) & (PortBalance[1]<=0) & (PortBalance[2]<=0):

            # Calculating lowest and highest cost BOM

            matchfound=1
            if empty==1:
                lowest=ProcessMPC[:]
                lowest.append(TotalCost)
		lowPTracking=PortTracking[:]
                highest=lowest[:]
		highPTracking=PortTracking[:]
                empty=0
            elif TotalCost < lowest[len(lowest)-1]:
                lowest=ProcessMPC[:]
                lowest.append(TotalCost)
		lowPTracking=PortTracking[:]
            elif TotalCost > highest[len(highest)-1]:
                highest=ProcessMPC[:]
                highest.append(TotalCost)
		highPTracking=PortTracking[:]

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
    if scbe==0:
    	print "SCBE:        2+1 (redundant)"
    else:
	print "SCBE:        3+0 (active)"
    print
    print '##############################'
    print "RESULTS: CHEAPEST OPTION"
    print
    if matchfound==1:
        for i in range(0,len(lowest)):
            if i==(len(lowest)-1):
                print ('Total:   ' + 'USD ${:,.2f}'.format(lowest[i]))
            else:
		if i==0:
		    print MainReq,lowest[i]
                else:
		    print lowPTracking[i-1],lowest[i]
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
                if i==0:
                    print MainReq,highest[i]
                else:
                    print highPTracking[i-1],highest[i]
    else:
        print highest

########################
# MAIN PROGRAM #

loadTinyDB()
for z in range(0,depth):
        tmp.append(999)
RetrieveSKUfromDB()
SKUconditioning()
ComboRecursive()
SKUnReqMapping()

########################
