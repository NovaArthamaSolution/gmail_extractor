#! /usr/bin/python3
import argparse
import logging
import sys
import yaml
import os 
try:
    from yaml import CFullLoader as Loader
except ImportError:
    from yaml import FullLoader as Loader

from cerberus import Validator
from distutils.util import strtobool
from pathlib import Path
import jinja2
from datetime import datetime, timedelta
from pprint import pprint

class CustomValidator(Validator):
    def __init__(self, *args, **kwargs):
        self.path_to_document = kwargs.get('path_to_document')
        super(CustomValidator, self).__init__(*args, **kwargs)

    def _validate_value_must_match_filename(self, value_must_match_filename, field, value):
        """ Test that the value of the field matches the given filename.
        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        filename = Path(self.path_to_document).stem
        matches = filename == value
        if value_must_match_filename and not matches:
            self._error(field, f"\"{value}\" does not match the filename \"{filename}\" at \"{self.path_to_document}\"")


def _load_yaml_document(path):
    with open(path, 'r') as stream:
        try:
            return yaml.load(stream, Loader=Loader)
        except yaml.YAMLError as exception:
            raise exception

def render_config(template_file):
# cleanup(tmp_local_dir)
  with open(template_file) as file_:
    config_template = jinja2.Template(file_.read())

  datetime_end = datetime.today()
  datetime_start= datetime_end - timedelta(days=1)
  config_rendered = config_template.render(datetime_start=datetime_start, 
        datetime_end=datetime_end, 
        now=datetime.now(),
        env=os.environ,
        timedelta=timedelta)
  
  return yaml.load(config_rendered,Loader=Loader)

def _validate_single(validator, document_path, validate_file_extension):
    if document_path.suffix not in [".yml", ".yaml"]:
        if validate_file_extension and not document_path.is_dir():
            logging.error(f"❌\t'{document_path}' does not have a file extension matching [.yml, .yaml].")
            return False
        return None

    
    try:
        document = render_config(document_path)    
        valid = validator.validate(document)        

        if not valid:
            logging.error(f"❌\t'{document_path}'")
            logging.error(f"\n{yaml.dump(validator.errors, default_flow_style=False)}")
    except Exception as ex :
        valid = False
        logging.error(f"❌\t'{document_path}'")
        logging.error(f"❌\t{ex.__class__.__name__} : '{ex}'")
        logging.error(f"\n{yaml.dump(validator.errors, default_flow_style=False)}")

    return valid


def _validate_path(root, schema_path, document_paths, validate_file_extension):
    schema = _load_yaml_document(schema_path)
    validator = Validator(schema)

    results = [
        (path.relative_to('./'), _validate_single(validator, path.relative_to('./'), validate_file_extension))
        for path in document_paths
    ]
    results = list(filter(lambda x: x[1] is not None, results))

    total_count = len(results)

    if any(not is_valid for (_, is_valid) in results):
        invalid_count = len([(path, is_valid) for (path, is_valid) in results if not is_valid])
        logging.error(f"{invalid_count} of {total_count} document(s) in '{root}' failed to validate:")
        [logging.error(f'❌\t{path}') for (path, is_valid) in results if not is_valid]
        sys.exit(1)
    else:
        logging.info(f"✅\t{total_count} of {total_count} documents in '{root}' are valid!")


def _process(schema_path, document_path, validate_file_extension):
    logging.info(f"😘\tValidating '{document_path}' against schema '{schema_path}'...")

    root = Path(document_path).relative_to('./')
    paths = Path('.').glob(document_path)

    if Path(document_path).is_dir():
        if not document_path.endswith('/'):
            document_path = document_path + '/'
        paths = Path('.').glob(document_path + '**/*')

    _validate_path(root, schema_path, paths, validate_file_extension)


def main():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)-6s %(message)s")
    parser = argparse.ArgumentParser(description='YAML validator')
    parser.add_argument("schema_path", help="Path to the YAML schema to validate against")
    parser.add_argument("document_path", help="Path to the YAML document or directory of documents to be validated. "
                                              "Accepts globs. Defaults to recursive search if only a directory is "
                                              "provided.")
    # parser.add_argument("validate_file_extension",
    #                     default="false",
    #                     help="Validate that all the given documents have a valid YAML file extension")
    args = parser.parse_args()
    schema_path = args.schema_path
    document_path = args.document_path
    validate_file_extension = False

    _process(schema_path, document_path, validate_file_extension)


if __name__ == "__main__":
    main()