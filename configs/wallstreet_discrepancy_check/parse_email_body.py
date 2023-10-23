
from lxml import etree
from lxml.etree import HTMLParser  
parser = HTMLParser()



def parse_email_body(eml_file,**kwargs):
  xpath = '//div/p'
  htmlparser = HTMLParser()
  doc = etree.parse(eml_file,parser=htmlparser)
  unmatchlines = []
  try:
      els = doc.xpath(xpath)
      # el =  els.pop()
      for el in els:
        if 'NOT FOUND' not in el.text: continue 
        # print(el.text)
        unmatchlines.append(el.text.strip())
      # if '()' not in attribute:
      #     return el.get(attribute).strip()
      # else:
      # return els.text.strip()
      return unmatchlines 
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