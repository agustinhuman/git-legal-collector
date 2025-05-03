"""
Storage module for saving BOE data to CSV and managing resume state.
"""

import os
import csv
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from git_legal.config import Config

# Set up logging
logger = logging.getLogger(__name__)

class FileStorage:
    """Storage handler for BOE data."""

    def __init__(self, config: Config):
        """Initialize the storage handler with configuration."""
        self.config = config
        self.config.ensure_output_dir()
        self.resume_path = self.config.resume_file

    def save_items(self, text, indexer: str):
        path = os.path.join(self.config.documents_dir, f"{indexer}.xml")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        logger.info(f"Saved document to {path}")
        return 1

class CsvStorage:
    """Storage handler for BOE data."""
    
    def __init__(self, config: Config):
        """Initialize the storage handler with configuration."""
        self.config = config
        self.config.ensure_output_dir()
        self.csv_path = os.path.join(self.config.output_dir, self.config.csv_filename)
        self.resume_path = self.config.resume_file
        
        # Create CSV file with headers if it doesn't exist
        self._ensure_csv_exists()
    
    def _ensure_csv_exists(self):
        """Ensure the CSV file exists with headers."""
        if not os.path.exists(self.csv_path):
            logger.info(f"Creating new CSV file: {self.csv_path}")
            # Define the headers based on the expected data structure
            headers = [
                "fecha_publicacion",
                "identificador",
                "control",
                "titulo",
                "url_pdf",
                "url_pdf_szBytes",
                "url_pdf_szKBytes",
                "url_pdf_pagina_inicial",
                "url_pdf_pagina_final",
                "url_html",
                "url_xml",
                "seccion_codigo",
                "seccion_nombre",
                "departamento_codigo",
                "departamento_nombre",
                "epigrafe_nombre"
            ]
            
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
    
    def save_items(self, items: List[Dict[str, Any]], indexer: str) -> int:
        """
        Save items to the CSV file.
        
        Args:
            items: List of item dictionaries to save
            
        Returns:
            Number of items saved
        """
        if not items:
            return 0
        
        try:
            # Get existing headers from the CSV file
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
            
            # Append items to the CSV file
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                
                for item in items:
                    # Filter out any keys not in headers
                    filtered_item = {k: v for k, v in item.items() if k in headers}
                    writer.writerow(filtered_item)
            
            logger.info(f"Saved {len(items)} items to CSV")
            return len(items)
            
        except Exception as e:
            logger.error(f"Error saving items to CSV: {str(e)}")
            return 0
    
    def save_resume_state(self, last_date: str):
        """
        Save the resume state to allow continuing from where we left off.
        
        Args:
            last_date: The last date processed (YYYYMMDD format)
        """
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(self.resume_path), exist_ok=True)
            
            state = {
                "last_date": last_date,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(self.resume_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
                
            logger.info(f"Saved resume state: last_date={last_date}")
            
        except Exception as e:
            logger.error(f"Error saving resume state: {str(e)}")
    
    def load_resume_state(self) -> Optional[str]:
        """
        Load the resume state to continue from where we left off.
        
        Returns:
            The last date processed (YYYYMMDD format) or None if no state exists
        """
        if not os.path.exists(self.resume_path):
            logger.info("No resume state found, starting from the beginning")
            return None
        
        try:
            with open(self.resume_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            last_date = state.get("last_date")
            if last_date:
                logger.info(f"Loaded resume state: last_date={last_date}")
                return last_date
            else:
                logger.warning("Invalid resume state: missing last_date")
                return None
                
        except Exception as e:
            logger.error(f"Error loading resume state: {str(e)}")
            return None


def get_storer(target: str):
    """Get the storage handler based on the target."""
    if target == "index":
        return CsvStorage(Config())
    elif target == "document":
        return FileStorage(Config())
    else:
        raise ValueError(f"Invalid target: {target}")
