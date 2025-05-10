"""
Parser for BOE API XML responses.
"""
import copy
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Any

from git_legal.storage import LawInfo

# Set up logging
logger = logging.getLogger(__name__)

def date_to_timestamp(date_str: int | str) -> int:
    """
    Convert a date string in YYYYMMDD format to UTC timestamp.

    Args:
        date_str: Date string in YYYYMMDD format (e.g., "20240315")

    Returns:
        Integer UTC timestamp in seconds

    Example:
        >>> date_to_timestamp(20240315)
        1710460800
    """
    if type(date_str) == int:
        date_str = str(date_str)

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
    def parse(xml_content: str) -> List[LawInfo]:
        """
        Parse the XML content from a BOE API response.
        
        Args:
            xml_content: XML string from the API
            
        Returns:
            List of dictionaries containing the extracted data
        """
        try:
            law_info = LawInfo()

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
            law_info.fecha_publicacion = metadata["fecha_publicacion"]
            law_info.fecha_publicacion = int(law_info.fecha_publicacion) if law_info.fecha_publicacion else None
            law_info.timestamp = date_to_timestamp(law_info.fecha_publicacion)
            
            # Extract items
            items = []
            
            for diario_item in root.findall(".//diario"):
                # Deal with diario
                sumario_diario = diario_item.find(".//sumario_diario")
                if sumario_diario is not None and sumario_diario.tag == "sumario_diario":
                    law_info.numero_diario = sumario_diario.get("numero", None)
                else:
                    law_info.identificador_diario = None


                for seccion_item in diario_item.findall(".//seccion"):
                    law_info.seccion_codigo = seccion_item.get("codigo", "")
                    law_info.seccion_nombre = seccion_item.get("nombre", "")

                    for departamento_item in seccion_item.findall(".//departamento"):
                        law_info.departamento_codigo = departamento_item.get("codigo", "")
                        law_info.departamento_nombre = departamento_item.get("nombre", "")

                        for epigrafe_elem in departamento_item.findall(".//epigrafe"):
                            law_info.epigrafe_nombre = epigrafe_elem.get("nombre", "")
                            law_info = IndexXmlParser.decode_item(law_info, epigrafe_elem)
                            items.append(copy.copy(law_info))
                        else:
                            law_info.epigrafe_nombre = None
                            law_info = IndexXmlParser.decode_item(law_info, departamento_item)
                            items.append(copy.copy(law_info))
            return items
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error parsing XML: {str(e)}")
            return []

    @staticmethod
    def decode_item(item: LawInfo, epigrafe_elem):
        for item_elem in epigrafe_elem.findall(".//item"):
            item.epigrafe_nombre = epigrafe_elem.get("nombre", None)

            # Extract URLs
            for url_type in ["url_pdf", "url_html", "url_xml", "titulo", "identificador", "control"]:
                url_elem = item_elem.find(f".//{url_type}")
                if url_elem is not None:
                    setattr(item, url_type, url_elem.text.strip() if url_elem.text else "")
                else:
                    setattr(item, url_type, None)
        return item
