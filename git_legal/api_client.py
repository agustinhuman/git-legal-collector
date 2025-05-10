"""
API client for fetching data from the BOE API.
"""

import datetime
import logging
import time
from math import isnan
from typing import Optional, Tuple, Any

import requests

from git_legal.config import Config
from git_legal.parser import IndexXmlParser
from git_legal.storage import LawInfo

# Set up logging
logger = logging.getLogger(__name__)

class APIClient:
    """Client for interacting with the BOE API."""
    
    def __init__(self, config: Config):
        """Initialize the API client with configuration."""
        self.config = config
        self.session = requests.Session()
    
    def get_date_str(self, date: datetime.date) -> str:
        """Convert a date to the format required by the API (YYYYMMDD)."""
        return date.strftime("%Y%m%d")
    
    def get_daily_boes(self, date: int) -> list[LawInfo]:
        """
        Fetch the summary for a specific date.
        """
        date_literal = str(date)
        url = f"{self.config.api_base_url}{date_literal}"
        headers = {"Accept": "application/xml"}

        status_code, text = self._def_get_data(url, headers, name=date_literal)
        if text is not None:
            return IndexXmlParser.parse(text)
        return []

    def get_file(self, law_info: LawInfo, format: str = "xml"):
        field_name = "url_" + format
        url = getattr(law_info, field_name, None)
        if url is None or not type(url) == str:
            logger.warning(f"No {field_name} found for law {law_info.identificador}")
            return None
        headers = {"Accept": "application/xml"}
        status_code, text = self._def_get_data(url, headers, name=law_info.identificador)
        return text if status_code == 200 else None


    def _def_get_data(self, url, headers, name: str = ""):
        self.apply_cooldown()
        for attempt in range(self.config.max_retries + 1):
            try:
                logger.info(f"Requesting data for {name}")

                # Add delay for rate limiting (except for first attempt)
                if attempt > 0:
                    time.sleep(self.config.retry_delay)

                response = self.session.get(url, headers=headers, timeout=30)

                # Check if we got a valid response
                if response.status_code == 200:
                    logger.debug(f"Successfully retrieved data for {name}")
                    return response.status_code, response.text
                elif response.status_code == 404:
                    # 404 is expected for some dates, not an error
                    logger.info(f"No data available for {name} (404)")
                    return response.status_code, None
                else:
                    logger.warning(f"Request failed with status code {response.status_code} for {name}")

            except requests.RequestException as e:
                logger.error(f"Request error for date {name}: {str(e)}")

            # If we're not on the last attempt, log retry
            if attempt < self.config.max_retries:
                logger.info(f"Retrying request for date: {name} (attempt {attempt + 1}/{self.config.max_retries})")

        # If we've exhausted all retries
        logger.error(f"Failed to retrieve data for date: {name} after {self.config.max_retries} retries")
        return 0, None  # Return 0 to indicate a client-side failure
    
    def apply_cooldown(self):
        """Apply cooldown between requests to avoid rate limiting."""
        if self.config.cooldown > 0:
            time.sleep(self.config.cooldown)
