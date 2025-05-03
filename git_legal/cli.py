"""
Command-line interface for the git-legal application.
"""

import argparse
import logging
import sys
from typing import List, Optional

from git_legal.config import Config
from git_legal.downloader import BOEDownloader

logger = logging.getLogger(__name__)

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download BOE data from the public administration API."
    )
    
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date in YYYYMMDD format. If not provided, uses the resume state or default (19800101)."
    )
    
    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Use concurrent downloading instead of sequential."
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Number of concurrent workers (default: 5). Only used with --concurrent."
    )
    
    parser.add_argument(
        "--use-proxy",
        action="store_true",
        help="Use Bright Data residential proxy for requests."
    )
    
    parser.add_argument(
        "--proxy-url",
        type=str,
        help="Bright Data residential proxy URL. Required if --use-proxy is specified."
    )
    
    parser.add_argument(
        "--cooldown",
        type=float,
        default=1.0,
        help="Cooldown between requests in seconds (default: 1.0)."
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to store output files (default: ./data)."
    )
    
    parser.add_argument(
        "--csv-filename",
        type=str,
        help="Name of the CSV file to store data (default: boe_data.csv)."
    )

    parser.add_argument(
        "target",
        type=str,
        default="index",
        choices=["index", "document"],
    )
    
    return parser.parse_args(args)

def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the application."""
    parsed_args = parse_args(args)
    
    # Create configuration
    config = Config()
    
    # Update configuration from command-line arguments
    if parsed_args.end_date:
        config.end_date = parsed_args.end_date
    
    if parsed_args.use_proxy:
        config.use_proxy = True
        if parsed_args.proxy_url:
            config.proxy_url = parsed_args.proxy_url
        else:
            logger.error("--proxy-url is required when --use-proxy is specified")
            return 1
    
    if parsed_args.concurrent:
        config.concurrent_requests = parsed_args.workers
    
    if parsed_args.cooldown:
        config.cooldown_seconds = parsed_args.cooldown
    
    if parsed_args.output_dir:
        config.output_dir = parsed_args.output_dir
    
    if parsed_args.csv_filename:
        config.csv_filename = parsed_args.csv_filename

    config.target = parsed_args.target
    
    # Create downloader
    downloader = BOEDownloader(config)
    
    try:
        # Run the appropriate download method
        if parsed_args.concurrent:
            total_saved = downloader.download_concurrent(parsed_args.end_date, config.target)
        else:
            total_saved = downloader.download_sequential(parsed_args.end_date, config.target)
        
        logger.info(f"Download completed successfully. Total items saved: {total_saved}")
        return 0
    
    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
        return 130  # Standard exit code for SIGINT
    
    except Exception as e:
        logger.exception(f"Error during download: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
