from fastapi import FastAPI, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, text
import os
import shutil
import datetime
from typing import List, Optional
import numpy as np

from database import get_db, init_db
from config import settings
import models
import schemas
import ai_service
import ingestion
from storage_service import StorageService

# Initialize FastAPI App
app = FastAPI(
    title="The Company Brain API",
    description="Backend API and Q&A Engine for Soil Systems",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    await init_db()

# ----------------------------------------------------
# 1. Structured Metadata CRUD Endpoints
# ----------------------------------------------------

@app.post("/api/companies", response_model=schemas.CompanyResponse)
async def create_company(company: schemas.CompanyCreate, db: AsyncSession = Depends(get_db)):
    db_company = models.Company(name=company.name)
    db.add(db_company)
    try:
        await db.commit()
        await db.refresh(db_company)
        return db_company
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Company already exists or invalid data: {e}")

@app.get("/api/companies", response_model=List[schemas.CompanyResponse])
async def get_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Company))
    return result.scalars().all()

@app.post("/api/projects", response_model=schemas.ProjectResponse)
async def create_project(project: schemas.ProjectCreate, db: AsyncSession = Depends(get_db)):
    db_project = models.Project(company_id=project.company_id, name=project.name)
    db.add(db_project)
    try:
        await db.commit()
        await db.refresh(db_project)
        return db_project
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/projects", response_model=List[schemas.ProjectResponse])
async def get_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Project))
    return result.scalars().all()

@app.post("/api/land-parcels", response_model=schemas.LandParcelResponse)
async def create_land_parcel(parcel: schemas.LandParcelCreate, db: AsyncSession = Depends(get_db)):
    db_parcel = models.LandParcel(
        project_id=parcel.project_id,
        survey_number=parcel.survey_number,
        village=parcel.village,
        area=parcel.area,
        conversion_status=parcel.conversion_status,
        lawyer_handled=parcel.lawyer_handled,
        current_status=parcel.current_status
    )
    db.add(db_parcel)
    try:
        await db.commit()
        await db.refresh(db_parcel)
        return db_parcel
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/land-parcels", response_model=List[schemas.LandParcelResponse])
async def get_land_parcels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.LandParcel))
    return result.scalars().all()

@app.post("/api/vendors", response_model=schemas.VendorResponse)
async def create_vendor(vendor: schemas.VendorCreate, db: AsyncSession = Depends(get_db)):
    db_vendor = models.Vendor(
        name=vendor.name,
        category=vendor.category,
        contact=vendor.contact,
        gst=vendor.gst,
        payment_status=vendor.payment_status
    )
    db.add(db_vendor)
    try:
        await db.commit()
        await db.refresh(db_vendor)
        return db_vendor
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/vendors", response_model=List[schemas.VendorResponse])
async def get_vendors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Vendor))
    return result.scalars().all()

@app.post("/api/meeting-notes", response_model=schemas.MeetingNoteResponse)
async def create_meeting_note(note: schemas.MeetingNoteCreate, db: AsyncSession = Depends(get_db)):
    db_note = models.MeetingNote(
        project_id=note.project_id,
        date=note.date,
        attendees=note.attendees,
        topic=note.topic,
        notes_text=note.notes_text
    )
    db.add(db_note)
    try:
        await db.commit()
        await db.refresh(db_note)
        return db_note
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/meeting-notes", response_model=List[schemas.MeetingNoteResponse])
async def get_meeting_notes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.MeetingNote))
    return result.scalars().all()

# ----------------------------------------------------
# 2. File Upload and Ingestion Endpoints
# ----------------------------------------------------

@app.post("/api/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    project_id: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # Check if project exists
    proj_result = await db.execute(select(models.Project).where(models.Project.id == project_id))
    if not proj_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    # Clean filename and read file bytes
    file_bytes = await file.read()
    
    # Upload via StorageService (handles Supabase bucket or local fallback)
    try:
        file_path = await StorageService.upload_file(file.filename, file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Create document record in database
    db_doc = models.Document(
        project_id=project_id,
        title=title,
        file_type=os.path.splitext(file.filename)[1].replace('.', '').upper(),
        file_path=file_path,
        upload_date=datetime.datetime.utcnow()
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)

    # Queue the ingestion process in the background
    background_tasks.add_task(ingestion.ingest_document, db_doc.id, db)

    return {"message": "File uploaded successfully. Ingestion started in background.", "document_id": db_doc.id}

@app.get("/api/documents", response_model=List[schemas.DocumentResponse])
async def get_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Document))
    return result.scalars().all()

# ----------------------------------------------------
# 3. Hybrid Search & Q&A RAG Engine Endpoint
# ----------------------------------------------------

@app.post("/api/search/ask", response_model=schemas.QuestionResponse)
async def ask_question(request: schemas.QuestionRequest, db: AsyncSession = Depends(get_db)):
    question = request.question
    q_lower = question.lower()
    
    # ----------------------------------------------------
    # Phase 5: Action Agent Routing Logic
    # ----------------------------------------------------
    # If the user asks for real-time live operational stats, route to the tool-use agent.
    is_live_query = any(word in q_lower for word in ["lead", "call", "payables", "pending payment", "vikas", "crm", "books"])
    
    if is_live_query:
        answer, sources = await ai_service.answer_with_agent(question)
        return schemas.QuestionResponse(answer=answer, sources=sources, type="agent")

    # ----------------------------------------------------
    # Phase 2: Hybrid RAG Search Retrieval Logic
    # ----------------------------------------------------
    # 1. Vector Search
    query_emb = await ai_service.get_embedding(question)
    
    if db.bind.dialect.name == "postgresql":
        # Cosine distance vector search
        vector_query = (
            select(models.DocumentChunk, models.Document.title)
            .join(models.Document, models.DocumentChunk.document_id == models.Document.id)
        )
        if request.project_id:
            vector_query = vector_query.where(models.Document.project_id == request.project_id)
            
        vector_query = vector_query.order_by(models.DocumentChunk.embedding.cosine_distance(query_emb)).limit(5)
        vector_results = await db.execute(vector_query)
        vector_chunks = vector_results.all()
    else:
        # SQLite fallback: load chunks and compute similarity in Python
        query = (
            select(models.DocumentChunk, models.Document.title)
            .join(models.Document, models.DocumentChunk.document_id == models.Document.id)
        )
        if request.project_id:
            query = query.where(models.Document.project_id == request.project_id)
        result = await db.execute(query)
        all_chunks = result.all()
        
        def cosine_similarity(v1, v2):
            if not v1 or not v2: return 0.0
            v1, v2 = np.array(v1), np.array(v2)
            dot = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 == 0 or norm2 == 0: return 0.0
            return dot / (norm1 * norm2)

        scored_chunks = []
        for chunk, title in all_chunks:
            sim = cosine_similarity(chunk.embedding, query_emb)
            scored_chunks.append(((chunk, title), sim))
        
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        vector_chunks = [item[0] for item in scored_chunks[:5] if item[1] > 0.05]

    # 2. Text Keyword Search (FTS-like or word-matching on content)
    # Split query into words to match
    keywords = [f"%{word}%" for word in question.split() if len(word) > 3]
    keyword_chunks = []
    
    if keywords:
        text_filters = [models.DocumentChunk.content.ilike(kw) for kw in keywords]
        text_query = (
            select(models.DocumentChunk, models.Document.title)
            .join(models.Document, models.DocumentChunk.document_id == models.Document.id)
            .where(or_(*text_filters))
        )
        if request.project_id:
            text_query = text_query.where(models.Document.project_id == request.project_id)
        text_query = text_query.limit(5)
        text_results = await db.execute(text_query)
        keyword_chunks = text_results.all()

    # 3. Combine Chunks and De-duplicate by Chunk ID
    combined_chunks = {}
    
    # Add vector chunks first (higher priority)
    for chunk, doc_title in vector_chunks:
        combined_chunks[chunk.id] = (chunk.content, doc_title)
        
    # Add keyword chunks
    for chunk, doc_title in keyword_chunks:
        if chunk.id not in combined_chunks:
            combined_chunks[chunk.id] = (chunk.content, doc_title)

    context_list = list(combined_chunks.values())

    # 4. Generate Answer via RAG
    answer, sources = await ai_service.answer_with_rag(question, context_list)
    return schemas.QuestionResponse(answer=answer, sources=sources, type="rag")

# ----------------------------------------------------
# 4. UI Mount and Serving
# ----------------------------------------------------

# Basic dashboard HTML served directly
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    # Reading Dashboard from static folder or served raw (we will write a beautiful HTML index file)
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback raw response in case directory mounting hasn't happened yet
        return "<h3>The Company Brain dashboard loading... Please check back in a second!</h3>"

# Mount static folder
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
# Mount uploads folder to allow clickable link preview of files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
