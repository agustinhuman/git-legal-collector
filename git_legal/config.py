"""
Configuration settings for the git-legal application.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Config:
    """Configuration settings for the application."""
    format: list[str] = field(default_factory = lambda: ["xml"])
    index_only: bool = False

    # API settings
    api_base_url: str = "https://www.boe.es/datosabiertos/api/boe/sumario/"
    law_base_url: str = "https://www.boe.es/diario_boe/xml.php?id="
    start: int = 19700101  # Format: YYYYMMDD
    end: int = int(datetime.now().strftime("%Y%m%d")) # Format: YYYYMMDD

    # Request settings
    cooldown: float = 0.0  # Time to wait between requests
    max_retries: int = 3  # Maximum number of retries for failed requests
    retry_delay: float = 5.0  # Delay between retries in seconds
    concurrency: int = 1  # Default to sequential execution
    
    # Storage settings
    output: str = os.path.join(os.getcwd(), "data")
    csv_filename: str = "boe_data.csv"
    resume_file: str = os.path.join(os.getcwd(), "data", "resume_state.json")

    
    # Create output directory if it doesn't exist
    def ensure_output_dir(self):
        """Ensure the output directory exists."""
        os.makedirs(self.output, exist_ok=True)
