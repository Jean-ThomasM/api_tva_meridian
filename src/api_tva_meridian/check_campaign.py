import argparse
import time
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.api_tva_meridian.database import SessionLocal
from src.api_tva_meridian.models import TvaRecord
from src.api_tva_meridian.vies import check_vies

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_campaign(sample_size: int = None, delay_seconds: float = 1.0):
    session = SessionLocal()
    
    try:
        # On cherche les numéros normalisés uniques qui sont structurellement valides
        # et qui n'ont pas de verdict final (None ou INDETERMINE)
        query = (
            select(TvaRecord.numero_tva_normalise, TvaRecord.pays_deduit)
            .where(TvaRecord.verdict_structurel == 'VALIDE')
            .where((TvaRecord.verdict_en_ligne.is_(None)) | (TvaRecord.verdict_en_ligne == 'INDETERMINE'))
            .distinct()
        )
        
        if sample_size is not None:
            query = query.limit(sample_size)
            
        results = session.execute(query).fetchall()
        total = len(results)
        
        logger.info(f"Début de la campagne: {total} numéros uniques à vérifier (mode échantillon: {sample_size}).")
        
        for i, (numero_normalise, pays_deduit) in enumerate(results, 1):
            logger.info(f"[{i}/{total}] Vérification de {numero_normalise} ...")
            
            verdict, error = check_vies(pays_deduit, numero_normalise)
            now = datetime.now(timezone.utc)
            
            # On met à jour TOUS les enregistrements qui partagent ce numéro normalisé
            # C'est ici que l'on capitalise sur la déduplication !
            records_to_update = session.query(TvaRecord).filter_by(numero_tva_normalise=numero_normalise).all()
            for record in records_to_update:
                record.verdict_en_ligne = verdict
                record.date_verification_en_ligne = now
                
            session.commit()
            
            if verdict == 'INDETERMINE':
                logger.warning(f"  -> {verdict} ({error})")
            else:
                logger.info(f"  -> {verdict}")
                
            if i < total:
                time.sleep(delay_seconds)
                
        logger.info("Campagne terminée avec succès.")

    except Exception as e:
        logger.error(f"La campagne a été interrompue par une erreur: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Campagne de vérification VIES")
    parser.add_argument("--sample", type=int, default=None, help="Nombre de numéros uniques à vérifier (mode échantillon)")
    parser.add_argument("--delay", type=float, default=1.0, help="Délai entre les requêtes (secondes)")
    args = parser.parse_args()
    
    run_campaign(sample_size=args.sample, delay_seconds=args.delay)
