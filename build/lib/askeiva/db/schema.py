import os
import weaviate
from weaviate.classes.config import Configure, Property, DataType, ReferenceProperty
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """Manages the connection and schema for the Weaviate Cloud cluster using v4 standards."""
    
    def __init__(self):
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
            headers={
                "X-Mistral-Api-Key": os.getenv("MISTRAL_API_KEY")
            }
        )

    def initialize_schema(self):
        """Builds the triple-collection schema using the modern vector_config syntax."""
        if not self.client.is_ready():
            print("Failed to connect to the cloud cluster.")
            return

        # 1. Forge the Document Library (The Manuals)
        doc_name = "DocumentLibrary"
        if not self.client.collections.exists(doc_name):
            print(f"Constructing '{doc_name}' with modern vector config...")
            self.client.collections.create(
                name=doc_name,
                # Modern V4 Syntax: named vector configurations
                vector_config=Configure.VectorIndex.hnsw(),
                vectorizer_config=Configure.Vectorizer.text2vec_mistral(),
                generative_config=Configure.Generative.mistral(model="mistral-large-latest"),
                properties=[
                    Property(name="document_id", data_type=DataType.TEXT, skip_vectorization=True),
                    Property(name="title", data_type=DataType.TEXT),
                    Property(name="document_type", data_type=DataType.TEXT),
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="url", data_type=DataType.TEXT, skip_vectorization=True),
                    Property(name="image_urls", data_type=DataType.TEXT_ARRAY, skip_vectorization=True),
                    Property(name="tags", data_type=DataType.TEXT, description="Mistral-extracted entities")
                ]
            )

        # 2. Forge the Knowledge Node (The Tickets)
        knowledge_name = "KnowledgeNode"
        if not self.client.collections.exists(knowledge_name):
            print(f"Constructing '{knowledge_name}'...")
            self.client.collections.create(
                name=knowledge_name,
                vector_config=Configure.VectorIndex.hnsw(),
                vectorizer_config=Configure.Vectorizer.text2vec_mistral(),
                generative_config=Configure.Generative.mistral(model="mistral-large-latest"),
                properties=[
                    Property(name="source_id", data_type=DataType.TEXT, skip_vectorization=True),
                    Property(name="data_type", data_type=DataType.TEXT), 
                    Property(name="subject", data_type=DataType.TEXT),
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="url", data_type=DataType.TEXT, skip_vectorization=True),
                    Property(name="status", data_type=DataType.INT, skip_vectorization=True),
                    Property(name="priority", data_type=DataType.INT, skip_vectorization=True),
                    Property(name="tags", data_type=DataType.TEXT_ARRAY, skip_vectorization=True),
                    Property(name="attachment_urls", data_type=DataType.TEXT_ARRAY, skip_vectorization=True),
                ],
                references=[
                    ReferenceProperty(name="hasSourceDocument", target_collection=doc_name)
                ]
            )

        # 3. Forge the Interaction Log (The Feedback Loop)
        log_name = "InteractionLog"
        if not self.client.collections.exists(log_name):
            print(f"Constructing '{log_name}'...")
            self.client.collections.create(
                name=log_name,
                vector_config=Configure.VectorIndex.hnsw(),
                vectorizer_config=Configure.Vectorizer.text2vec_mistral(),
                properties=[
                    Property(name="query", data_type=DataType.TEXT),
                    Property(name="answer", data_type=DataType.TEXT),
                    Property(name="timestamp", data_type=DataType.DATE),
                    Property(name="referenced_doc_ids", data_type=DataType.TEXT_ARRAY),
                    Property(name="was_successful", data_type=DataType.BOOL),
                ]
            )
            print("--- [MODERN SCHEMA INITIALIZED] ---")
        else:
            print(f"Collections are already live")

    def close(self):
        self.client.close()

if __name__ == "__main__":
    db = DatabaseManager()
    try:
        db.initialize_schema()
    finally:
        db.close()