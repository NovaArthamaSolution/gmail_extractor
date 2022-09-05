
from .finrec_etl import FinrectETL
from .xlsx2csv import xlsx2csv

class ExcelSplitSheet(FinrectETL):

    def __init__(self):
        self.source_file = source_file
    
    def perform(self,source_file) -> list:
        return xlsx2csv(source_file)
