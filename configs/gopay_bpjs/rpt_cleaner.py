import os
import re
from .finrec_etl import FinrectETL


class RPTCleaner(FinrectETL):
    def perform(self) -> list:
        tmpfile,ext = os.path.splitext(self.source_file)
        tmpfile += '.tsv'

        expr = re.compile(r'^\d{6}.*')
        print(tmpfile)
        with open(self.source_file, mode='r') as in_file, open(tmpfile, mode='w') as out_file:
            for inline in in_file.readlines():
                if expr.match(inline):
                    out_file.write(inline)
        
        return [tmpfile]
