import os
import re


def rpt_cleaner(source_file) -> list:
    tmpfile,ext = os.path.splitext(source_file)
    tmpfile += '.tsv'

    expr = re.compile(r'^\d{6}.*')
    with open(source_file, mode='r') as in_file, open(tmpfile, mode='w') as out_file:
        for inline in in_file.readlines():
            if expr.match(inline):
                out_file.write(inline)
    
    return [tmpfile]



def main():
    fn = sys.argv[1]
    ret = rpt_cleaner(fn)
    print(ret)


if __name__ == '__main__':
    main()
