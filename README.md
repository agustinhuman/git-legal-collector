# Git Legal - BOE Data Downloader

A Python application for downloading data from the Spanish BOE (Boletín Oficial del Estado) API and storing it in CSV format.

## Features

- Downloads data from the BOE API systematically from today backwards until 1980
- Handles 404 responses gracefully (expected for some dates)
- Saves data in CSV format with all relevant fields
- Supports resume capability if the download is interrupted
- Configurable cooldown between requests to avoid rate limiting
- Supports both sequential and concurrent execution
- Optional proxy support for concurrent execution (Bright Data residential proxy)
- Configurable concurrency rate

## Installation

### From Source

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/git-legal.git
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

#### Options

- `--start-date YYYYMMDD`: Start date in YYYYMMDD format (default: 19800101 or resume state)
- `--concurrent`: Use concurrent downloading instead of sequential
- `--workers N`: Number of concurrent workers (default: 5, only used with --concurrent)
- `--use-proxy`: Use Bright Data residential proxy for requests
- `--proxy-url URL`: Bright Data residential proxy URL (required if --use-proxy is specified)
- `--cooldown SECONDS`: Cooldown between requests in seconds (default: 1.0)
- `--output-dir DIR`: Directory to store output files (default: ./data)
- `--csv-filename FILENAME`: Name of the CSV file to store data (default: boe_data.csv)

### Examples

1. Basic sequential download:
   ```
   git-legal
   ```

2. Start from a specific date:
   ```
   git-legal --start-date 20200101
   ```

3. Concurrent download with proxy:
   ```
   git-legal --concurrent --workers 10 --use-proxy --proxy-url "http://your-proxy-url"
   ```

4. Customize output location:
   ```
   git-legal --output-dir /path/to/data --csv-filename my_boe_data.csv
   ```

### Python API

You can also use the application programmatically:

```python
from git_legal.config import Config
from git_legal.downloader import BOEDownloader

# Create a custom configuration
config = Config()
config.end_date = "20200101"
config.cooldown_seconds = 2.0

# Create the downloader
downloader = BOEDownloader(config)

# Run sequential download
downloader.download_sequential()

# Or run concurrent download
config.use_proxy = True
config.proxy_url = "http://your-proxy-url"
config.concurrent_requests = 10
downloader.download_concurrent()
```

## Data Format

The downloaded data is stored in CSV format with the following fields:

- `fecha_publicacion`: Publication date
- `identificador`: Unique identifier
- `control`: Control number
- `titulo`: Title of the publication
- `url_pdf`: URL to the PDF version
- `url_pdf_szBytes`: Size of the PDF in bytes
- `url_pdf_szKBytes`: Size of the PDF in kilobytes
- `url_pdf_pagina_inicial`: Initial page number
- `url_pdf_pagina_final`: Final page number
- `url_html`: URL to the HTML version
- `url_xml`: URL to the XML version
- `seccion_codigo`: Section code
- `seccion_nombre`: Section name
- `departamento_codigo`: Department code
- `departamento_nombre`: Department name
- `epigrafe_nombre`: Epigraph name

## Resume Capability

If the download process is interrupted, you can resume it by running the application again with the same output directory. The application will automatically continue from where it left off.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
