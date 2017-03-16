#! /usr/bin/python
from tinydb import TinyDB, Query
import yaml
import pprint, os.path

#Simulate User Requirement Inputs
req100GE=0
req40GE=0
req10GE=49
Available_Slots=6
#SCBE settings: 0 - redundant (2+1), 1 - active (3+0)
SCBE=1
#if SCBE=0, the MPC bandwidth for MPC7 is reset to MPC7_Redundant_BW value specified below.
MPC7_Redundant_BW=340

#Internal workspace
tmp=[]
SKU_Combo_Matrix=[]
Slot_Position=-1

#Place user requirements in a list called UserReq (Main Requirements)
UserReq=[]
UserReq.append(req100GE)
UserReq.append(req40GE)
UserReq.append(req10GE)

#Initialize selected SKUs list. SKUs will be populated here from TinyDB based on user criteria
SKU_DB_Selected_List=[]

#######################
# This function will recursively create relevant SKU combinations based
# on number of line card slots (eg. Available_Slots) specified in user requirement

def ComboRecursive():

        global tmp,Available_Slots,Slot_Position,SKU_Combo_Matrix,SKU_DB_Selected_List

        if (Slot_Position < (Available_Slots-1)):
                Slot_Position+=1
                for i in range(0,len(SKU_DB_Selected_List)):
                        tmp[Slot_Position]=i
                        if Slot_Position == (Available_Slots-1):
                                SKU_Combo_Matrix.append(tmp[:])
                        ComboRecursive()
                Slot_Position-=1

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

	global SKU_DB_Selected_List,Available_Slots,tmp

	db=TinyDB('data2.json')
	BOM=Query()

    	for z in range(0,Available_Slots):
        	tmp.append(999)

	#Retrieve corresponding SKUs based on user requirement of 100G, 40G, 10G
	for index, item in enumerate(UserReq):
		Prodata=[]
		sindex=PortTypeMap(index)
		if item != 0:
			Prodata=db.search((BOM.Type == 'MPC') & (BOM.Provides[0][sindex] != 0))
			if len(Prodata)>0:
				for x in range(0, len(Prodata)):
					SKU_DB_Selected_List.append(Prodata[x])

	#Remove duplicate SKUs from list

	tempSKU_DB_Selected_List=SKU_DB_Selected_List
	SKU_DB_Selected_List=[]
	for x in range(0, len(tempSKU_DB_Selected_List)):
		if tempSKU_DB_Selected_List[x] not in SKU_DB_Selected_List:
			SKU_DB_Selected_List.append(tempSKU_DB_Selected_List[x])

########################
# Process relevant SKUs by:
# - removing duplicate SKUs
# - creating an internally defined SKU list for program processing

def SKUconditioning():

	global SKU_DB_Selected_List,SKU_Internal_List,SCBE,MPC7_Redundant_BW

	SKU_Internal_List=[]
	for i in range(0,len(SKU_DB_Selected_List)):
		temp=[]
		temp.append(SKU_DB_Selected_List[i]['SKU'])
		for j in range(0,len(UserReq)):
			sindex=PortTypeMap(j)
			try:
				if SKU_DB_Selected_List[i]['Provides'][0][sindex] != 0:
					temp.append(SKU_DB_Selected_List[i]['Provides'][0][sindex])
			except:
				temp.append(0)
		if (SCBE==0) & (SKU_DB_Selected_List[i]['SKU'][:4]=='MPC7'):
			temp.append(MPC7_Redundant_BW)
		else:
			temp.append(SKU_DB_Selected_List[i]['MPCBW'])
		temp.append(SKU_DB_Selected_List[i]['Price'])
	        if SKU_DB_Selected_List[i]['Provides'][1]['ports'] != 'NA':
     			temp.append(SKU_DB_Selected_List[i]['Provides'][1]['ports'])
        	else:
            		temp.append(0)
		SKU_Internal_List.append(temp[:])

########################
# Run thru the various SKU combinations. Process the SKUs by identifying which ones are
# used in meeting the user requirement of et100, et and xe ports.

def SKUnReqMapping():

    global SKU_Internal_List,SKU_Combo_Matrix,Lowest_Priced,UserReq_Port_Balance,UserReq

    Lowest_Priced=[]
    Lowest_Priced.append("You are FUCKED! Can't meet requirements! Need more slots!")
    Highest_Priced=[]
    Highest_Priced.append("You are FUCKED! Can't meet requirements! Need more slots!")

    UserReqFullfilled=0
    Empty_BOM=1
    for i in range(0,len(SKU_Combo_Matrix)):

        # iterating thru the SKU combination list. "SKU_Combo_Matrix" represents the
        # 2-dimensional list of all SKU combinations. This loops thru the line
        # item

        UserReq_Port_Balance=UserReq[:]
        Stored_MPC_Entry=[]
        y=SKU_Combo_Matrix[i]
        TotalCost=0
	PortTracking=[]
        for j in range(0,len(y)):

            # Loops thru the individual SKUs within the line item

            BW=0
            MPC_Used=0
            Port_Consumed=0
            All_Ports_Consumed=0

            for h in range(0,len(UserReq_Port_Balance)):

                # Processing port Interface_Count (et100, et, xe) against each SKU

                Interface_Count=0
		MPC_BW_Reached=0
                Inf_Max_Count_Reached=0

                # MPC bandwidth tracking. incrementing bandwidth based on port type
                # "Port_Inf_Ratio" is specific for MRATE cards to ensure physical port limits
                # are enforced

		Port_Inf_Ratio=1
                if h==0:
                    Port_BW=100
                elif h==1:
                    Port_BW=40
		elif h==2:
		    Port_BW=10
		    if SKU_Internal_List[(y[j])][6] != 0:
                        Port_Inf_Ratio = (SKU_Internal_List[(y[j])][6]*1.0) / SKU_Internal_List[(y[j])][3]

          	while (UserReq_Port_Balance[h]>0) & (All_Ports_Consumed == 0) & (Inf_Max_Count_Reached==0) & (MPC_BW_Reached==0):

           	    if SKU_Internal_List[(y[j])][6] != 0:
                        if (Port_Consumed+Port_Inf_Ratio) > SKU_Internal_List[(y[j])][6]:
                            All_Ports_Consumed=1
                    if (Interface_Count + 1) > SKU_Internal_List[(y[j])][h+1]:
			Inf_Max_Count_Reached=1
		    if ((BW + Port_BW) > SKU_Internal_List[(y[j])][4]):
			MPC_BW_Reached=1
		    if (All_Ports_Consumed==0) & (Inf_Max_Count_Reached==0) & (MPC_BW_Reached==0):
                        Interface_Count+=1
                        Port_Consumed+=Port_Inf_Ratio
                        BW+=Port_BW
                        UserReq_Port_Balance[h]=UserReq_Port_Balance[h]-1
                        MPC_Used=1
            if MPC_Used==1:
		PortTracking.append(UserReq_Port_Balance[:])
                Stored_MPC_Entry.append(SKU_Internal_List[(y[j])])
                TotalCost=TotalCost+SKU_Internal_List[(y[j])][5]

	Zero_Balance=1
	for z in range(0,len(UserReq_Port_Balance)):
	    if UserReq_Port_Balance[z] != 0:
	        Zero_Balance=0

        if Zero_Balance==1:

            # Calculating Lowest_Priced and Highest_Priced cost BOM

            UserReqFullfilled=1
            if Empty_BOM==1:
                Lowest_Priced=Stored_MPC_Entry[:]
                Lowest_Priced.append(TotalCost)
		Port_Tracking_Lowest_Priced=PortTracking[:]
                Highest_Priced=Lowest_Priced[:]
		Port_Tracking_Highest_Priced=PortTracking[:]
                Empty_BOM=0
            elif TotalCost < Lowest_Priced[len(Lowest_Priced)-1]:
                Lowest_Priced=Stored_MPC_Entry[:]
                Lowest_Priced.append(TotalCost)
		Port_Tracking_Lowest_Priced=PortTracking[:]
            elif TotalCost > Highest_Priced[len(Highest_Priced)-1]:
                Highest_Priced=Stored_MPC_Entry[:]
                Highest_Priced.append(TotalCost)
		Port_Tracking_Highest_Priced=PortTracking[:]

    print
    print '##############################'
    print "USER REQUIREMENTS:"
    print
    for i in range(0,len(UserReq)):
        if i==0:
            print "et100:       " + str(UserReq[i])
        if i==1:
            print "et:          " + str(UserReq[i])
        if i==2:
            print "xe:          " + str(UserReq[i])
    print "Max Slots:   " + str(Available_Slots)
    if SCBE==0:
    	print "SCBE:        2+1 (redundant)"
    else:
	print "SCBE:        3+0 (active)"
    print
    print '##############################'
    print "RESULTS: CHEAPEST OPTION"
    print
    if UserReqFullfilled==1:
        for i in range(0,len(Lowest_Priced)):
            if i==(len(Lowest_Priced)-1):
                print ('Total:   ' + 'USD ${:,.2f}'.format(Lowest_Priced[i]))
            else:
		if i==0:
		    print UserReq,Lowest_Priced[i]
                else:
		    print Port_Tracking_Lowest_Priced[i-1],Lowest_Priced[i]
    else:
        print Lowest_Priced
    print
    print '##############################'
    print "RESULTS: MOST EXPENSIVE OPTION"
    print
    if UserReqFullfilled==1:
        for i in range(0,len(Highest_Priced)):
            if i==(len(Highest_Priced)-1):
                print ('Total:   ' + 'USD ${:,.2f}'.format(Highest_Priced[i]))
            else:
                if i==0:
                    print UserReq,Highest_Priced[i]
                else:
                    print Port_Tracking_Highest_Priced[i-1],Highest_Priced[i]
    else:
        print Highest_Priced

########################
# MAIN PROGRAM #

loadTinyDB()
RetrieveSKUfromDB()
SKUconditioning()
ComboRecursive()
SKUnReqMapping()

########################
