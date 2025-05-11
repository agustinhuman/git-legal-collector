# Git Legal - BOE Data Downloader

A Python application for downloading data from the Spanish BOE (Boletín Oficial del Estado) API.

## Installation

### From Source

1. Clone the repository:
   ```
   git clone https://github.com/agustinhuman/git-legal.git
   cd git-legal
   ```

2. Install the package:
   ```
   pip install -e .
   ```

## Usage

### Command Line Interface

The application can be run from the command line:

```
git-legal [options]
```

By default it will download all laws in xml and store them in the folder structure: "data/xml /<seccion>/<year>/<name>.xml"

#### Options

-  `-h, --help`            Show help
- `--start START`         End date in YYYYMMDD format. If not provided, uses the resume state or default (19700101)
- `--end END`            End date in YYYYMMDD format. If not provided, uses the resume state or today as default
- `--concurrency CONCURRENCY`      Max number of concurrent requests (default to one)
- `--cooldown COOLDOWN`   Cooldown between requests in seconds. Has no effect if --concurrency is greater than one
- `--output OUTPUT`       Directory to store output files (default: ./boe_data)
- `--index-only INDEX_ONLY`      Only download the list of BOEs, not the BOEs itself
- `--format {xml,html,pdf}`      Format of the downloaded files. Multiple appearance supported
- 
### Examples

1. Basic sequential download:
   ```
   git-legal --concurrency --format xml
   ```

## Resume Capability

If the download process is interrupted, you can resume it by running the application again with the same output directory. The application will automatically continue from where it left off.

## License

This project code is licensed under the MIT License.
