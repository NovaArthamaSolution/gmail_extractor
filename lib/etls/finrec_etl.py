
# from .excel_split_sheet import ExcelSplitSheet 
import re 
import os 

class FinrectETL(object):
    def __init__(self, source_file):
        self.source_file = source_file

    def perform(self,filename) -> list:
        return [filename]

class ExcelSplitSheet(FinrectETL):    
    def perform(self) -> list:
        return xlsx2csv(self.source_file,multi=True)


        # with open(self.source_file) as src:
        #     pass

        

def get_etl_class(etl_name,kwargs):
    print(etl_name,kwargs)
    return ExcelSplitSheet(kwargs)
