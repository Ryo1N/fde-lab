import os
from typing import Annotated, Optional
from fastapi import BackgroundTasks, Depends, Request, Response, status, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from ai import evaluate_resume_with_ai
from auth import AdminAuthzMiddleware, AdminSessionMiddleware, authenticate_admin, delete_admin_session
from converter import extract_text_from_pdf_bytes
from db import get_db, get_db_session
from emailer import send_email
from file_storage import upload_file
from models import JobApplication, JobApplicationAIEvaluation, JobBoard, JobPost
from config import settings

app = FastAPI()
app.add_middleware(AdminAuthzMiddleware)
app.add_middleware(AdminSessionMiddleware)

from sqlalchemy.orm import Session

@app.get("/api/health")
async def health(db: Session = Depends(get_db)):
  try:
    db.execute(text("SELECT 1"))
    return {"database": "ok"}
  except Exception as e:
    print(e)
    return {"database": "down"}


@app.get("/api/me")
async def me(req: Request):
   return {"is_admin": req.state.is_admin}

@app.get("/api/job-boards")
async def api_job_boards(db: Session = Depends(get_db)):
   jobBoards = db.query(JobBoard).all()
   return jobBoards

@app.get("/api/job-application-ai-evaluations")
async def api_job_boards():
    with get_db_session() as session:
       results = session.query(JobApplicationAIEvaluation).all()
       return results
    
class JobBoardForm(BaseModel):
   slug : str = Field(..., min_length=2, max_length=20)
   logo: UploadFile = File(...)

@app.post("/api/job-boards")
async def api_create_new_job_board(job_board_form: Annotated[JobBoardForm, Form()]):
   logo_contents = await job_board_form.logo.read()
   file_url = upload_file("company-logos", job_board_form.logo.filename, logo_contents, job_board_form.logo.content_type)
   with get_db_session() as session:
      new_job_board = JobBoard(slug=job_board_form.slug, logo_url=file_url)
      session.add(new_job_board)
      session.commit()
      session.refresh(new_job_board)
      return new_job_board

if not settings.PRODUCTION:
   app.mount("/uploads", StaticFiles(directory="uploads"))

@app.get("/api/job-boards/{job_board_id}/job-posts")
async def api_company_job_board_posts(job_board_id):
  with get_db_session() as session:
     jobPosts = session.query(JobPost).filter(JobPost.job_board_id.__eq__(job_board_id)).all()
     return jobPosts

@app.get("/api/job-boards/{job_board_id}")
async def api_get_company_job_board(job_board_id):
  with get_db_session() as session:
     jobBoard = session.get(JobBoard, job_board_id)
     if not jobBoard:
        raise HTTPException(status_code=404)
     return jobBoard

@app.delete("/api/job-boards/{job_board_id}")
async def api_get_company_job_board(job_board_id):
  with get_db_session() as session:
     jobBoard = session.get(JobBoard, job_board_id)
     if not jobBoard:
        raise HTTPException(status_code=404)
     session.delete(jobBoard)
     session.commit()
     return jobBoard
  
class JobBoardEditForm(BaseModel):
   slug : str = Field(..., min_length=2, max_length=20)
   logo: Optional[UploadFile] = None

@app.put("/api/job-boards/{job_board_id}")
async def api_get_company_job_board(job_board_id, job_board_edit_form: Annotated[JobBoardEditForm, Form()]):
  with get_db_session() as session:
     jobBoard = session.get(JobBoard, job_board_id)
     if not jobBoard:
        raise HTTPException(status_code=404)
     jobBoard.slug = job_board_edit_form.slug
     if job_board_edit_form.logo is not None and job_board_edit_form.logo.filename != '':
        logo_contents = await job_board_edit_form.logo.read()
        file_url = upload_file("company-logos", job_board_edit_form.logo.filename, logo_contents, job_board_edit_form.logo.content_type)
        jobBoard.logo_url = file_url
     session.add(jobBoard)
     session.commit()
     return jobBoard

@app.post("/api/job-posts/{job_post_id}/close")
async def api_close_job_post(job_post_id):
  with get_db_session() as session:
     jobPost = session.get(JobPost, job_post_id)
     if not jobPost:
        raise HTTPException(status_code=404)
     jobPost.is_open = False
     session.add(jobPost)
     session.commit()
     return jobPost
  
class JobPostForm(BaseModel):
   title : str
   description: str
   job_board_id : int

@app.post("/api/job-posts")
async def api_create_job_post(job_post_form: Annotated[JobPostForm, Form()]):
  with get_db_session() as session:
     jobBoard = session.get(JobBoard, job_post_form.job_board_id)
     if not jobBoard:
        raise HTTPException(status_code=400)
     jobPost = JobPost(title=job_post_form.title, 
                       description=job_post_form.description, 
                       job_board_id = job_post_form.job_board_id)
     session.add(jobPost)
     session.commit()
     session.refresh(jobPost)
     return jobPost

@app.get("/api/job-boards/{slug}")
async def api_company_job_board(slug):
  with get_db_session() as session:
     jobPosts = session.query(JobPost) \
        .join(JobPost.job_board) \
        .filter(JobBoard.slug.__eq__(slug)) \
        .all()
     return jobPosts
  

class JobApplicationForm(BaseModel):
   first_name : str = Field(..., min_length=3, max_length=20)
   last_name : str = Field(..., min_length=3, max_length=20)
   email : EmailStr
   job_post_id : int
   resume: UploadFile = File(...)

def evaluate_resume(resume_content, job_post_description, job_application_id):
   resume_raw_text = extract_text_from_pdf_bytes(resume_content)
   ai_evaluation = evaluate_resume_with_ai(resume_raw_text, job_post_description)
   with get_db_session() as session:
      evaluation = JobApplicationAIEvaluation(
         job_application_id = job_application_id,
         overall_score = ai_evaluation["overall_score"],
         evaluation = ai_evaluation
      )
      session.add(evaluation)
      session.commit()

@app.post("/api/job-applications")
async def api_create_new_job_application(job_application_form: Annotated[JobApplicationForm, Form()], background_tasks: BackgroundTasks):
   with get_db_session() as session:
      jobPost = session.get(JobPost, job_application_form.job_post_id)
      if not jobPost or not jobPost.is_open:
         raise HTTPException(status_code=400)
      resume_content = await job_application_form.resume.read()
      file_url = upload_file("resumes", job_application_form.resume.filename, resume_content, job_application_form.resume.content_type)
      new_job_application = JobApplication(
         first_name=job_application_form.first_name, 
         last_name=job_application_form.last_name, 
         email=job_application_form.email, 
         job_post_id = job_application_form.job_post_id,
         resume_url=file_url)
      session.add(new_job_application)
      session.commit()
      session.refresh(new_job_application)
      background_tasks.add_task(send_email, 
                              new_job_application.email, 
                              "Acknowledgement", 
                              "We have received your job application")
      
      background_tasks.add_task(evaluate_resume, resume_content, 
                                jobPost.description, new_job_application.id)
      
      return new_job_application
  
app.mount("/assets", StaticFiles(directory="frontend/build/client/assets"))

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
  indexFilePath = os.path.join("frontend", "build", "client", "index.html")
  return FileResponse(path=indexFilePath, media_type="text/html")


class AdminLoginForm(BaseModel):
   username : str
   password : str

@app.post("/api/admin-login")
async def admin_login(response: Response, admin_login_form: Annotated[AdminLoginForm, Form()]):
   auth_response = authenticate_admin(admin_login_form.username, admin_login_form.password)
   if auth_response is not None:
      secure = settings.PRODUCTION
      
      response.set_cookie(key="admin_session", 
                          value=auth_response, 
                          httponly=True, secure=secure, 
                          samesite="Lax")
      return {}
   else:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
   
@app.post("/api/admin-logout")
async def admin_login(request: Request, response: Response):
   delete_admin_session(request.cookies.get("admin_session"))
   secure = settings.PRODUCTION
   response.delete_cookie(key="admin_session", 
                        httponly=True, secure=secure, 
                        samesite="Lax")
   return {}