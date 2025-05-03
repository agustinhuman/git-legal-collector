"""
Parser for BOE API XML responses.
"""
from datetime import datetime
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
import logging

# Set up logging
logger = logging.getLogger(__name__)


def date_to_timestamp(date_str: str) -> int:
    """
    Convert a date string in YYYYMMDD format to UTC timestamp.

    Args:
        date_str: Date string in YYYYMMDD format (e.g., "20240315")

    Returns:
        Integer UTC timestamp in seconds

    Example:
        >>> date_to_timestamp("20240315")
        1710460800
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        timestamp = int(date_obj.timestamp())
        return timestamp
    except ValueError as e:
        return 0


class LawXmlParser:
    @staticmethod
    def parse(xml_content: str):
       return xml_content


def get_parser(target: str):
    if target == "index":
        return IndexXmlParser()
    elif target == "document":
        return LawXmlParser()
    else:
        raise ValueError(
            f"Invalid target: {target}. "
            "Valid targets are 'index' and 'document'."
        )

class IndexXmlParser:
    """Parser for BOE API XML responses."""
    
    @staticmethod
    def parse(xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse the XML content from a BOE API response.
        
        Args:
            xml_content: XML string from the API
            
        Returns:
            List of dictionaries containing the extracted data
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Check if the response is valid
            status_code = root.find(".//status/code")
            if status_code is None or status_code.text != "200":
                logger.error("Invalid response: status code not 200")
                return []
            
            # Extract metadata
            metadata = {}
            metadatos_elem = root.find(".//metadatos")
            if metadatos_elem is not None:
                for child in metadatos_elem:
                    metadata[child.tag] = child.text
            
            metadata["timestamp"] = date_to_timestamp(metadata.get("fecha_publicacion", ""))
            
            # Extract items
            items = []
            
            for diario_item in root.findall(".//diario"):
                # Deal with diario
                diario = {}
                sumario_diario = diario_item.find(".//sumario_diario")
                if sumario_diario is not None and sumario_diario.tag == "sumario_diario":
                    diario["identificador"] = sumario_diario.get("identificador", "")
                    diario["url_pdf "] = sumario_diario.get("url_pdf ", "")

                seccion_item = None
                for seccion_candidate in diario_item.findall(".//seccion"):
                    if seccion_candidate.get("codigo", "") == "1":
                        seccion_item = seccion_candidate
                if seccion_item is None:
                    continue

                departamento = {}
                for departamento_item in seccion_item.findall(".//departamento"):
                    departamento["departamento_codigo"] = departamento_item.get("codigo", "")
                    departamento["departamento_nombre"] = departamento_item.get("nombre", "")

                    epigrafe = {}
                    for epigrafe_elem in departamento_item.findall(".//epigrafe"):
                        epigrafe["epigrafe_nombre"] = epigrafe_elem.get("nombre", "")
                        item = IndexXmlParser.decode_item(epigrafe, epigrafe_elem)
                        consolidated_item = {**item, **epigrafe, **departamento, **diario, **metadata}
                        items.append(consolidated_item)
                    else:
                        item = IndexXmlParser.decode_item({}, departamento_item)
                        consolidated_item = {**item, **departamento, **diario, **metadata}
                        items.append(consolidated_item)
            return items
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error parsing XML: {str(e)}")
            return []

    @staticmethod
    def decode_item(epigrafe, epigrafe_elem):
        item = {}
        for item_elem in epigrafe_elem.findall(".//item"):
            epigrafe["epigrafe_nombre"] = epigrafe_elem.get("nombre", "")

            # Extract URLs
            for url_type in ["url_pdf", "url_html", "url_xml"]:
                url_elem = item_elem.find(f".//{url_type}")
                if url_elem is not None:
                    item[url_type] = url_elem.text.strip() if url_elem.text else ""

                    # Extract attributes for PDF
                    if url_type == "url_pdf":
                        for attr in ["szBytes", "szKBytes", "pagina_inicial", "pagina_final"]:
                            if attr in url_elem.attrib:
                                item[f"{url_type}_{attr}"] = url_elem.attrib[attr]
        return item
