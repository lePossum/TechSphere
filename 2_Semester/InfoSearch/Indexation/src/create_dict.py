import struct
import mmap
import pickle
from collections import defaultdict

#from settings import hash_type = 'I', encoding_varbyte_code = 0
from doc2words import extract_words
from compress import integer_to_varbyte


def resize_mmap(file_, size):
    file_.write('\0')
    file_.flush()
    file_mmap = mmap.mmap(file_.fileno(), 0)
    file_mmap.resize(size)
    return file_mmap


def create_dict_part_varbyte(dict_, last_doc_id, words, docid):
    encoder = integer_to_varbyte

    list_size_delta = 0

    for term_hash in words:
        if last_doc_id[term_hash] == 0:
            last_doc_id[term_hash] = docid
            new_docid_delta = encoder(docid)
            dict_[term_hash] += new_docid_delta
            list_size_delta += len(new_docid_delta)
            continue
        if docid - last_doc_id[term_hash] != 0:
            new_docid_delta = encoder(docid - last_doc_id[term_hash])
            dict_[term_hash] += new_docid_delta
            list_size_delta += len(new_docid_delta)
            last_doc_id[term_hash] = docid
    return list_size_delta

# create index with files from @reader
def create_dict_varbyte(dict_file_name, support_file_name, info_file_name, url_file_name, reader, if_continue):
    url_file = open(url_file_name, 'a')

    if not if_continue:
        # hash of term to string on bytes in encoding (string == list of deltas between docid)
        dict_ = defaultdict(str)
        # hash of term to last_doc_id in list of deltas
        last_doc_id = defaultdict(int)

        # number of max doc_id
        max_docid = 0
        # size of all lists
        lists_size = 0

        max_docid_prev = 0
    else:
        dict_pickle_file = open(dict_file_name + 'pickle', 'rb')
        dict_ = pickle.load(dict_pickle_file)
        dict_pickle_file.close()

        last_doc_id_pickle_file = open(support_file_name + '_last_pickle', 'rb')
        last_doc_id = pickle.load(last_doc_id_pickle_file)
        last_doc_id_pickle_file.close()

        max_docid_pickle_file = open(support_file_name + '_max_pickle', 'rb')
        max_docid_prev = pickle.load(max_docid_pickle_file)
        max_docid = max_docid_prev
        max_docid_pickle_file.close()

        lists_size_pickle_file = open(support_file_name + '_size_pickle', 'rb')
        lists_size = pickle.load(lists_size_pickle_file)
        lists_size_pickle_file.close()

    for docid, doc in enumerate(reader):
        if if_continue:
            docid += max_docid_prev
        max_docid = docid + 1
        url_file.write(doc.url + '\n')
        lists_size += create_dict_part_varbyte(dict_, last_doc_id, extract_words(doc.text), docid + 1)

    if not if_continue:
        dict_pickle_file = open(dict_file_name + 'pickle', 'wb')
        pickle.dump(dict_, dict_pickle_file)
        dict_pickle_file.close()

        last_doc_id_pickle_file = open(support_file_name + '_last_pickle', 'wb')
        pickle.dump(last_doc_id, last_doc_id_pickle_file)
        last_doc_id_pickle_file.close()

        max_docid_pickle_file = open(support_file_name + '_max_pickle', 'wb')
        pickle.dump(max_docid, max_docid_pickle_file)
        max_docid_pickle_file.close()

        lists_size_pickle_file = open(support_file_name + '_size_pickle', 'wb')
        pickle.dump(lists_size, lists_size_pickle_file)
        lists_size_pickle_file.close()
        quit()

    write_stuff(dict_file_name, support_file_name, info_file_name,
                dict_, lists_size, max_docid, encoding_varbyte_code)

# write all necessary stuff for index
def write_stuff(dict_file_name, support_file_name, info_file_name,
                dict_, lists_size, max_docid, encoding_code):
    # hash of term to bias of list of deltas in dict file
    hash_to_bias = defaultdict(int)
    # hash of term to len of list of deltas in dict file
    hash_to_len = defaultdict(int)

    # write lists to the memory
    with open(dict_file_name, 'w+b') as dict_file:
        dict_mmap = resize_mmap(dict_file, lists_size)

        bias = 0
        for term_hash, list_ in sorted(dict_.iteritems()):
            dict_mmap[bias:bias + len(list_)] = list_
            hash_to_bias[term_hash] = bias
            hash_to_len[term_hash] = len(list_)
            bias += len(list_)

        dict_mmap.close()
        dict_file.close()
    # write support information of lists (corresponding term hash, list bias, list len)
    with open(support_file_name, 'w+b') as support_file:
        chunk_size = struct.calcsize(hash_type + 'II')
        support_mmap = resize_mmap(support_file, chunk_size * len(dict_))

        for ind, term_hash in enumerate(sorted(dict_.keys())):
            support_mmap[chunk_size * ind:chunk_size * (ind + 1)] = \
                struct.pack(hash_type + 'II', term_hash, hash_to_bias[term_hash], hash_to_len[term_hash])

        support_mmap.close()
        support_file.close()
    # write global wide information about dict (number of documents, ...)
    with open(info_file_name, 'wb') as info_file:
        info_file.write(struct.pack('I', max_docid))
        info_file.write(struct.pack('I', encoding_code))
        info_file.close()
