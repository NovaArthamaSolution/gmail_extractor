import iso8601
import datetime
import os
import yaml 
import jinja2

def parse_date(date) -> datetime:
    return iso8601.parse_date(date)

def str2bool(input_config) -> bool:
    if input_config.lower() in ["true", "1", "yes", "y"]:
        return True
    else:
        return False

def get_env_config(name, default=None, raise_if_empty=False):
    val = os.environ.get(name, default=default)
    if not raise_if_empty:
        return val
    if val == "" or val is None:
        raise AssertionError("config '{}' must be provided".format(name))
    return val


class AppConfig(dict):
    """generates config from environment variables for app"""

    DEFAULT_XCOM_PATH = "/airflow/xcom/return.json"
    DEFAULT_JOB_DIR = "/data"
    JOB_INPUT_SUBDIR = "in"
    JOB_OUTPUT_SUBDIR = f"{DEFAULT_JOB_DIR}/out"
    QUERY_FILE_NAME = "query.sql"
    CONFIG_FILE_NAME = "config.yaml"

    def __init__(self,config_file,dstart=None,dend=None):
        self.config_file = config_file
        self.dstart = dstart
        self.dend   = dend
        self.execution_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
        self.dry_run = str2bool(get_env_config("DRY_RUN", "false"))
        self.xcom_path = get_env_config("XCOM_PATH", self.DEFAULT_XCOM_PATH)

        os.environ['JOB_DIR'] = os.path.dirname(self.config_file)
        self._parse_datetime_vars()
        self._render()

    def _parse_datetime_vars(self):
        default_execution_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
        try:
            if not self.dstart :
                dstart = get_env_config("DSTART", raise_if_empty=True)
                self.dstart = parse_date(dstart)
            if not self.dend:
                dend = get_env_config("DEND", raise_if_empty=True)
                self.dend = parse_date(dend)
            self.execution_time = parse_date(get_env_config("EXECUTION_TIME", default_execution_time))
        except iso8601.ParseError:
            print("dstart/dend/execution-time should be YYYY-mm-dd or date time iso8601 format YYYY-mm-ddTHH:MM:SSZ")
            raise

    def _render(self):
        try:
            self.config_dir = os.path.dirname((os.path.abspath(self.config_file)))
            with open(self.config_file) as file_:
                config_template = jinja2.Template(file_.read())
            rendered_config = config_template.render(datetime_start=self.dstart, 
                                        datetime_end=self.dend, 
                                        now=datetime.datetime.now(), 
                                        execution_time=self.execution_time, 
                                        env=os.environ,
                                        timedelta=datetime.timedelta )
            self.__dict__  = {** self.__dict__,** yaml.safe_load(rendered_config)}
        except yaml.YAMLError as exc:
            print(exc)
            raise

    @property
    def token_file(self):
        token_file = f"{self.DEFAULT_JOB_DIR}/{self.JOB_INPUT_SUBDIR}/token.json"
        if  os.path.exists(token_file): return token_file
        if self.__dict__.get('account') and self.__dict__.get('account').get('token_file'):
            token_file = self.__dict__.get('account').get('token_file')
        else:
            token_file = get_env_config('GMAIL_TOKEN_FILE',raise_if_empty=False)
        
        if not os.path.isfile(token_file):
            tmp_token_file = f"{self.DEFAULT_JOB_DIR}/{self.JOB_INPUT_SUBDIR}/token.json"
            with open(tmp_token_file,'w') as tmpfile:
                tmpfile.write(token_file)
            token_file = tmp_token_file
        
        return token_file

    @property
    def credential_file(self):
        return os.environ.get('GMAIL_CREDENTIAL_FILE')

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        if key in ['config_file','dstart','dend']:
            return getattr(self,key)
        return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)
