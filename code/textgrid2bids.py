#!/usr/bin/python3
"""
author: Christian Olaf Haeusler
created on Friday October 22th 2019

TextGrid format specifications:
http://www.fon.hum.uva.nl/praat/manual/TextGrid_file_formats.html

"""
import csv
import sys
from collections import defaultdict


def read_data(infile):
    '''
    '''
    with open(infile, 'r', encoding='utf-16') as f:
        textGridLines = f.readlines()
        textGridLines = [line.strip() for line in textGridLines]

    data = defaultdict(lambda: defaultdict(list))
    for line in textGridLines[9:]:
        linepair = line.split(' = ')

        if len(linepair) == 2:
            if linepair[0] == 'name':
                tiername = linepair[1].strip('"')
            elif linepair[0] == 'xmin':
                xmin = linepair[1]
            elif linepair[0] == 'xmax':
                xmax = linepair[1]
            elif linepair[0] == 'text' and linepair[1] != '""':
                text = linepair[1].strip('"')
                diff = str(round(float(xmax)-float(xmin), 3))
                onOffset = (float(xmin), float(diff))

                data[onOffset][tiername] = [text]

    return data


def build_word_line(data, onOffset, person):
    '''
    '''
    line = [onOffset[0], onOffset[1]]
    line.extend(person)
    line.extend(data[onOffset]['words'])
    line.extend(data[onOffset]['pos'])
    line.extend(data[onOffset]['tag'])
    line.extend(data[onOffset]['dep'])
    line.extend(data[onOffset]['lemma'])
    line.extend(data[onOffset]['stop'])
    if 'descr' in data[onOffset].keys():
        line.extend(data[onOffset]['descr'])
        line.extend(data[onOffset]['vector'])
    else:
        line.append('')
        line.extend(data[onOffset]['vector'])

    return line


def build_phone_line(data, onOffset, person):
    '''
    '''
    line = [onOffset[0], onOffset[1]]
    line.extend(person)
    line.extend(data[onOffset]['phones'])
    line.append('PHONEME')

    return line


def write_to_tsv(outputFile, header, toWrite):
    '''
    '''
    with open(outputFile, 'w') as tsvFile:
        writer = csv.writer(tsvFile, delimiter='\t')
        writer.writerow(header)
        writer.writerows(toWrite)


# main programm
if __name__ == "__main__":
    # read textgrid
    inFile = sys.argv[1]

    data = read_data(inFile)

    toWrite = []
    sortedKeys = sorted(data, key=lambda y: (y[0], -y[1]))
    for onOffset in sortedKeys:
        keys = data[onOffset].keys()
        # process on-/offset matching a whole sentences
        if 'sentence' in keys:
            line = [onOffset[0], onOffset[1]]
            person = data[onOffset]['person']
            line.extend(person)
            line.extend(data[onOffset]['sentence'])
            line.append('SENTENCE')
            toWrite.append(line)
            # process sentences with only one word
            if 'words' in keys:
                line = build_word_line(data, onOffset, person)
                toWrite.append(line)
            # process sentences with only one word
            # AND just one phoneme (essentially "sentences" that contain
            # justone non-speech vocalization
            if 'phones' in keys:
                line = build_phone_line(data, onOffset, person)
                toWrite.append(line)

        # process on-/offset matching a single word (that is not a "sentence")
        elif 'sentence' not in keys and 'words' in keys:
            line = build_word_line(data, onOffset, person)
            toWrite.append(line)
            # and the single words' corresponding phonemes
            if 'phones' in keys:
                line = build_phone_line(data, onOffset, person)
                toWrite.append(line)

        # process onOffset matching a single phoneme
        elif len(keys) == 1 and 'phones' == list(keys)[0]:
            line = build_phone_line(data, onOffset, person)
            toWrite.append(line)

        else:
            print(line)

    # write to csv
    outputFile = inFile.replace('.TextGrid', '.tsv')
    header = ['onset', 'duration', 'person', 'text',
              'pos', 'tag', 'dep', 'lemma', 'stop',
              'descr', 'vector']

    write_to_tsv(outputFile, header, toWrite)
