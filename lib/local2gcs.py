"""
Send file from local Filesystem to SFTP Server
"""
import os
import logging
import argparse
import glob
from google.cloud import storage


def main():
  argument = parse_arg()
  logging.getLogger("local2gcs").setLevel(logging.WARNING)
  put_files(
      bucket=argument.gcs_bucket_name,
      source_pattern=argument.source_pattern,
      destination_path=argument.destination_path)


def parse_arg():
  parser = argparse.ArgumentParser(
      description="Sending file from local to SFTP")
  parser.add_argument(
      "-u",
      "--username",
      action="store",
      dest="username",
      default="gojek",
      help="SFTP Username")
  parser.add_argument(
      "-p", "--password", action="store", dest="password", help="SFTP Password")
  parser.add_argument(
      "-i",
      "--identity-file",
      action="store",
      dest="identity_file",
      help="Identity File")
  parser.add_argument(
      "--port",
      action="store",
      dest="port",
      type=int,
      default=22,
      help="SFTP Port")
  parser.add_argument(
      "--bucket",
      "--bucket_name",
      action="store",
      dest="gcs_bucket_name",
      default="bi_playground_eoch7goo",
      help="GCS Bucket Name")
  parser.add_argument(
      "--source-pattern",
      action="store",
      dest="source_pattern",
      help="Pattern of source Files")
  parser.add_argument(
      "--dir-destination",
      "--dest",
      "--destination",
      "--dir-dest",
      action="store",
      dest="destination_path",
      default="./",
      help="Destination Directory")

  result = parser.parse_args()

  return result


def put_files(source_pattern='/tmp/*.csv', bucket='bi_playground_eoch7goo',destination_path='access_fat/sap_interface'):
  """
  Send file to sftp servers. 
  
  parameters:
    bucket (str):
    destination_path (str):
    source_pattern (str):

  return
  """

  storage_client = storage.Client()
  bucket = storage_client.get_bucket(bucket)
  # print(source_pattern)
  # list_local_files = glob.glob(source_pattern)
  for local_file in source_pattern:
    (dir_path, filename) = os.path.split(local_file)
    remotepath = 'gs://{}/{}/{}'.format(bucket,destination_path, filename)
    blob = bucket.blob('{}/{}'.format(destination_path,filename))
    blob.upload_from_filename(local_file)
    # os.system("gsutil cp {}  {}".format(local_file, remotepath) )
    



if __name__ == '__main__':
  main()
