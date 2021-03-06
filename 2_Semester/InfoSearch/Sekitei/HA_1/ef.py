# coding: utf-8

import sys
import re
import random
from operator import itemgetter
from collections import Counter
import urllib


def count_segments(line):
    if len(line) == 0:
        return 0
    if line[len(line) - 1] == '/':
        line = line[0:len(line) - 1]
    return line.count('/', 0, len(line)) - 2


def extract_segments(line):
    # drop / at the end of url
    if len(line) > 0 and line[len(line) - 1] == '/':
        line = line[0:len(line) - 1]

    # drop scheme (defined as scheme:[other url])
    schema_end = line.find(':')
    if schema_end != -1:
        line = line[schema_end + 1:len(line)]

    # drop // from the beginning if exists
    if line[0:2] == "//":
        line = line[2:len(line)]

    # drop all stuff before path
    path_begin = line.find('/')
    if path_begin == -1:
        return []
    else:
        line = line[path_begin + 1:len(line)]

    # drop all stuff after path
    query_begin = line.find('?')
    if query_begin != -1:
        line = line[0:query_begin]
    fragment_begin = line.find('#')
    if fragment_begin != -1:
        line = line[0:fragment_begin]

    # drop / at the end of path part
    if len(line) > 0 and line[len(line) - 1] == '/':
        line = line[0:len(line) - 1]

    if len(line) == 0:
        return []
    return re.split('/', line)


def extract_param_names(line):
    names = []
    start_params = line.find('?')
    if start_params == -1:
        return names
    else:
        start_params += 1

    end_params = line.find('#')
    if end_params == -1:
        end_params = len(line) - 1

    for param_sub in re.split('&', line[start_params:end_params]):
        names.append(re.split('=', param_sub)[0])

    return names


def extract_params(line):
    names = []
    start_params = line.find('?')
    if start_params == -1:
        return names
    else:
        start_params += 1

    end_params = line.find('#')
    if end_params == -1:
        end_params = len(line) - 1

    for param_sub in re.split('&', line[start_params:end_params]):
        names.append(re.split('=', param_sub))

    return names

def get_extension(segment):
    ext_begin = segment.rfind('.')
    if ext_begin == -1:
        return ""
    return segment[ext_begin + 1: len(segment)]

# reads files with INPUT FILES and writes features with frequency into OUTPUT FILE
def extract_features(INPUT_FILE_1, INPUT_FILE_2, OUTPUT_FILE):
    examined = open(INPUT_FILE_1, "r")
    general = open(INPUT_FILE_2, "r")
    result = open(OUTPUT_FILE, "w")

    sample_size = 1000
    min_count = 100

    examined_lines = random.sample(examined.read().split('\n'), sample_size)
    general_lines = random.sample(general.read().split('\n'), sample_size)

    features = extract_features_from_list(examined_lines, general_lines)

    for key, value in features:
        if value < min_count:
            break
        result.write(key + '\t' + str(value) + '\n')


# returns sorted Counter dictionary with features
def extract_features_from_list(QLINK_LIST, UNKNOWN_URLS_LIST):
    lines = []
    features = Counter()

    examined_lines = QLINK_LIST
    general_lines = UNKNOWN_URLS_LIST
    lines.extend(examined_lines)
    lines.extend(general_lines)

    for line in lines:
        if line.find('\n') != -1:
            line = line[0:len(line) - 1]
        features_from_url = extract_features_from_url(line)
        if (features_from_url):
	        for feature in features_from_url:
	            features[feature] += 1
        else:
        	print (line)
    features = features.most_common()

    print(features)
    return features


# extracts features from one url
def extract_features_from_url(url):
    features = []

    # feature 1
    features.append("segments:" + str(count_segments(url)))
    # feature 2
    for name in extract_param_names(url):
        features.append("param_name:" + name)
    # feature 3
    for param in extract_params(url):
        if len(param) == 1:
            param.append("")
        features.append("param:" + param[0] + "=" + param[1])
    # features 4a - 4f
    #print(features)
    segments = extract_segments(url)
    #if not segments:
    #	return features
    for pos, segment in enumerate(segments):
        segment_decoded = urllib.parse.unquote(segment)
        regex_res = re.findall("[^\\d]+\\d+[^\\d]+$", segment_decoded)
        # feature 4a
        features.append("segment_name_" + str(pos) + ":" + segment)
        # feature 4b
        if segment.isdigit():
            features.append("segment_[0-9]_" + str(pos) + ":1")
        # feature 4c
        if len(regex_res) == 1 and regex_res[0] == segment_decoded:
            features.append("segment_substr[0-9]_" + str(pos) + ":1")
        # feature 4d
        extension = get_extension(segment)
        if len(extension) != 0:
            features.append("segment_ext_" + str(pos) + ":" + extension)
        # feature 4e
        if len(regex_res) == 1 and regex_res[0] == segment_decoded and len(extension) != 0:
            features.append("segment_ext_substr[0-9]_" + str(pos) + ":" + extension)
        # feature 4f
        features.append("segment_len_" + str(pos) + ":" + str(len(segment)))
    return features
