from xlsx2csv import xlsx2csv

def excel_split_sheet(source_file)-> list:
    return xlsx2csv(source_file)


def main():
    fn = sys.argv[1]
    ret = excel_split_sheet(fn)
    print(ret)


if __name__ == '__main__':
    main()
