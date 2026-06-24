from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Date, Index
from sqlalchemy.orm import relationship
from database import Base
import datetime
from sqlalchemy.types import TypeDecorator, Text as SqlText
import json
from config import settings

class SQLiteVector(TypeDecorator):
    impl = SqlText
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None

if settings.DATABASE_URL.startswith("postgresql"):
    from pgvector.sqlalchemy import Vector
    EmbeddingVectorType = Vector(768)
else:
    EmbeddingVectorType = SQLiteVector

class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    projects = relationship("Project", back_populates="company", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)

    company = relationship("Company", back_populates="projects")
    land_parcels = relationship("LandParcel", back_populates="project", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    meeting_notes = relationship("MeetingNote", back_populates="project", cascade="all, delete-orphan")

class LandParcel(Base):
    __tablename__ = 'land_parcels'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    survey_number = Column(String, nullable=False)
    village = Column(String, nullable=False)
    area = Column(Float, nullable=False)  # Area in acres
    conversion_status = Column(String, nullable=True)  # e.g., Converted, Pending, Agricultural
    lawyer_handled = Column(String, nullable=True)  # Lawyer name
    current_status = Column(String, nullable=True)  # e.g., Owned, Disputed, Under Process

    project = relationship("Project", back_populates="land_parcels")

    # Add text search indexes on survey number and lawyer handled
    __table_args__ = (
        Index('idx_land_survey_num', 'survey_number'),
        Index('idx_land_lawyer', 'lawyer_handled'),
    )

class Vendor(Base):
    __tablename__ = 'vendors'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # e.g., drip irrigation, legal, fencing
    contact = Column(String, nullable=True)
    gst = Column(String, nullable=True)
    payment_status = Column(String, nullable=True)  # e.g., Paid, Pending, Partially Paid

    __table_args__ = (
        Index('idx_vendor_name', 'name'),
        Index('idx_vendor_category', 'category'),
    )

class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    contact = Column(String, nullable=True)
    agreement_reference = Column(String, nullable=True)

    project = relationship("Project", back_populates="customers")

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    title = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # e.g., PDF, Excel, txt, mp3
    file_path = Column(String, nullable=False)
    full_text = Column(Text, nullable=True)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(EmbeddingVectorType, nullable=True)  # Gemini 768-dim embeddings

    document = relationship("Document", back_populates="chunks")

class MeetingNote(Base):
    __tablename__ = 'meeting_notes'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    attendees = Column(String, nullable=True)  # e.g., Zameer, Darshan
    topic = Column(String, nullable=False)
    notes_text = Column(Text, nullable=False)

    project = relationship("Project", back_populates="meeting_notes")

    __table_args__ = (
        Index('idx_notes_attendees', 'attendees'),
        Index('idx_notes_topic', 'topic'),
    )
