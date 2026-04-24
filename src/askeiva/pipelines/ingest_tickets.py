import os
import weaviate
from weaviate.util import generate_uuid5
from dotenv import load_dotenv

# Relative imports for the pipeline neighborhood
from .freshdesk_crawler import FreshdeskCrawler
from .ticket_processor import TicketProcessor

load_dotenv()

class DataIngestionEngine:
    """Orchestrates the ingestion of structured tickets into Weaviate as semantic chunks."""
    
    def __init__(self):
        # Establish link to the cloud cluster
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
            headers={
                "X-Mistral-Api-Key": os.getenv("MISTRAL_API_KEY")
            }
        )
        self.collection = self.client.collections.get("KnowledgeNode")

    def run_ticket_ingestion(self, domain="eiva", fetch_count=5):
        from tqdm import tqdm
        print(f"--- Initiating Ticket Ingestion for {domain} ---")
        crawler = FreshdeskCrawler(domain=domain)
        processor = TicketProcessor()

        raw_tickets = crawler.fetch_tickets(per_page=fetch_count)
        clean_tickets = processor.process_tickets_with_dialogue(raw_tickets, crawler, domain)

        # Wrap the loop in tqdm for a progress bar
        with self.collection.batch.dynamic() as batch:
            for ticket in tqdm(clean_tickets, desc="Ingesting Tickets", unit="ticket"):
                chunks = processor.chunk_text(ticket["content"])
                
                for i, chunk_content in enumerate(chunks):
                    chunk_id = f"{ticket['source_id']}_part_{i}"
                    batch.add_object(
                        uuid=generate_uuid5(chunk_id),
                        properties={
                            "source_id": chunk_id,
                            "data_type": ticket["data_type"],
                            "subject": f"{ticket['subject']} (Part {i+1})" if len(chunks) > 1 else ticket['subject'],
                            "content": chunk_content,
                            "url": ticket["url"],
                            "status": ticket["status"],
                            "priority": ticket["priority"],
                            "tags": ticket["tags"],
                            "attachment_urls": ticket["attachment_urls"]
                        }
                    )
        print("\n--- Ticket Ingestion Sequence Complete ---")

    def close(self):
        self.client.close()

if __name__ == "__main__":
    engine = DataIngestionEngine()
    try:
        # Starting with a small batch to ensure the chunking is perfect
        engine.run_ticket_ingestion(domain="eiva", fetch_count=5)
    finally:
        engine.close()