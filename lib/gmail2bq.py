# from __future__ import print_function
import sys

import os
import yaml
import argparse
import re
from datetime import datetime, timedelta
import jinja2

from glob import glob

from gmail_app import GmailApp
from util import * 

from local2gcs import put_files as send_gcs_files
from local2sftp import put_files as send_sftp_files
from local2bq import file_to_bq


JOB_DIR=os.getenv('JOB_DIR','/data')

def main():
  parser = parse_arg()
  if parser.config_fullpath:
    config_fullpath = parser.config_fullpath
  else:
    config_fullpath = f'{JOB_DIR}/in/config.yaml'
  os.environ['CONFIG_DIRPATH'] = os.path.dirname(config_fullpath)  


  if parser.datetime_start is not None:
    datetime_start = datetime.fromisoformat(parser.datetime_start)
  else:
    datetime_start = datetime.now() #- timedelta(days=1)

  if parser.datetime_end is None:
    parser.datetime_end = datetime_start + timedelta(days=1)
    parser.datetime_end = parser.datetime_end.isoformat()
    # parser.datetime_end = "%sT%s" % ( datetime_start.strftime('%Y-%m-%d') , datetime.now().strftime("%H:%M:%S") )

  datetime_end = datetime.fromisoformat(parser.datetime_end)

  d_start = datetime_start.strftime('%Y%m%d')
  d_end = datetime_end.strftime("%Y%m%d")

  with open(config_fullpath) as file_:
    config_template = jinja2.Template(file_.read())

  config_rendered = config_template.render(datetime_start=datetime_start, datetime_end=datetime_end, now=datetime.now(), env=os.environ )
  configurations = None
  try:
    configurations = yaml.safe_load(config_rendered)
  except yaml.YAMLError as exc:
    print(exc)


  print(f"Starting GMAIL Extractor with config file {config_fullpath} for {d_start}")
  print(f"Config:\n{config_rendered}")

  return gmail_extract( configurations )



def gmail_extract(config):
  home = os.path.expanduser("~")

  token_file = os.environ.get('GMAIL_TOKEN_FILE','')
  if config.get('account') and config.get('account').get('token_file'):
    token_file = config.get('account').get('token_file')

  if not os.path.isfile(token_file):
      tmp_token_file = f"{JOB_DIR}/token.json"
      with open(tmp_token_file,'w') as tmpfile:
          tmpfile.write(token_file)
      token_file = tmp_token_file
      
  creds_file = os.environ.get('GMAIL_CREDENTIAL_FILE')
  
  tmp_local_dir = str(os.environ.get('TMP_DIR', '/data/out')).rstrip('/') 

  try:
    gMailApp = GmailApp(token_file)
  except:
    print('TOKEN LOGIN FAILED: Please proceed this link with respectfully account')
    gMailApp = GmailApp.login(token_file,credentials_file=creds_file)

  emails = gMailApp.get_emails( from_=config['mail_filter'].get('from'),
                                subject=config['mail_filter'].get('subject'),
                                after=config['mail_filter'].get('after'),
                                before=config['mail_filter'].get('before'),
                                attachment=config['mail_filter'].get('attachment'),
                                save_body= config['file_to_extract'].get('source') != 'attachment' )

  # print(" Matched emails: %d " % len(emails) )
  ## GET THE FILES
  filenames = []
  if config['file_to_extract'].get('source') == 'url_in_body':
    for email in emails:
      working_dir = os.path.join(tmp_local_dir,email['id'])
      mail_body_file = os.path.join(working_dir,'body.eml')

      # try:
      url_xpath = config['file_to_extract']['url_xpath']
      urls = extract_urls_xmlfile(mail_body_file, url_xpath)
      for idx,file_url in enumerate(urls): 
        downloaded_file = download_file(file_url, working_dir)
        filenames.append(downloaded_file)

      if config['file_to_extract'].get('password_xpath'):
        password_xpath = config['file_to_extract']['password_xpath']
        password = extract_string_xmlfile(mail_body_file,password_xpath,'text()')
        if password:
          config['transform']['zip_password'] = password

      # except Exception as ex:
      #   print(ex)

  else:
    for email in emails:
      attachments = find_attachment(email,config['file_to_extract']['file_pattern'], config['file_to_extract'].get('mime_type',None) ) 
      # fnames = []
      for attachment in attachments:
        fname =  gMailApp.download_attachement(email['id'],attachment) 
        filenames.append(fname)


  if filenames:
    ## ETL
    filenames = process_file_transform(config['transform'],filenames)
    # print(filenames)

    ## SEND THE FILES
    filenames = send_files(filenames,config['load_destination'])

    ## Mark proceesed email 
    processed_label_id = gMailApp.get_processed_label_id()
    if os.getenv('env') != 'TEST_CONFIG' :
      [ gMailApp.mark_label(email['id'],processed_label_id) for email in emails ]
  else:
    if  datetime.now().hour >= config.get('ignore_after',23) : return True
    raise Exception("No expected files  match found from email")      
  
  return True

def process_file_transform(transform_config, filenames):
  etlfnames = []
  if transform_config.get('transform_model'):
    import importlib.util

    transformation = transform_config.get('transform_model')
  
    try:
      libdir = os.path.dirname(__file__)
      spec = importlib.util.spec_from_file_location(transformation, f"{libdir}/{transformation}.py")
      transform = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(transform)
    except FileNotFoundError as ex:
      spec = importlib.util.spec_from_file_location(transformation, f"{os.getenv('CONFIG_DIRPATH')}/{transformation}.py")
      transform = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(transform)

    print(f"\nProcessing file {transformation} transformation to {filenames} ")
    for fname in filenames:
      try:
        if '{source_file}' in transform_config.get('filename_format',''):
          transform_config['filename_format'] = transform_config.get('filename_format').format(**{'source_file': os.path.basename(fname)})

        etlfnames += getattr(transform,transformation)(fname, transform_config)
      
      except Exception as ex:
        print(f"Failed to process file transformation {fname} : {transformation} : {ex}")
        etlfnames += [fname]

  elif transform_config.get('filename_format'):
    for fname in filenames:
      etlfnames.append( safe_rename(fname,transform_config.get('filename_format'),{}) ) 
  else: 
    etlfnames = filenames

  return etlfnames


def send_files(extracted_file,channels):

  if isinstance(channels,dict) :
    channels = [channels]

  protocol = ''
  for channel in channels:
    target_name = channel.get('bucket',None) or channel.get('hostname',None)
    dest_dir = channel.get('dir',False) 
    # if not target_name : continue 
    tic = time.time()

    protocol = channel.pop('protocol')
    if protocol == 'gcs':
      # if export_gcs == channel['bucket']: continue

      destination_gcs_bucket = channel['bucket']
      send_gcs_files(
        source_pattern=extracted_file,
        bucket=destination_gcs_bucket,
        destination_path=dest_dir,
        )
    elif protocol == 'sftp':
      send_sftp_files(
        source_pattern=extracted_file,
        hostname=channel['hostname'],
        username=channel['username'],
        port=channel['port'],
        identity_file=channel.get('private_key', None),
        password=channel.get('password', None),
        destination_path=dest_dir
        )
    else:
      extracted_files = extracted_file
      if '*' in extracted_file or not isinstance(extracted_file,list):
        extracted_files = glob(extracted_file)
      
      table_id = channel.pop('table_id')
      for f in extracted_files:
        dest_dir= file_to_bq(f,table_id,**channel)
      target_name = table_id

    toc = time.time()
    print("%.2f seconds elapsed to send %s via %s to %s at %s " % ( (toc-tic), extracted_file,protocol,target_name, dest_dir) )


if __name__ == '__main__':
    try:
      main()
    except KeyboardInterrupt: 
      pass
