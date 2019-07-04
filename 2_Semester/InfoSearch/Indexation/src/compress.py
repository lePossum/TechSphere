# coding=utf-8

import struct

def integer_to_varbyte(value):
    str_ = ""
    while value >= 0x80:
        str_ += chr(value & 0x7f)
        value >>= 7
    if value == 0 and len(str_) > 0:
        str_[len(str_) - 1] = chr(ord(str_[len(str_) - 1]) | 0x80)
    else:
        str_ += chr(value | 0x80)
    return str_[::-1]


def get_next_int_varbyte(mmaped_file, bias):
    value = ord(mmaped_file[bias]) - 0x80
    readed = 1
    while bias + readed < mmaped_file.size() and not(ord(mmaped_file[bias + readed]) & 0x80):
        value = (value << 7) | ord(mmaped_file[bias + readed])
        readed += 1
    return value, readed