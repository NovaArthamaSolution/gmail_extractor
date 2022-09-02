#! /usr/bin/python

import os, sys, re
import importlib
from etls import xlsx2csv
# from etls import * 
etls_path = '/opt/gmail_extractor/lib/etls'

from util import *

class ETL():
    CLASSES = {}
    def __init__(self,**params):
        self.__dict__.update(params)
    
    def __str__(self):
        return str(self.__dict__)

    @staticmethod
    def add_model(model,cls):
        ETL.CLASSES.update({model:cls})

    @staticmethod
    def get_model(model,params={}):
        # print (ETL.CLASSES)
        try:
            # module_file = os.path.join(etls_path, model +'.py' )
            # print(module_file, os.path.exists(module_file))    
            # etl_module = __import__(module_file)
            # etl_model = getattr(etl_module,model)
            # print(etl_module)
            ETLClass = ETL.CLASSES[model]
            etl = ETLClass(**params)
            # print(etl,ETLClass)
            return etl
        except Exception as ex :
            print("error etl:%s" % ex)
            return FinrectETL(**params)



class FinrectETL(ETL):
    filename_format="TMXXXX_DSXXXX_{source_file}"
    def __init__(self,**params):
        self.__dict__.update(params)

    def perform(self,filename,params={}):
        print(self.filename_format)
        path = os.path.dirname(filename)
        basename= os.path.basename(filename)
        params['source_file'] = basename
        newfn = self.filename_format.format(**params)
        newfn = os.path.join(path,newfn)
        print(newfn)
        os.rename(filename,newfn)
        return [newfn]

ETL.add_model('finrec',FinrectETL)

class MKMRemoveVersion(ETL):       
    def perform(self,fn,params={}):
        try:
            path = os.path.dirname(fn)
            basename = os.path.basename(fn)[::-1]
            basename = re.sub(r'\.\d_','.',basename,1)[::-1]
            params['source_file'] = basename
            params['file_date'] = basename[10:18]
            newfn = self.filename_format.format(**params)
            newfn = os.path.join(path, newfn )
            os.rename(fn,newfn)
            return [newfn]
        except Exception as ex:
            print(ex)
            return [fn]


ETL.add_model('mkm_remove_version',MKMRemoveVersion)


class ExcelSplitSheet(FinrectETL):

    def perform(self,source_file,**params) -> list:
        ## ACTUAL REQUIREMENT
        res = []
        source_files = unzip(source_file)
        for f in source_files:
            res += xlsx2csv.xlsx2csv(f,True)    

        ## URUSAN ATURAN FILENAME
        ret = []
        for fn in res:
            path = os.path.dirname(fn)
            basename = os.path.basename(fn)[::-1]
            basename = re.sub(r'\.\d_','.',basename,1)[::-1]
            params['source_file'] = basename
            params['file_date'] = basename[18:26]
            newfn = self.filename_format.format(**params)
            newfn = secure_filename(newfn)
            newfn = os.path.join(path, newfn )
            os.rename(fn,newfn)
            ret += [newfn]

        return ret

ETL.add_model('excel_split_sheet',ExcelSplitSheet)


class RPTCleaner(FinrectETL):
    def perform(self,source_file,**params) -> list:
        tmpfile,ext = os.path.splitext(source_file)

        if ext == 'zip':
            source_file = unzip(source_file).pop()
        else:
            tmpfile += '.tsv'

        expr = re.compile(r'^\d{6}.*')
        with open(source_file, mode='r',errors='replace') as in_file, open(tmpfile, mode='w') as out_file:
            for inline in in_file.readlines():
                if expr.match(inline):
                    out_file.write(inline)
        
        path = os.path.dirname(tmpfile)
        basename = os.path.basename(tmpfile)[::-1]
        basename = re.sub(r'\.\d_','.',basename,1)[::-1]
        params['source_file'] = basename
        params['file_date'] = basename[29:39].replace("-",'')
        newfn = self.filename_format.format(**params)
        newfn = secure_filename(newfn)
        newfn = os.path.join(path, newfn )
        os.rename(tmpfile,newfn)
        
        return [newfn]


ETL.add_model('rpt_cleaner',RPTCleaner)
