"""
Send file from local Filesystem to SFTP Server
"""
import os
# import logging
import argparse
import glob
import paramiko
import logging

def main():
  argument = parse_arg()
  logging.getLogger("paramiko").setLevel(logging.WARNING)
  put_files(
      hostname=argument.hostname,
      username=argument.username,
      port=argument.port,
      identity_file=argument.identity_file,
      password=argument.password,
      destination_path=argument.destination_path,
      source_pattern=argument.source_pattern)


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
      "--host",
      "--hostname",
      action="store",
      dest="hostname",
      default="localhost",
      help="SFTP Server Hostname")
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


def put_files(**kwargs):
  """
  Send file to sftp servers. 
  
  parameters:
    hostname (str):
    username (str):
    port (int):
    password (str):
    identity_file (str):
    destination_path (str):
    source_pattern (str):

  return
  """
  hostname = kwargs['hostname']
  username = str(kwargs['username'])
  port = kwargs['port']
  identity_file = kwargs.get('identity_file', None)
  password = kwargs.get('password', None)
  destination_path = kwargs['destination_path']
  source_pattern = kwargs['source_pattern']

  list_local_files = []
  if isinstance(source_pattern,list):
    list_local_files = source_pattern
  else:
    list_local_files = glob.glob(source_pattern)

  sshclient = paramiko.client.SSHClient()
  sshclient.load_system_host_keys()
  sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  if identity_file:
    pkey = paramiko.RSAKey.from_private_key_file(identity_file)
    sshclient.connect(hostname,port,username, pkey=pkey)
  else:
    sshclient.connect(hostname,port,username, password=password)
  sftp = sshclient.open_sftp()

  try:
    sftp.mkdir(destination_path)
  except:
    pass

  for local_file in list_local_files:
    (dir_path, filename) = os.path.split(local_file)
    remotepath = '{}/{}'.format(destination_path, filename)
    sftp.put(local_file, remotepath)

  sftp.close()
  sshclient.close()


if __name__ == '__main__':
  main()
