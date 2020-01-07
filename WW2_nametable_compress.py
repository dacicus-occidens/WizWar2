#! python3

import os
import sys

zero_cutoff = 3
control_bytes = [253, 254, 255]

#############
# Functions #
#############

def usage_info():
    print('\nUsage: WW2_nametable_compress.py <input> <output>')
    print('Generates a compressed Ironsword nametable.')
    print('<input>  file contains the uncompressed nametable, size 0x3C0 (960) bytes.')
    print('<output> file will contain the compressed nametable.')
    print('If no output file is provided, will report the size of the compressed data.')

def check_file_exists(file):
    if not os.path.exists(file):
        print('\nERROR: Unable to find', file)
        sys.exit()
    elif not os.path.isfile(file):
        print('\nERROR:', file, 'is not a file.')
        sys.exit()

def get_yesno(prompt):
    answer = input(prompt)
    while answer.lower() not in ['y', 'n']:
        print('ERROR: Answer must be y or n.')
        answer = input(prompt)
    return answer.lower()

def check_overwrite_file(file):
    if os.path.exists(file):
        if os.path.isfile(file):
            answer = get_yesno('WARNING: ' + file + ' already exists.  Overwrite (y/n)? ')
            if answer == 'n':
                print('Aborting.')
                sys.exit()
        elif os.path.isdir(file):
            print('ERROR:', file, 'is a directory.')
            sys.exit()

def parse_sysargs(args):
    in_fn = sys.argv[1]
    check_file_exists(in_fn)
    in_size = os.path.getsize(in_fn)
    if in_size != 960:
        print('\nERROR: Input file size is incorrect:', in_size, 'bytes.  Must be 960 bytes.')
        sys.exit()
    if len(args) >= 3:
        out_fn = sys.argv[2]
        check_overwrite_file(out_fn)
    else:
        out_fn = ''
    return in_fn, out_fn

def get_nametable(file):
    in_file = open(file, 'rb')
    nt = in_file.read(960)
    in_file.close()
    return nt

def find_nonzero(nt, addr):
    curr_addr = addr
    while curr_addr < 960 and nt[curr_addr] == 0:
       curr_addr += 1
    return curr_addr

def get_nonzero(nt, curr_addr, zero_cutoff):
    zero_bytes = bytes(zero_cutoff)
    byte_len = zero_cutoff + 1
    curr_bytes = nt[curr_addr:curr_addr + byte_len]
    while zero_bytes not in curr_bytes:
        byte_len += 1
        curr_bytes = nt[curr_addr:curr_addr + byte_len]
    return curr_bytes[0:-zero_cutoff], byte_len - zero_cutoff

def contains_control_bytes(curr_bytes, control_bytes):
    for ctrl in control_bytes:
        if ctrl in curr_bytes:
            return True
        else:
            return False

def compress_addr(addr):
    byte1 = addr % 0x20
    byte2 = int((addr - byte1) / 0x20)
    return [0xFE, byte1, byte2]

def compress_FD(curr_addr, curr_bytes, byte_len):
    FE_data = compress_addr(curr_addr)
    FD_data = [0xFD, byte_len]
    return FE_data + FD_data + list(curr_bytes)

def compress_FE(curr_addr, curr_bytes):
    FE_data = compress_addr(curr_addr)
    return FE_data + list(curr_bytes)

def process_nametable(nt, zc, cb):
    curr_addr = 0
    compressed_nt = []
    while curr_addr < 960:
        curr_addr = find_nonzero(nt, curr_addr)
        if curr_addr >= 960:
            break
        curr_bytes, byte_len = get_nonzero(nt, curr_addr, zc)
        if contains_control_bytes(curr_bytes, cb):
            compressed_nt += compress_FD(curr_addr, curr_bytes, byte_len)
        else:
            compressed_nt += compress_FE(curr_addr, curr_bytes)
        curr_addr += byte_len
    compressed_nt += [255]
    return compressed_nt

#############
# Algorithm #
#############

if len(sys.argv) < 2:
    usage_info()
else:
    in_filename, out_filename = parse_sysargs(sys.argv)
    nt = get_nametable(in_filename)
    compressed_nt = process_nametable(nt, zero_cutoff, control_bytes)
    if out_filename == '':
        print('Nametable compresses to', len(compressed_nt), 'bytes.')
    else:
        out_file = open(out_filename, 'wb')
        out_file.write(bytes(compressed_nt))
        out_file.close()
        print('Wrote', len(compressed_nt), 'bytes to', out_filename, '.')
