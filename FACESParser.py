#!/usr/bin/env python
"""FACES Task Parser

Usage: FACESParser.py <eprime_filename> <destination>

This script will convert the eprime output text file for OPT-Neuro's FACES task into a tsv file formatted according to BIDS specification.

It then outputs the trial number, onset time, accurracy, and reaction time values for each trial.
Originally written by Ella Wiljer, 2018
BIDS-ified by Gabi Herman, 21 Nov 2018
"""
from docopt import docopt
import codecs
import pandas as pd
import numpy as np
import re
import os


# function to read the eprime file
def read_eprime(eprimefile):
    eprime = codecs.open(eprimefile, "r", encoding="utf-16", errors="strict")
    lines = []
    for line in eprime:
        lines.append(str(line))
    return lines


# find all data entries in one dataset
def find_all_data(eprime, tag):
    dataset = [(i, s) for i, s in enumerate(eprime) if tag in s]
    return dataset


def findnum(ln):
    try:
        txtnum = re.findall('(\d+)\r\n', ln)
        return float(txtnum[0])
    except ValueError:
        return txtnum[0]


def get_event_value(eprime, event):

    events = find_all_data(eprime, event)
    if not events:
        return np.nan
    elif len(events) > 1:
        print("Was expecting only one event, but received multiple!")
        raise ValueError

    return findalphanum(events[0][1])


def event_is_empty(e):
    return e.strip().endswith(':')


def findalphanum(ln):

    # Check if any values exist
    if event_is_empty(ln):
        return np.nan
    try:
        txtnum = re.findall('(?<=: )[A-Za-z0-9]+', ln)[0]
    except IndexError:
        print(f"Value found is unexpected!: {ln}")
        raise
    return txtnum


def get_event_response(eprime, rsp_event):
    resp = get_event_value(eprime, rsp_event)
    return map_response(resp)


def map_response(x):
    '''
    Some FACES task files use "c" and "d" instead of 1,2
    '''

    if pd.isnull(x):
        return x

    if x.isdigit():
        return x

    mapdict = {'c': 1, 'd': 2}
    try:
        res = int(mapdict[x])
    except KeyError:
        print("Value is not numeric or matches 'c or d'")
        print(f"Value found: {x}")

    return res


def main():

    arguments = docopt(__doc__)
    eprimefile = arguments['<eprime_filename>']
    destination = arguments['<destination>']

    print(f"Parsing faces for {eprimefile}")
    text_file = eprimefile

    mr_id = eprimefile[eprimefile.find('OPT01'):eprimefile.find('OPT01') + 23]

    eprime = read_eprime(eprimefile)

    # tag the trials to obtain the data for each trial
    taglist = find_all_data(eprime, "Procedure: TrialsPROC\r\n")

    trial_start = np.empty([len(taglist)], dtype=int)
    trial_end = np.empty([len(taglist)], dtype=int)

    for i, ind_trial_proc in enumerate(taglist):
        if (i < (len(taglist)) - 1):
            trial_end[i] = taglist[i + 1][0]
        elif (i == (len(taglist)) - 1):
            trial_end[i] = len(eprime) - 1

        trial_start[i] = ind_trial_proc[0]

    trial_blocks = [eprime[s:e] for s, e in zip(trial_start, trial_end)]

    entries = []
    for b in trial_blocks:
        entries.append({
            'onset':
            get_event_value(b, 'StimSlide.OnsetTime:'),
            'duration':
            get_event_value(b, 'StimSlideOnsetToOnsetTime:'),
            'trial_type':
            'Shapes' if 'Shape' in str(b) else 'Faces',
            'response_time':
            get_event_value(b, 'StimSlide.RT:'),
            'accuracy':
            get_event_value(b, 'StimSlide.ACC:'),
            'correct_response':
            map_response(get_event_value(b, 'CorrectResponse:')),
            'participant_response':
            map_response(get_event_value(b, 'StimSlide.RESP:'))
        })

    data = pd.DataFrame.from_dict(entries).astype({
            "onset": np.float,
            "duration": np.float,
            "response_time": np.float,
            "accuracy": np.float,
            "correct_response": np.float,
            "participant_response": np.float
            })\
            .astype({
                "correct_response": "Int64",
                "participant_response": "Int64",
                "accuracy": "Int64"
            })

    log_head, log_tail = os.path.split(eprimefile)

    find = re.compile('FACES_eprime_parser\/(OPT01[^\/]*)')
    m = find.findall(log_head)
    find2 = re.compile('(part\d).log')
    n = find2.findall(log_tail)
    sub_id = os.path.basename(log_head)

    file_name = '{}/{}_FACES.tsv'.format(destination, sub_id)

    if not os.path.exists(os.path.dirname(file_name)):
        os.makedirs(os.path.dirname(file_name))

    #change it to proper BIDS naming
    data.to_csv(file_name, sep='\t', index=False)


if __name__ == '__main__':
    main()
