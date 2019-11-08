#!/usr/bin/python3
"""
author: Christian Olaf Haeusler
created on Friday October 7th 2019

TextGrid format specifications:
http://www.fon.hum.uva.nl/praat/manual/TextGrid_file_formats.html

SpaCy annotation:
https://spacy.io/usage/linguistic-features

Setting up:
pip3 install -U spacy
python3 -m spacy download de_core_news_sm # 10 MB
python3 -m spacy download de_core_news_md # 210 MB
"""

import spacy
import sys
import numpy as np
import os.path
from copy import deepcopy


# German language model to be used by spaCy
MODEL = 'de_core_news_md'  # '_dm' = medium model; '_sm' = small model

# originial tiers are the tiers in the manually revised TextGrid (aka input)
ORGTIERS = ['person', 'sentence', 'words', 'descr', 'phones']

# linguistics are the tiers to be added by spaCy's NLP analysis
LINGUISTICS = ['pos', 'tag', 'dep', 'lemma', 'stop', 'vector']

# the three templates for the TextGrid file to be created
TEMPLHEADER = ['File type = "ooTextFile"\n',
               'Object class = "TextGrid"\n',
               '\n',
               'xmin = 0\n',
               'xmax = 7085.28\n',  # hard coded for research cut's length
               'tiers? <exists>\n',
               'size = ##\n',
               'item []:\n'
               ]

TEMPLTIER = ['    item [##]:\n',
             '        class = "IntervalTier"\n',
             '        name = "##"\n',
             '        xmin = 0\n',  # hard coded for length of research cut
             '        xmax = 7085.28\n',  # , hard coded end
             '        intervals: size = ##\n'
             ]

TEMPLINTERV = ['        intervals [##]:\n',
               '            xmin = ##\n',
               '            xmax = ##\n ',
               '            text = "##"\n'
               ]

# some corrections for words that spacy more often tags
# more often incorrectly than correctly
CORRECTIONS = {
    ('PROPN', 'NE'): [  # = proper noun, proper noun
        'flame',
        'amber',
        'astor',
        'bayou',
        'bobbie',
        'bubba',
        'bubbas',
        'dan',
        'dans',
        'elvis',
        'enquirer',
        'flex-o-light-pingpong-schläger',
        'forrest',
        'forrests',
        'groom',
        'jenny',
        'jennys',
        'johnson',
        'la',  # bayou la batre
        'lincoln',
        'louise',
        'nixon',
        'pinoccio',
        'robert-zemeckis-film',
        'sesamstraße',
        'tex'],
    ('NOUN', 'NN'): [  # = noun, noun
        'abendessen',
        'ärmel',
        'barbecue',
        'barbecues',
        'bergsee',
        'bh',
        'bluse',
        'cappy',
        'cocktail',
        'cocktails',
        'colas',
        'ferien',
        'football',
        'g.i.s',
        'grill',
        'gumbo',
        'hornbrille',
        'idiot',
        'kapitän',
        'kokain',
        'kokainlinien',
        'kokosnussshrimps',
        'konfetti',
        'limonenshrimps',
        'lügner',
        'mg',
        'nachthemd',
        'napalm',
        'opas',
        'pingpong',
        'platoon',
        'rollo',
        'schwachkopf',
        'seemannskrankenhaus',
        'shit',
        'shrimpbootcaptain',
        'shrimpkutterkapitän',
        'shrimps',
        'shrimpscreol',
        'shrimpssandwich',
        'shrimpssuppe',
        'smiley',
        'stecker',
        'tischtennisschläger',
        'trottel',
        'veteran',
        'wartebank',
        'wichser',
        'zauberbeine',
        'zeitlupe'],
    ('NUM', 'CARD'): [  # = numeral, cardinal number
        'einhundertsiebzig',
        'fünfundzwanzigtausend',
        'hundertsechzig',
        'neunzehnhunderteinundachtzig',
        'vierundzwanzigtausendfünfhundertzweiundsechzig'],
    ('X', 'FM'): [  # = other, foreign material
        'go',
        'happens'],
    ('X', 'XY'): [  # other, other; here mostly "Appellinterjektionen"
        'ey',
        'hallo',
        'hey',
        'okay',
        'na',
        'wow'],
    ('NONSPEECH'): [  # here mostly "Symptominterjektionen"
        'aah',
        'ach',
        'äch',
        'ache',
        'ah',
        'äh',
        'aha',
        'ähm',
        'al',
        'ärch',
        'aua',
        'aueh',
        'auh',
        'börp',
        'd',
        'each',
        'ech',
        'eh',
        'ergh',
        'ha',
        'hä',
        'hach',
        'häch',
        'he',
        'hech',
        'hi',
        'hihi',
        'hm',
        'ho',
        'hua',
        'huach',
        'huch',
        'i',
        'ie',
        'lu',
        'mh',
        'mhm',
        'o',
        'och',
        'oh',
        'öh',
        'öhm',
        'ouh',
        'ouha',
        'pf',
        'pfuh',
        'psst',
        'schniff',
        'tchich',
        'tzm',
        'u',
        'uch',
        'uhm',
        'uaech',
        'w',
        'wah',
        'wäh',
        'whoo',
        'whou']
    }


def read_n_clean(inFile):
    '''
    '''
    with open(inFile, 'r', encoding='utf-16') as f:
        '''
        reads the .TextGrid file, does some cleaning, and puts the content into
        a dict with tiers as keys
        '''
        intervalsFlag = False
        contentDict = {}

        for i, line in enumerate(f):
            if 'class = "IntervalTier"' in line:
                intervalsFlag = False
            elif "name = " in line:
                tierKey = line.split('"')[1]
                contentDict[tierKey] = []
            elif 'intervals [' in line:
                intervalsFlag = True
            elif intervalsFlag is True and ' = ' in line:
                line = line.split(' = ')[1].replace('"', '').strip()
                # try to convert the string to float
                # and round the float to milliseconds
                try:
                    line = str(round(float(line), 3))
                except:
                    pass

                contentDict[tierKey].append(line.strip())

        # now that you have all tiers in the dict,
        # clean all tiers' data
        for key in contentDict.keys():
            cleanedTier = [contentDict[key][i:i+3] for i in
                           range(0, len(contentDict[key]), 3)]
            contentDict[key] = cleanedTier

    return contentDict


def add_punctuation(wordList):
    '''
    '''
    # because spaCy tags non-speech with regular speech tags
    # not an elegant solution but spares punctuation in other words/sentences
    toAdd1 = [word + '.' for word in wordList]
    toAdd2 = [word + ',' for word in wordList]
    toAdd3 = [word + '!' for word in wordList]

    wordList.extend(toAdd1)
    wordList.extend(toAdd2)
    wordList.extend(toAdd3)
    wordList = sorted(wordList)

    return wordList


def match_n_analyze(dataDict, nlp):
    '''
    '''
    # words to ignore
    nonspeech = add_punctuation(CORRECTIONS['NONSPEECH'])
    other = add_punctuation(CORRECTIONS[('X', 'XY')])
    pNouns = add_punctuation(CORRECTIONS[('PROPN', 'NE')])
    nouns = add_punctuation(CORRECTIONS[('NOUN', 'NN')])
    numbers = add_punctuation(CORRECTIONS[('NUM', 'CARD')])

    for sentRow in dataDict['sentence']:
        # in the sentence tier, skip intervals of silence
        if sentRow[2] == '':
            continue
        # and only process the intervals with sentences
        else:
            # define for better readability
            sentStart = float(sentRow[0])
            sentEnd = float(sentRow[1])
            sentText = sentRow[2]

            # remove non-speech and 'other' from the sentence
            # so spaCy does not analyze the words
            # which spaCy does wrongly if it does
            sentList = [word for word in sentText.split()
                        if word not in nonspeech]
            sentList = [word for word in sentList
                        if word not in other]
            sentText = ' '.join(sentList)

            # Read sentence via spaCy to analyze linguistic feature
            nlpSentence = nlp(sentText)
            # filter by rejecting punctuation
            nlpWords = [nlpSentence[i] for i, word in enumerate(nlpSentence)
                        if word.pos_ != 'PUNCT']

        wordInd = 0
        # match the words of the tier "sentence" to the tier "words"
        # at the moment, the for loop loops through the whole word tier
        # don't touch it! it works!
        for wordTierRow in dataDict['words']:
            wordStart = float(wordTierRow[0])
            wordEnd = float(wordTierRow[1])
            wordText = wordTierRow[2]

            # check if the sentences contains anywords
            # it iss not the case if the sentences comprised only non-speech
            # that was filtered from the sentence
            if len(nlpWords) > 0:
                nlpWord = nlpWords[wordInd]

            # look up the single word in the whole sentence
            # and ignore pauses containing no string/word

            if wordStart < sentStart or wordText == '':
                continue

            # in the following condition, the current word of the inner loop
            # is embedded somewhere in the outer loop's sentence
            elif wordStart >= sentStart and wordEnd <= sentEnd:
                # timing is right, so actually check if it's the same word
                if wordText.lower() != nlpWord.text.lower():
                    if wordText in nonspeech:
                        wordTierRow.append('NONSPEECH')
                    elif wordText in other:
                        wordTierRow.extend(['X', 'XY'])
                    else:
                        # CHANGE to raising an exception
                        print('not matching words in:', sentRow[2], ';', sentText, '\n', nlpWord, wordText, '\n')
                        # following words in the sentence are probably wrong, too
                        continue

                # when word from the sentences matches the word from the
                # tier "word", add the linguistic tags
                else:
                    # first, do some heuristic corrections for words that spaCy
                    # more often tags wrongly than correctly
                    if nlpWord.text.lower() in pNouns:
                        nlpPos = 'PROPN'
                        nlpTag = 'NE'
                    elif nlpWord.text.lower() in nouns:
                        nlpPos = 'NOUN'
                        nlpTag = 'NN'
                    elif nlpWord.text.lower() in numbers:
                        nlpPos = 'NUM'
                        nlpTag = 'CARD'
                    else:
                        nlpPos = nlpWord.pos_
                        nlpTag = nlpWord.tag_

                    # create the entry for the column "syntactic dependency"
                    # get all word's children (= dependent words)
                    # and ignore punctuation
                    nlpChildren = [x.text for x in nlpWord.children
                                   if x.text.isalnum() == True]
                    # join all items/children to one string
                    if nlpChildren != []:
                        nlpChildren = ','.join(nlpChildren)
                    # if word has no children put in a placeholder
                    else:
                        nlpChildren = '-'

                    # prepare the string to write into the TextGrid interval
                    nlpDependText = '%s;%s;%s'
                    nlpDependText = nlpDependText % (nlpWord.dep_,
                                                     nlpWord.head.text.upper(),
                                                     nlpChildren)

                    # clean the word2vector
                    # check if it is a null vector
                    # and process the string to be written into the intervall
                    if np.absolute(nlpWord.vector).sum() > 0:
                        nlpVector = nlpWord.vector.tolist()
                        nlpVector = [str(x) for x in nlpVector]
                        nlpVector = ','.join(nlpVector)
                    # if it is a null vector the word is unknown,
                    # hence flag it with '#' (which saves space)
                    else:
                        nlpVector = '#'

                    # finally, extend the row of the current word with
                    # the additional linguistic features
                    # the function "write_to_file" will use the extended
                    # row(s) to build the new actual tiers
                    wordTierRow.extend(
                        [nlpPos,  # simple part-of-speech tag
                         nlpTag,  # detailed part-of-speech tag
                         nlpDependText,
                         nlpWord.lemma_,  # word's base/root
                         nlpWord.is_stop,  # word among most common words?
                         nlpVector])

                    wordInd += 1
                    if wordInd == len(nlpWords):
                        break

    return dataDict


def write_to_file(data, outfname):
    '''
    '''
    # prepare order of the old and new tiers
    allTiers = deepcopy(ORGTIERS)
    allTiers[4:4] = LINGUISTICS[-1:]
    allTiers[3:3] = LINGUISTICS[:-1]

    # write number of tiers into the TextGrid header
    TEMPLHEADER[6] = TEMPLHEADER[6].replace('##', str(len(allTiers)))

    # write the header
    toWrite = []
    toWrite.extend(TEMPLHEADER)

    # write the tiers
    column = 3
    for nr, tierName in enumerate(allTiers[:], 1):
        # write the header for the current tier
        tierText = deepcopy(TEMPLTIER)
        tierText[0] = tierText[0].replace('##', str(nr))
        tierText[2] = tierText[2].replace('##', tierName)

        # FACTORIZE THE FOLLOWING
        # processing of the tiers that are already in the original file
        if tierName in ORGTIERS:
            # add the tier text to the header of the file
            tierText[5] = tierText[5].replace('##', str(len(data[tierName])))
            toWrite.extend(tierText)

            for i, row in enumerate(data[tierName], 1):
                intervText = deepcopy(TEMPLINTERV)
                # the number of the intervall
                intervText[0] = intervText[0].replace('##', str(i))
                # start
                intervText[1] = intervText[1].replace('##', row[0])
                # end
                intervText[2] = intervText[2].replace('##', row[1])
                # text
                intervText[3] = intervText[3].replace('##', row[2])

                toWrite.extend(intervText)

        # processing of the new tiers that will contain the spaCy annotations
        # all timings / rows are based on the words annotation
        # hence, pull the information from the dictionary with key 'words'
        if tierName in LINGUISTICS:
            tierText[5] = tierText[5].replace('##', str(len(data['words'])))
            toWrite.extend(tierText)

            for i, row in enumerate(data['words'], 1):
                intervText = deepcopy(TEMPLINTERV)
                # the number of the intervall
                intervText[0] = intervText[0].replace('##', str(i))
                # start
                intervText[1] = intervText[1].replace('##', row[0])
                # end
                intervText[2] = intervText[2].replace('##', row[1])
                # text
                # columns later in the row contain the linguistic information
                # handle exception when the row/list is shorter
                # because there was no word but a pause in the intervall
                try:
                    intervText[3] = intervText[3].replace('##', str(row[column]))
                except IndexError:
                    intervText[3] = intervText[3].replace('##', '')

                toWrite.extend(intervText)

            # prepare for the next newly created tier
            column += 1

    with open(outfname, 'w', encoding='utf-16') as textGridFile:
        textGridFile.writelines(toWrite)


# main programm
if __name__ == "__main__":
    # read in annotation
    inFile = sys.argv[1]
    oldName = os.path.basename(inFile)
    newName = os.path.splitext(oldName)[0] + '_tagged.TextGrid'
    outFile = inFile.replace(oldName, newName)

    data = read_n_clean(inFile)

    nlp = spacy.load(MODEL)
    data = match_n_analyze(data, nlp)

    # bring data in shape and write them to file
    write_to_file(data, outFile)

    # counter the number of items in the tiers for
    # descriptive statistics
    for tier in sorted(data.keys()):
            counter = 0
            for i in data[tier]:
                if i[2] != '':
                    counter += 1
            print(tier, counter)
