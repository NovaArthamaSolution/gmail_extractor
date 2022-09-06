import os
import tempfile
import pyminizip
from glob import glob

def unzip(filename: str,password=None) -> list: 
    dest_path = tempfile.mkdtemp(prefix='gmail_extractor_')
    pyminizip.uncompress(filename, password, dest_path, int(True) )
    
    files = glob(f"{dest_path}/*.*")
    print(f"unzip: {filename} to {dest_path} \nresult: {files}")
    
    return list(filter(lambda f: list(os.path.splitext('.')).pop() != 'zip' , files))


def main(filename):
    ret = unzip(filename)
    print(ret)
    return ret

if __name__ == '__main__' :
    import sys
    filename = sys.argv[1]
    main(filename)