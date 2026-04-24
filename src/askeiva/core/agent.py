import os
import httpx
import weaviate
from datetime import datetime
from weaviate.classes.query import HybridFusion
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

class AskEIVA:
    def __init__(self):
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
            headers={"X-Mistral-Api-Key": os.getenv("MISTRAL_API_KEY")}
        )
        self.http_client = httpx.Client(timeout=120.0)
        self.mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY"), client=self.http_client)
        
        self.tickets = self.client.collections.get("KnowledgeNode")
        self.docs = self.client.collections.get("DocumentLibrary")
        self.logs = self.client.collections.get("InteractionLog")
        
    def get_sources(self, query: str):
        """Fetches metadata for the sources used in the query."""
        tix, docs = self.search(query)
        sources = []
        seen = set()
        
        # Pull from Manuals
        for d in docs:
            title = d.properties.get("title", "Unknown Manual")
            if title not in seen:
                sources.append({
                    "type": "Manual",
                    "title": title,
                    "url": d.properties.get("url", "https://eiva.com")
                })
                seen.add(title)
                
        # Pull from Tickets
        for t in tix:
            subject = t.properties.get("subject", "Support Ticket")
            if subject not in seen:
                sources.append({
                    "type": "Ticket",
                    "title": subject,
                    "url": t.properties.get("url", "https://eiva.freshdesk.com")
                })
                seen.add(subject)
                
        return sources

    def search(self, query: str):
        tix = self.tickets.query.hybrid(query=query, limit=3, fusion_type=HybridFusion.RELATIVE_SCORE)
        docs = self.docs.query.hybrid(query=query, limit=3, fusion_type=HybridFusion.RELATIVE_SCORE)
        return tix.objects, docs.objects

    def stream_answer(self, query: str):
        """Generates a streaming response and logs the result once completed."""
        tix, docs = self.search(query)
        
        context_blocks = []
        for d in docs:
            context_blocks.append(f"DOC [{d.properties.get('title')}]: {d.properties.get('content', '')[:3000]}")
        for t in tix:
            context_blocks.append(f"TICKET [{t.properties.get('subject')}]: {t.properties.get('content', '')[:3000]}")
        
        context_text = "\n\n".join(context_blocks)
        full_response = ""

        try:
            # We use .stream() here to get the generator
            stream_response = self.mistral.chat.stream(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": "You are askEIVA, the technical lead AI for EIVA survey solutions. Cite sources."},
                    {"role": "user", "content": f"KNOWLEDGE POOL:\n{context_text}\n\nQUERY: {query}"}
                ]
            )

            for chunk in stream_response:
                content = chunk.data.choices[0].delta.content
                if content:
                    full_response += content
                    yield content

            # Log interaction to Knowledge Graph after stream finishes
            ref_ids = [str(obj.uuid) for obj in docs] + [str(obj.uuid) for obj in tix]
            self.logs.data.insert(
                properties={
                    "query": query,
                    "answer": full_response,
                    "timestamp": datetime.now().astimezone(),
                    "referenced_doc_ids": ref_ids,
                    "was_successful": True 
                }
            )

        except Exception as e:
            yield f"EIVA System Error: {str(e)}"

    def close(self):
        self.client.close()
        self.http_client.close()