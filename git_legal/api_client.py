"""
API client for fetching data from the BOE API.
"""

import time
import logging
import datetime
import requests
from typing import Optional, Dict, Any, Tuple

from git_legal.config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIClient:
    """Client for interacting with the BOE API."""
    
    def __init__(self, config: Config):
        """Initialize the API client with configuration."""
        self.config = config
        self.session = requests.Session()
        
        # Configure proxies if enabled
        if config.use_proxy and config.proxy_url:
            self.session.proxies = {
                'http': config.proxy_url,
                'https': config.proxy_url
            }
            logger.info("Using proxy for requests")
    
    def get_date_str(self, date: datetime.date) -> str:
        """Convert a date to the format required by the API (YYYYMMDD)."""
        return date.strftime("%Y%m%d")
    
    def get_data(self, indexer: str, target) -> Tuple[int, Optional[str]]:
        """
        Fetch the summary for a specific date.
        
        Args:
            indexer: Date string in YYYYMMDD format
            
        Returns:
            Tuple of (status_code, response_text)
            If the request fails, response_text will be None
        """
        if target == "index":
            url = f"{self.config.api_base_url}{indexer}"
        elif target == "document":
            url = f"{self.config.law_base_url}{indexer}"
        else:
            raise ValueError(f"Invalid target: {target}")

        headers = {"Accept": "application/xml"}
        for attempt in range(self.config.max_retries + 1):
            try:
                logger.info(f"Requesting data for date: {indexer}")
                
                # Add delay for rate limiting (except for first attempt)
                if attempt > 0:
                    time.sleep(self.config.retry_delay)
                
                response = self.session.get(url, headers=headers, timeout=30, verify=False)

                # Check if we got a valid response
                if response.status_code == 200:
                    # Verify that the response contains XML data
                    if response.text and "xml" in response.text:
                        logger.info(f"Successfully retrieved data for date: {indexer}")
                        return response.status_code, response.text
                    else:
                        logger.warning(f"Received non-XML response for date: {indexer}")
                        # This might be rate limiting or another issue
                        time.sleep(self.config.retry_delay)
                elif response.status_code == 404:
                    # 404 is expected for some dates, not an error
                    logger.info(f"No data available for date: {indexer} (404)")
                    return response.status_code, None
                else:
                    logger.warning(f"Request failed with status code {response.status_code} for date: {indexer}")
                
            except requests.RequestException as e:
                logger.error(f"Request error for date {indexer}: {str(e)}")
                
            # If we're not on the last attempt, log retry
            if attempt < self.config.max_retries:
                logger.info(f"Retrying request for date: {indexer} (attempt {attempt + 1}/{self.config.max_retries})")
        
        # If we've exhausted all retries
        logger.error(f"Failed to retrieve data for date: {indexer} after {self.config.max_retries} retries")
        return 0, None  # Return 0 to indicate a client-side failure
    
    def apply_cooldown(self):
        """Apply cooldown between requests to avoid rate limiting."""
        time.sleep(self.config.cooldown_seconds)
