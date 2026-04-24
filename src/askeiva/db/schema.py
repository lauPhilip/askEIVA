import os
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """Manages the connection and schema for the Weaviate Cloud cluster."""
    
    def __init__(self):
        # Connect to Weaviate Cloud, passing the Mistral key so Weaviate can auto-vectorize
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
            headers={
                "X-Mistral-Api-Key": os.getenv("MISTRAL_API_KEY")
            }
        )

    def initialize_schema(self):
        """Builds the dual-collection schema with relational graph edges."""
        if not self.client.is_ready():
            print("Failed to connect to the cloud cluster.")
            return

        # 1. Forge the Document Library (The Raw Materials)
        doc_collection_name = "DocumentLibrary"
        if not self.client.collections.exists(doc_collection_name):
            print(f"Constructing '{doc_collection_name}'...")
            self.client.collections.create(
                name=doc_collection_name,
                vectorizer_config=Configure.Vectorizer.text2vec_mistral(),
                generative_config=Configure.Generative.mistral(model="mistral-large-latest"),
                properties=[
                    Property(name="document_id", data_type=DataType.TEXT, skip_vectorization=True),
                    Property(name="title", data_type=DataType.TEXT),
                    Property(name="document_type", data_type=DataType.TEXT), # 'PDF_Manual', 'Blog_Post', etc.
                    Property(name="content", data_type=DataType.TEXT), # Full text or Mistral OCR markdown
                    Property(name="url", data_type=DataType.TEXT, skip_vectorization=True),
                    Property(name="image_urls", data_type=DataType.TEXT_ARRAY, skip_vectorization=True)
                ]
            )
        else:
            print(f"'{doc_collection_name}' is already online.")

        # 2. Forge the Knowledge Node (The Actionable Intel)
        knowledge_collection_name = "KnowledgeNode"
  
        
        if not self.client.collections.exists(knowledge_collection_name):
            print(f"Constructing '{knowledge_collection_name}' with relational edges...")
            
            # To create a reference, the target collection (DocumentLibrary) must exist first
            from weaviate.classes.config import ReferenceProperty
            
            self.client.collections.create(
                name=knowledge_collection_name,
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
                # This is the critical graph edge linking a ticket to a master document
                references=[
                    ReferenceProperty(
                        name="hasSourceDocument",
                        target_collection=doc_collection_name
                    )
                ]
            )
            print("Relational schema successfully initialized.")
        else:
            print(f"'{knowledge_collection_name}' is already online.")

    def close(self):
        """Always sever the connection gracefully."""
        self.client.close()

if __name__ == "__main__":
    db = DatabaseManager()
    try:
        db.initialize_schema()
    finally:
        db.close()