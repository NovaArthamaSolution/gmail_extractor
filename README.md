# GMAIL EXTRACTOR

## Introduction

This project provides a set of tools designed to extract data from various sources, primarily focusing on Gmail, and load it into destinations like BigQuery, Google Cloud Storage (GCS), or SFTP servers. It streamlines the process of fetching data, filtering it, performing transformations, and delivering it to the required destination. This makes it particularly useful for tasks like automated financial reconciliation, report aggregation, and data pipeline integration.

Key Features:

*   **Data Extraction:**
    *   Extract data files from email attachments.
    *   Extract URLs from email bodies (using XPath for targeting) and download the linked data.
*   **Filtering:**
    *   Filter emails based on sender, subject, and date ranges to process only relevant messages.
*   **Preprocessing & Transformation:**
    *   Perform file preprocessing tasks like unzipping archives or renaming files to safe, consistent filenames.
    *   Apply custom data transformations using Python classes, allowing for flexible data manipulation.
*   **Multiple Destinations:**
    *   Load data directly into BigQuery tables.
    *   Send data files to Google Cloud Storage (GCS) buckets.
    *   Transfer data files via SFTP to specified servers.
*   **Processing Management:**
    *   Mark emails as processed (e.g., by applying a label) to prevent duplicate handling in subsequent runs.
    *   Dynamically call custom transformation functions/classes based on job configuration.

## Installation

*(Detailed installation instructions will be added here. Currently, the project is typically deployed as a set of scripts and configurations.)*

> **Important:** Please consult with your Data Warehouse (DWH) or Business Intelligence (BI) team regarding credentials management and security best practices. **Do not embed any plain text credentials directly in the codebase or configuration files.** Use environment variables or a secure secret management system.

## Usage

*(Detailed usage instructions, including command-line examples and operational guidance, will be added here. The primary way to use this library is by setting up YAML configuration files for specific extraction jobs and then executing the main script.)*

### Project Components

This project is organized into several key scripts and directories:

*   **`bin/gmail2bq`**: This is the main executable script responsible for initiating the data extraction process. It parses command-line arguments, reads the specified job configuration, and orchestrates the extraction, transformation, and loading tasks using the `lib/gmail2bq.py` library.
*   **`lib/gmail2bq.py`**: This Python library contains the core logic for the Gmail extraction and data processing workflow. It handles tasks such as connecting to Gmail, applying filters to select emails, downloading attachments or files from URLs, executing transformations, and loading data to the configured destination (BigQuery, GCS, SFTP).
*   **`configs/`**: This directory houses all the YAML configuration files that define different data extraction jobs. Each subdirectory within `configs/` typically represents a unique data source, pipeline, or a specific extraction task (e.g., `configs/financial_reports/`, `configs/system_alerts/`). These configuration files detail how emails should be filtered, what data to extract, any transformations to apply, and the final destination for the data.

## Configuration

To use this library, you typically need to create two main types of files for each extraction job:

1.  **Job Configuration File:** A YAML file (e.g., `config.yaml`) specifying the extraction, transformation, and loading parameters.
2.  **Table Schema File:** (Primarily for BigQuery loading) A file describing the table schema, often in a simple `name:type` list or a BigQuery JSON schema format.

### Config File Details

*   For each distinct data extraction job, create a dedicated folder (e.g., `configs/my_report_job/`).
*   Inside this folder, create the YAML configuration file (e.g., `config.yaml`).

Here is a sample configuration structure:

```yaml
mail_filter:
  from: sender@example.com
  subject: 'Your Daily Report Subject Keyword' # Partial subject match
  after: {{ datetime_start.timestamp() | int }} # Process emails after this UNIX timestamp
  before: {{ now.timestamp() | int }}          # Process emails before this UNIX timestamp
  attachment: true                         # Only process emails with attachments

file_to_extract:
  source: attachment # Options: 'attachment' or 'url_in_body'
  
  # --- If source is 'attachment' ---
  file_pattern: 'report_*.zip'         # Glob pattern for attachment filename
  mime_type: 'application/zip'        # Expected MIME type of the attachment

  # --- If source is 'url_in_body' ---
  # url_xpath: "//a[contains(@href, 'download.php')]/@href" # XPath to extract download URL from email body
  # password_xpath: "//p[contains(text(), 'Password:')]/span/text()" # XPath to extract a password from email body

transform:
  transform_model: MyReportTransform # Python class name for custom transformations
  filename_format: "{source_file}_{{now.strftime('%Y%m%d%H%M%S')}}" # Output filename pattern
  # Custom parameters for the transform_model class constructor:
  custom_param_for_transform: "custom_value"
  another_param: 123

load_destination:
  protocol: bq # Options: 'sftp', 'gcs', 'bq'

  # --- Common for SFTP & GCS ---
  # dir: "/remote/path/on/server/" # For SFTP
  # dir: "gcs_path_prefix/data/"   # For GCS (no leading slash)

  # --- For SFTP protocol ---
  # hostname: sftp.example.com
  # username: "your_sftp_user"    # Ensure quoting if special characters are used
  # port: 22
  # private_key: "/path/to/your/.ssh/id_rsa" # Path to SSH private key
  # password: "{{ env.get('SFTP_PASSWORD') }}" # Example: Use Jinja to get from environment variable
  # dir: "/upload/financial_data/"

  # --- For GCS protocol ---
  # bucket: "your-gcs-bucket-name"
  # dir: "data/reports/" # Path prefix within the bucket

  # --- For BQ (BigQuery) protocol ---
  project: your-gcp-project-id # GCP Project ID (optional if included in table_id)
  table_id: "your-gcp-project-id.your_dataset.your_table_name"
  schema: "schema.json" # Path to schema file (e.g., in the job's config folder)
  load_method: replace # Options: 'replace' (overwrite), 'append', 'merge'
  # Partition for BQ table (optional):
  partition: "{{datetime_start.strftime('%Y%m%d')}}" # Example: YYYYMMDD date string
  # partition: "regex:filename_.*_(\\d{8})_.*.csv" # Example: Extract YYYYMMDD from filename using regex
  clustering_fields: ["customer_id", "transaction_date"] # Optional list of fields for BQ clustering
  skip_leading_rows: 1 # Optional: Number of header rows in the source file to skip
  # time_partitioning_type: DAY # Optional: e.g., DAY, MONTH (if the BQ table is time-partitioned)
  # time_partitioning_field: "transaction_date" # Optional: Field used for BQ time partitioning

# Optional: Hour (0-23 UTC) to mark job as success if no data found.
# Useful for the last daily retry to prevent continuous runs if data isn't expected later.
ignore_after: 18
```

### Jinja Variables in Configuration

The following Jinja variables can be used within the YAML configuration file for dynamic values:

| Variable         | Type       | Description                                                                                                |
| ---------------- | ---------- | ---------------------------------------------------------------------------------------------------------- |
| `datetime_start` | `datetime` | The start datetime provided as an input argument to the job. Format as needed (e.g., using `.timestamp()`). |
| `datetime_end`   | `datetime` | The end datetime provided as an input argument to the job. Format as needed.                               |
| `now`            | `datetime` | The current datetime when the extraction process starts. Format as needed.                                 |
| `env`            | `dict`     | Dictionary of environment variables (`os.environ`). Useful for accessing secrets or settings (e.g., `{{ env.get('API_KEY') }}`). |

### Configuration Parameters Explanation

Below are detailed explanations of the main configuration sections and their parameters.

#### `mail_filter`
This section defines criteria for selecting specific emails to process.

| Parameter  | Type    | Description                                                                                                | Example                               |
| ---------- | ------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `from`     | string  | The exact email address of the sender.                                                                     | `sender@example.com`                  |
| `subject`  | string  | A string or keyword that must be present in the email's subject. This is a substring match, not a regex.    | `'Your Daily Report'`                 |
| `after`    | integer | Unix timestamp. Only emails received strictly after this time will be processed. Commonly `{{ datetime_start.timestamp() | int }}`. | `1677628800`                          |
| `before`   | integer | Unix timestamp. Only emails received strictly before this time will be processed. Commonly `{{ now.timestamp() | int }}`.           | `1677715200`                          |
| `attachment`| boolean | Optional. If `true`, only process emails that have one or more attachments. Defaults to `false`.             | `true`                                |

#### `file_to_extract`
This section specifies how to locate and extract the target file.

| Parameter        | Type   | Description                                                                                                                               | Example                                           |
| ---------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `source`         | string | Specifies the source of the file. Must be either `attachment` or `url_in_body`.                                                             | `attachment`                                      |
| `file_pattern`   | string | **If `source` is `attachment`**: A glob-like pattern to match attachment filenames (e.g., `*.csv`, `report-?.zip`).                         | `'report_*.zip'`                                  |
| `mime_type`      | string | **If `source` is `attachment`**: The expected MIME type of the attachment (e.g., `application/zip`, `text/csv`, `application/pdf`).        | `'application/zip'`                               |
| `url_xpath`      | string | **If `source` is `url_in_body`**: An XPath expression to find the download URL(s) in the email's HTML body. This should select the URL string directly (e.g., from an `href` attribute). | `//a[contains(text(),'Download Report')]/@href`   |
| `password_xpath` | string | **If `source` is `url_in_body`** (Optional): An XPath expression to find a password for a protected file (e.g., a ZIP archive password) in the email's HTML body. | `//p[starts-with(text(), 'Password:')]/span/text()`|

#### `transform`
This section defines custom transformations to be applied to the extracted file.

| Parameter         | Type   | Description                                                                                                                                                              | Example                                                              |
| ----------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| `transform_model` | string | The name of the Python class (e.g., `MyCustomTransform`) that handles the data transformation. This class must be defined in a `.py` file (e.g., `transform.py`) located in the job's configuration directory or a shared `assets` directory. | `MyReportTransform`                                                  |
| `filename_format` | string | A Python f-string or `str.format()` template to rename the output file after transformation. `{source_file}` is a placeholder for the original downloaded filename. Jinja variables can also be used. | `"{source_file}_{{now.strftime('%Y%m%d%H%M%S')}}.csv"`                |
| `*` (any other)   | any    | Any additional key-value pairs provided in this section are passed as keyword arguments (`**kwargs`) to the constructor (`__init__`) of the `transform_model` class. This allows for passing custom settings or parameters to your transformation logic. | `date_format: "%d/%m/%Y"` <br/> `skip_summary: true`                 |

#### `load_destination`
This section configures the target destination for the processed file.

| Parameter    | Type   | Description                                                                                                | Example                                            |
| ------------ | ------ | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `protocol`   | string | The target protocol. Supported values: `sftp`, `gcs`, `bq`.                                                | `bq`                                               |
| `dir`        | string | **For `sftp`**: The absolute target directory path on the SFTP server (e.g., `/uploads/data/`). <br/> **For `gcs`**: The path prefix within the GCS bucket (e.g., `processed_data/reports/`). | `/uploads/daily/` or `data/processed/`             |
| `hostname`   | string | **For `sftp`**: The hostname or IP address of the SFTP server.                                               | `sftp.example.com`                                 |
| `username`   | string | **For `sftp`**: The username for SFTP login.                                                                 | `sftp_user`                                        |
| `port`       | integer| **For `sftp`**: The port number for the SFTP server. Defaults to `22`.                                       | `2222`                                             |
| `private_key`| string | **For `sftp`**: Full path to the SSH private key file for authentication. If provided, `password` is typically ignored. | `~/.ssh/id_rsa_sftp`                               |
| `password`   | string | **For `sftp`**: The password for SFTP login. Use if `private_key` is not specified. Consider using environment variables for passwords. | `{{ env.get('SFTP_PASSWORD') }}`                   |
| `bucket`     | string | **For `gcs`**: The name of the Google Cloud Storage bucket.                                                  | `my-data-bucket-name`                              |
| `project`    | string | **For `bq`**: The Google Cloud Project ID where the BigQuery table resides. Optional if `table_id` includes the project ID. | `my-gcp-project-id`                                |
| `table_id`   | string | **For `bq`**: The full BigQuery table ID in the format: `<project_id>.<dataset_id>.<table_name>`.             | `my-gcp-project.my_dataset.my_table`               |
| `schema`     | string | **For `bq`**: Path to the schema file for the BigQuery table. This can be a simple `name:type` list (e.g., `schema.txt`) or a BigQuery JSON schema file (e.g., `schema.json`). | `schema.json` or `schema.erd`                      |
| `load_method`| string | **For `bq`**: How data should be loaded into BigQuery. <br/> `replace`: Overwrites the table/partition. <br/> `append`: Adds new data to the table/partition. <br/> `merge`: (More complex) Merges data based on keys (requires additional configuration not covered here). | `replace`                                          |
| `partition`  | string | **For `bq`** (Optional): The partition ID for the destination table (e.g., a date string `YYYYMMDD`). Can also use `regex:<pattern>` to extract the partition ID from the filename (e.g., `regex:report_(\\d{8})_.*` would use the first captured group). | `{{datetime_start.strftime('%Y%m%d')}}`            |
| `clustering_fields` | list   | **For `bq`** (Optional): A list of field names (strings) to use for clustering in the BigQuery table.   | `["customer_id", "order_date"]`                    |
| `skip_leading_rows` | integer| **For `bq`** (Optional): Number of header rows in the source file to skip during the BigQuery load.     | `1`                                                |
| `time_partitioning_type` | string | **For `bq`** (Optional): Specifies the time partitioning type (e.g., `DAY`, `MONTH`). If used, `time_partitioning_field` is typically required. | `DAY`                                              |
| `time_partitioning_field`| string | **For `bq`** (Optional): The field in the table schema used for time-based partitioning.            | `transaction_date`                                 |

#### `ignore_after`
This is an optional top-level parameter used for scheduling control.

| Parameter    | Type    | Description                                                                                                                                                              | Example |
| ------------ | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------- |
| `ignore_after` | integer | Optional. An hour of the day (0-23, UTC). If the job runs at or after this specified hour and finds no new emails/data to process, it will mark itself as successful without error. This is useful for a final daily retry to prevent continuous execution if data is not expected later in the day. | `18` (6 PM UTC) |


### 2. Schema File (for BigQuery)

When loading data into BigQuery, a schema file is often required, especially if the table does not exist or if strict schema validation is desired. This file can be:

*   A simple text file with each line defining a field as `name:type` (e.g., `transaction_id:STRING`, `amount:FLOAT`).
*   A JSON file following the BigQuery schema definition format (an array of objects, where each object defines a field with `name`, `type`, `mode`, etc.).

Example (`schema.json`):
```json
[
  {"name": "transaction_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "transaction_date", "type": "DATE", "mode": "NULLABLE"},
  {"name": "amount", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "description", "type": "STRING", "mode": "NULLABLE"}
]
```

## Contributing

We welcome contributions to enhance the Gmail Extractor! Whether it's adding new features, improving existing functionality, or fixing bugs, your help is appreciated.

Please try to follow the existing code style and conventions. If your changes introduce new features or modify existing behavior, please update the documentation (this README or other relevant files) accordingly.

### Adding New Capabilities (to the core library)

1.  **Fork the repository**: Start by forking the project to your own GitHub account.
2.  **Create a new branch**: For each new feature or bugfix, create a dedicated branch in your fork. Name it descriptively (e.g., `feature/support-new-auth-method` or `fix/improve-retry-logic`).
3.  **Implement your changes**:
    *   Write clear, concise, and well-commented code.
    *   Include docstrings for new functions, classes, and methods, explaining their purpose, arguments, and return values.
4.  **Add unit tests**:
    *   Write unit tests that thoroughly cover your changes.
    *   Ensure tests are specific and verify the intended behavior, including edge cases and error conditions.
5.  **Ensure all tests pass**: Run the existing test suite and your new tests to confirm that everything works correctly and no existing functionality is broken.
6.  **Submit a pull request**: Push your changes to your fork and submit a pull request to the main repository. Provide a clear title and a detailed description of your changes, the problem they solve, and how you tested them.

### Adding a new ETL (Transform) Class

ETL (Extract, Transform, Load) classes are used to perform custom data transformations tailored to specific jobs.

1.  **Create your transform class**:
    *   Conventionally, create a Python class in a file named `transform.py`. This file can be located within your specific job's configuration directory (e.g., `configs/my_job_name/transform.py`) or in a shared `assets/transform.py` directory if the class is intended for reuse across multiple jobs.
    *   Your class should have an `__init__` method. This method must accept `**kwargs` to receive parameters defined in the `transform:` section of your YAML job configuration. Store these parameters as instance variables (e.g., `self.date_format = kwargs.get('date_format')`).
2.  **Implement the core transformation logic**:
    *   Add a primary method to your class (commonly named `transform`, `execute`, or `run`). This method will be called by the main library.
    *   This method should accept the path to the input file (the file downloaded from Gmail or a URL) as its primary argument. It can also accept `**kwargs` if additional runtime parameters are needed.
    *   Inside this method, implement all necessary data processing steps: reading the file (e.g., using pandas, csv module), cleaning data, reshaping columns, filtering rows, performing calculations, etc.
    *   The method **must return the path to the transformed output file**. The library operates on a file-based workflow, so the output of your transformation should be a new file written to disk.
3.  **Configure your job**:
    *   In your job's YAML configuration file, under the `transform:` section, set the `transform_model` key to the name of your Python class (e.g., `MyDataTransformer`).
    *   Any other parameters you define under the `transform:` section in the YAML (e.g., `date_format: '%Y-%m-%d'`, `target_columns: ["col_a", "col_b"]`) will be passed as keyword arguments to your class's `__init__` method.
4.  **Example ETL Class**:
    ```python
    # Located in: configs/my_job_name/transform.py or assets/transform.py
    import pandas as pd # Example using pandas for transformation

    class MyDataTransformer:
        def __init__(self, target_columns=None, date_format='%Y-%m-%d', input_separator=',', **kwargs):
            """
            Initializes the transformer with configuration.
            target_columns: Optional list of columns to keep in the output.
            date_format: The expected date format in a 'transaction_date' column.
            input_separator: CSV Separator for input file
            kwargs: Catches any other parameters passed from the config.
            """
            self.target_columns = target_columns
            self.date_format = date_format
            self.input_separator = input_separator
            self.other_params = kwargs # Store any other custom parameters

        def transform(self, input_filepath, **kwargs):
            """
            Transforms the input file and returns the path to the transformed file.
            input_filepath: Path to the raw data file.
            """
            try:
                # Read the input file (e.g., CSV)
                df = pd.read_csv(input_filepath, sep=self.input_separator)

                # Example transformation: Convert a date column (if it exists)
                if 'transaction_date' in df.columns:
                    df['transaction_date'] = pd.to_datetime(df['transaction_date'], format=self.date_format, errors='coerce')

                # Example transformation: Keep only target columns if specified
                if self.target_columns and all(col in df.columns for col in self.target_columns):
                    df = df[self.target_columns]
                elif self.target_columns:
                    print(f"Warning: Not all target_columns ({self.target_columns}) found in DataFrame.")

                # ... add more complex, domain-specific transformations here ...
                # For example, handling missing values, creating new features, etc.
                # print(f"Other transform parameters received: {self.other_params}")

                # Define the output filepath
                # It's good practice to make the output filename distinct
                output_filepath = f"{input_filepath.rsplit('.', 1)[0]}_transformed.csv"

                df.to_csv(output_filepath, index=False)

                return output_filepath
            except FileNotFoundError:
                print(f"Error: Input file not found at {input_filepath}")
                raise
            except pd.errors.EmptyDataError:
                print(f"Error: Input file at {input_filepath} is empty.")
                raise
            except Exception as e:
                print(f"Error during transformation of {input_filepath}: {e}")
                # Consider re-raising the exception or returning None/error marker
                # depending on desired error handling strategy for the pipeline
                raise

    # Example usage in config.yaml for this transform_model:
    # transform:
    #   transform_model: MyDataTransformer # Name of the class
    #   filename_format: "{source_file}_processed_{{now.strftime('%Y%m%d')}}" # This is applied by the main library after transform returns the output path
    #   # --- Custom parameters for MyDataTransformer's __init__ ---
    #   target_columns: ["ID", "Name", "transaction_date", "Amount"]
    #   date_format: "%m/%d/%Y" # Passed to __init__
    #   input_separator: ";"    # Passed to __init__
    #   some_other_custom_setting: "value123" # Passed to __init__ via kwargs
    ```
5.  **Test Thoroughly**:
    *   Create sample input files that cover various scenarios: valid data, malformed data, empty files, files with different delimiters (if applicable), and edge cases specific to your data.
    *   Write unit tests for your transformation class. You can mock file system interactions or use temporary files/directories for testing.
    *   Test your ETL class independently before integrating it into a full job configuration.
    *   Ensure your transformation logic is robust, handles potential errors gracefully (e.g., missing columns, incorrect data types), and logs informative messages.

Remember to **TEST, TEST, TEST!** Your new ETL class is a critical component of the data pipeline, and thorough testing is essential for data quality and reliability.
