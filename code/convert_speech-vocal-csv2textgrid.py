#!/usr/bin/python3
"""
author: Christian Olaf Haeusler
created on Friday August 30 2019

textgrid format
http://www.fon.hum.uva.nl/praat/manual/TextGrid_file_formats.html

Working in Praat's GUI:
insert boundary: enter
del boundary: Alt + del
play intervall: Tab

"""
import csv
import os
import sys


def time_stamp_to_msec(t_stamp='01:50:34:01'):
    '''
    Input:
        time stamp (str) in format HH:MM:SS:Frame

    Output:
        time point in milliseconds (int)
    '''
    splitted_stamp = t_stamp.split(':')
    milliseconds = (int(splitted_stamp[0]) * 60 * 60 * 1000) +\
                   (int(splitted_stamp[1]) * 60 * 1000) +\
                   (int(splitted_stamp[2]) * 1000) +\
                   (int(splitted_stamp[3]) * 40)

    return milliseconds


def sec_to_time_stamp(seconds=6634.040):
    """describe what the function does

    Parameters
    ----------
    x : type (e.g. str)
        description of the parameter `x`

    Returns
    -------
    type
        Description of the to be returned variable.

    if returned value has a name:
    varname : str
        Description
    """
    milliseconds = seconds * 1000

    hours = (milliseconds / (60*60*1000))
    minutes = (milliseconds % (60*60*1000) / (60*1000))
    seconds = (milliseconds % (60*60*1000) % (60*1000) / 1000)
    frame = (milliseconds % (60*60*1000) % (60*1000) % (1000) // 40)
    time_stamp = '%02d:%02d:%02d:%02d' % (hours, minutes, seconds, frame)

    return time_stamp


# main programm
if __name__ == "__main__":
    # read in annotation
    inFile = sys.argv[1]
    outFile = sys.argv[2]


    with open(inFile) as csv_file:
        data = csv.reader(csv_file)

        # skip the file header
        next(data, None)

        # populate nested list
        data = [row for row in data]
#
    text = ['File type = "ooTextFile"',
            'Object class = "TextGrid"',
            '',
            'xmin = 0 ',
            'xmax = 7085.28 ',
            'tiers? <exists> ',
            'size = 1 ',
            'item []: ',
            '    item [1]:',
            '        class = "IntervalTier" ',
            '        name = "sentence" ',
            '        xmin = 0 ' ,
            '        xmax = 7085.28 ' ,
            '        intervals: size = ## '
            ]

    intervallTempl = ['        intervals [##]:',
                      '            xmin = ## ',
                      '            xmax = ## ',
                      '            text = "##" ']


    lastTextEnd = 0

    intNr = 1
    for row in data[:]:

        # filter rows with unknown timing
        if '#' in row[0]:
            continue
        if '#' in row[1]:
            continue
        # filter rows with Soundtracks or (longer) songs
        # they span over longer times with words spoken within the song
        if 'OST' in row[2] or 'song' in row[4]:
            continue

        textRow = [time_stamp_to_msec(row[0])/1000.0, time_stamp_to_msec(row[1])/1000.0, row[7]]

        # check manually created annotation for temporal errors
        if textRow[0] - textRow[1] >= 0:
            print('Anfang for Ende\n', row)
            raw_input()

        if textRow[0] - lastTextEnd <= 0:
            print('Ende nach Anfang\n', row)
            raw_input()


        blankIntervall = intervallTempl[:]
        blankIntervall[0] = blankIntervall[0].replace('##', str(intNr*2-1))
        blankIntervall[1] = blankIntervall[1].replace('##', str(lastTextEnd))
        blankIntervall[2] = blankIntervall[2].replace('##', str(textRow[0]))
        blankIntervall[3] = blankIntervall[3].replace('##', '')

        textIntervall = intervallTempl[:]
        textIntervall[0] = textIntervall[0].replace('##', str(intNr*2))
        textIntervall[1] = textIntervall[1].replace('##', str(textRow[0]))
        textIntervall[2] = textIntervall[2].replace('##', str(textRow[1]))
        textIntervall[3] = textIntervall[3].replace('##', textRow[2])

        lastTextStart = textRow[0]
        lastTextEnd =  textRow[1]

        text.extend(blankIntervall)
        text.extend(textIntervall)

        intNr += 1

    text[13] = text[13].replace('##', str(intNr*2-1))
    ende = ['        intervals [##]: ',
            '            xmin = 7084.24 ',
            '            xmax = 7085.28 ',
            '            text = "_" ']

    ende[0] = ende[0].replace('##', str(intNr*2-1))
    text.extend(ende)

    # write that shit to file
    with open(outFile, 'w', encoding='utf-16') as textGridFile:
        for line in text:
            textGridFile.write('%s\n' % line)
