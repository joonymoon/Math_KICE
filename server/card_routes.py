"""
Card Upload Routes
Handles uploading and saving problem cards from the card maker UI
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

router = APIRouter(prefix="/api/card", tags=["card"])


@router.post("/upload")
async def upload_card(
    file: UploadFile = File(...),
    problem_id: str = Form(...),
    year: int = Form(...),
    exam: str = Form(...),
    question_no: int = Form(...),
    difficulty: str = Form(...),
    category: str = Form(...),
    subject: str = Form(None),
    answer: str = Form(None),
    solution: str = Form(None)
):
    """
    Upload a problem card image and save to database

    Args:
        file: PNG file of the card
        problem_id: Problem ID (e.g., 2025_수능_Q01)
        year: Year
        exam: Exam name
        question_no: Question number
        difficulty: Difficulty (2점, 3점, 4점)
        category: Category

    Returns:
        JSON with success status and image URL
    """
    try:
        # Read file content
        file_content = await file.read()

        # Upload to Supabase Storage
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_KEY")
        bucket = "problem-images-v2"

        # Filename: problem_id.png
        filename = f"{problem_id}.png"
        upload_url = f"{url}/storage/v1/object/{bucket}/{filename}"

        headers = {
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "image/png",
            "x-upsert": "true"
        }

        resp = requests.post(upload_url, headers=headers, data=file_content)

        if resp.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Upload failed: {resp.text}")

        # Generate public URL
        image_url = f"{url}/storage/v1/object/public/{bucket}/{filename}"

        # Save to database
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )

        # Map exam names
        exam_map = {
            "수능": "CSAT",
            "6월 모의평가": "KICE6",
            "9월 모의평가": "KICE9",
            "3월 학력평가": "MOCK3",
            "4월 학력평가": "MOCK4",
            "7월 학력평가": "MOCK7",
            "10월 학력평가": "MOCK10",
        }
        exam_code = exam_map.get(exam, exam)

        # Parse difficulty score
        score_map = {"2점": 2, "3점": 3, "4점": 4}
        score = score_map.get(difficulty, 3)

        problem_data = {
            "problem_id": problem_id,
            "year": year,
            "exam": exam_code,
            "question_no": question_no,
            "score": score,
            "problem_image_url": image_url,
            "status": "ready",  # Card maker = ready to send
            "unit": category,  # Use category as unit
        }

        # Add optional metadata if provided
        if subject:
            problem_data["subject"] = subject
        if answer:
            problem_data["answer"] = answer
            problem_data["answer_verified"] = answer  # Also set verified answer
        if solution:
            problem_data["solution"] = solution

        supabase.table("problems").upsert(
            problem_data,
            on_conflict="problem_id"
        ).execute()

        return {
            "success": True,
            "image_url": image_url,
            "problem_id": problem_id,
            "message": "Card uploaded and saved successfully"
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] Card upload failed:")
        print(error_details)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
