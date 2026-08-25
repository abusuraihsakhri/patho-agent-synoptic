"""
FastAPI REST Application & Webhooks for PathoAgent Synoptic: Autonomous Surgical Pathology Synoptic Completeness & Biomarker Triager.
"""
from typing import Dict, Any, Optional
from .models import ClinicalCasePayload
from .agents import PathologyDirectorCoordinator

coordinator = PathologyDirectorCoordinator()

def create_app():
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel

        app = FastAPI(
            title="PathoAgent Synoptic: Autonomous Surgical Pathology Synoptic Completeness & Biomarker Triager",
            description="Multi-agent digital pathology system auditing CAP Cancer Protocols, margin clearance (mm), lymph node tallies, and ER/PR/HER2/Ki-67 biomarker discordances.",
            version="2.0.0-PRO",
        )

        class AuditRequest(BaseModel):
            case_id: str = "CASE-2026-001"
            patient_synthetic_id: str = "SYNTH-PT-881"
            primary_metric: float = 24.5
            secondary_metric: float = 14.0
            status_flag: str = "DISCORDANT"
            is_stat: bool = True
            clinical_notes: str = ""
            biomarkers: Dict[str, Any] = {}

        class ChatRequest(BaseModel):
            query: str

        @app.get("/health")
        def health():
            return {"status": "HEALTHY", "system": "patho-agent-synoptic", "domain": "Digital Pathology", "version": "2.0.0-PRO"}

        @app.post("/api/audit")
        def api_audit(req: AuditRequest):
            payload = ClinicalCasePayload(
                case_id=req.case_id,
                patient_synthetic_id=req.patient_synthetic_id,
                primary_metric=req.primary_metric,
                secondary_metric=req.secondary_metric,
                status_flag=req.status_flag,
                is_stat=req.is_stat,
                clinical_notes=req.clinical_notes,
                biomarkers=req.biomarkers,
            )
            return coordinator.process_case(payload)

        @app.post("/api/chat")
        def api_chat(req: ChatRequest):
            return {"response": coordinator.query_supervisory_chat(req.query)}

        return app
    except ImportError:
        return None
