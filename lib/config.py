import iso8601
import datetime
import os


def parse_date(date) -> datetime:
    return iso8601.parse_date(date)


def get_env_config(name, default=None, raise_if_empty=False):
    val = os.environ.get(name, default=default)
    if not raise_if_empty:
        return val
    if val == "" or val is None:
        raise AssertionError("config '{}' must be provided".format(name))
    return val


class AppConfig:
    """generates config from environment variables for app"""

    DEFAULT_XCOM_PATH = "/airflow/xcom/return.json"
    DEFAULT_JOB_DIR = "/data"
    JOB_INPUT_SUBDIR = "in"
    JOB_OUTPUT_SUBDIR = f"{DEFAULT_JOB_DIR}/out"
    QUERY_FILE_NAME = "query.sql"
    CONFIG_FILE_NAME = "config.yaml"

    def __init__(self):
        self.sql_file: Optional[str] = None
        self.config_file: Optional[str] = None
        self.dstart: datetime = None
        self.dend: datetime = None
        self.execution_time: datetime = None
        self.dry_run = self._is_dry_run(get_env_config("DRY_RUN", "false"))
        self.xcom_path = get_env_config("XCOM_PATH", self.DEFAULT_XCOM_PATH)

        self._parse_datetime_vars()
        self._parse_specs_dir()

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

    def _parse_specs_dir(self):
        dir = get_env_config("JOB_DIR", default=self.DEFAULT_JOB_DIR)
        dir = "{}/{}".format(dir, self.JOB_INPUT_SUBDIR)
        for dirpath, _, files in os.walk(dir):
            for filename in files:
                filepath = os.path.join(dirpath, filename)
                if filename == self.QUERY_FILE_NAME:
                    self.sql_file = filepath
                if filename == self.CONFIG_FILE_NAME:
                    self.config_file = filepath

    def _is_dry_run(self, input_config) -> bool:
        if input_config.lower() in ["true", "1", "yes", "y"]:
            logger.info("Task is running in dry-run mode")
            return True
        else:
            return False
