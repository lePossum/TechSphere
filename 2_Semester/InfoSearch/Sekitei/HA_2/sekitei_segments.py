 # coding: utf-8

import sys
import os
import re
import random
import time
from sklearn.cluster import KMeans
import numpy
from extract_features import *

sekitei = None;
clusterization = None
classifications = []
links_distr = None

def get_attrs(chosen_features, features_from_url):
    attrs = np.zeros([len(chosen_features)])
    for j, feature in enumerate(chosen_features):
        if feature in features_from_url:
            attrs[j] = 1
    return attrs

def define_segments(QLINK_URLS, UNKNOWN_URLS, QUOTA):
    #print "define_segments is not implemented";
    features = get_features(QLINK_URLS, UNKNOWN_URLS)
    cur_quota = QUOTA

    #

    clusterization = KMeans(n_clusters=num_clusters)
    clusterization.fit(X)
    cluster_nums = clusterization.predict(X)

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
    if is_qlinq > 0.95:
        return True
    if links_distr[cluster_n][3] > links_distr[cluster_n][2]:
        links_distr[cluster_n][2] += 1
        return True
    return False

