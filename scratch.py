from sqlalchemy import create_engine, text
engine = create_engine("postgresql://meridian:meridian@localhost:5435/tva")
with engine.connect() as conn:
    print("ERREUR_STRUCTURELLE_INCONNUE:")
    res = conn.execute(text("SELECT numero_tva_brut, pays_declare, numero_tva_normalise FROM tva_records WHERE motif_structurel = 'ERREUR_STRUCTURELLE_INCONNUE' LIMIT 10"))
    for row in res.fetchall(): print(row)
    print("\nFORMAT_INVALIDE:")
    res = conn.execute(text("SELECT numero_tva_brut, pays_declare, numero_tva_normalise FROM tva_records WHERE motif_structurel = 'FORMAT_INVALIDE' LIMIT 10"))
    for row in res.fetchall(): print(row)
