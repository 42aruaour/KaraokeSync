import os
import re
from functools import reduce
from datetime import datetime
import pickle

data_dir = 'data/ass'
save_dir = 'data'
dialogue_keyword = '[Events]\n'
effects = ['karaoke']


def filter_event_line(line):
    '''
    treats the incomming [Events] line as a csv and extracts the start time, end time, and
    :param line: the raw line in the [Events] section of the .ass file to extract data from. Acts like a csv.
    :return: [start time, end time, string for line]
    '''
    parts = line.split(',')
    return parts[1], parts[2], ','.join(parts[9:])


def expand_times(line):
    '''
    breaks down each line by word and timing, as well as copies over start and end times per each syllable.
    also converts start and end time to centi seconds.
    :param line:a tuple with (start time, end time, string dialogue from .ass file)
    :return: list of tuples containing (start time, end time, delay amount, word)
    '''
    dialogue_string = line[2]
    splits = re.split("(\{\\\\k[f]?[0-9]+\})", dialogue_string)
    splits = splits[1:]
    splits = list(zip(*[iter(splits)] * 2))

    # also convert start and end times to centi-seconds here since it's convenient
    start_time = (datetime.strptime(line[0], '%H:%M:%S.%f') - datetime(1900, 1, 1)).total_seconds() * 100
    end_time = (datetime.strptime(line[1], '%H:%M:%S.%f') - datetime(1900, 1, 1)).total_seconds() * 100

    out = map(lambda x: [start_time, end_time, float(re.search('[0-9]+', x[0]).group(0)), x[1]], splits)
    return list(out)


def combine_syllables(expanded_line):
    '''
    Converts expanded lines into list of tuple with (start time, end time , [delay amounts], [words])
    :param expanded_line: a list of lists, where each list is the syllable in a line, and the whole collection is the whole line.
    :return: a single collection with (start time, end time , [delay amounts], [words])
    '''
    # grab start time from first element since it should be the same across
    start_time = expanded_line[0][0]
    end_time = expanded_line[0][1]
    times = list(map(lambda x: x[2], expanded_line))
    syllables = list(map(lambda x: x[3], expanded_line))
    return [start_time, end_time, times, syllables]

# expanded data separates the information per syllable
# expanded data lines separates the information per syllable and per line, so it is an extra dimension deep.
expanded_data_y = []
expanded_data_x = []
expanded_data_lines_y = []
expanded_data_lines_x = []

# look at all ass files.
filenames = os.listdir(data_dir)
filenames = list(filter(lambda name: name.endswith('.ass'), filenames))
n_files = len(filenames)
i = 1
for filename in filenames:
    print('Processing',i,'/',n_files,'files')
    # extract data from ass files
    with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as file:
        raw = file.read()
        events_txt = raw[raw.index(dialogue_keyword) + len(dialogue_keyword):]
        lines = events_txt.split('\n')
        key = lines[0]
        lines = lines[1:]

    # filter out empty lines and separate into list of (start time, end time, string to show)
    filtered_lines = filter(lambda txt: txt.strip() != '', lines)
    filtered_lines = filter(lambda txt: txt.split(',')[8] == '' or txt.split(',')[8] in effects, filtered_lines)
    filtered_lines = list(map(filter_event_line, filtered_lines))

    # separate each syllable with their time, grouped by original lyric line.
    expanded_lines = list(map(expand_times, filtered_lines))

    # flatmap to combine each syllable with time into one list
    syllable_list = reduce(list.__add__, expanded_lines)

    # combine each syllable per line to get list of lines, with associated list of start time for each syllable.
    line_list = list(map(combine_syllables, expanded_lines))

    # save in list for other processing
    expanded_data_y.append(syllable_list)
    expanded_data_lines_y.append(line_list)

    # get just lyrics out of list
    expanded_data_x.append(list(map(lambda x:x[3], syllable_list)))
    expanded_data_lines_x.append(list(map(lambda x:''.join(x[3]), line_list)))

    # print(expanded_lines)
    # print(syllable_list)
    # print(line_list)
    i = i + 1

# convert words into numbers, then convert into numpy array

# save as pickle
with open(save_dir + "/syllable_x.pkl", 'wb') as file:
    pickle.dump(expanded_data_x, file)
with open(save_dir + "/syllable_y.pkl", 'wb') as file:
    pickle.dump(expanded_data_y, file)
with open(save_dir + "/line_x.pickle", 'wb') as file:
    pickle.dump(expanded_data_lines_x, file)
with open(save_dir + "/line_y.pickle", 'wb') as file:
    pickle.dump(expanded_data_lines_y, file)
