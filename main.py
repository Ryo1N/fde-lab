import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from db import get_db_session
from models import JobBoard

app = FastAPI()

@app.get("/health")
async def health():
  try:
    with get_db_session() as session:
        session.execute(text("SELECT 1"))
        return {"database": "ok"}
  except Exception as e:
    print(e)
    return {"database": "down"}


app.mount("/app", StaticFiles(directory="frontend/dist"))
@app.get("/")
async def root():
  indexFilePath = os.path.join("frontend", "dist", "index.html")
  return FileResponse(path=indexFilePath, media_type="text/html")

from models import JobBoard
@app.get("/api/job-boards")
async def api_job_boards():
    with get_db_session() as session:
       jobBoards = session.query(JobBoard).all()
       return jobBoards
    
jobBoards = {
    "acme": [
        {
            "title": "Customer Support Executive",
            "jobDescription": "We are seeking an empathetic and proactive Customer Support Executive to join our team and provide exceptional service to our customers. In this role, you will be the primary point of contact for our clients, addressing inquiries, troubleshooting problems, and ensuring a positive experience across various communication channels (phone, email, and chat). The ideal candidate is a patient, problem-solving individual with excellent communication skills and a commitment to customer satisfaction.",
        },
        {
            "title": "Project Manager",
            "jobDescription": "We are seeking a highly organized and strategic Project Manager to lead a variety of projects from initiation to closure. The ideal candidate will be responsible for defining project scopes, managing resources, mitigating risks, and ensuring timely delivery within budget. This role requires strong leadership, exceptional communication skills, and the ability to inspire a team to meet project goals and exceed stakeholder expectations.",
        },
    ],
    "bcg": [
        {
            "title": "Technical Arcitect",
            "jobDescription": "We are looking for an innovative and strategic Technical Architect to design and oversee the implementation of complex enterprise solutions. This role requires a visionary leader capable of translating business needs into robust, scalable technical architecture, providing technical guidance to development teams, and ensuring our technology stack aligns with industry best practices. The ideal candidate possesses deep expertise in software design patterns, infrastructure, cloud technologies, and a proven track record of delivering resilient architectural solutions.",
        },
        {
            "title": "Junior Software Developer",
            "jobDescription": "We are seeking a motivated and eager Junior Software Developer to join our dynamic development team. This entry-level position is perfect for a recent graduate or early-career professional looking to kick-start a career in technology. You will collaborate with senior developers and engineers on various projects, contributing to coding, testing, debugging, and maintaining high-quality software solutions. The ideal candidate has a foundational understanding of programming principles, a passion for learning new technologies, and a keen eye for detail.",
        },
    ],
    "atlas": [
        {
            "title": "Senior Accountant",
            "jobDescription": "We are seeking a detail-oriented and experienced Senior Accountant to manage and oversee key accounting functions within our finance department. The successful candidate will be responsible for a variety of general ledger activities, financial reporting, account reconciliations, and compliance tasks. This role requires strong analytical skills, in-depth knowledge of accounting principles, and the ability to work collaboratively to ensure the integrity of our financial records. The ideal candidate will be a proactive problem-solver ready to take on a leadership role in financial operations.",
        },
        {
            "title": "Accounting Clerk",
            "jobDescription": "We are seeking a meticulous and reliable Accounting Clerk to support our finance department with daily administrative and accounting tasks. This entry-level position is ideal for an organized individual with strong attention to detail and a foundational understanding of basic accounting principles. The successful candidate will be responsible for processing transactions, maintaining accurate financial records, and ensuring the smooth operation of our accounts payable and accounts receivable functions.",
        },
    ],
}

@app.get("/api/job-boards/{slug}")
async def api_company_job_board(request : Request, slug):
  if slug in jobBoards:
    jobBoard = jobBoards[slug]
    return jobBoard
  raise HTTPException(status_code=404, detail="Job board not found")