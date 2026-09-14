import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import sys

from src.api_tva_meridian.database import SessionLocal, engine
from src.api_tva_meridian.models import TvaRecord
from src.api_tva_meridian.normalize import normalize_and_validate

def load_csv(filepath: str):
    """Charge le CSV, normalise et insÃ¨re dans la base."""
    print(f"Chargement du fichier {filepath}...")
    df = pd.read_csv(filepath)
    
    # Remplacer les NaN par None pour la base de donnÃ©es
    df = df.where(pd.notnull(df), None)

    session: Session = SessionLocal()
    
    records = []
    
    print("Normalisation et validation structurelle en cours...")
    
    # On itÃ¨re sur le dataframe
    for _, row in df.iterrows():
        brut = row.get("numero_tva")
        pays_declare = row.get("pays_declare")
        
        # SÃ©curitÃ© si null
        if brut is None:
            brut = ""
        if pays_declare is None:
            pays_declare = ""
            
        numero_normalise, pays_deduit, verdict, motif = normalize_and_validate(str(pays_declare), str(brut))
        
        record = {
            "id": row["id"],
            "raison_sociale": row.get("raison_sociale"),
            "pays_declare": pays_declare,
            "numero_tva_brut": brut,
            "date_saisie": row.get("date_saisie"),
            "source_saisie": row.get("source_saisie"),
            
            "numero_tva_normalise": numero_normalise,
            "pays_deduit": pays_deduit,
            "verdict_structurel": verdict,
            "motif_structurel": motif
        }
        records.append(record)
    
    print(f"Insertion de {len(records)} lignes dans la base de donnÃ©es...")
    
    # Insertion en masse avec gestion des conflits (pour Ã©viter les doublons au rechargement)
    stmt = insert(TvaRecord).values(records)
    
    # En cas de conflit sur l'id, on met Ã  jour les valeurs
    update_dict = {
        c.name: c
        for c in stmt.excluded
        if not c.primary_key
    }
    
    stmt = stmt.on_conflict_do_update(
        index_elements=['id'],
        set_=update_dict
    )
    
    session.execute(stmt)
    session.commit()
    session.close()
    
    print("Chargement terminÃ© avec succÃ¨s.")

if __name__ == "__main__":
    filepath = "numeros_tva.csv"
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    load_csv(filepath)
