from sqlalchemy import create_engine, text
import argparse

from src.api_tva_meridian.database import DATABASE_URL

def generate_report():
    engine = create_engine(DATABASE_URL)
    
    print("=======================================")
    print("   RAPPORT DE RECONCILIATION TVA       ")
    print("=======================================\n")
    
    with engine.connect() as conn:
        # 1. Vue d'ensemble
        total = conn.execute(text("SELECT count(*) FROM tva_records")).scalar()
        print(f"Total des enregistrements: {total}")
        
        # 2. Validation Structurelle
        print("\n--- Validation Structurelle ---")
        res = conn.execute(text("SELECT verdict_structurel, motif_structurel, count(*) FROM tva_records GROUP BY verdict_structurel, motif_structurel ORDER BY count(*) DESC"))
        for verdict, motif, count in res.fetchall():
            print(f"[{verdict}] {motif}: {count}")
            
        # 3. Doublons
        print("\n--- Doublons et Réduction ---")
        valides = conn.execute(text("SELECT count(*) FROM tva_records WHERE verdict_structurel = 'VALIDE'")).scalar()
        uniques = conn.execute(text("SELECT count(DISTINCT numero_tva_normalise) FROM tva_records WHERE verdict_structurel = 'VALIDE'")).scalar()
        print(f"Numéros structurellement valides : {valides}")
        print(f"Numéros uniques à vérifier       : {uniques}")
        print(f"Appels VIES économisés (doublons): {valides - uniques}")
        
        # 4. Validation en ligne (VIES)
        print("\n--- Validation en ligne (VIES) ---")
        # Sur l'ensemble des records structurellement valides
        res = conn.execute(text("SELECT verdict_en_ligne, count(*) FROM tva_records WHERE verdict_structurel = 'VALIDE' GROUP BY verdict_en_ligne"))
        stats_vies = {row[0]: row[1] for row in res.fetchall()}
        
        # Formatage propre
        print(f"VALIDE      : {stats_vies.get('VALIDE', 0)}")
        print(f"INVALIDE    : {stats_vies.get('INVALIDE', 0)}")
        print(f"INDETERMINE : {stats_vies.get('INDETERMINE', 0)}")
        print(f"NON TESTE   : {stats_vies.get(None, 0)}")
        
    print("\n=======================================")
    print("Fin du rapport.")

if __name__ == "__main__":
    generate_report()
