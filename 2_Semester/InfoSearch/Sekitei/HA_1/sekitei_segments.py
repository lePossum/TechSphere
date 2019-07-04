 # coding: utf-8

import sys
import os
import re
import random
import time
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from collections import Counter
import urlparse

#from sklearn.decomposition import PCA
#import matplotlib.pyplot as plt

def count_segments(line):
    if len(line) == 0:
        return 0
    if line[len(line) - 1] == '/':
        line = line[0:len(line) - 1]
    return line.count('/', 0, len(line)) - 2


def get_segments(line):
    if len(line) > 0 and line[len(line) - 1] == '/':
        line = line[0:len(line) - 1]

    schema_end = line.find(':')
    if schema_end != -1:
        line = line[schema_end + 1:len(line)]

    if line[0:2] == "//":
        line = line[2:len(line)]

    path_begin = line.find('/')
    if path_begin == -1:
        return []
    else:
        line = line[path_begin + 1:len(line)]

    query_begin = line.find('?')
    if query_begin != -1:
        line = line[0:query_begin]
    fragment_begin = line.find('#')
    if fragment_begin != -1:
        line = line[0:fragment_begin]

    if len(line) > 0 and line[len(line) - 1] == '/':
        line = line[0:len(line) - 1]

    if len(line) == 0:
        return []
    return re.split('/', line)

def get_param_names(line):
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


def get_params(line):
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

def extract_features(INPUT_FILE_1, INPUT_FILE_2, OUTPUT_FILE):
    examined = open(INPUT_FILE_1, "r")
    general = open(INPUT_FILE_2, "r")
    result = open(OUTPUT_FILE, "w")

    examined_lines = random.sample(examined.read().split('\n'), 1000)
    general_lines = random.sample(general.read().split('\n'), 1000)

    features = get_features(examined_lines, general_lines)

    for key, value in features:
        if value < 100:
            break
        result.write(key + '\t' + str(value) + '\n')

def get_features(l1, l2):
    lines = []
    features = Counter()

    examined_lines = l1
    general_lines = l2
    lines.extend(examined_lines)
    lines.extend(general_lines)

    for line in lines:
        if line.find('\n') != -1:
            line = line[0:len(line) - 1]
        features_from_url = get_features1(line)
        if (features_from_url):
            for feature in features_from_url:
                features[feature] += 1
        else:
            print line
    features = features.most_common()
    #print features
    return features

# gets features from one url
def get_features1(url):
    features = []

    features.append("segments:" + str(count_segments(url)))
    for name in get_param_names(url):
        features.append("param_name:" + name)
    for param in get_params(url):
        if len(param) == 1:
            param.append("")
        features.append("param:" + param[0] + "=" + param[1])
    segments = get_segments(url)
    #if not segments:
    #   return features
    for pos, segment in enumerate(segments):
        #print pos
        segment_decoded = urlparse.unquote(segment)
        regex_res = re.findall("[^\\d]+\\d+[^\\d]+$", segment_decoded)
        features.append("segment_name_" + str(pos) + ":" + segment)
        if segment.isdigit():
            features.append("segment_[0-9]_" + str(pos) + ":1")
        if len(regex_res) == 1 and regex_res[0] == segment_decoded:
            features.append("segment_substr[0-9]_" + str(pos) + ":1")
        extension = get_extension(segment)
        if len(extension) != 0:
            features.append("segment_ext_" + str(pos) + ":" + extension)
        if len(regex_res) == 1 and regex_res[0] == segment_decoded and len(extension) != 0:
            features.append("segment_ext_substr[0-9]_" + str(pos) + ":" + extension)
        features.append("segment_len_" + str(pos) + ":" + str(len(segment)))
    return features

sekitei = None;

clusterization = None
classifications = []
clusters_amount = 10
links_distr = None

min_freq = 0.1
max_freq = 0.9
min_features_count = 10

chosen_features = set()
min_quota = 100
max_quota = 1000

def get_attrs(chosen_features, features_from_url):
    attrs = np.zeros([len(chosen_features)])
    for j, feature in enumerate(chosen_features):
        if (feature in features_from_url):
            attrs[j] = 1
    return attrs

def define_segments(QLINK_URLS, UNKNOWN_URLS, QUOTA):
    #print "define_segments is not implemented";
    global clusterization
    global classifications
    global clusters_amount
    global links_distr
    global min_freq
    global max_freq
    global min_features_count
    global min_quota
    global max_quota
    global chosen_features

    cur_quota = QUOTA

    features = get_features(QLINK_URLS, UNKNOWN_URLS)
    l_size = len(QLINK_URLS) + len(UNKNOWN_URLS)

    for key, value in features:
        if (value > min_freq * l_size) and (value < max_freq * l_size):
            chosen_features.add(key)
    #print chosen_features

    X = np.zeros([l_size, len(chosen_features)])
    # 0 - unknown_url, 1 - qlink url
    y = np.zeros([l_size])
    y[:len(QLINK_URLS)] = np.ones([len(QLINK_URLS)])

    for i, u in enumerate(QLINK_URLS + UNKNOWN_URLS):
        X[i] = get_attrs(chosen_features, set(get_features1(u)))
    clusterization = KMeans(n_clusters=clusters_amount)
    clusterization.fit(X)
    cluster_nums = clusterization.predict(X)

    links_distr = np.zeros([clusters_amount, 4])
    good_like = np.zeros(clusters_amount)
    for cl_num in range(clusters_amount):
        links_distr[cl_num][0] = np.sum(cluster_nums == cl_num)
        links_distr[cl_num][1] = np.sum(cluster_nums[y == 1] == cl_num)

    in_top_quota = np.percentile(links_distr[:, 0], 25)
    for cl_num in range(clusters_amount):
        links_distr[cl_num][3] = (links_distr[cl_num][1] + in_top_quota * np.sum(good_like) /\
            clusters_amount) / (links_distr[cl_num][0] + in_top_quota)
    links_distr[:, 3] *= cur_quota / (np.sum(links_distr[:, 3]))
    links_distr[links_distr[:, 3] < min_quota, 3] = min_quota
    links_distr[:, 3] *= cur_quota / (np.sum(links_distr[:, 3]))

    # 0 - UNKNOWN, 1 - QLINK
    for i in range(clusters_amount):
        if (X[cluster_nums == i].shape[0] == 0):
            classifications.append(None)
        else:
            classifications.append(RandomForestClassifier(max_depth=4, random_state=0, n_estimators=3))
            classifications[i].fit(X[cluster_nums == i], y[cluster_nums == i])

#
# returns True if need to fetch url
#
def fetch_url(url):
    global clusterization
    global classifications
    global links_distr
    attrs = get_attrs(chosen_features, set(get_features1(url)))
    cluster_n = clusterization.predict(attrs.reshape(1, -1))[0]
    is_qlinq = classifications[cluster_n].predict(attrs.reshape(1, -1))
    if (is_qlinq > 0.95):
        return True
    if (links_distr[cluster_n][3] > links_distr[cluster_n][2]):
        links_distr[cluster_n][2] += 1
        return True
    return False
    