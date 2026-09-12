"""
knowledge_agent.py
-------------------
This agent handles RAG (Retrieval Augmented Generation):
1. Loads our knowledge base .txt files
2. Stores them in ChromaDB as embeddings
3. Given a ticket, retrieves the most relevant knowledge chunk(s)

UPDATED (Day 8): now also returns a confidence/distance score, so the
pipeline can detect when NOTHING relevant was actually found, instead of
always confidently returning the "closest" (but possibly unrelated) match.
"""

import os
import chromadb
from chromadb.utils import embedding_functions

chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

collection = chroma_client.get_or_create_collection(
    name="helpdesk_knowledge",
    embedding_function=embedding_fn
)

# Threshold for what counts as "relevant enough." ChromaDB's default
# distance metric is such that SMALLER = more similar/relevant.
# This number was chosen by testing - not a universal constant. We'll
# verify it works for our data in a moment.
DISTANCE_THRESHOLD = 1.0


def load_knowledge_base(data_folder: str = "data") -> None:
    files = [f for f in os.listdir(data_folder) if f.endswith(".txt")]

    for filename in files:
        filepath = os.path.join(data_folder, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        collection.upsert(
            documents=[content],
            ids=[filename]
        )

    print(f"Loaded {len(files)} knowledge documents into ChromaDB.")


def retrieve_relevant_knowledge(ticket_description: str, top_k: int = 1) -> dict:
    """
    UPDATED: now returns a dict with BOTH the retrieved content AND
    whether it's actually considered relevant, based on distance score.

    Returns:
        {
            "content": <retrieved text, or a "no relevant info" message>,
            "is_relevant": True/False,
            "distance": <the raw distance score, for debugging/logging>
        }
    """
    results = collection.query(
        query_texts=[ticket_description],
        n_results=top_k
    )

    retrieved_docs = results["documents"][0]
    distances = results["distances"][0]

    # We only check the TOP result's distance (the closest match)
    best_distance = distances[0]
    is_relevant = best_distance <= DISTANCE_THRESHOLD

    if is_relevant:
        content = "\n\n".join(retrieved_docs)
    else:
        content = ("No relevant knowledge base entry was found for this "
                    "ticket. This may require manual review by a support agent.")

    return {
        "content": content,
        "is_relevant": is_relevant,
        "distance": best_distance
    }


# Quick standalone test
if __name__ == "__main__":
    load_knowledge_base()

    test_cases = [
        "I forgot my password and can't log into my laptop.",
        "What's the weather like today?",  # should be irrelevant
    ]

    print("\n=== Knowledge Agent - Confidence Threshold Test ===\n")
    for ticket in test_cases:
        result = retrieve_relevant_knowledge(ticket)
        print(f"Ticket: {ticket}")
        print(f"Distance: {result['distance']:.3f}")
        print(f"Is Relevant: {result['is_relevant']}")
        print(f"Content: {result['content'][:100]}...\n")