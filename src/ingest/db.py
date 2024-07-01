import logging
from datetime import datetime
from sqlalchemy.orm import Session
from src.model import Base, Metadata, SourceMetadata


def create_schema(engine):
    """
    Create empty tables using defined SQLAlchemy model
    """
    Base.metadata.create_all(engine)


def clear_table_and_insert_data(session, table, df, df_column_order=None):
    """
    Deletes rows from the given table and reinsert data from dataframe
    table is a SQLAlchemy mapped class
    df_column_order specifies the names of the columns in df so they match the order of the table's SQLAlchemy definition
    """
    # Clear data in DB table
    session.query(table).delete()
    session.commit()

    # Reorder columns to match SQLAlchema table definition
    if df_column_order is not None:
        df = df[df_column_order]

    # Load data into table using Pandas to_sql
    logging.info(f"Loading table {table}")
    df.to_sql(
        table.__tablename__,
        con=session.bind,
        index=False,
        if_exists="append",
    )


def update_meta(engine, modified, contracted_hours_updated_month):
    """
    Populate the sources_meta table with metadata for the source files
    """
    # Write timestamps to DB
    logging.info("Writing metadata")
    with Session(engine) as session:
        # Clear metadata tables
        session.query(Metadata).delete()
        session.query(SourceMetadata).delete()
        session.commit()

        # Set last ingest time and other metadata fields
        session.add(
            Metadata(
                last_updated=datetime.now(),
                contracted_hours_updated_month=contracted_hours_updated_month,
            )
        )

        # Store last modified timestamps for ingested files
        for file, modified_time in modified.items():
            source_metadata = SourceMetadata(filename=file, modified=modified_time)
            session.add(source_metadata)

        session.commit()
