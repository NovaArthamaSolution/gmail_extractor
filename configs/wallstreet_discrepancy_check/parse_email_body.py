
from lxml import etree
from lxml.etree import HTMLParser  
parser = HTMLParser()
import re
import os
import csv

TIMESTAMP_RE = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')

def save_to_file(discrepancies,output_file):
  header= list(discrepancies[0].keys())
  with open(output_file,'w',encoding='UTF-8') as out:
    writer = csv.DictWriter(out,fieldnames=header, delimiter='\t')
    writer.writeheader()
    writer.writerows(discrepancies)
  return output_file

def parse_email_body(eml_file,**kwargs):
  xpath = '//div/p'
  htmlparser = HTMLParser()
  doc = etree.parse(eml_file,parser=htmlparser)
  discrepancies = []
  try:

    unmatch_date_el = doc.xpath('//div/p[contains(text(),"with result")]')
    checking_time, unmatch_date = unmatch_date_el[0].text.split('result:')
    checking_time = TIMESTAMP_RE.search(checking_time.strip())

    if checking_time:
      checking_time = checking_time[0]
    else:
      checking_time = os.getenv('DSTART')

    unmatch_date = TIMESTAMP_RE.search(unmatch_date.strip())
    if unmatch_date:
      unmatch_date = unmatch_date[0]
    else:
      unmatch_date = os.getenv('DSTART')

    els = doc.xpath(xpath)
    unmatchlines = []
    for el in els:
      if 'NOT FOUND' not in el.text: continue       
      unmatchlines.append(el.text.strip())

    for ul in unmatchlines:
      source, ids = ul.split(':')
      source = source.strip()[15:]

      ids = ids.strip().split(',')
      for id in ids:
        discrepancy = {'checking_timestamp': checking_time, 'unmatched_timestamp': unmatch_date, 'discrepancy_description': source}
        discrepancy['transaction_id'] = id.strip()
        discrepancies.append(discrepancy)
    return save_to_file(discrepancies,f"{os.getenv('JOB_OUTPUT_SUBDIR','/data/out')}/{kwargs.get('filename_format')}.csv")
  
  except Exception as ex:
      print(f"Ex:{ex}")
      return None
   


def main(eml_file):
  lines = parse_email_body(eml_file)
  print(lines)

if __name__ == '__main__':
  import sys
  eml_file =  sys.argv[1]
  main(eml_file)