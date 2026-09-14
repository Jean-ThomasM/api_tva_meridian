from sqlalchemy import create_engine, text
engine = create_engine('postgresql://meridian:meridian@localhost:5435/tva')
with engine.connect() as conn:
    res = conn.execute(text("SELECT numero_tva_brut, motif_structurel FROM tva_records WHERE motif_structurel IN ('FORMAT_INVALIDE', 'CLE_CONTROLE_INVALIDE', 'ERREUR_STRUCTURELLE_INCONNUE') LIMIT 30"))
    for row in res.fetchall(): print(row)
