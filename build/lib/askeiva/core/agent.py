import os
import httpx
import weaviate
from datetime import datetime
from weaviate.classes.query import HybridFusion
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

class AskEIVA:
    """
    The core intelligence for the askEIVA platform.
    Designed for integration into Streamlit, Flask, or FastApi.
    """
    def __init__(self):
        # Establish persistent connection to Weaviate Cloud
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
            headers={"X-Mistral-Api-Key": os.getenv("MISTRAL_API_KEY")}
        )
        
        # Initialize heavy HTTP clients once
        self.http_client = httpx.Client(timeout=120.0)
        self.mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY"), client=self.http_client)
        
        # Direct collection references
        self.tickets = self.client.collections.get("KnowledgeNode")
        self.docs = self.client.collections.get("DocumentLibrary")
        self.logs = self.client.collections.get("InteractionLog")

    def search(self, query: str):
        """Unified hybrid search across EIVA libraries."""
        ticket_results = self.tickets.query.hybrid(
            query=query, limit=3, fusion_type=HybridFusion.RELATIVE_SCORE,
            return_properties=["subject", "content", "tags"]
        )
        doc_results = self.docs.query.hybrid(
            query=query, limit=3, fusion_type=HybridFusion.RELATIVE_SCORE,
            return_properties=["title", "content", "tags"]
        )
        return ticket_results.objects, doc_results.objects

    def generate_answer(self, query: str):
        """Main synthesis engine. Grounded in EIVA context and logged to the Graph."""
        tix, docs = self.search(query)
        
        context_blocks = []
        for d in docs:
            context_blocks.append(f"DOC [{d.properties.get('title')}]: {d.properties.get('content', '')[:3000]}")
        for t in tix:
            context_blocks.append(f"TICKET [{t.properties.get('subject')}]: {t.properties.get('content', '')[:3000]}")

        context_text = "\n\n".join(context_blocks)
        
        system_instructions = (
            "You are askEIVA, the technical lead AI for EIVA survey solutions. "
            "You provide grounded, expert advice based on internal technical debt and documentation. "
            "Always cite sources and acknowledge if specific data is missing."
        )

        try:
            response = self.mistral.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": f"DATA:\n{context_text}\n\nQUERY: {query}"}
                ]
            )
            answer = response.choices[0].message.content

            # LOGGING: The Feedback Loop (Learns in real-time)
            referenced_ids = [str(obj.uuid) for obj in docs] + [str(obj.uuid) for obj in tix]
            current_time = datetime.now().astimezone()

            self.logs.data.insert(
                properties={
                    "query": query,
                    "answer": answer,
                    "timestamp": current_time,
                    "referenced_doc_ids": referenced_ids,
                    "was_successful": True 
                }
            )
            
            return answer
        except Exception as e:
            return f"EIVA Intelligence Error: {str(e)}"

    def close(self):
        """Cleanup method for manual shutdown."""
        if self.client:
            self.client.close()
        if self.http_client:
            self.http_client.close()

    def __del__(self):
        """Automatic garbage collection cleanup."""
        try:
            self.close()
        except:
            pass