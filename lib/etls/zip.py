
import pyminizip

class Zip():
    zip_password = None
    def __init__(self,**kwargs):
        self.zip_password = kwargs.get('zip_password',None)
        self.dest_fname = kwargs.get('dest_file')

    def perform(self,filenames) -> list: 
        dest_fname = self.dest_fname.format(source_file=)
        pyminizip.compress_multiple(filenames, [], dest_fname,self.zip_password,COMPRESSION_LEVEL)
        return [dest_fname]