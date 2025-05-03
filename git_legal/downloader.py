"""
Main downloader module for fetching BOE data.
"""

import logging
import datetime
import os
from urllib.parse import urlparse, parse_qs
import time
import pandas as pd
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from git_legal.config import Config
from git_legal.api_client import APIClient
from git_legal.parser import IndexXmlParser, get_parser
from git_legal.csvstorage import CsvStorage, get_storer

# Set up logging
logger = logging.getLogger(__name__)

def date_literal_to_datetime(date_literal: str, default: datetime.date | str) -> datetime.date:
    """Convert a date literal to a datetime.date object."""
    if not date_literal:
        if type(default) == str:
            return date_literal_to_datetime(default, datetime.date.today())
        else:
            return default
    start_year = int(date_literal[:4])
    start_month = int(date_literal[4:6])
    start_day = int(date_literal[6:8])
    date = datetime.date(start_year, start_month, start_day)
    return date


class BOEDownloader:
    """Main downloader class for BOE data."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the downloader with configuration."""
        self.config = config or Config()
        self.api_client = APIClient(self.config)
        self.storage = CsvStorage(self.config)
    
    def _get_parse_range(self, end_date_lit: Optional[str], target: str) -> List[str]:

        if target == "index":
            # Use the provided start date, resume state, or configured start date
            default_start_date = self.storage.load_resume_state() or datetime.date.today()
            start_date = date_literal_to_datetime(self.config.end_date)
            end_date = date_literal_to_datetime(end_date_lit, default_start_date)

            # Generate the date range
            date_range = []
            current_date = end_date
            while current_date >= start_date:
                date_range.append(self.api_client.get_date_str(current_date))
                current_date -= datetime.timedelta(days=1)

            return date_range
        elif target == "document":
            data_path = os.path.join(self.config.output_dir, self.config.csv_filename)
            try:
                df = pd.read_csv(data_path)
                if "url_xml" not in df.columns:
                    raise ValueError("CSV file does not contain 'data' column")
                col = df["url_xml"].tolist()
                acc = []
                for item in col:
                    if item is None or pd.isna(item) or not item.startswith("http"):
                        logger.warning(f"Invalid URL found in CSV: {item}")
                        continue
                    parsed = urlparse(item)
                    query = parse_qs(parsed.query) or ""
                    boe_id = (query["id"] or [None]) [0]
                    if boe_id is None:
                        logger.warning(f"No BOE ID found in URL: {item}")
                        continue
                    acc.append(boe_id)
                resume_checkpoint = self.storage.load_resume_state()
                if resume_checkpoint is not None and resume_checkpoint in acc:
                    acc = acc[acc.index(resume_checkpoint)+1:]
                return acc
            except FileNotFoundError:
                raise FileNotFoundError(f"CSV file not found at {data_path}")

        else:
            raise ValueError(f"Invalid target: {target}")


    
    def _process_item(self, indexer: str, target) -> int:
        """
        Process a single date: fetch data, parse it, and save to CSV.
        
        Args:
            indexer: Date string in YYYYMMDD format
            
        Returns:
            Number of items saved
        """
        # Apply cooldown to avoid rate limiting
        self.api_client.apply_cooldown()
        
        # Fetch data from API
        status_code, response_text = self.api_client.get_data(indexer, target=target)


        # If we got a successful response with data
        if status_code == 200 and response_text:
            # Parse the XML
            items = get_parser(target).parse(response_text)
            
            # Save to CSV
            saved_count = get_storer(target).save_items(items, indexer)
            
            # Save resume state
            self.storage.save_resume_state(indexer)
            
            return saved_count
        
        # For 404 or other errors, just save the resume state and return 0
        if status_code != 0:  # 0 indicates a client-side failure
            self.storage.save_resume_state(indexer)
        
        return 0
    
    def download_sequential(self, end_date: Optional[str], target: str) -> int:
        logger.info("Starting sequential download")
        
        date_range = self._get_parse_range(end_date, target)
        total_saved = 0
        
        for range_item in date_range:
            try:
                saved_count = self._process_item(range_item, target)
                total_saved += saved_count
                logger.info(f"Processed date {range_item}: saved {saved_count} items")
            except Exception as e:
                logger.error(f"Error processing date {range_item}: {str(e)}")
                # Continue with the next date
        
        logger.info(f"Sequential download completed: saved {total_saved} items in total")
        return total_saved
    
    def download_concurrent(self, end_date: Optional[str], target) -> int:
        if not self.config.use_proxy:
            logger.warning("Concurrent download requested but proxy is not enabled. "
                          "This may lead to IP blocking. Consider enabling proxy.")
        logger.info(f"Starting concurrent download with {self.config.concurrent_requests} workers")
        date_range = self._get_parse_range(end_date, target)
        total_saved = 0
        
        with ThreadPoolExecutor(max_workers=self.config.concurrent_requests) as executor:
            # Submit all tasks
            future_to_date = {executor.submit(self._process_item, date_str, target): date_str
                             for date_str in date_range}
            
            # Process results as they complete
            for future in as_completed(future_to_date):
                date_str = future_to_date[future]
                try:
                    saved_count = future.result()
                    total_saved += saved_count
                    logger.info(f"Processed date {date_str}: saved {saved_count} items")
                except Exception as e:
                    logger.error(f"Error processing date {date_str}: {str(e)}")
        
        logger.info(f"Concurrent download completed: saved {total_saved} items in total")
        return total_saved
