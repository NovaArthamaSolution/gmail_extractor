#!/usr/bin/python

import sys
import os
import logging
import argparse
import glob
import re
import json
import ndjson

import datetime
from google.cloud import storage
from google.cloud import bigquery
from xlsx2csv import DELIMITER

from utils import *

def main():
  logging.getLogger("local2bq").setLevel(logging.WARNING)

  argument = parse_arg()
  file_path = argument.file
  table_id = argument.table
  del argument.file
  del argument.table
  
  params = argument.params
  params = list(map(lambda l:{l[0]:l[1]}, map(lambda p: p.split("="), params )))
  params = dict((key,d[key]) for d in params for key in d)

  del argument.params
 
  arguments = vars(argument)  
  params['dataframe'] = {'sep': ";" }
  file_to_bq(file_path,table_id,**params)


def file_to_bq(file_path,table_id,*args,**kwargs):
        
    try:
        # print(args,kwargs)
        schema_file = kwargs.pop('schema') 
        # if os.path.exists(schema_file ):
        #     raise Exception(f'Cannot load table {table_id} without schema file')

        fmt = kwargs.get('format','csv') 
        schema, dtypes = load_schema(schema_file)

        if fmt.lower() == 'json' :
            return json_to_bq(file_path,table_id,schema=schema,**kwargs)
        else:
            return csv_to_bq(file_path,table_id,schema=schema,**kwargs)

    except Exception as ex:
        print("error file_to_bq %s" % ex)
        raise

def csv_to_bq(file_path, table_id, schema=None,*args,**kwargs):
    return load_to_bq(file_path,table_id,bigquery.SourceFormat.CSV, schema,**kwargs)

def json_to_bq(file_path, table_id, schema=None,*args,**kwargs):
    basename, ext = os.path.splitext(file_path)
    if ext == '.ndjson':
        file_to_load = file_path
    else:
        file_to_load = f"{basename}.ndjson"
        with open(file_path,'r') as source, open(file_to_load,'w') as dest:
            data = json.load(source)
            ndjson.dump(data,dest)

    return load_to_bq(file_to_load,table_id,bigquery.SourceFormat.NEWLINE_DELIMITED_JSON, schema,**kwargs)

def load_to_bq(file_to_load, table_id, source_format,schema=None,*args,**kwargs):

    job_config = bigquery.LoadJobConfig(source_format=source_format)

    if kwargs.get('dataset') and  kwargs.get('dataset') not in table_id:
        table_id = f"{kwargs.get('dataset')}.{table_id}"

    if kwargs.get('project') and  kwargs.get('project') not in table_id:
        table_id = f"{kwargs.get('project')}.{table_id}"

    if kwargs.get('field_delimiter',None):
        job_config.field_delimiter = r"\t" if kwargs.get('field_delimiter')== 'tab' else kwargs.get('field_delimiter', DELIMITER)

    if kwargs.get('skip_leading_rows',None):
        job_config.skip_leading_rows = int(kwargs.get('skip_leading_rows')) or 0
    # else:
    #     job_config.skip_leading_rows = 1

    if kwargs.get('allow_quoted_newlines',None):
        job_config.allow_quoted_newlines = bool(kwargs.get('allow_quoted_newlines')) or true
    # else:
    #     job_config.allow_quoted_newlines = true

    if kwargs.get('ignore_unknown_values',None):
        job_config.ignore_unknown_values = bool(kwargs.get('ignore_unknown_values')) or true
    # else:
    #     job_config.ignore_unknown_values = true


    if kwargs.get('ignore_unknown_values',None):
        job_config.ignore_unknown_values = bool(kwargs.get('ignore_unknown_values')) or true
    # else:
    #     job_config.ignore_unknown_values = true

    if kwargs.get('null_marker',None):
        job_config.null_marker = kwargs.get('null_marker') or ''

    if kwargs.get('quote_character',None):
        job_config.quote_character = kwargs.get('quote_character') or '"'

    if kwargs.get('allow_jagged_rows',None):
        job_config.allow_jagged_rows = bool(kwargs.get('allow_jagged_rows')) or true


    partition_test = re.compile(r"\$(\d{8})$")
    if kwargs.get('partition',None) and not bool(partition_test.search(table_id)):
        partition=kwargs.get('dtstart')
        kwargs['time_partitioning_type'] = 'DAY'
        try:
            if str(kwargs['partition']).isnumeric() and len(str(kwargs['partition']))==8:
                partition=kwargs['partition']
                table_id = f'{table_id}${partition}'
            elif 'regex' in kwargs['partition']:
                expr = kwargs['partition'][6:]
                expr = re.compile(expr)
                partition = expr.search(file_to_load).group(1)
                table_id = f'{table_id}${partition}'
            else: ##
                kwargs.set('time_partitioning_field',kwargs.get('partition'))

        except Exception as ex:
            print(ex)
            partition=kwargs.get('dtstart') or datetime.now().strftime("%Y%m%d")
        

    job_config.autodetect=True
    if schema :
        job_config.schema = schema
        job_config.autodetect = None

    if kwargs.get('clustering_fields',None) :
        job_config.clustering_fields = kwargs['clustering_fields'].split(',')

    job_config.write_disposition = 'WRITE_APPEND'
    if kwargs.get('load_method').lower() == 'replace':
        job_config.write_disposition = 'WRITE_TRUNCATE'         

    if kwargs.get('time_partitioning_type',None) : 
        job_config.time_partitioning = bigquery.TimePartitioning(type_= kwargs['time_partitioning_type'].upper() )
    
    if kwargs.get('time_partitioning_field',None):
        job_config.time_partitioning_field = kwargs.get('time_partitioning_field')

    bqclient = bigquery.Client()
    try:
        job = bqclient.load_table_from_file(open(file_to_load,'rb'),
                    table_id,
                    job_config=job_config,
                )
        logging.info(f"Running on job Id {job}")
        job.result()
        logging.info(f"successfully insert data to table {table_id} finished")
        return partition
    except Exception as err:
        logging.error("Error happens when attempt to insert data to bq")
        logging.error("{err}".format(err=err))
        return None



def parse_arg():
  parser = argparse.ArgumentParser(
      description="Load Localfile to")
  parser.add_argument("-s","--schema", help="schema file of the table for validation",required=False)
  parser.add_argument("file", help="File to load to the table")
  parser.add_argument("table", help="table to be loaded into")
  parser.add_argument("params", nargs='*', help="additional parameter for bq command")
  return parser.parse_args()


def load_schema(schema_file):
    fields = [] 
    dtypes = {}
    schema = None
    if not os.path.exists(schema_file):
        schema_file = os.path.join(os.environ.get('CONFIG_DIRPATH','assets'),schema_file)

    with open(schema_file,'r') as f:
        schema = json.load(f)
    
    for field in schema:
        if field['type'] == 'FLOAT':
            dtypes[field['name']] = float
        elif field['type'] == 'INTEGER':
            dtypes[field['name']] = int
        elif field['type'] == 'BOOLEAN':
            dtypes[field['name']] = bool
        elif field['type'] == 'DATE':
            dtypes[field['name']] = datetime.date
        elif field['type'] == 'DATETIME':
            dtypes[field['name']] = datetime
        else: 
            dtypes[field['name']] = str 

        fields.append(bigquery.SchemaField(field['name'],field['type'],field.get('mode','NULLABLE')))

    return fields, dtypes

  
if __name__ == "__main__":
    main()
