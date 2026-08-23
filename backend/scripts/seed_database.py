"""scripts/seed_database.py: Initializes tables and seeds raw data into Supabase."""

import asyncio
import json
import selectors
import sys

import aiofiles
from database.session import Base, SessionLocal, engine
from langchain_cloudflare import CloudflareWorkersAIEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector
from schemas.db_models import DiseaseTreatment


async def init_tables():
    """Instructs SQLAlchemy to create all tables defined in db_models.py if they do not exist."""
    async with engine.begin() as conn:
        print("Creating relational tables in Supabase...")
        await conn.run_sync(Base.metadata.create_all)


async def seed_all():
    """Seeds relational data into PostgreSQL and vector data into pgvector."""

    # Initialize tables
    await init_tables()

    # Load Raw Knowledge Base
    async with aiofiles.open("scripts/raw_data/paddy_diseases.json", mode="r") as f:
        contents = await f.read()
        data = json.loads(contents)

    vector_documents = []

    # Open Async SQLAlchemy Session
    async with SessionLocal() as session:
        for item in data:
            treatment_record = DiseaseTreatment(
                disease_name=item["disease_name"],
                treatment_guide_doc=item["treatment_guide_doc"],
                weather_constraints=item["weather_constraints"],
            )
            session.add(treatment_record)

            await session.flush()

            # Create Vector Document using the newly generated UUID
            doc = Document(
                page_content=item["diagnostic_text"],
                metadata={
                    "disease_id": str(treatment_record.disease_id),
                    "disease_name": item["disease_name"],
                    "valid_stages": item["valid_stages"],
                },
            )
            vector_documents.append(doc)

        await session.commit()
        print(f"Successfully seeded {len(data)} SQL treatment records.")

    # Ingest into PGVector via LangChain
    print("Initializing pgvector store and embedding documents...")

    embeddings = CloudflareWorkersAIEmbeddings(model_name="@cf/baai/bge-base-en-v1.5")

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="paddy_diseases",
        connection=engine,
        use_jsonb=True,
    )

    await vector_store.aadd_documents(documents=vector_documents)

    print(
        f"Successfully embedded {len(vector_documents)} diagnostic vectors into Supabase pgvector."
    )


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(
            seed_all(),
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        )
    else:
        asyncio.run(seed_all())
