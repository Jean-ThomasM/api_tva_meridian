from src.api_tva_meridian.database import engine, Base
from src.api_tva_meridian.models import TvaRecord

def init_db():
    print("CrÃ©ation des tables dans la base de donnÃ©es...")
    Base.metadata.create_all(bind=engine)
    print("Tables crÃ©Ã©es avec succÃ¨s.")

if __name__ == "__main__":
    init_db()
