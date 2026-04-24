import json

class EIVAKnowledgeGraph:
    def __init__(self, mistral_client):
        self.mistral = mistral_client

    def distill_ticket_to_triples(self, ticket_text: str):
        """Processes raw support text into Subject-Predicate-Object triples."""
        prompt = (
            "You are a Maritime Systems Knowledge Engineer. Analyze the following support ticket "
            "and extract technical relationships as triples. "
            "Focus on hardware (ScanFish, Winch), software (NaviPac, NaviModel), versions, and errors. "
            "Relationships should be like: [Component] -> HAS_ISSUE -> [Symptom], [Error] -> FIXED_BY -> [Action]. "
            "Output ONLY JSON: {'relations': [{'source': '', 'relation': '', 'target': ''}]}"
        )
        
        response = self.mistral.chat.complete(
            model="mistral-large-latest",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": f"{prompt}\n\nTicket: {ticket_text}"}]
        )
        return json.loads(response.choices[0].message.content)