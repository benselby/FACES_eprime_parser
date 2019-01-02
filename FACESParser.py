#!/usr/bin/env python

"""FACES Task Parser

Usage: FACESParser.py <eprime_filename>

This script will convert a null eprime file to a tsv file.
It then outputs the trial number, onset time, accurracy, and reaction time values for each trial.
Written by Ella Wiljer, 2018
Edited by Gabi Herman, 21 Nov 2018



Note to self from Gabi: It would be good to have options for everything in a folder or just for individuals. (Erin says not to.)



For BIDs-ification
Onset (in seconds) of the event measured from the beginning of the acquisition of the first volume in the corresponding task imaging data file.
If any acquired scans have been discarded before forming the imaging data file, ensure that a time of 0 corresponds to the first image stored.
In other words negative numbers in "onset" are allowed5.

"""
from docopt import docopt
import sys
import codecs
import pdb

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

#take in a string from the eprime file to be parsed into an integer
def findnum(ln):
    index = ln.find(":")
    txtnum = ln[index + 2:-2]
    return int(txtnum)

def main():

    arguments       = docopt(__doc__)
    eprimefile      = arguments['<eprime_filename>']

    eprimefile = '/scratch/gherman/OPT/FACES/gabi_behav/used_textfiles/OPT01_UP1_10006_01_02_EMOTION.txt'
    eprime = read_eprime(eprimefile)




    print("It is running!")


    #create the tsv file from the eprime file
    with open (eprimefile[0:-4] + ".tsv", "w")as tsv:
        tsv.write("Trial\ttrial_type\tonset\taccuracy\treaction time\n")

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
    #loop to grab the data from each trial and output it in tsv format
    for i, ind_trial_proc in enumerate(taglist):

        #grab the data slice for each trial
        if (i < (len(taglist))-1):
            trial_end = taglist[i+1][0]
        elif (i == (len(taglist))-1):
            trial_end = len(eprime)

        trial_start = ind_trial_proc[0]
        trial_block = eprime[trial_start: trial_end]

        with open (eprimefile[0:-4] + ".tsv", "a")as tsv:
            #output trial number
            tsv.write(str(i + 1) + "\t")
            #check if data exists for the trial
            onset_time = find_all_data(trial_block, 'StimSlide.OnsetTime:') #onset time of presentation of current trial in ms from script startup
            if not onset_time:
                tsv.write('n/a\tn/a\tn/a\r\n')
                continue
            #trial type and its average accuracy
            shape_trial = find_all_data(trial_block, 'ShapeBlock')
            face_trial = find_all_data(trial_block, 'FaceBlock')
            if shape_trial:
                tsv.write('Shapes\t')
                shapes_num += 1 #should this really be hard coded?
                acc = find_all_data(trial_block, 'StimSlide.ACC: ')
                shapes_avg += findnum(acc[0][1])

            if face_trial:
                tsv.write('Faces\t')
                faces_num += 1
                acc = find_all_data(trial_block, 'StimSlide.ACC: ')
                faces_avg += findnum(acc[0][1])
            #output the trial's onset time(- the base onset time)
            tsv.write(str(findnum(onset_time[0][1]) - basetime)+ "\t") #this is the time of the trial onset in relation to the acquisition of the first TR.
            #output the trial's accuracy
            ACC = find_all_data(trial_block, 'StimSlide.ACC: ')
            tsv.write(str(findnum(ACC[0][1])) + "\t")
            #output trial reaction time
            RTnum = find_all_data(trial_block, 'StimSlide.RT:')
            tsv.write(str(findnum(RTnum[0][1])) + "\r\n")

    with open (eprimefile[0:-4] + ".tsv", "a")as tsv:
        tsv.write("shapes Average\t" + str(float(shapes_avg) / float(shapes_num)) + "\n")
        tsv.write(("faces Average\t" + str(float(faces_avg) / float(faces_num)) + "\n"))



print(onset_time[0][1])

if __name__ == '__main__':
    arguments = docopt(__doc__)
    main()
