import os
import pytest
from converter import extract_text_from_pdf_bytes
from ai import evaluate_resume_with_ai

def test_pdf_parsing():
    """
    Test PDF parsing using an existing sample file.
    """
    pdf_path = "./uploads/resumes/md-to-pdf.pdf"
    assert os.path.exists(pdf_path), f"Sample PDF not found at {pdf_path}"
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    text = extract_text_from_pdf_bytes(pdf_bytes)
    assert text, "Extracted text is empty"
    print(f"Extracted text length: {len(text)}")
    # Optional: check for specific content if known, but length > 0 is a good start

def test_ai_evaluation():
    """
    Test AI evaluation with a dummy resume and job description.
    """
    resume_text = "Software Engineer with 5 years of experience in Python and FastAPI."
    job_desc = "Looking for a Python developer with FastAPI experience."
    
    result = evaluate_resume_with_ai(resume_text, job_desc)
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "overall_score" in result, "Result missing 'overall_score'"
    assert "strengths" in result, "Result missing 'strengths'"
    assert "gaps" in result, "Result missing 'gaps'"
    
    print(f"AI Evaluation Result: {result}")
