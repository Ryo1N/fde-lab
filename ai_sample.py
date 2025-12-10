import json
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Literal
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_qdrant import QdrantVectorStore
from braintrust import init_logger, traced
from braintrust_langchain import BraintrustCallbackHandler, set_global_handler
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from config import settings

client = OpenAI(api_key = settings.OPENAI_API_KEY)
init_logger(project="Prodapt", api_key=settings.BRAINTRUST_API_KEY)
set_global_handler(BraintrustCallbackHandler())

resume_eval_prompt = """
You are an expert hiring screener. Given the candidate resume text and a job description, evaluate candidate's fit.

Inputs (do not invent facts):
- RESUME_TEXT: {0}
- JOB_DESC: {1}

Return a JSON object with these fields:
{
  "overall_score": integer 0-100,  
  "strengths": [strings],         // 3 most important strengths
  "gaps": [strings],              // 3 main gaps or risks
  "match_by_section": {           // short mapping of job sections to match info
    "required_skills": "match summary",
    "experience_years": "match summary",
    "education": "match summary"
  },
  "rewrite_snippet": "one paragraph resume intro tailored to the job (50-70 words)",
  "actionable_recommendations": [strings]  // 3-5 concrete edits or next steps
}

Be concise. Use the resume text only for facts; do not hallucinate experience or dates. If the resume is very long, summarize conservatively.
"""


def build_system_and_user_messages(resume_text: str, job_desc: str):
    prompt = resume_eval_prompt.replace("{0}", resume_text).replace("{1}", job_desc)
    return [
        {"role": "system", "content": "You are a helpful, neutral, accurate recruiter assistant."},
        {"role": "user", "content": prompt}
    ]

def evaluate_resume_with_ai(resume_text: str, 
                            job_desc: str, 
                            model="gpt-4o-mini", temperature=0):
    messages = build_system_and_user_messages(resume_text, job_desc)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=1000
    )
    return json.loads(resp.choices[0].message.content.strip())

class ReviewedApplication(BaseModel):
    revised_description: str
    overall_summary: str

class JDAnalysis(BaseModel):
    unclear_sections: List[str]
    jargon_terms: List[str]
    biased_language: List[str]
    missing_information: List[str]
    overall_summary: str

ANALYSIS_SYSTEM_PROMPT = """
You are an expert HR job description analyst specializing in inclusive hiring practices.

Analyze the provided job description for potential issues across these dimensions:

1. CLARITY: Identify sections with vague responsibilities, unclear expectations, or ambiguous requirements.
   Flag phrases like "various duties," "other tasks as assigned," or undefined acronyms.

2. JARGON: Flag unnecessarily technical language inappropriate for the role level.
   Consider whether terms would be understood by qualified candidates unfamiliar with internal terminology.

3. BIAS: Identify language that may discourage diverse candidates:
   - Gender-coded words (e.g., "rockstar," "ninja," "aggressive," "nurturing")
   - Age bias (e.g., "digital native," "recent graduate")
   - Exclusionary phrases (e.g., "culture fit," "work hard/play hard")
   - Excessive requirements (unnecessarily requiring degrees or years of experience)

4. MISSING INFORMATION: Note absent critical details:
   - Salary range or compensation structure
   - Work location/arrangement (remote/hybrid/onsite)
   - Reporting structure or team context
   - Clear distinction between required vs. preferred qualifications
   - Application process and timeline
   - Growth/development opportunities

5. SUMMARY: Provide 2-3 sentences describing overall quality and primary concerns.

For each issue you identify:
- Quote the exact problematic text
- Explain why it is problematic
- Suggest an improvement (when applicable)

Your output MUST be valid JSON that conforms exactly to the provided schema.
Do not include any text outside the JSON.

If information is missing, return empty arrays.
"""

ANALYSIS_USER_PROMPT = """
Analyze the following job description:

--- JOB DESCRIPTION ---
{job_description}
----------------------

Return only JSON.

{format_instructions}
"""

class RewrittenSection(BaseModel):
    category: Literal["clarity", "jargon", "bias", "missing_information"]
    original_text: str
    issue_explanation: str
    improved_text: str

class JDRewriteOutput(BaseModel):
    rewritten_sections: List[RewrittenSection]

REWRITE_SYSTEM_PROMPT = """
You are an expert HR editor specializing in rewriting job descriptions for clarity, inclusivity,
and accessibility.

You will receive:
1. The original job description.
2. A structured analysis of issues found in Step 1.

Your task is to rewrite ONLY the problematic sections, not the entire job description.

For each identified issue:
- Include the original problematic text (quoted exactly)
- Include the category (clarity, jargon, bias, or missing_information)
- Provide an improved, inclusive alternative that preserves meaning
- Maintain neutral, professional tone
- Ensure suggestions follow inclusive hiring practices

Return ONLY valid JSON matching the provided schema. Do not write any prose outside JSON.
"""

REWRITE_USER_PROMPT = """
Original Job Description:
-------------------------
{job_description}

Analysis Findings:
------------------
{analysis_json}

Rewrite ONLY the problematic sections using the schema.
Return only JSON.

{format_instructions}
"""

FINALISE_SYSTEM_PROMPT = """
You are an expert HR writer specializing in creating clear, concise, and inclusive job descriptions.

Your job is to produce the final polished version of the job description.

You will receive:
1. The original job description.
2. A list of rewritten sections (from Step 2).

Your tasks:
- Incorporate all improved rewritten sections into the original job description.
- Remove or replace the problematic text that was flagged in earlier steps.
- Maintain the original intent, structure, and role scope.
- Ensure clarity, inclusivity, and accessibility.
- Make tone consistent: professional, warm, and concise.
- Improve flow and readability where necessary.
- Do NOT invent new responsibilities, requirements, or benefits.

Return ONLY the final polished job description as plain text. Do not include JSON.
"""

FINALISE_USER_PROMPT = """
Original Job Description:
-------------------------
{job_description}

Rewritten Sections:
-------------------
{rewritten_sections_json}

Create the final polished job description by integrating the improvements.
Return only the final text.
"""

@traced(name="Review Job Description")
def review_application(job_description: str) -> ReviewedApplication:
    llm = ChatOpenAI(model="gpt-5.1", temperature=0, api_key=settings.OPENAI_API_KEY)

    analysis_parser = PydanticOutputParser(pydantic_object=JDAnalysis)
    analysis_prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYSIS_SYSTEM_PROMPT),
        ("human", ANALYSIS_USER_PROMPT),
    ]).partial(format_instructions=analysis_parser.get_format_instructions())
    analysis_chain = analysis_prompt | llm | analysis_parser
    analysis = analysis_chain.invoke({"job_description": job_description})

    rewrite_parser = PydanticOutputParser(pydantic_object=JDRewriteOutput)
    rewrite_prompt = ChatPromptTemplate.from_messages([
        ("system", REWRITE_SYSTEM_PROMPT),
        ("human", REWRITE_USER_PROMPT),
    ]).partial(format_instructions=rewrite_parser.get_format_instructions())
    rewrite_chain = rewrite_prompt | llm | rewrite_parser
    rewrite = rewrite_chain.invoke({"job_description": job_description, "analysis_json": analysis.json()})

    finalise_prompt = ChatPromptTemplate.from_messages([
        ("system", FINALISE_SYSTEM_PROMPT),
        ("human", FINALISE_USER_PROMPT),
    ])
    finalise_chain = finalise_prompt | llm
    final_output = finalise_chain.invoke({
        "job_description": job_description, 
        "rewritten_sections_json": rewrite.json()})
    revised_description = final_output.text
    overall_summary = analysis.overall_summary
    return ReviewedApplication(revised_description=revised_description, overall_summary=overall_summary)

def get_vector_store():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=settings.OPENAI_API_KEY)
    if settings.PRODUCTION:
        vector_store = QdrantVectorStore.from_existing_collection(
            embedding=embeddings, 
            collection_name="resumes", 
            url=str(settings.QDRANT_URL), 
            api_key=settings.QDRANT_API_KEY)
    else:
        vector_store = QdrantVectorStore.from_existing_collection(
            embedding=embeddings, 
            collection_name="resumes", 
            path="qdrant_store")
    return vector_store

def inmemory_vector_store():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=settings.OPENAI_API_KEY)
    client = QdrantClient(":memory:")
    client.create_collection(collection_name="resumes", vectors_config=VectorParams(size=3072, distance=Distance.COSINE))
    vector_store = QdrantVectorStore(client=client, collection_name="resumes", embedding=embeddings)
    try:
        yield vector_store
    finally:
        client.close()

def ingest_resume(resume_text, resume_url, resume_id, vector_store):
    doc = Document(page_content=resume_text, metadata={"url": resume_url})
    vector_store.add_documents(documents=[doc], ids=[resume_id])

def get_recommendation(job_description, vector_store):
    retriever = vector_store.as_retriever(search_kwargs={"k": 1})
    results = retriever.invoke(job_description)
    return results[0]