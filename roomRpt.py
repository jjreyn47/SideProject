#!/usr/bin/env python
#*************************************************************************
# Name: roomRpt.py
#
# Description:
#   A module that determines which rooms are occupied for each hour.
#
#   FIRST - Find out how much $$ we were leaking each month.
#
#*************************************************************************

import pdb
import sys
import csv

def readCSV_WithEncoding(file_path, encoding='utf-8-sig'):
    with open(file_path, 'r', encoding=encoding, newline='\r\n') as f:
        reader = csv.reader(f)
        for row in reader:
            yield row

def readCVSTable(dataFile, term):
    '''Accumulate rows into a list of dictionaries, only accepting good data.'''

    accumulator    = []
    keys           = []
    xlstValues     = []  # use to drop duplicates.  Doesn't matter which row we drop.
    
    nMalformedRows   = 0  # not enough data fields to match keys. Blank line mostly.
    nRoomEmpty       = 0  # Had data but it was all 0's
    nWrongTerm       = 0  # Wrong term
    nOnline          = 0  # row ignored because is an online class
    nXLSTDups        = 0
    nXLSTEmpty       = 0
    nStartOrEndEmpty = 0  # Don't care about these.
    nRowsGood        = 0  # The data was what we want
    nRow             = 0  # The total number of rows.
    nBadStart        = 0  # start time is out of range
    nBadEnd          = 0  # end time is out of range
    nBOMmarkers      = 0

    # weed out the data we don't want.

    try:
        # We assume this is a utf-8 file with a BOM.  If it is not encoded that way,
        # an exception will be thrown.
        
        for row in readCSV_WithEncoding(dataFile, encoding='utf-8-sig'):

            nRow += 1

            if len(keys) == 0:

                keys = row

                print('Keys : ', row)
                continue
            
            # use 2 lists to initialize a dictionary for the row.
            if len(row) != len(keys):
                nMalformedRows += 1
                #print('\nWARNING: len(row)=%d BUT len(keys)=%d\n'%(len(row),len(keys)))
                continue
            
            d = dict(zip(keys, row))

            #if nRow == 584:
            #    print('Unexpected input, nRow=%d'%(nRow))

            if d['ROOM'] == ' ' or d['ROOM'] == '':
                nRoomEmpty += 1
            elif d['TERM'] != term:
                nWrongTerm += 1
            elif 'ONLINE' in d['ROOM']: # sometimes the data in 'ONLINE '
                nOnline += 1
                        
            elif d['XLST'] in xlstValues:
                nXLSTDups += 1
            elif d['START'] == '' or d['END'] == '':
                nStartOrEndEmpty += 1
            elif int(d['START']) < 700 or int(d['START']) > 2100:
                print('WARNING: row%d start=%s is out of range.'%(nRow, d['START']))
                nBadStart += 1
            elif int(d['END']) < 700 or int(d['END']) > 2200:
                print('WARNING: row%d end=%s is out of range.'%(nRow, d['END']))
                nBadEnd += 1
            else:
                nRowsGood += 1
                # print(row)

                if d['XLST'] != '':
                    xlstValues.append(d['XLST'])
                else:
                    nXLSTEmpty += 1
                
                accumulator.append(d)

    except UnicodeDecodeError:
        raise UnicodeDecodeError("Failed to decode the file with 'utf-8-sig'. Please check the file encoding.")
        

    print('Total rows       : ', nRow)
    print('nMalformedRows   : ', nMalformedRows)
    print('nRoomEmpty       : ', nRoomEmpty)
    print('nWrongTerm       : ', nWrongTerm)
    print('nXLSTDups        : ', nXLSTDups)
    print('nXLSTEmpty       : ', nXLSTEmpty)
    print('nOnline          : ', nOnline)
    print('nStartOrEndEmpty : ', nStartOrEndEmpty)
    print('nBadStart        : ', nBadStart)
    print('nBadEnd          : ', nBadEnd)
    print('nRowsGood        : ', nRowsGood)  
    
    return accumulator

def mapDay(day):
    d = ''
    if day == 'M':
        d = 'Monday'
    elif day == 'T':    
        d = 'Tuesday'
    elif day == 'W':    
        d = 'Wednesday'
    elif day == 'R':    
        d = 'Thursday'
    elif day == 'F':    
        d = 'Friday'
    elif day == 'S':    
        d = 'Saturday'
    else:
        d = 'Unknown'
    return d

def setTime(hrBools, startTime, endTime):
    # set hour slots for this room for these times. hrBools[0] is 7 AM

    beg = int(startTime) // 100  # '//' does integer division

    # end must point to the bucket after this class which this class does not use.
    end = int(endTime) // 100

    # make sure the end points to the next bucket if even a fractional time uses it
    if (end * 100) < int(endTime):
        end += 1
        
    # fill in whatever hour slots the class occupies the room
    hr = beg
    while hr < end:
        hrBools[hr-7] = 1
        hr += 1

def createCSVRow(room, day, hrBools):
    # create a csv string for the row

    day2 = mapDay(day)

    # converts a list of integers to a list of strings
    hrBools_str = list(map(str, hrBools))

    l = [ room, day2]

    row = l + hrBools_str

    return row
    
def doWork(classFile, term):
    
    '''Determine room occupation for each day of the week, by setting a boolean
       for each hour it is occupied. '''

    classData = readCVSTable(classFile, term)

    # Fields :  ['TERM', 'CAMPUS', 'XLST', 'CRN', 'DAYS', 'START', 'END', 'ROOM']

    roomTimes = {}

    week = [ 'M', 'T', 'W', 'R', 'F', 'S' ]

    # accumulate all of the time data for each room in a dictionary keyed by room
    for row in classData:
        # build a dictionary of roomTimes
        
        room = row['ROOM']
        crn  = row['CRN']
        days = row['DAYS']
        start = row['START']
        end   = row['END']

        # get the times organized for each day of the week by creating a list of
        # tuples, one for each day.  Each tuple will populate rows in the final
        # output.

        if room not in roomTimes:
            # initialize the room in the dictionary
            # This makes a copy of the initial dictionary.
            roomTimes[room] = [(crn, days, start, end)]
        else:
            roomTimes[room].append((crn, days, start, end))

    # extract all of the keys, which are individual roomTimes
    roomList = list(roomTimes)

    # sort the roomList
    roomList.sort()

    #print(roomList)
    #print(roomTimes)

    # Use csv to write this to a file.
    # now create the output in csv format...
    #
    # NOTE: MIGHT HAVE TO ADD THE BOM STRING

    csvList = []
    outputFileName = 'rooms-new.csv'
    with open(outputFileName, 'w', newline='') as csvfile:

        # need to create a list of lists where each inner list is a row.
        writer = csv.writer(csvfile, dialect='excel') # every char is ',' separated.
    
        keys=['Room','Day','7 am','8 am','9 am','10 am','11 am','12 am','1 pm',
              '2 pm','3 pm','4 pm','5 pm','6 pm','7 pm','8 pm','8 pm','9 pm']

        csvList.append(keys)

        for room in roomList:
        
            # cycle through time info for a room
            #print('BEFORE -- %s --- '%room, roomTimes[room])

            for day in 'MTWRFS':
                # set the time slots the room is used for this class.
                        
                # an entry per hour of the day hrBools[0] is 7 AM.
                hrBools = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
                        
                for time in roomTimes[room]:
                    #print(times)
                    crn   = time[0]
                    start = time[2]
                    end   = time[3]
            
                    if day in time[1]:
                        setTime(hrBools, start, end)
        
                row = createCSVRow(room, day, hrBools)

                #print(row)

                csvList.append(row)
                    
        writer.writerows(csvList)
    
if __name__ == "__main__":

    # TODO: Read in the PDF files Gary sent. They show what rooms are used for
    # things for tutoring, etc, on a regular basis.  They aren't classes.  But they
    # need to be accounted for and reported on because the goal is room occupation
    # being understood.
                        
    usage = '%prog requires term,csv-filename pairs. Example: 202408,CoursHistory.csv'
    from optparse import OptionParser
    
    parser = OptionParser(usage=usage)

    parser.add_option("-o", "--outputFile", action="store", type="string", dest="file", 
                     help="Name of the output file, which is csv of room occupation. 'Rooms.csv'")
    
    (options, args) = parser.parse_args()
    
    print('options : ', options)
    print('args    : ', args)
    
    if len(args) <= 0:
        parser.print_help()
        #print('ERROR: Must supply a csv file of classroom data.')
        sys.exit(1)

    arg = args[0]
    term,file = arg.split(',')
            
    print('Inputs: term=%s csvFile=%s '% (file,term) )
                        
    doWork(file, term)
    

