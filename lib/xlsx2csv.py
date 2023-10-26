#! /usr/bin/python

import os
import xlrd
import csv
import time 
import re
from datetime import datetime


DELIMITER = os.environ.get('DELIMITER','\t')
DATE_FORMAT  = os.environ.get("DATE_FORMAT","%Y-%m-%d")
DATETIME_FORMAT  = os.environ.get("DATETIME_FORMAT","%Y-%m-%dT%H:%M:%S%z")

base_date = datetime(1900, 1, 1).toordinal()
def datevalue(excel_date):
    print(excel_date)
    return datetime.fromordinal(base_date + int(excel_date) - 2 ).strftime(DATETIME_FORMAT)

def camel_to_snake(name):
  name = name.replace(' ','')
  name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name.strip())
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower().replace(' _','_').replace('/_','/')

def snake_to_camel(string):
    string = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
    string = re.sub('(.)([0-9]+)', r'\1\2', string)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', string).lower().replace(' ','').replace('/_','/')


def xlsx2csv(filepath,**config):
    global DELIMITER
    if config.get('delimiter'):
        DELIMITER = config.pop('delimiter')
    def sheet_to_csv(sh):
        
        target_file = config.get('filename_format',filepath)  if config else filepath
        target_file = f"{os.getenv('TMP_DIR','.')}/{target_file}"
        csv_filepath = "%s_%s.%s"  %   (target_file.rsplit('.',1)[0] ,sh.name, 'csv')
        csv_fh = open(csv_filepath, 'w')
        wr = csv.writer(csv_fh, dialect='excel', quoting=csv.QUOTE_NONNUMERIC,delimiter=DELIMITER, lineterminator="\n", strict=True)
        headers = list(map(snake_to_camel, sh.row_values(0)))
        wr.writerow(headers)
        for rownum in range(1,sh.nrows):
            types = sh.row_types(rownum)
            row = sh.row_values(rownum)
            for idx,tipe in enumerate(types):
                if tipe == 1 :
                    row[idx] = str(row[idx]).replace("\n"," ").replace("\t",' ').replace('"','\"')
                if tipe == 2 :
                    row[idx] = round(row[idx])
                if tipe == 3 :
                    row[idx] = xlrd.xldate_as_datetime(row[idx],0).strftime(DATETIME_FORMAT)
                    if row[idx][10:]=='T00:00:00':
                        row[idx] = row[idx][:10]
                    if headers[idx].endswith('_month'):
                        row[idx] = row[idx][:7]
                    if headers[idx].endswith('_year'):
                        row[idx] = row[idx][:4]

            wr.writerow(row)

        csv_fh.close()
        return csv_filepath
    
    wb = xlrd.open_workbook(filepath)
    ret = []
    if config.get('multi','').lower() in ['yes','true','1']:
        for sh in wb.sheets():
            ret.append(sheet_to_csv(sh))
    else:
        sh = wb.sheet_by_index(0)
        ret.append(sheet_to_csv(sh))

    return ret


class ExcelToCsv():

    def perform(self,filename):
        return xlsx2csv(filepath,filename)

if __name__ == '__main__':
    import sys
    filepath = sys.argv[1]
    tic = time.time()
    print(xlsx2csv(filepath))
    toc = time.time() - tic
    print("elapsed %f" % toc)
