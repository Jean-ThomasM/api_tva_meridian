import httpx
import time
import logging
from typing import Tuple, Optional
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VIES_API_URL = "https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number"

def check_vies(country_code: str, vat_number: str) -> Tuple[str, Optional[str]]:
    """
    Appelle l'API REST de VIES pour vérifier un numéro de TVA.
    Retourne un tuple: (verdict, motif_erreur)
    verdict peut être: "VALIDE", "INVALIDE", "INDETERMINE"
    """
    # Enlever le country code du numéro s'il y est, car VIES attend le numéro sans le préfixe
    if vat_number.startswith(country_code):
        vat_number = vat_number[len(country_code):]

    payload = {
        "countryCode": country_code,
        "vatNumber": vat_number
    }

    try:
        # Timeout généreux car VIES peut être lent
        with httpx.Client(timeout=15.0) as client:
            response = client.post(VIES_API_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Gestion des erreurs de l'API VIES (ex: MS_UNAVAILABLE, TIMEOUT)
            if "errorWrappers" in data and data["errorWrappers"]:
                error_msg = data["errorWrappers"][0].get("error", "UNKNOWN_ERROR")
                logger.warning(f"VIES Error pour {country_code}{vat_number}: {error_msg}")
                return "INDETERMINE", error_msg

            if data.get("valid") is True:
                return "VALIDE", None
            elif data.get("valid") is False:
                return "INVALIDE", None
            else:
                logger.warning(f"Réponse inattendue de VIES pour {country_code}{vat_number}: {data}")
                return "INDETERMINE", "REPONSE_INATTENDUE"
                
    except httpx.HTTPError as e:
        logger.error(f"Erreur HTTP lors de l'appel VIES pour {country_code}{vat_number}: {e}")
        return "INDETERMINE", "ERREUR_RESEAU"
    except Exception as e:
        logger.error(f"Erreur inattendue pour {country_code}{vat_number}: {e}")
        return "INDETERMINE", "ERREUR_SYSTEME"

