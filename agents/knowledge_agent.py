"""
knowledge_agent.py
-------------------
This agent handles RAG (Retrieval Augmented Generation):
1. Loads our knowledge base .txt files
2. Stores them in ChromaDB as embeddings (numeric "meaning" representations)
3. Given a ticket, retrieves the most relevant knowledge chunk(s)

This runs BETWEEN triage and resolver in our pipeline:
Triage (what category?) -> Knowledge Retrieval (what do we know about this?)
-> Resolver (use that knowledge to suggest a fix)
"""

import os
import chromadb
from chromadb.utils import embedding_functions

# Step 1: Set up a ChromaDB client that saves data to disk (not just memory)
# so we don't have to reload/re-embed documents every single run.
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Step 2: Use ChromaDB's built-in default embedding function.
# This handles converting text into those "meaning coordinate" numbers
# automatically - we don't need to call Ollama for this part.
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

# Step 3: Create (or get, if it already exists) a "collection" -
# think of this as a table/folder inside ChromaDB for our documents.
collection = chroma_client.get_or_create_collection(
    name="helpdesk_knowledge",
    embedding_function=embedding_fn
)


def load_knowledge_base(data_folder: str = "data") -> None:
    """
    Reads every .txt file in the data folder and stores it in ChromaDB.
    Only needs to run once (or whenever knowledge files change) - ChromaDB
    persists to disk in the chroma_db folder.
    """
    files = [f for f in os.listdir(data_folder) if f.endswith(".txt")]

    for filename in files:
        filepath = os.path.join(data_folder, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Each document needs a unique ID - we use the filename
        collection.upsert(
            documents=[content],
            ids=[filename]
        )

    print(f"Loaded {len(files)} knowledge documents into ChromaDB.")


def retrieve_relevant_knowledge(ticket_description: str, top_k: int = 1) -> str:
    """
    Given a ticket, searches ChromaDB for the most relevant knowledge
    document(s) by meaning (vector search), and returns their content.
    """
    results = collection.query(
        query_texts=[ticket_description],
        n_results=top_k
    )

    # results["documents"] is a list of lists (one list per query) -
    # we only sent one query, so we take the first list.
    retrieved_docs = results["documents"][0]
    combined_knowledge = "\n\n".join(retrieved_docs)

    return combined_knowledge


# Quick standalone test
if __name__ == "__main__":
    load_knowledge_base()

    test_ticket = "I forgot my password and can't log into my laptop."
    knowledge = retrieve_relevant_knowledge(test_ticket)

    print("\n=== Knowledge Agent - Test Run ===\n")
    print(f"Ticket: {test_ticket}")
    print(f"\nRetrieved Knowledge:\n{knowledge}")