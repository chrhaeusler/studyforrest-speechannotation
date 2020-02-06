#!/usr/bin/python3
"""
author: Christian Olaf Haeusler
created on Friday October 22th 2019
"""
import argparse
import csv
import spacy
import sys
from collections import defaultdict


SEGMENTS_OFFSETS = (
    (0.00, 0.00),
    (886.00, 0.00),
    (1752.08, 0.08),  # third segment's start
    (2612.16, 0.16),
    (3572.20, 0.20),
    (4480.28, 0.28),
    (5342.36, 0.36),
    (6410.44, 0.44),  # last segment's start
    (7086.00, 0.00))  # movie's last time point


def parse_arguments():
    '''
    '''
    parser = argparse.ArgumentParser(
        description='Show decriptive statistics for the annotation of speech'
    )
    parser.add_argument('-i',
                        default='annotation/fg_rscut_ad_ger_speech_tagged.tsv',
                        help='The input file')

    parser.add_argument('-o',
                        required=False,
                        default=None,
                        help='the tex-file the statistics to write to')

    args = parser.parse_args()

    inFile = args.i
    outFile = args.o

    return inFile, outFile


def read_file(inFile):
    '''
    '''
    with open(inFile) as csvfile:
        content = csv.reader(csvfile, delimiter='\t')
        header = next(content, None)
        content = [x for x in content]

    return header, content


def get_run_number(starts, onset):
    '''
    '''
    for start in sorted(starts, reverse=True):
        if float(onset) >= start:
            run = starts.index(start)
            break

    return run


def populate_name_count(sent, nonSpeech, phones, data):
    '''
    '''
    segmStarts = [start for start, offset in SEGMENTS_OFFSETS]

    for line in data:
        # check the run/segment we are in
        run = get_run_number(segmStarts, line[0])
        segment = str(run + 1)

        # does the row contain a sentence?
        if 'SENTENCE' in line[4]:
            # counter for the whole stimulus (key=0)
            sent[line[2]]['0'] += 1
            # counter for the segments
            sent[line[2]][segment] += 1
        elif 'NONSPEECH' in line[4]:
            nonSpeech[line[2]]['0'] += 1
            nonSpeech[line[2]][segment] += 1
        elif 'PHONEME' in line[4]:
            phones[line[3]][segment] += 1
            phones[line[3]]['0'] += 1
        else:
            # column entry belongs to POS tagging of single words
            pass

    return sent, nonSpeech, phones


def populate_column_cat_count(columnDict, data):
    '''
    '''
    segmStarts = [start for start, offset in SEGMENTS_OFFSETS]

    for line in data:
        # check the run/segment we are in
        run = get_run_number(segmStarts, line[0])
        segment = str(run + 1)

        # does the row contain a word?
        if len(line) >= 6:
            for column in header[2:-1]:
                # NON-SPECH and X, XY (=other) have 6 not 11 columns
                # so try for all columns in the header
                try:
                    # get word's category by looking in the cell belonging
                    # to the current column/spaCy annotation
                    category = line[header.index(column)]
                    # correct entry for columns 'dep' and 'descr'
                    if column in ['dep', 'descr']:
                        category = category.split(';')[0]
                    # increase count for the whole stimulus
                    columnDict[column][category]['0'] += 1
                    # increase count for the run/segment
                    columnDict[column][category][segment] += 1
                except:
                    pass

    return columnDict


def print_name_per_run(statsFor, countsDict, topNr):
    '''
    '''
    # print the total number of sentences (or non-speech or phonemes)
    nrOfSents = sum([countsDict[x]['0'] for x in countsDict.keys()])
    print(statsFor + '\t', nrOfSents)

    # sentences per speaker
    # get a list of all speakers
    speakers = [[speaker] for speaker in countsDict.keys()]
    # add the counts for the whole stimulus [str('0')]
    # and the individual runs [indices 1-8])
    for speaker in speakers:
        allRuns = [countsDict[speaker[0]][str(x)] for x in range(0, 9)]
        speaker.extend(allRuns)
    # sort the list from speaker with most spoken sentences to
    # speaker with least spoken sentences
    speakers = sorted(speakers, key=lambda x: -x[1])

    # PRINTING FOR SENTENCES
    for speaker in speakers[:topNr]:
        x = [str(index) for index in speaker]
        print('\t'.join(x))

    print('\n')

    return None


def print_words_and_columns(countsWor, topNr):
    '''
    '''
    # count & print the total number of words
    nrOfWords = sum([countsWor['text'][x]['0'] for x in countsWor['text'].keys()])
    print('\nWords', '\t', nrOfWords)

    # overview of words' additional columns
    for column in header:
        # filter for the relevant coulmns
        if column not in ['person', 'pos', 'tag', 'dep', 'descr']:
            continue
        else:
            # for the current column/annotation, make a list of all
            # occuring categories by looking up the keys that exist in the dict
            # add the counts per segment later by extending a category's item
                categories = [[category] for category in countsWor[column].keys()
                          if category not in ['', '##']]

        # create the list with the counts per segment
        # that will be added
        for category in categories:
            # add explanation of categories of 'pos', 'tag', and 'dep'
            if column in ['pos', 'tag', 'dep']:
                allRuns = [countsWor[column][category[0]][str(x)]
                           for x in range(0, 9)]
                allRuns.append(spacy.explain(category[0]))
            else:
                allRuns = [countsWor[column][category[0]][str(x)]
                           for x in range(0, 9)]

            # add the information of all runs
            category.extend(allRuns)

        categories = sorted(categories, key=lambda x: -x[1])

        # PRINTING FOR WORDS
        print(column)
        for x in categories[:topNr]:
            x = [str(index) for index in x]
            print('\t'.join(x))
        print('\n')

    return None


def write_tex_file(outFile):
    '''
    '''
    # this is used to generate the .tex-file for the reproducible paper
    print(' \tall\tseg1\tseg2\tseg3\tseg4\tseg5\tseg6\tseg7\tseg8\tExplanation')

    forTexFile = []
    print('% Overview:')
    forTexFile.append('% Overview\n')
    # sentences per run
    forFile = statsSentPhones('Sentences', countsSen)
    forTexFile.append(forFile)

    # words per run
    forFile = statsWords(countsWor)
    forTexFile.append(forFile)

    # phones per run
    forFile = statsSentPhones('Phones', countsPho)
    forTexFile.append(forFile)

    # SENTENCES
    # list the most often occuring speakers
    print('\n% Sentences by Speakers:')
    forTexFile.append('\n% Sentences by Speaker\n')
    forFile = sentsBySpeaker(countsSen, 10)
    forTexFile.append(forFile)

    # WORDS
    # Top x simple tagging + description
    print('\n% POS-Tagging:')
    forTexFile.append('\n% POS-Tagging\n')
    currentColumnDict = countsWor['pos']
    forFile = statsWordsColumns('Pos', currentColumnDict, 15)
    forTexFile.append(forFile)

    # top x detailed tagging, alpabetisch
    print('\n% TAG-Tagging:')
    forTexFile.append('\n% TAG-Tagging\n')
    currentColumnDict = countsWor['tag']
    forFile = statsWordsColumns('Tag', currentColumnDict, 15)
    forTexFile.append(forFile)

    # top x syntactic dependencies
    print('\n% Syntactic Dependencies:')
    forTexFile.append('\n% Syntactic Dependencies\n')
    currentColumnDict = countsWor['dep']
    forFile = statsWordsColumns('Dep', currentColumnDict, 15)
    forTexFile.append(forFile)

    # descriptive nouns
    print('\n% Descriptive Nouns:')
    forTexFile.append('\n% Descriptive Nouns\n')
    currentColumnDict = countsWor['descr']
    forFile = statsWordsColumns('Descr', currentColumnDict, 25)
    forTexFile.append(forFile)

    # word2vector
    # meaningful statistics?

    # PHONEMES
    # meaningful statistics?

    toWrite = [inner for outer in forTexFile for inner in outer]
    with open(outFile, 'w') as f:
        f.writelines(toWrite)


def statsSentPhones(statsFor, countsDict):
    '''
    '''
    countsPerRun = defaultdict(int)
    for speaker in list(countsDict.keys()):
        for run in countsDict[speaker].keys():
            countsPerRun[run] += countsDict[speaker][run]

    perRun = [countsPerRun[run] for run in sorted(countsPerRun.keys())]

    line = [str(x) for x in perRun]
    line = statsFor + '\t' + '\t'.join(line)
    print(line)

    labels = ['%sRun%s' % (statsFor, x) for x in range(0,9)]
    labelsAndCounts = list(zip(labels, perRun))
    linesForLatex = ['\\newcommand{\\%s}{%s}\n' % (label, count)
                    for label, count in labelsAndCounts]

    linesForLatex.append('\n')

    return(linesForLatex)


def statsWords(countsWor):
    '''
    '''
    statsFor = 'Words'

    countsPerRun = defaultdict(int)
    for speaker in list(countsWor['person'].keys()):

        for run in countsWor['person'][speaker].keys():
            countsPerRun[run] += countsWor['person'][speaker][run]

    perRun = [countsPerRun[run] for run in sorted(countsPerRun.keys())]

    line = [str(x) for x in perRun]
    line = 'Words\t' + '\t'.join(line)
    print(line)

    labels = ['%sRun%s' % (statsFor, x) for x in range(0,9)]
    labelsAndCounts = list(zip(labels, perRun))
    linesForLatex = ['\\newcommand{\\%s}{%s}\n' % (label, count)
                    for label, count in labelsAndCounts]

    linesForLatex.append('\n')

    return(linesForLatex)


def sentsBySpeaker(countSen, topNr):
    '''
    '''
    # get a list of all speakers
    speakers = [[speaker] for speaker in countsSen.keys()]
    # add the counts for the whole stimulus [str('0')]
    # and the individual runs [indices 1-8])
    for speaker in speakers:
        allRuns = [countsSen[speaker[0]][str(x)] for x in range(0, 9)]
        speaker.extend(allRuns)
    # sort the list from speaker with most spoken sentences to
    # speaker with least spoken sentences
    # sort by count, most first
    speakers = sorted(speakers, key=lambda x: -x[1])
    # sort top x alphabetically
    speakers = sorted(speakers[:topNr])

    # PRINTING FOR SENTENCES
    for speaker in speakers[:topNr]:
        x = [str(index) for index in speaker]
        print('\t'.join(x))

    linesForLatex = []
    for speaker in speakers:
        for run, count in enumerate(speaker[1:]):
            name = ''.join([char for char in speaker[0] if char.isalpha()])
            name = name.lower().capitalize()
            label = name + 'Run' + str(run)

            line = '\\newcommand{\\%s}{%s}\n' % (label, count)
            linesForLatex.append(line)

        # after every speaker, insert a line break
        linesForLatex.append('\n')


    return linesForLatex


def statsWordsColumns(colName, currentColumnDict, topNr):
    '''
    '''
    categories = [[category] for category in currentColumnDict.keys()
                    if category not in ['', '###']]

    for category in categories:
        # add explanation of categories of 'pos', 'tag', and 'dep'
        allRuns = [currentColumnDict[category[0]][str(x)]
                    for x in range(0, 9)]
        allRuns.append(spacy.explain(category[0]))

        # add the information of all runs
        category.extend(allRuns)

    # sort by count, most first
    categories = sorted(categories, key=lambda x: -x[1])
    # sort by top x by alphabetically
    categories = sorted(categories[:topNr])

    for x in categories[:topNr]:
        x = [str(index) for index in x]
        print('\t'.join(x))

    linesForLatex = []
    for category in categories:

        name = ''.join([char for char in category[0] if char.isalpha()])
        name = name.lower().capitalize()

        # add the description of the category label taken from Spacy
        if category[-1] != None:
            spaCyExplanation = category[-1]
            line = '\\newcommand{\\%s%s}{%s}\n' % (colName, name, spaCyExplanation)
            linesForLatex.append(line)

        for run, count in enumerate(category[1:-1]):

            label = '%s%sRun%s' % (colName, name, run)

            line = '\\newcommand{\\%s}{%s}\n' % (label, count)
            linesForLatex.append(line)

        # after every run, insert a line break
        linesForLatex.append('\n')

    return linesForLatex


# main programm
if __name__ == "__main__":
    # read the BIDS .tsv
    inFile, outFile = parse_arguments()

    header, fContent = read_file(inFile)

    # get data in shape to do the descriptive statistics
    # initialize the dictionaries
    countsSen = defaultdict(lambda: defaultdict(int))
    countsNon = defaultdict(lambda: defaultdict(int))
    countsPho = defaultdict(lambda: defaultdict(int))
    countsWor = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    # loop through the annotation content and populate the dictionaries
    # sentences, non-speech und phonemes
    countsSen, countsNon, countsPho = populate_name_count(
        countsSen, countsNon, countsPho, fContent)
    # single words and their additional columns with linguistic features
    countsWor = populate_column_cat_count(countsWor, fContent)

    if outFile == None:
        # this was used for exploratory analyses of the
        # natural language statistics in the stimulus
        # statistics for Sentences, Non-Spech, Phonemes
        # last argument ist the top count of categories to print
        print_name_per_run('Sentences:', countsSen, -1)
        print_name_per_run('Non-Speech:', countsNon, -1)
        print_words_and_columns(countsWor, -1)
        print_name_per_run('Phonemes:', countsPho, -1)

    if outFile != None:
        write_tex_file(outFile)
