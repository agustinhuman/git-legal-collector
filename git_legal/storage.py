"""
Storage module for saving BOE data to CSV and managing resume state.
"""
import abc
import csv
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

from git_legal.config import Config

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class LawInfo:
    fecha_publicacion: int | None = None
    timestamp: int | None = None
    identificador: str | None = None
    control: str | None = None
    titulo: str | None = None
    numero_diario: str | None = None
    url_html: str | None = None
    url_xml: str | None = None
    url_pdf: str | None = None
    seccion_codigo: str | None = None
    seccion_nombre: str | None = None
    departamento_codigo: str | None = None
    departamento_nombre: str | None = None
    epigrafe_nombre: str | None = None

    def to_iterable(self):
        return iter(
            [
                self.fecha_publicacion,
                self.timestamp,
                self.identificador,
                self.numero_diario,
                self.control,
                self.titulo,
                self.url_pdf,
                self.url_html,
                self.url_xml,
                self.seccion_codigo,
                self.seccion_nombre,
                self.departamento_codigo,
                self.departamento_nombre,
                self.epigrafe_nombre
            ]
        )

    @staticmethod
    def get_header():
        return [
            "fecha_publicacion",
            "timestamp",
            "identificador",
            "numero_diario",
            "control",
            "titulo",
            "url_pdf",
            "url_html",
            "url_xml",
            "seccion_codigo",
            "seccion_nombre",
            "departamento_codigo",
            "departamento_nombre",
            "epigrafe_nombre"
        ]


class FileStorage:
    """Storage handler for BOE data."""

    def __init__(self, config: Config):
        """Initialize the storage handler with configuration."""
        self.config = config

    def save_item(self, data: str, law_info: LawInfo, extension: str = "pdf" ):
        seccion = law_info.seccion_nombre or "OTROS"
        key = law_info.identificador
        folder = Path(self.config.output) / extension / seccion
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{key}.{extension}"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(data)
        logger.info(f"Saved document to {path}")
        return 1



class CsvStorage:
    """Storage handler for BOE index."""
    
    def __init__(self, config: Config):
        """Initialize the storage handler with configuration."""
        self.config = config
        self.csv_path = os.path.join(self.config.output, self.config.csv_filename)
        
        # Create CSV file with headers if it doesn't exist
        self.data = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        self._ensure_csv_exists()
        df = pd.read_csv(self.csv_path)
        df.replace(np.nan, None)
        return df.sort_values('fecha_publicacion')


    def get_values_for_date(self, date: int) -> list[LawInfo] | None:
        if self.data.empty or date > self.data.fecha_publicacion.max() or date < self.data.fecha_publicacion.min():
            return None
        rows = self.data.loc[self.data["fecha_publicacion"] == date]
        decoded_rows = [
            LawInfo(**record)
            for record
            in rows.to_dict(orient='records')
        ]
        return decoded_rows



    
    def _ensure_csv_exists(self):
        """Ensure the CSV file exists with headers."""
        if not os.path.exists(self.csv_path):
            logger.info(f"Creating new CSV file: {self.csv_path}")
            # Define the headers based on the expected data structure
            headers = LawInfo.get_header()
            
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
    
    def save_items(self, items: List[LawInfo]) -> int:
        """
        Save items to the CSV file.
        
        Args:
            items: List of item dictionaries to save
            
        Returns:
            Number of items saved
        """
        if not items:
            return 0

        dicts = [item.__dict__ for item in items]

        try:
            # Get existing headers from the CSV file
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
            
            # Append items to the CSV file
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                
                for item in dicts:
                    # Filter out any keys not in headers
                    filtered_item = {k: v for k, v in item.items() if k in headers}
                    writer.writerow(filtered_item)

            self.data = pd.concat([self.data, pd.DataFrame.from_records(dicts)], ignore_index=True)
            logger.info(f"Saved {len(items)} items to CSV")

            return len(items)
            
        except Exception as e:
            logger.error(f"Error saving items to CSV: {str(e)}")
            return 0
    
class ResumeStorage:

    def __init__(self, config: Config):
        self.config = config
        self.resume_path = os.path.join(self.config.output, "resume.json")

    def save_resume_state(self, last_date: int):
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

    def load_resume_state(self) -> Optional[int]:
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
                last_date = int(last_date)
                logger.info(f"Loaded resume state: last_date={last_date}")
                return last_date
            else:
                logger.warning("Invalid resume state: missing last_date")
                return None

        except Exception as e:
            logger.error(f"Error loading resume state: {str(e)}")
            return None
