#!/usr/bin/python3
"""
author: Christian Olaf Haeusler
created on Friday October 22th 2019
"""
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

    print('\n\n')

    return None


def print_words_and_columns(countsWor):
    '''
    '''
    nrOfWords = sum([countsWor['text'][x]['0'] for x in countsWor['text'].keys()])
    print('\n\nWords', '\t', nrOfWords)

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
                          if category not in ['', '###']]

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
        for x in categories:
            x = [str(index) for index in x]
            print('\t'.join(x))
        print('\n')

    return None


# main programm
if __name__ == "__main__":
    # read the BIDS .tsv
    inFile = sys.argv[1]
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

    # statistics for Sentences, Non-Spech, Phonemes
    print_name_per_run('Sentences:', countsSen, 12)
    print_name_per_run('Non-Speech:', countsNon, 12)
    print_name_per_run('Phonemes:', countsPho, -1)

    # descriptive statistics for the words
    print_words_and_columns(countsWor)
