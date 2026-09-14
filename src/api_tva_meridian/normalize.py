import re
from stdnum.eu import vat as eu_vat
from stdnum.exceptions import ValidationError, InvalidFormat, InvalidChecksum, InvalidLength

def clean_vat_string(vat_str: str) -> str:
    """Nettoie le numÃ©ro de TVA (enlÃ¨ve espaces, tirets, points) et met en majuscules."""
    if not vat_str or not isinstance(vat_str, str) or str(vat_str).strip().upper() in ("NAN", "NULL", "NONE"):
        return ""
    # On retire tout ce qui n'est pas alphanumÃ©rique
    return re.sub(r'[^A-Za-z0-9]', '', vat_str).upper()

def normalize_and_validate(pays_declare: str, numero_tva_brut: str):
    """
    Normalise et vÃ©rifie structurellement un numÃ©ro de TVA.
    Renvoie : (numero_normalise, pays_deduit, verdict_structurel, motif)
    """
    # 1. Normalisation
    cleaned = clean_vat_string(numero_tva_brut)
    if not cleaned:
        return "", pays_declare, "INVALIDE", "VIDE_OU_NUL"

    pays_deduit = pays_declare
    
    # Si le numÃ©ro ne commence pas par le code pays, on peut supposer qu'il manque.
    # Ex: SI le pays dÃ©clarÃ© est FR, et que le numÃ©ro est 12345678901
    if pays_declare and not cleaned.startswith(pays_declare.upper()):
        # On tente de prÃ©fixer par le pays dÃ©clarÃ©, sauf si le numÃ©ro possÃ¨de dÃ©jÃ  un code pays valide au dÃ©but
        if len(cleaned) >= 2 and cleaned[:2].isalpha():
            # Il a dÃ©jÃ  un prÃ©fixe lettre, c'est peut-Ãªtre le vrai pays
            pays_deduit = cleaned[:2]
        else:
            cleaned = pays_declare.upper() + cleaned

    # Si on n'a toujours pas de code pays valide, stdnum.eu.vat va planter
    if len(cleaned) < 3 or not cleaned[:2].isalpha():
        return cleaned, pays_deduit, "INVALIDE", "PAS_DE_CODE_PAYS"

    pays_deduit = cleaned[:2]

    # 2. Validation structurelle
    try:
        # eu_vat.validate lÃ¨ve une exception si invalide, ou retourne le numÃ©ro compact si valide
        validated_num = eu_vat.validate(cleaned)
        return validated_num, pays_deduit, "VALIDE", "OK"
    except (InvalidFormat, InvalidChecksum, InvalidLength) as original_error:
        # Tentative de correction du bruit de saisie (O -> 0, I -> 1)
        if len(cleaned) > 2:
            corrected = cleaned[:2] + cleaned[2:].replace('O', '0').replace('I', '1')
            if corrected != cleaned:
                try:
                    validated_num = eu_vat.validate(corrected)
                    return validated_num, pays_deduit, "VALIDE", "OK"
                except Exception:
                    pass
        # Si la correction échoue, on relève l'erreur d'origine
        if isinstance(original_error, InvalidFormat):
            return cleaned, pays_deduit, "INVALIDE", "FORMAT_INVALIDE"
        elif isinstance(original_error, InvalidChecksum):
            return cleaned, pays_deduit, "INVALIDE", "CLE_CONTROLE_INVALIDE"
        else:
            return cleaned, pays_deduit, "INVALIDE", "LONGUEUR_INVALIDE"
    except ValidationError as e:
        return cleaned, pays_deduit, "INVALIDE", "ERREUR_STRUCTURELLE_INCONNUE"
    except Exception as e:
        return cleaned, pays_deduit, "INVALIDE", "PAYS_NON_SUPPORTE_OU_INCONNU"

