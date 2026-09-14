from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel

from src.api_tva_meridian.database import get_db, SessionLocal
from src.api_tva_meridian.models import TvaRecord
from src.api_tva_meridian.normalize import normalize_and_validate
from src.api_tva_meridian.vies import check_vies

app = FastAPI(title="API Validation TVA Meridian", description="Service de validation de numéros de TVA intracommunautaires.")

class ValidationResponse(BaseModel):
    verdict: str  # VALIDE, INVALIDE, INDETERMINE
    origine: str  # VIES_FRAIS, CACHE, STRUCTUREL
    fraicheur: datetime
    motif: Optional[str] = None

MAX_CACHE_DAYS = 30

@app.get("/validate/{pays}/{numero}", response_model=ValidationResponse)
def validate_tva(
    pays: str = Path(..., title="Code pays d'origine (ex: FR)"), 
    numero: str = Path(..., title="Numéro de TVA brut"),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    
    # 1. Normalisation et vérification structurelle
    numero_normalise, pays_deduit, verdict_struct, motif_struct = normalize_and_validate(pays, numero)
    
    if verdict_struct == "INVALIDE":
        return ValidationResponse(
            verdict="INVALIDE",
            origine="STRUCTUREL",
            fraicheur=now,
            motif=motif_struct
        )
        
    # 2. Recherche en base
    # On prend l'enregistrement le plus récent s'il y en a plusieurs
    record = db.query(TvaRecord).filter(
        TvaRecord.numero_tva_normalise == numero_normalise
    ).order_by(TvaRecord.date_verification_en_ligne.desc()).first()
    
    # Doit-on appeler VIES ?
    need_vies_call = False
    if not record or not record.verdict_en_ligne or record.verdict_en_ligne == "INDETERMINE":
        need_vies_call = True
    else:
        # On a une valeur. Est-elle trop vieille ?
        if record.date_verification_en_ligne:
            # S'assurer que les dates sont comparables (timezone aware)
            date_verif = record.date_verification_en_ligne
            if date_verif.tzinfo is None:
                date_verif = date_verif.replace(tzinfo=timezone.utc)
                
            age = now - date_verif
            if age > timedelta(days=MAX_CACHE_DAYS):
                need_vies_call = True
                
    if not need_vies_call:
        return ValidationResponse(
            verdict=record.verdict_en_ligne,
            origine="CACHE",
            fraicheur=record.date_verification_en_ligne,
            motif="Valeur connue et récente"
        )
        
    # 3. Appel VIES (si nécessaire ou cache expiré)
    verdict_vies, error = check_vies(pays_deduit, numero_normalise)
    
    if verdict_vies == "INDETERMINE":
        # Si VIES échoue, a-t-on une vieille valeur en cache ?
        if record and record.verdict_en_ligne and record.verdict_en_ligne != "INDETERMINE":
            return ValidationResponse(
                verdict=record.verdict_en_ligne,
                origine="CACHE",
                fraicheur=record.date_verification_en_ligne,
                motif="VIES injoignable, repli sur vieille valeur connue"
            )
        else:
            return ValidationResponse(
                verdict="INDETERMINE",
                origine="VIES_FRAIS",
                fraicheur=now,
                motif=f"VIES injoignable: {error}"
            )
            
    # Mise à jour ou insertion dans la base
    if record:
        record.verdict_en_ligne = verdict_vies
        record.date_verification_en_ligne = now
    else:
        new_record = TvaRecord(
            pays_declare=pays,
            numero_tva_brut=numero,
            numero_tva_normalise=numero_normalise,
            pays_deduit=pays_deduit,
            verdict_structurel=verdict_struct,
            motif_structurel=motif_struct,
            verdict_en_ligne=verdict_vies,
            date_verification_en_ligne=now
        )
        db.add(new_record)
        
    db.commit()
    
    return ValidationResponse(
        verdict=verdict_vies,
        origine="VIES_FRAIS",
        fraicheur=now,
        motif="Vérification en ligne réussie"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api_tva_meridian.main:app", host="0.0.0.0", port=8000, reload=True)
