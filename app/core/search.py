from typing import List

from tantivy import Index, SchemaBuilder, Document
from sqlmodel import SQLModel, select

from app.core.db import get_session
from app.core.logger import logger
from app.data.db import Exercise

Exercise_search = None


def create_index(model: SQLModel, searchable_fields: List[str]) -> SchemaBuilder:
    schema_builder = SchemaBuilder()

    for field in searchable_fields:
        schema_builder.add_text_field(field, stored=True)

    schema = schema_builder.build()
    index = Index(schema)

    writer = index.writer()

    for session in get_session():
        documents: List[SQLModel] = session.exec(select(model)).all()
        for document in documents:
            writer.add_document(
                Document().from_dict(document.model_dump(exclude_none=True))
            )
        writer.commit()


def init_search():
    global Exercise_search

    Exercise_search = create_index(Exercise, ["name", "description"])
    logger.info("Search indexes created")
