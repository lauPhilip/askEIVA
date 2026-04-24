import re
from bs4 import BeautifulSoup

class TicketProcessor:
    """Processes raw Freshdesk data into clean, structured, and chunked Markdown."""

    def clean_html(self, html_content):
        """Standardizes HTML into clean text, preserving line breaks."""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text(separator="\n").strip()

    def chunk_text(self, text, max_chars=8000): # Dropping to 8k chars for a safety buffer
        """
        Recursively splits text to ensure no chunk ever exceeds Mistral's token limit.
        Prioritizes: Headers -> Double Newlines -> Single Newlines -> Sentences.
        """
        if len(text) <= max_chars:
            return [text]

        chunks = []
        
        # 1. Try splitting by Markdown Headers first
        sections = re.split(r'(?=\n#{1,3} |\n\*\*Dialogue:)', text)
        
        current_chunk = ""
        for section in sections:
            # If the section itself is small enough, add it to the buffer
            if len(current_chunk) + len(section) <= max_chars:
                current_chunk += section
            else:
                # If current_chunk has content, save it before dealing with the big section
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # If the individual section is still too big, sub-split it by paragraphs
                if len(section) > max_chars:
                    sub_parts = section.split('\n\n')
                    for part in sub_parts:
                        if len(current_chunk) + len(part) <= max_chars:
                            current_chunk += "\n\n" + part
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            
                            # If a SINGLE PARAGRAPH is still too big, split by sentence
                            if len(part) > max_chars:
                                sentences = re.split(r'(?<=[.!?]) +', part)
                                sub_chunk = ""
                                for sent in sentences:
                                    if len(sub_chunk) + len(sent) <= max_chars:
                                        sub_chunk += " " + sent
                                    else:
                                        chunks.append(sub_chunk.strip())
                                        sub_chunk = sent
                                current_chunk = sub_chunk
                            else:
                                current_chunk = part
                else:
                    current_chunk = section

        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return [c for c in chunks if c.strip()]

    def process_tickets_with_dialogue(self, raw_tickets, crawler, domain):
        """Transforms raw API tickets into structured dialogue strings."""
        processed_data = []

        for ticket in raw_tickets:
            ticket_id = ticket['id']
            subject = ticket.get('subject', 'No Subject')
            description = self.clean_html(ticket.get('description', ''))
            
            # Compile initial ticket info
            full_dialogue = f"Ticket ID: {ticket_id}\nSubject: {subject}\n\n**Dialogue: Initial Request**\n{description}"

            # Fetch and append the conversation thread
            conversations = crawler.fetch_ticket_conversations(ticket_id)
            for comment in conversations:
                body = self.clean_html(comment.get('body', ''))
                if body:
                    # Determine if it's a private note or a public reply
                    note_type = "Private Note" if comment.get('private') else "Reply"
                    full_dialogue += f"\n\n**Dialogue: {note_type}**\n{body}"

            processed_data.append({
                "source_id": f"ticket_{ticket_id}",
                "data_type": "Ticket",
                "subject": subject,
                "content": full_dialogue,
                "url": f"https://{domain}.freshdesk.com/a/tickets/{ticket_id}",
                "status": ticket.get('status'),
                "priority": ticket.get('priority'),
                "tags": ticket.get('tags', []),
                "attachment_urls": [a.get('attachment_url') for a in ticket.get('attachments', [])]
            })

        return processed_data