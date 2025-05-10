"""
Main downloader module for fetching BOE data.
"""

import datetime
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List
from urllib.parse import urlparse, parse_qs

import pandas as pd

from git_legal.api_client import APIClient
from git_legal.config import Config
from git_legal.storage import CsvStorage, FileStorage, ResumeStorage, LawInfo
from git_legal.parser import get_parser
import tqdm

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

def date_literal_to_datetime(date_literal: str | int) -> datetime.date:
    """Convert a date literal to a datetime.date object."""
    if type(date_literal) == int:
        date_literal = str(date_literal)
    start_year = int(date_literal[:4])
    start_month = int(date_literal[4:6])
    start_day = int(date_literal[6:8])
    date = datetime.date(start_year, start_month, start_day)
    return date


class BOEDownloader:
    """Main downloader class for BOE data."""

    def __init__(self, config: Config):
        """Initialize the downloader with configuration."""
        self.config: Config = config
        self.api_client = APIClient(self.config)
        self.index = CsvStorage(self.config)
        self.files = FileStorage(self.config)
        self.resume_state = ResumeStorage(self.config)

    def _get_date_range(self) -> List[int]:
        # Use the provided start date, resume state, or configured start date
        start_date_lit = self.resume_state.load_resume_state() or self.config.start
        start_date = date_literal_to_datetime(start_date_lit)
        end_date = date_literal_to_datetime(self.config.end)

        # Generate the date range
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            formated_date = int(current_date.strftime("%Y%m%d"))
            date_range.append(formated_date)
            current_date += datetime.timedelta(days=1)

        return date_range


    def _get_daily_boes(self, date) -> list[LawInfo] | None:
        # Here
        boes = self.index.get_values_for_date(date)
        if boes is not None:
            return boes
        else:
            boes = self.api_client.get_daily_boes(date)
            if boes is not None:
                self.index.save_items(boes)
                return boes
            else:
                return []


    def _process_item(self, law_info: LawInfo) -> int:
        """
        Process a single date: fetch data, parse it, and save to CSV.

        Args:
            indexer: Date string in YYYYMMDD format

        Returns:
            Number of items saved
        """

        # Fetch data from API
        total_downloaded = 0
        for format in self.config.format:
            response_text = self.api_client.get_file(law_info, format)

            if response_text:
                total_downloaded += self.files.save_item(response_text, law_info, format)
        return total_downloaded


    def start(self) -> int:
        logger.info(f"Starting concurrent download with {self.config.concurrency} workers")
        date_range = self._get_date_range()
        total_saved = 0

        with ThreadPoolExecutor(max_workers=self.config.concurrency) as executor:
            for date in tqdm.tqdm(date_range, desc="Days"):
                daily_boes = self._get_daily_boes(date)
                if daily_boes is None or self.config.index_only:
                    continue

                future_to_date = {executor.submit(self._process_item, law_info): law_info
                                  for law_info in daily_boes}
                for future in tqdm.tqdm(as_completed(future_to_date),total=len(future_to_date), desc="Daily BOEs", leave=False):
                    date_str = future_to_date[future]
                    try:
                        saved_count = future.result()
                        total_saved += saved_count
                        logger.info(f"Processed date {date_str}: saved {saved_count} items")
                    except Exception as e:
                        logger.error(f"Error processing date {date_str}: {str(e)}")

                self.resume_state.save_resume_state(date)

        logger.info(f"Concurrent download completed: saved {total_saved} items in total")
        return total_saved
