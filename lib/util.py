
import os
import argparse
import configparser
from datetime import datetime

import re 
from glob  import glob
import pyminizip
import tempfile
import requests
import unicodedata 
from urllib.parse import urlparse 

from pprint import pprint
import time

from lxml import etree
from lxml.etree import HTMLParser  
parser = HTMLParser()


COMPRESSION_LEVEL = int(os.environ.get('COMPRESSION_LEVEL','5'))
_filename_ascii_strip_re = re.compile(r'[^A-Za-z0-9_.-]')


def parse_arg():
  parser = argparse.ArgumentParser(description="Extract Big Query to SFTP")
  parser.add_argument("config_fullpath", help="Path to config YAML",nargs="?", default='/data/in/config.yaml')
  parser.add_argument(
      "-s",
      action='store',
      dest="datetime_start",
      help="datetime start parameter",
      default=os.getenv('DSTART'))

  parser.add_argument(
      "-e",
      action='store',
      dest="datetime_end",
      help="datetime end parameter",
      default=os.getenv('DEND'))
  result = parser.parse_args()

  return result


def read_config(path_config):
  config = configparser.ConfigParser()
  if os.path.exists(path_config):
    config.read(path_config)
  else:
    print("No config file")
    pass
  return config

# If modifying these scopes, delete the file token.json.
def download_file(url, dest_path=''):
    if not dest_path:
        dest_path = tempfile.mkdtemp(prefix='gmail_extractor_')

    parsed = urlparse(url)
    ext = ''    
    fname = os.path.basename(dest_path) or os.path.basename(parsed.path)
    dest_path = os.path.dirname(dest_path)
    tic = time.time()
    with requests.get(url,allow_redirects=True,stream=True) as r :    
        if r.url != url:
            fname = os.path.basename(urlparse(r.url).path) 
        cd_fname =  get_filename_from_cd(r.headers.get('Content-Disposition'))
        if cd_fname:
            fname = cd_fname

        if r.headers.get('Content-Type',None) == 'application/zip':
            fname ,ext = os.path.splitext(fname)
            fname += '.zip'

        fname = os.path.join(dest_path,secure_filename(fname))
        with open(fname,'wb') as fh:
            for chunk in r.iter_content(chunk_size=10*1024): 
                if chunk:
                    fh.write(chunk)

    toc = time.time()
    print("%.3f seconds elapsed to downloading %s" % ((toc-tic), fname ) )
    return fname
    


def get_filename_from_cd(cd):
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0]


def extract_urls_xmlfile(html_file, xpath):

    f = open(html_file,'r')
    html = f.read()
    f.close()

    doc = etree.parse(html_file,parser=parser)
    # print(etree.tostring(doc))
    try:
        els = doc.xpath(xpath)
        return [el.get('href') for el in els ]
    except Exception as ex:
        return []
    

def extract_string_xmlfile(mail_file,xpath,attribute='href'):
    f = open(html_file,'r')
    html = f.read()
    f.close()

    doc = etree.parse(html_file,parser=parser)
    try:
        els = doc.xpath(xpath)
        el =  els.pop()
        if '()' not in attribute:
            return el.get(attribute).strip()
        else:
            return el.text.strip()
    except Exception as ex:
        return None

    

def find_attachment(email, filename_pattern='*.zip', mime_type=''):
    if '*' in filename_pattern and  '.*' not in filename_pattern:
        filename_pattern = filename_pattern.replace('.','\.').replace('*','.*')

    p = re.compile(filename_pattern)
    found = []
    for part in email['payload'].get('parts',''):
        # pprint(part)
        if mime_type and part['mimeType'] != mime_type:
            continue
        # pprint( part )
        if p.search(part['filename']):
            found.append(part)
    return found

def zip(filenames,dest_fname,password=None):
    pyminizip.compress_multiple(filenames, [], dest_fname,password,COMPRESSION_LEVEL)

def unzip(zipfile, dest_path=None, password=None):
    if not dest_path:
        dest_path = tempfile.mkdtemp(prefix='gmail_extractor_')
    
    pyminizip.uncompress(zipfile, password,dest_path,int(True))
    files = glob("%s/*.*" % dest_path )

    return list(filter(lambda f: list(os.path.splitext('.')).pop() != 'zip' , files))


def cleanup(tmp_local_dir):
    cleanup_cmd = 'rm -r {}/*'.format(tmp_local_dir)
    os.system(cleanup_cmd)
    os.system("mkdir -p {}".format(tmp_local_dir))

def safe_rename(filename,file_format='',params={}):
    path = os.path.dirname(filename)

    basename = os.path.basename(filename)
    basename, ext = os.path.splitext(basename)
    params['source_file'] = params.get('source_file',None) or  basename
    basename = file_format.format(**params)
    basename = secure_filename(f"{basename}{ext}")
    safe_filename = os.path.join(path,basename)

    os.rename(filename,safe_filename)
    return safe_filename



def remove_accents(s): 
    """remove accents for ascii analogs"""
    nkfd_form = unicodedata.normalize('NFKD', s) 
    return u''.join([c for c in nkfd_form if not unicodedata.combining(c)])

def remove_reserved(s):
    """only keep characters liked across most file systems"""
    # http://serverfault.com/questions/124611/special-characters-in-samba-filenames
    # https://amigotechnotes.wordpress.com/2015/04/02/invalid-characters-in-file-names/
    PERMITTED_CHARS = "[^\w\-_\. \^&'@\{\}\[\],$=\!-#\(\)%.+~]"
    s = s.replace(u'’', "'") # I like apostrophes, but no smart ones
    s = s.replace(u'?', "") # makes more sense just to remove '?'
    s = re.sub(PERMITTED_CHARS, '_', s)
    return s

def secure_filename(filename):
    if isinstance(filename, bytes):
        from unicodedata import normalize
        filename = normalize('NFKD', filename).encode('ascii', 'ignore')
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
    filename = str(_filename_ascii_strip_re.sub('', '_'.join(
                   filename.split()))).strip('._')

    if os.name == 'nt' and filename and \
       filename.split('.')[0].upper() in _windows_device_files:
        filename = '_' + filename

    return filename
def camel_to_snake(name):
  name  = name.replace(' ','').lower().strip()
  name  = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
  name  = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
  return re.sub(r"\W", "_", name)

def str2bool(v):
  return str(v).lower() in ("yes", "true", "t", "1")
