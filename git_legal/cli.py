"""
Command-line interface for the git-legal application.
"""

import argparse
import logging
import sys
from datetime import datetime
from typing import List, Optional

from git_legal.config import Config
from git_legal.downloader import BOEDownloader

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def parse_args(args: Optional[List[str]] = None) -> Config:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download BOE data from the public administration API."
    )
    
    parser.add_argument(
        "--start",
        type=int,
        default=19700101,
        help="End date in YYYYMMDD format. If not provided, uses the resume state or default (19700101)."
    )

    parser.add_argument(
        "--end",
        type=int,
        default=int(datetime.now().strftime("%Y%m%d")),
        help="End date in YYYYMMDD format. If not provided, uses the resume state or today as default."
    )
    
    parser.add_argument(
        "--concurrency",
        default=1,
        type=int,
        help="Max number of concurrent requests (default to one)"
    )
    
    parser.add_argument(
        "--cooldown",
        type=float,
        default=1.0,
        help="Cooldown between requests in seconds. Has no effect if --concurrency is greater than one."
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="data",
        help="Directory to store output files (default: ./boe_data)."
    )
    
    parser.add_argument(
        "--index-only",
        type=bool,
        default=False,
        help="Only download the list of BOEs, not the BOEs itself."
    )

    parser.add_argument(
        "--format",
        action="append",
        type=str,
        choices=["xml", "html", "pdf"],
        help="Format of the downloaded files.."
    )
    
    parsed_args =  parser.parse_args(args)

    config = Config()

    for arg in vars(parsed_args):
        value = getattr(parsed_args, arg)
        if value is not None:
            setattr(config, arg, getattr(parsed_args, arg))

    config.ensure_output_dir()
    if config.concurrency > 1:
        parsed_args.cooldown = 0.0
    return config


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the application."""
    config = parse_args(args)

    downloader = BOEDownloader(config)
    
    try:
        total_saved = downloader.start()
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
