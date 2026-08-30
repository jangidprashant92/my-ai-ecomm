
import pandas as pd
from app.database.session import engine
from sqlalchemy import insert
from sqlmodel import SQLModel


def ingest_csv(
    csv_path: str,
    model: type[SQLModel],
    date_columns: list[str] | None = None,
    chunksize: int = 5000,
):
    print(f"Loading {csv_path}")

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            csv_path,
            chunksize=chunksize,
        ),
        start=1,
    ):

        # --------------------------------
        # Convert datetime columns
        # --------------------------------

        if date_columns:
            for column in date_columns:

                if column in chunk.columns:

                    chunk[column] = pd.to_datetime(
                        chunk[column],
                        errors="coerce",
                    )

        # --------------------------------
        # Convert NaN -> None
        # --------------------------------

        chunk = chunk.astype(object)

        chunk = chunk.where(
            pd.notnull(chunk),
            None,
        )

        records = chunk.to_dict(
            orient="records"
        )

        # --------------------------------
        # Bulk insert
        # --------------------------------

        with engine.begin() as connection:

            connection.execute(
                insert(model),
                records,
            )

        print(
            f"Chunk {chunk_number}: "
            f"{len(records)} rows inserted"
        )

    print(f"Finished: {csv_path}")