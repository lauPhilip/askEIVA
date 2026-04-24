import time
from tqdm import tqdm
from src.askeiva.core.agent import AskEIVA
from src.askeiva.core.graph_engine import EIVAKnowledgeGraph

class KnowledgeDistiller:
    def __init__(self):
        self.agent = AskEIVA()
        self.graph_engine = EIVAKnowledgeGraph(self.agent.mistral)
        self.tickets = self.agent.client.collections.get("KnowledgeNode")
        self.graph = self.agent.client.collections.get("EntityGraph")

    def process_tickets(self, limit=100):
        """Processes a batch of tickets into the EntityGraph organism."""
        print(f"--- [ STARTING DISTILLATION BATCH: {limit} TICKETS ] ---")
        
        try:
            # Fetch a fresh batch of tickets
            response = self.tickets.query.fetch_objects(limit=limit)
            
            for ticket in tqdm(response.objects, desc="Mapping EIVA Knowledge"):
                content = ticket.properties.get("content", "")
                ticket_id = str(ticket.uuid)
                
                if not content or len(content) < 50:
                    continue

                try:
                    # Reasoning step: Extract Triples
                    triples = self.graph_engine.distill_ticket_to_triples(content)
                    
                    # Store in Graph
                    for rel in triples.get("relations", []):
                        self.graph.data.insert(
                            properties={
                                "subject": str(rel["source"]),
                                "predicate": str(rel["relation"]),
                                "object": str(rel["target"]),
                                "evidence_id": ticket_id
                            }
                        )
                    # Respect rate limits for Mistral
                    time.sleep(0.7)
                    
                except Exception as e:
                    print(f"\n[!] Error processing {ticket_id}: {e}")

            print(f"--- [ BATCH COMPLETE ] ---")
            
        finally:
            self.agent.close()

if __name__ == "__main__":
    distiller = KnowledgeDistiller()
    # Master Lau, increase this number for the full 6,000 run
    distiller.process_tickets(limit=100)