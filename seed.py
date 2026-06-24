import asyncio
import os
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import init_db, async_session
import models
import ingestion
from config import settings

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

async def seed_data():
    print("Starting database seeding...")
    # Initialize DB (creates extensions and tables)
    await init_db()

    async with async_session() as db:
        # Check if company already seeded
        result = await db.execute(select(models.Company).where(models.Company.name == "Soil Systems"))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        # 1. Seed Companies
        soil_systems = models.Company(name="Soil Systems")
        wexora_ai = models.Company(name="Wexora AI")
        db.add_all([soil_systems, wexora_ai])
        await db.commit()

        # 2. Seed Projects
        p1 = models.Project(company_id=soil_systems.id, name="Woods & Spices P1")
        p2 = models.Project(company_id=soil_systems.id, name="Woods & Spices P2")
        windflower = models.Project(company_id=soil_systems.id, name="Windflower")
        coorg = models.Project(company_id=soil_systems.id, name="La Cavana Resort (Coorg)")
        db.add_all([p1, p2, windflower, coorg])
        await db.commit()

        # 3. Seed Land Parcels
        lp1 = models.LandParcel(
            project_id=windflower.id,
            survey_number="12/A",
            village="Windflower Village",
            area=5.4,
            conversion_status="Approved",
            lawyer_handled="Advocate Ramesh & Associates",
            current_status="Owned"
        )
        lp2 = models.LandParcel(
            project_id=coorg.id,
            survey_number="104/3",
            village="Coorg Town",
            area=12.2,
            conversion_status="Pending",
            lawyer_handled="Advocate Ramesh & Associates",
            current_status="Under Process"
        )
        db.add_all([lp1, lp2])

        # 4. Seed Vendors
        v1 = models.Vendor(
            name="Netafim Drip Irrigation",
            category="Drip Irrigation",
            contact="+91 98450 12345",
            gst="29AAAAA1111A1Z1",
            payment_status="Pending"
        )
        v2 = models.Vendor(
            name="Hedge-Grow Fencing Ltd",
            category="Fencing",
            contact="+91 98450 67890",
            gst="29BBBBB2222B1Z2",
            payment_status="Paid"
        )
        v3 = models.Vendor(
            name="Advocate Ramesh & Associates",
            category="Legal",
            contact="+91 99001 22334",
            gst=None,
            payment_status="Pending"
        )
        db.add_all([v1, v2, v3])

        # 5. Seed Meeting Notes
        mn1 = models.MeetingNote(
            project_id=windflower.id,
            date=datetime.date(2026, 5, 14),
            attendees="Zameer, Darshan, Ramesh",
            topic="Land Use Conversion Update",
            notes_text="Zameer updated us that the land-use conversion for the Windflower project was approved by the local authority. Formal certificate is pending and expected in 2 weeks. Ramesh will follow up."
        )
        db.add(mn1)

        # 6. Seed Customers
        c1 = models.Customer(
            project_id=p1.id,
            name="Rajesh Kumar",
            contact="+91 98860 11223",
            agreement_reference="SS-WS-P1-042"
        )
        db.add(c1)
        await db.commit()

        # 7. Create and Ingest Mock Documents representing the 5 owner questions
        doc_definitions = [
            {
                "project_id": coorg.id,
                "title": "La Cavana Advance Receipt",
                "filename": "La_Cavana_advance_receipt.pdf",
                "content": "Advance Payment Receipt. Paid Rs. 1,500,000 (15 Lakhs) for the Coorg resort project. Recipient: Coorg Resort Land Owner. Date: 2026-04-12. Payment verified in Zoho Books."
            },
            {
                "project_id": windflower.id,
                "title": "Land Title Records & Legal Handler",
                "filename": "land_records.pdf",
                "content": "Land Ownership Deed. Survey Number: 12/A, Village: Windflower. Representative handling legal proceedings: Advocate Ramesh & Associates. Land Use Conversion status: approved. Status: Clean Title."
            },
            {
                "project_id": p1.id,
                "title": "Pepper Cultivation SOP",
                "filename": "pepper_cultivation_SOP.pdf",
                "content": "Standard Operating Procedure: Pepper Cultivation. Setup spacing at 3x3 meters. Apply organic compost twice per year. Spray neem oil for pest management. Ensure regular drip irrigation. Target yield: 400kg dry pepper per acre."
            },
            {
                "project_id": windflower.id,
                "title": "Zameer Conversation Meeting Notes",
                "filename": "meeting_notes_2026_05.pdf",
                "content": "Minutes of Meeting. Date: May 14, 2026. Attendees: Zameer, Darshan. Discussion points: Zameer confirmed that land-use conversion for the Windflower project was approved by the local authority, and formal certification is pending receipt within two weeks."
            },
            {
                "project_id": windflower.id,
                "title": "Vendor Master Record",
                "filename": "vendor_master.xlsx",
                "content": "Vendor Details: Netafim Drip Irrigation is the registered supplier for drip irrigation systems. Current contract amount is pending payment. Hedge-Grow Fencing is fully paid. Contact Netafim: +91 98450 12345."
            }
        ]

        for doc_def in doc_definitions:
            file_path = os.path.join(settings.UPLOAD_DIR, doc_def["filename"])
            # Write mock text file content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(doc_def["content"])
            
            db_doc = models.Document(
                project_id=doc_def["project_id"],
                title=doc_def["title"],
                file_type=os.path.splitext(doc_def["filename"])[1].replace('.', '').upper(),
                file_path=file_path,
                upload_date=datetime.datetime.utcnow()
            )
            db.add(db_doc)
            await db.commit()
            await db.refresh(db_doc)

            # Process / Ingest document to create chunks and embeddings
            await ingestion.ingest_document(db_doc.id, db)

        print("Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
