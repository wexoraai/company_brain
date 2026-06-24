from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date

# Base configuration
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# Company Schemas
class CompanyBase(BaseSchema):
    name: str

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: int

# Project Schemas
class ProjectBase(BaseSchema):
    company_id: int
    name: str

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int

# LandParcel Schemas
class LandParcelBase(BaseSchema):
    project_id: int
    survey_number: str
    village: str
    area: float
    conversion_status: Optional[str] = None
    lawyer_handled: Optional[str] = None
    current_status: Optional[str] = None

class LandParcelCreate(LandParcelBase):
    pass

class LandParcelResponse(LandParcelBase):
    id: int

# Vendor Schemas
class VendorBase(BaseSchema):
    name: str
    category: str
    contact: Optional[str] = None
    gst: Optional[str] = None
    payment_status: Optional[str] = None

class VendorCreate(VendorBase):
    pass

class VendorResponse(VendorBase):
    id: int

# Customer Schemas
class CustomerBase(BaseSchema):
    project_id: int
    name: str
    contact: Optional[str] = None
    agreement_reference: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int

# MeetingNote Schemas
class MeetingNoteBase(BaseSchema):
    project_id: int
    date: date
    attendees: Optional[str] = None
    topic: str
    notes_text: str

class MeetingNoteCreate(MeetingNoteBase):
    pass

class MeetingNoteResponse(MeetingNoteBase):
    id: int

# Document Schemas
class DocumentBase(BaseSchema):
    project_id: int
    title: str
    file_type: str
    file_path: str
    upload_date: datetime

class DocumentResponse(DocumentBase):
    id: int
    full_text: Optional[str] = None

# Q&A / Search Schemas
class QuestionRequest(BaseModel):
    question: str
    project_id: Optional[int] = None

class QuestionResponse(BaseModel):
    answer: str
    sources: List[str]
    type: str  # 'rag' or 'agent'
