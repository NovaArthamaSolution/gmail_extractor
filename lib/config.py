import iso8601
import datetime
import os
import jinja2

def parse_date(date) -> datetime:
    return iso8601.parse_date(date)


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

    def __init__(self,config_file,dstart,dend):
        self.config_file: Optional[str] = None
        self.dstart: datetime = None
        self.dend: datetime = None
        self.execution_time: datetime = None
        self.dry_run = self._is_dry_run(get_env_config("DRY_RUN", "false"))
        self.xcom_path = get_env_config("XCOM_PATH", self.DEFAULT_XCOM_PATH)

        self._parse_datetime_vars()
        self._parse_specs_dir()
        self._render()

    def _parse_datetime_vars(self):
        dstart = get_env_config("DSTART", raise_if_empty=True)
        dend = get_env_config("DEND", raise_if_empty=True)
        default_execution_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
        try:
            self.execution_time = parse_date(get_env_config("EXECUTION_TIME", default_execution_time))
            self.dstart = parse_date(dstart)
            self.dend = parse_date(dend)
        except iso8601.ParseError:
            logger.error(
                "dstart/dend/execution-time should be YYYY-mm-dd or date time iso8601 format YYYY-mm-ddTHH:MM:SSZ")
            raise

    def _render(self):
        try:
            with open(config_fullpath) as file_:
                config_template = jinja2.Template(file_.read())
            self.__dict__ = config_template.render(datetime_start=datetime_start, datetime_end=datetime_end, now=datetime.now(), env=os.environ,timedelta=datetime.timedelta )
        except yaml.YAMLError as exc:
            print(exc)


    def _parse_specs_dir(self):
        dir = get_env_config("JOB_DIR", default=self.DEFAULT_JOB_DIR)
        dir = "{}/{}".format(dir, self.JOB_INPUT_SUBDIR)
        for dirpath, _, files in os.walk(dir):
            for filename in files:
                filepath = os.path.join(dirpath, filename)
                if filename == self.CONFIG_FILE_NAME:
                    self.config_file = filepath

    def _is_dry_run(self, input_config) -> bool:
        if input_config.lower() in ["true", "1", "yes", "y"]:
            logger.info("Task is running in dry-run mode")
            return True
        else:
            return False
            
     def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)
