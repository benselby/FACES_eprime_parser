#!/usr/bin/env python

"""FACES Task Parser

Usage: FACESParser.py <eprime_filename> <destination>

This script will convert the eprime output text file for OPT-Neuro's FACES task into a tsv file formatted according to BIDS specification.

It then outputs the trial number, onset time, accurracy, and reaction time values for each trial.
Originally written by Ella Wiljer, 2018
BIDS-ified by Gabi Herman, 21 Nov 2018
"""
from docopt import docopt
import sys
import codecs
import pdb
import pandas as pd
import numpy as np
import re

# function to read the eprime file
def read_eprime(eprimefile):
    eprime = codecs.open(eprimefile, "r", encoding = "utf-16", errors ="strict")
    lines = []
    for line in eprime:
        lines.append(str(line))
    return lines

#find all data entries in one dataset
def find_all_data (eprime, tag):
    dataset = [(i,s) for i,s in enumerate(eprime) if tag in s]
    return dataset

def findnum(ln): #TODO: make this use pattern matching rather than just looking for lines
    try:
        txtnum = re.findall('(\d+)\r\n', ln)
        return int(txtnum)
    except:
        return "n/a"

#TODO: Separate this into more functions that make sense. :)
def main():

    arguments       = docopt(__doc__)
    eprimefile      = arguments['<eprime_filename>']
    destination     = arguments['<destination>']

    text_file = eprimefile

    mr_id = text_file[text_file.find('OPT01'):text_file.find('OPT01')+23]

    eprime = read_eprime(text_file)

    #tag the trials to obtain the data for each trial
    taglist = find_all_data(eprime,"Procedure: TrialsPROC\r\n") #that finds the trial numbers which actually have stimuli

    #obtain the base onset time for the dataset
    basetime_tag = find_all_data (eprime, 'SyncSlide.OnsetTime:')  #onset time of presentation of current trial in ms from script startup (according to HCP). The first one of these should be the time of the initial TR.
    basetime = findnum(basetime_tag[0][1])

    #Create variables to hold the accuracy averages for the two trial types
    shapes_avg = 0
    shapes_num = 0
    faces_avg = 0
    faces_num = 0
    trial_start=np.empty([len(taglist)], dtype=int)
    #trial_block=np.empty([len(taglist)])
    trial_end=np.empty([len(taglist)], dtype=int)
    #loop to grab the data from each trial and output it in tsv format
    for i, ind_trial_proc in enumerate(taglist):
        #grab the data slice for each trial
        if (i < (len(taglist))-1):
            trial_end[i] = taglist[i+1][0]
        elif (i == (len(taglist))-1):
            trial_end[i] = len(eprime)
        trial_start[i] = ind_trial_proc[0]

    trial_blocks=[eprime[trial_start[i]:trial_end[i]] for i in range(len(trial_end))]

    onset_times=[((findnum(find_all_data(trial_blocks[i], 'StimSlide.OnsetTime:')[0][1])-basetime)/1000) for i in range(len(trial_end))]
    trial_types =[('Shapes' if 'Shape' in str(trial_blocks[i]) else 'Faces') for i in range(len(trial_blocks))]
    RTs=[(findnum(find_all_data(eprime[trial_start[i]:trial_end[i]], 'StimSlide.RT:')[0][1])/1000) for i in range(len(trial_end))]

    durations=[2 for i in range(len(trial_end))]

    accuracy=[findnum(find_all_data(eprime[trial_start[i]:trial_end[i]], 'StimSlide.ACC:')[0][1]) for i in range(len(trial_end))]

    correct_response=[findnum(find_all_data(eprime[trial_start[i]:trial_end[i]], 'CorrectResponse:')[0][1]) for i in range(len(trial_end))]
    participant_response = [findnum(find_all_data(eprime[trial_start[i]:trial_end[i]], 'StimSlide.RESP:')[0][1]) for i in range(len(trial_end))]

    #consec_nr =[findnum(find_all_data(eprime[trial_start[i]:trial_end[i]], 'ConsecNonResp:')[0][1]) for i in range(len(trial_end))]

    #non_response= [(1 if consec_nr[i]>0 else 0) for i in range(len(trial_blocks))]

    data = {'onset': onset_times,'duration': durations,'trial_type': trial_types, 'response_time':RTs, 'accuracy': accuracy, 'correct_response': correct_response, 'participant_response': participant_response}
    data2 = pd.DataFrame(data)

    #change it to proper BIDS naming
    data2.to_csv((destination+ mr_id+"_FACES"+".tsv"), sep='\t', index=False)

if __name__ == '__main__':
    arguments = docopt(__doc__)
    main()
