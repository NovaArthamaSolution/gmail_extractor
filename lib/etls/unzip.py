
import os
import tempfile
import pyminizip

class Unzip():
    zip_password = None
    def __init__(self,password=None):
        self.zip_password = zip_password

    def perform(self,filename: str) -> list: 
        dest_path = tempfile.mkdtemp(prefix='gmail_extractor_')
        
        pyminizip.uncompress(zipfile, self.zip_password, dest_path, int(True) )
        files = glob("%s/*.*" % dest_path )

        return list(filter(lambda f: list(os.path.splitext('.')).pop() != 'zip' , files))
