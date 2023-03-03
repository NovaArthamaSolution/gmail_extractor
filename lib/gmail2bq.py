# from __future__ import print_function
import sys

import os
import yaml
import argparse
import re
from datetime import datetime, timedelta

from glob import glob

from gmail_app import GmailApp
from config import AppConfig
from utils import * 

from local2gcs import put_files as send_gcs_files
from local2sftp import put_files as send_sftp_files
from local2bq import file_to_bq


JOB_DIR=os.getenv('JOB_DIR','/data')
TMP_DIR=os.environ.get('TMP_DIR','/data/out')

def main():
  parsed = parse_arg()
  if parsed.config_fullpath:
    config_fullpath = parsed.config_fullpath
  else:
    config_fullpath = f'{JOB_DIR}/in/config.yaml'
  os.environ['CONFIG_DIRPATH'] = os.path.dirname(config_fullpath) 

  if parsed.datetime_start:
    datetime_start = datetime.fromisoformat(parsed.datetime_start)
  else:
    datetime_start = datetime.now() #- timedelta(days=1)

  if not parsed.datetime_end:
    parsed.datetime_end = datetime_start + timedelta(days=1)
    parsed.datetime_end = parsed.datetime_end.isoformat()

  datetime_end = datetime.fromisoformat(parsed.datetime_end)

  d_start = datetime_start.strftime('%Y-%m-%d')
  d_end = datetime_end.strftime("%Y-%m-%d")

  appconfig = AppConfig(config_fullpath,datetime_start,datetime_end)
  
  print(f"Starting GMAIL Extractor with config file {config_fullpath} for {d_start} and {d_end}")

  ret = gmail2bq( appconfig )
  
  #clean up
  os.system(f'rm -rf {TMP_DIR}*')
  return ret == True 




def gmail2bq(config):

  tmp_local_dir = str(os.environ.get('TMP_DIR', '/data/out')).rstrip('/') 

  try:
    gMailApp = GmailApp(config.token_file)
  except Exception as ex:
    print(f'TOKEN LOGIN FAILED: {ex} \nPlease proceed this link with respectfully account.' )
    gMailApp = GmailApp.login(config.token_file,credentials_file=config.credential_file)

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

      try:
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

      except Exception as ex:
        print(ex)

  else:
    for email in emails:
      attachments = find_attachment(email,config['file_to_extract']['file_pattern'], config['file_to_extract'].get('mime_type',None) ) 
      # fnames = []
      for attachment in attachments:
        fname =  gMailApp.download_attachment(email['id'],attachment) 
        filenames.append(fname)


  if filenames:
    ## ETL
    filenames = process_file_transform(filenames,config['transform'])
    # print(filenames)

    ## SEND THE FILES
    filenames = send_files(filenames,config)

    ## Mark proceesed email 
    processed_label_id = gMailApp.get_processed_label_id()
    if os.getenv('env') != 'TEST_CONFIG' :
      [ gMailApp.mark_label(email['id'],processed_label_id) for email in emails ]
  else:
    if  datetime.now().hour >= config.get('ignore_after',23) : return True
    raise Exception("No expected files  match found from email")      
  
  return True

def process_file_transform(filenames, transform_config):
  etlfnames = []
  transform, = get_udf(transform_config.get('transform_model','').lower())
  if transform:
      
    print(f"\nProcessing file {transform} transformation to {filenames} ")
    for fname in filenames:
      try:
        after_transform = []
        after_transform += transform(fname, **transform_config)

        # keep enforce filename_format for outputfile
        print(transform_config,after_transform)
        for transformed in after_transform:
          rename_params = {'source_file': f"{os.path.splitext(os.path.basename(fname))[0]}_{os.path.splitext(os.path.basename(transformed))[0]}" }
          etlfnames.append( safe_rename(transformed,
                                        transform_config.get('filename_format'), 
                                        rename_params ) ) 
      
      except Exception as ex:
        print(f"Failed to process file transformation {fname} : {transform} : {ex}")
        etlfnames += [fname]

  elif transform_config.get('filename_format'):
    for fname in filenames:
      etlfnames.append( safe_rename(fname,transform_config.get('filename_format'),{}) ) 
  else: 
    etlfnames = filenames

  return etlfnames


def send_files(extracted_files,config):
  channels = config['load_destination']
  if isinstance(channels,dict) :
    channels = [channels]

  protocol = ''
  for channel in channels:
    target_name = channel.get('bucket',None) or channel.get('hostname',None)
    dest_dir = channel.get('dir',channel.get('partition')) 
    # if not target_name : continue 
    tic = time.time()

    protocol = channel.pop('protocol')
    if protocol == 'gcs':
      # if export_gcs == channel['bucket']: continue

      destination_gcs_bucket = channel['bucket']
      send_gcs_files(
        source_pattern=extracted_files,
        bucket=destination_gcs_bucket,
        destination_path=dest_dir,
        )
    elif protocol == 'sftp':
      send_sftp_files(
        source_pattern=extracted_files,
        hostname=channel['hostname'],
        username=channel['username'],
        port=channel['port'],
        identity_file=f"{config.confid_dir}/{channel.get('private_key', None)}",
        password=channel.get('password', None),
        destination_path=dest_dir
        )
    else:
      if '*' in extracted_files or not isinstance(extracted_files,list):
        extracted_files = glob(extracted_files)
      
      table_id = channel.pop('table_id')
      bqconfig = {**channel,**{'schema':f"{config.config_dir}/{channel.pop('schema')}"}}
      for f in extracted_files:
        dest_dir= file_to_bq(f,table_id,**bqconfig)
      target_name = table_id

    toc = time.time()
    print("%.2f seconds elapsed to send %s via %s to %s at %s " % ( (toc-tic), extracted_files,protocol,target_name, dest_dir) )


if __name__ == '__main__':
    try:
      main()
    except KeyboardInterrupt: 
      pass
