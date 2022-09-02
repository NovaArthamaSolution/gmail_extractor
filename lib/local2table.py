#!/usr/bin/python

import sys
import os
import logging
import argparse
import glob
from google.cloud import storage


def main():
  argument = parse_arg()
  logging.getLogger("local2table").setLevel(logging.WARNING)
  print(argument)

def parse_arg():
  parser = argparse.ArgumentParser(
      description="Sending file from local to SFTP")
  parser.add_argument("-s","--schema", "schema of the table for validation")
  parser.add_argument("file", "File to load to the table")
  parser.add_argument("table", "table to be loaded into")
  parser.add_argument("params", "additional parameter for bq command")


def load_to_table(source_file,dest_table,**kwargs):
    pass





  
if __name__ == "__main__":
    main()