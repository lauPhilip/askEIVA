import os
import weaviate
from weaviate.util import generate_uuid5
from dotenv import load_dotenv
from pathlib import Path

# Fixed Relative Imports
from .freshdesk_crawler import FreshdeskCrawler
from .pdf_processor import PDFProcessor
from .ticket_processor import TicketProcessor

load_dotenv()

class KBIngestionEngine:
    def __init__(self):
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
            headers={"X-Mistral-Api-Key": os.getenv("MISTRAL_API_KEY")}
        )
        self.doc_collection = self.client.collections.get("DocumentLibrary")
        self.crawler = FreshdeskCrawler(domain="eiva")
        self.pdf_engine = PDFProcessor()
        self.html_cleaner = TicketProcessor()

    def run_assimilation(self):
        from tqdm import tqdm
        print("Initiating Multimodal Knowledge Base assimilation...")
        categories = self.crawler._get("solutions/categories")
        
        if not categories:
            print("No categories found.")
            return

        # We'll use a nested approach or just track articles
        for category in categories:
            folders = self.crawler._get(f"solutions/categories/{category['id']}/folders")
            for folder in folders:
                articles = self.crawler._get(f"solutions/folders/{folder['id']}/articles")
                
                # Progress bar for articles within each folder
                desc = f"Processing Folder: {folder['name'][:20]}..."
                with self.doc_collection.batch.dynamic() as batch:
                    for article in tqdm(articles, desc=desc, unit="art"):
                        self._process_article(article, folder['name'], batch)

    def _process_article(self, article, folder_name, batch):
        title = article['title']
        raw_html = article.get('description', '')
        base_text = self.html_cleaner.clean_html(raw_html)
        
        all_image_paths = []
        # Gather all text first
        full_content = f"Source: EIVA Help Center\nFolder: {folder_name}\nTitle: {title}\n\n{base_text}"
        
        attachments = article.get('attachments', [])
        for att in attachments:
            if att['name'].lower().endswith('.pdf'):
                self.crawler._download_pdf(att['attachment_url'], att['name'], folder_name)
                safe_folder = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                local_path = self.crawler.download_dir / safe_folder / att['name']
                
                result = self.pdf_engine.process_document(local_path)
                if result["markdown"]:
                    # We append the PDF text to the total content pool
                    full_content += f"\n\n--- PDF CONTENT: {att['name']} ---\n{result['markdown']}"
                all_image_paths.extend(result["local_image_paths"])

        # We MUST chunk the 'full_content' after all PDFs are added.
        # I'm using a very conservative 10,000 character limit (~2,500 tokens).
        chunks = self.html_cleaner.chunk_text(full_content, max_chars=10000)
        
        for i, chunk_content in enumerate(chunks):
            # If a chunk is STILL too big (safety check), we truncate it 
            # to prevent the 400 error from stopping the whole script.
            safe_chunk = chunk_content[:30000] # Hard character limit as a last resort
            
            chunk_id = f"kb_{article['id']}_part_{i}"
            deterministic_uuid = generate_uuid5(chunk_id)
            
            batch.add_object(
                uuid=deterministic_uuid,
                properties={
                    "document_id": chunk_id,
                    "title": f"{title} (Part {i+1})" if len(chunks) > 1 else title,
                    "document_type": "KB_Article",
                    "content": safe_chunk,
                    "url": f"https://eiva.freshdesk.com/a/solutions/articles/{article['id']}",
                    "image_urls": all_image_paths 
                }
            )

    def close(self):
        self.client.close()

if __name__ == "__main__":
    engine = KBIngestionEngine()
    try:
        engine.run_assimilation()
    finally:
        engine.close()