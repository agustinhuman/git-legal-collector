"""
Configuration settings for the git-legal application.
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Configuration settings for the application."""
    target: str = "index"

    # API settings
    api_base_url: str = "https://www.boe.es/datosabiertos/api/boe/sumario/"
    law_base_url: str = "https://www.boe.es/diario_boe/xml.php?id="
    end_date: str = "19600101"  # Format: YYYYMMDD
    
    # Request settings
    cooldown_seconds: float = 0.0  # Time to wait between requests
    max_retries: int = 3  # Maximum number of retries for failed requests
    retry_delay: float = 5.0  # Delay between retries in seconds
    
    # Concurrency settings
    use_proxy: bool = False
    concurrent_requests: int = 1  # Default to sequential execution
    
    # Proxy settings
    proxy_url: Optional[str] = None  # Bright Data residential proxy URL
    
    # Storage settings
    output_dir: str = os.path.join(os.getcwd(), "data")
    documents_dir: str = os.path.join(output_dir, "documents")
    csv_filename: str = "boe_data.csv"
    resume_file: str = os.path.join(os.getcwd(), "data", "resume_state.json")
    
    # Create output directory if it doesn't exist
    def ensure_output_dir(self):
        """Ensure the output directory exists."""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.documents_dir, exist_ok=True)
