#!/usr/bin/python

import os
import sys
import re 

from .etl import ETL

class MKMRemoveVersion(ETL):       
    def perform(self,fn):
        try:
            path = os.path.dirname(fn)
            basename = os.path.basename(fn)[::-1]
            basename = re.sub(r'\.\d_','.',basename,1)[::-1]
            params['source_file'] = basename
            params['file_date'] = basename[11:19]
            newfn = self.filename_format.format(**params)
            newfn = os.path.join(path, newfn )
            os.rename(fn,newfn)
            return [newfn]
        except:
            return [fn]


ETL.add_model('mkm_remove_version',MKMRemoveVersion)

def main():
    fn = sys.argv[1]
    etl = MKMReplaceVersion()
    ret = etl.perform(fn)
    print(ret)


if __name__ == '__main__':
    main()
