# System Architecture: The Company Brain

This document describes the design layers and data model of **The Company Brain**.

```mermaid
graph TD
    subgraph Layer 5: Action Agents
        CRM[Zoho CRM Client]
        Books[Zoho Books Client]
        Retell[Retell Voice API Client]
    end
    subgraph Layer 4: AI & Q&A
        RAG[RAG Retrieval QA Engine]
        LLM[Gemini 2.5 Flash]
    end
    subgraph Layer 3: Index & Search
        VS[Vector Cosine Search pgvector]
        FTS[Postgres tsvector FTS + Trigram pg_trgm]
    end
    subgraph Layer 2: Ingestion
        Parser[Background Ingestion Engine]
        PDF[PyMuPDF PDF Reader]
        Excel[Pandas/Openpyxl]
        WhatsApp[Custom Chat Parser]
        Whisper[Voice Note Transcriber]
    end
    subgraph Layer 1: Storage
        DB[(PostgreSQL Database)]
        FS[(Local/Cloud Storage)]
    end
    subgraph Layer 0: Security & Ownership
        Secrets[Vault / .env Config]
        Docker[Containerization]
    end

    Parser --> FS
    Parser --> DB
    RAG --> VS
    RAG --> FTS
    RAG --> LLM
    LLM --> CRM
    LLM --> Books
    LLM --> Retell
```

---

## The Six Architecture Layers

### Layer 5: Action Agents
Integrations with operational systems (Zoho CRM, Zoho Books, Retell). When a user asks live questions like *"How many leads came yesterday?"*, the LLM invokes function calling to fetch real-time facts instead of retrieving old documents.

### Layer 4: Ask in Plain English (AI Layer)
Receives natural language questions, coordinates with Layer 3 to query documents/records, builds prompts with a strict context-bound guardrail, and uses a Large Language Model (Gemini/Claude) to generate answers with inline source links.

### Layer 3: Index / Search
A hybrid search implementation combining **vector embeddings** (for semantic match) and **text keyword search** (for exact names, survey numbers, and IDs). 

### Layer 2: Ingestion
Asynchronous background pipeline parsing multiple file types (text PDFs, scanned documents, Excel sheets, WhatsApp chat exports, and audio recordings). Text is extracted, cleaned, chunked, embedded, and indexed.

### Layer 1: Storage
Stores structured records (projects, land records, vendors, customers, meeting notes) and unstructured files (original PDFs, voice clips, spreadsheets). Powered by PostgreSQL and Object Storage (or local folder fallback).

### Layer 0: Ownership & Security
Dockerized infrastructure, secrets management via environment variables, and ownership setups to prevent developer lock-in.

---

## Data Model (PostgreSQL)

```mermaid
erDiagram
    COMPANIES {
        int id PK
        string name
    }
    PROJECTS {
        int id PK
        int company_id FK
        string name
    }
    LAND_PARCELS {
        int id PK
        int project_id FK
        string survey_number
        string village
        float area
        string conversion_status
        string lawyer_handled
        string current_status
    }
    VENDORS {
        int id PK
        string name
        string category
        string contact
        string gst
        string payment_status
    }
    CUSTOMERS {
        int id PK
        int project_id FK
        string name
        string contact
        string agreement_reference
    }
    DOCUMENTS {
        int id PK
        int project_id FK
        string title
        string file_type
        string file_path
        string full_text
        timestamp upload_date
    }
    DOCUMENT_CHUNKS {
        int id PK
        int document_id FK
        string content
        vector embedding
    }
    MEETING_NOTES {
        int id PK
        int project_id FK
        date date
        string attendees
        string topic
        string notes_text
    }

    COMPANIES ||--o{ PROJECTS : owns
    PROJECTS ||--o{ LAND_PARCELS : contains
    PROJECTS ||--o{ CUSTOMERS : has
    PROJECTS ||--o{ DOCUMENTS : associates
    PROJECTS ||--o{ MEETING_NOTES : contains
    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : has
```
