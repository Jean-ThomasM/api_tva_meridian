from sqlalchemy import Column, Integer, String, Date, DateTime
from src.api_tva_meridian.database import Base

class TvaRecord(Base):
    __tablename__ = "tva_records"

    # DonnÃ©es brutes (reÃ§ues)
    id = Column(Integer, primary_key=True, index=True) # MÃªme ID que le CSV pour traÃ§abilitÃ©
    raison_sociale = Column(String, nullable=True)
    pays_declare = Column(String, nullable=True)
    numero_tva_brut = Column(String, nullable=True)
    date_saisie = Column(Date, nullable=True)
    source_saisie = Column(String, nullable=True)

    # DonnÃ©es dÃ©duites (normalisation et validation structurelle)
    numero_tva_normalise = Column(String, nullable=True)
    pays_deduit = Column(String, nullable=True)
    verdict_structurel = Column(String, nullable=True) # "VALIDE", "INVALIDE"
    motif_structurel = Column(String, nullable=True)

    # DonnÃ©es VIES (vÃ©rification en ligne)
    verdict_en_ligne = Column(String, nullable=True) # "VALIDE", "INVALIDE", "INDETERMINE"
    date_verification_en_ligne = Column(DateTime, nullable=True)
