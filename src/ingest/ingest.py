import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to sys.path and import the model definition
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from model import Base


def create_db(filename):
    # Create the SQLite database file
    engine = create_engine(f"sqlite:///{filename}", echo=True)

    # Create the tables in the database
    Base.metadata.create_all(engine)

    # Create a session to interact with the database
    Session = sessionmaker(bind=engine)
    session = Session()

    # Commit the changes to the database
    session.commit()

    # Close the session
    session.close()


if __name__ == "__main__":
    create_db("test.db")
