#!/usr/bin/python

import os
import sys
import re 

def mkm_remove_version(fn)
    try:
        path = os.path.dirname(fn)
        basename = os.path.basename(fn)[::-1]
        basename = re.sub(r'\.\d_','.',basename,1)[::-1]
        params['source_file'] = basename
        params['file_date'] = basename[11:19]
        newfn = source_file.format(**params)
        newfn = os.path.join(path, newfn )
        os.rename(fn,newfn)
        return [newfn]
    except:
        return [fn]



def main():
    fn = sys.argv[1]
    ret = mkm_remove_version(fn)
    print(ret)


if __name__ == '__main__':
    main()
