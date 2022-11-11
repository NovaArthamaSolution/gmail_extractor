# GMAIL EXTRACTOR

Tools to extract data from gmail to BQ ( or any file transfer first)  
designed to be used at Financial Reconcialiation Project.  

* extract data file from attachment
* extract url and download data file from body ( targetting using xpath )
* do some file preprosessing ( like unzip or rename to safe filename)
* do some file data transform ( with transform function provided previously)
* do some file post processing
* load data file to bq table (*on progress)
* send data to gcs/BQ/



## Tested Features

* filter emails
* download file from attachment
* download file from url in body
* make email as processed to prevent double processing
* do some transformation to attachment file
* send attachment file to gcs
* send attachment file to sftp
* load csv file to bq
* will call function `<transform>` from `<transform>.py` file ( python lib auto load, `<transform>.py` can be from assets folder)



### How To Use ( Config Only )

Usually, you are gonna create two file to use this library.  

1 Config file in the config file  
2 Table schema file in erd format ( if loaded to BQ)  

> please consult with DWH/BI team about credentials sharing,  don't put any credentials in code base.  




1. Config file
* please add folder for the job name (preferably match to table name)
* create config file ( YAML ) with format: 

as ( this is a sample )

available jinja variables in config.yaml

| variable          | type       | description |
| ----------------  | ---------- | ----------- |
| `datetime_start`  | datetime   | datetime start from input argument, to be formatted as needed |
| `datetime_end`    | datetime   | datetime end from input argument to be formatted as needed |
| `now`             | datetime   | current execution start time of process,  to be formatted as needed |
| `env`             | dictionary | `os.environ` to get ENVIRONMENT VARIABLE , from `bi_appsrc` and .`app.conf` |



```yaml
mail_filter: # entry to filter the emal
  from: <fix sender email address>
  subject: '<subject of email>'   # only the fix part, no need to add * as wildcard.
  after: {{ datetime_start.timestamp()  | int }} ### ussualy linked with daily date time ( we use the integer unix timestamp)
  before: {{ now.timestamp()  | int }}
  
file_to_extract: # configuration to find
  source : url_in_body ## or attachment
  url_xpath: //td/a[contains(text(),'txt')] #

  ## OR if source = attachement :
  file_pattern: <FIX PATTERN>*.zip #file pattern ( mind if there's date on the filename that may changed every day/ or any variable)
  mime_type: application/x-zip-compressed ( mime type of file ( please check on show original menu on gmail app))

transform:
  transform_model:
  filename_format: "{source_file}_{{now.strftime('%y%m%d%H%M%S')}}" # strftime ussualy as file ID {source_filename} is the real source filename


load_destination:
  protocol: sftp|gcs|bq

#FOR SFTP PROTOCOL  
  hostname: <hostname of sftp server>
  username: <username of sftp login>
  port: <custom port for sftp login>
  private_key: <path of sftp private key to login>
  dir: <dir path for destination at server> 


#for GCS protocol
  bucket: <bucketname>
  dir: <dir name in the bucket>

#for BQ protocol, make sure the table already created first.
  project: <project_id of table>
  table_id: <project_id>.<dataset>.<tablename>
  schema: <schema file, usualy schema.erd in the same config folder>
  load_method: <replace/merge>
  partition: <partition_id to use> ## {{date_start.strftime('%Y%m%d)}} or using regex to get date from filename 
  clustering_fields: <list of cluster fields in the table>
  skip_leading_rows: <int | number of header lines in file that need to skipped>

ignore_after: 18
```

| context             | config          | type/validation |Description |
| ------------------------- | --------------- | --------------- |----------- |
| *`mail_filter`*       | `from`          | string/email    |Email Identifier filter from sender email address |
|                     | `subject`       | string/         | Email Identifier filter from email subject      |
|                     | `after`         | int/ unix timestamp |Email Identifier filter by earliest email unix timestamp      |
|                     | `before`        | int/ unix timestamp |Email Identifier filter by last email unix timestamp      |
|                     | `attachment`    | boolean/        |Filter email that have attachment only ( default: False )      |
|   |   |   |   |
| *`file_to_extract`*   | `source`        | `attachment` / `url_in_body`  | source of files that need to acquire      |
|  * `source==attachment` | `file_pattern` | string/file(wildcard) | pattern of files that need to be acquire from attachments |
|  * `source==attachment` | `mime_type` | string/mime_type | Mime Type of file that need to be acquire (`text/csv`, `application/json`) |
|  * `source==url_in_body` | `url_xpath`| string/xpath  | xpath pattern to locate urls in the body content |
|  * `source==url_in_body` | `password_xpath` | string/xpath | xpath pattern to locate files zip password in the body content |
|   |    |   |    |
|`transform`          | `transform_model`     | string/class name | Class name of etl class that will do Transformation |
|                     | `filename_format`| string/python format | String as base of file rename pattern, add `{source_file}` to keep/add the original filename |
|                     | * | dictionary  | any other key dictionary in this will be used for etl model initialization |
|   |   |   |   |
| *`load_destination`*| `protocol`      | string/one of (sft/gcs/bq) | target protocol to data file to be sent | 
| * `protocol==gcs`   | `bucket`        | string/bucket name | target bucket to data file to be sent | 
| * `protocol==gcs`   | `dir`           | string/directory | target directory/path to data file to be sent | 
| * `protocol==sftp`  | `hostname`      | string/(hostname/ip) | target sftp server | 
| * `protocol==sftp`  | `port`          | int/(22)             | port of sftp server opened | 
| * `protocol==sftp`  | `username`      | string/         | username to be used to logging in to sftp server | 
| * `protocol==sftp`  | `password`      | string/password | password to be used to logging in to sftp server | 
| * `protocol==sftp`  | `private_key`   | string/path     | private key to be used to logging in to sftp server | 
| * `protocol==sftp`  | `dir`           | string/path     | target directory/path to data file to be sent in to sftp server | 
| * `protocol==bq`  | `table_id`        | string/table_id | target table id to load to (`<project_id.dataset.table_name>`) | 
| * `protocol==bq`  | `partition`       | string/(dateid/regex)     | date format `YYYYMMDD`, can be loaded from filename with `regex:<pattern to get (\d{8}) >` | 
| * `protocol==bq`  | `replace`         | boolean     | indicate to replace the table/partition or not (default:NOT) | 
| * `protocol==bq`  | `clustering_fields`| string/comma separated name     | argument to pass to bq load parameters  | 
| * `protocol==bq`  | `time_partitioning_type`| string/DAY     | argument to pass to bq load parameters  | 
| * `protocol==bq`  | `time_partitioning_field`| string/field name     | argument to pass to bq load parameters  | 
|   |   |   |   |
| *`ignore_after`*    | | integer/ hour(0-23) |  mark success if code already runnig at this hour and no data/email available, to  mark as last retry | 


2. Schema File  

Usual schema file from BQ table ( created first before first run ) in erd format.  
Used as validation.



### How to contribute ( changes on lib ( and/or ) ETL logic )

* To add capabilities of gmail extractor
1.
2.
3. 


* To add ETL class
1. create class that inherit ETLClass
2. Make sure creating function `perform` with input source filename and returning the result filename ( we work on file based operation) 
3. Add created `class_name` (snake_case) as the value of `transfrom_model` in config
4. TEST,TEST,TEST 
