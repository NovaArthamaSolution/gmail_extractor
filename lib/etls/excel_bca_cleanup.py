
from .finrec_etl import FinrectETL

class ExcelBCACleanup(FinrectETL):

    def __init__(self, source_file: str):
        self.source_file = source_file
    
    def perform(self) -> list:
        return self.source_file