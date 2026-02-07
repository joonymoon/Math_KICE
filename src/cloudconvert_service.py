"""
CloudConvert Service
Converts PDF files to individual problem images using CloudConvert API
"""

import os
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()


class CloudConvertService:
    """Convert PDF to images using CloudConvert API"""

    BASE_URL = "https://api.cloudconvert.com/v2"

    def __init__(self):
        self.api_key = os.getenv("CLOUDCONVERT_API_KEY")
        if not self.api_key or self.api_key == "your-cloudconvert-api-key":
            raise ValueError("CLOUDCONVERT_API_KEY is required. Get it from https://cloudconvert.com/dashboard/api/v2/keys")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request"""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = kwargs.pop("headers", self.headers)

        response = requests.request(method, url, headers=headers, **kwargs)

        if response.status_code >= 400:
            raise Exception(f"CloudConvert API error: {response.status_code} - {response.text}")

        return response.json() if response.text else {}

    def create_job(self, tasks: Dict[str, Any]) -> Dict[str, Any]:
        """Create a conversion job"""
        return self._request("POST", "jobs", json={"tasks": tasks})

    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get job status"""
        return self._request("GET", f"jobs/{job_id}")

    def wait_for_job(self, job_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for job to complete"""
        start_time = time.time()

        while True:
            job = self.get_job(job_id)
            status = job.get("data", {}).get("status")

            if status == "finished":
                return job
            elif status == "error":
                raise Exception(f"Job failed: {job}")

            if time.time() - start_time > timeout:
                raise TimeoutError(f"Job {job_id} timed out after {timeout}s")

            time.sleep(2)

    def convert_pdf_to_images(
        self,
        pdf_path: str,
        output_dir: str,
        dpi: int = 200,
        page_range: str = None
    ) -> List[str]:
        """
        Convert PDF to PNG images

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save images
            dpi: Image resolution (default 200)
            page_range: Optional page range (e.g., "1-5", "1,3,5")

        Returns:
            List of output image paths
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        print(f"Converting PDF: {pdf_path.name}")

        # Create conversion tasks
        convert_task = {
            "operation": "convert",
            "input_format": "pdf",
            "output_format": "png",
            "engine": "imagemagick",
            "pixel_density": dpi,
            "fit": "max",
            "width": 1200,
            "height": 1600
        }

        if page_range:
            convert_task["page_range"] = page_range

        tasks = {
            "import-file": {
                "operation": "import/upload"
            },
            "convert": {
                "operation": "convert",
                "input": ["import-file"],
                **convert_task
            },
            "export": {
                "operation": "export/url",
                "input": ["convert"],
                "inline": False,
                "archive_multiple_files": False
            }
        }

        # Create job
        job = self.create_job(tasks)
        job_id = job["data"]["id"]
        print(f"Created job: {job_id}")

        # Get upload URL
        upload_task = next(
            t for t in job["data"]["tasks"]
            if t["name"] == "import-file"
        )
        upload_url = upload_task["result"]["form"]["url"]
        upload_params = upload_task["result"]["form"]["parameters"]

        # Upload PDF
        print("Uploading PDF...")
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f)}
            upload_response = requests.post(
                upload_url,
                data=upload_params,
                files=files
            )

        if upload_response.status_code >= 400:
            raise Exception(f"Upload failed: {upload_response.text}")

        # Wait for conversion
        print("Converting... (this may take a while)")
        job = self.wait_for_job(job_id)

        # Download converted images
        output_paths = []
        export_task = next(
            t for t in job["data"]["tasks"]
            if t["name"] == "export"
        )

        for file_info in export_task.get("result", {}).get("files", []):
            file_url = file_info["url"]
            filename = file_info["filename"]
            output_path = output_dir / filename

            print(f"Downloading: {filename}")
            response = requests.get(file_url)
            with open(output_path, "wb") as f:
                f.write(response.content)

            output_paths.append(str(output_path))

        print(f"Converted {len(output_paths)} pages")
        return output_paths

    def convert_pdf_per_page(
        self,
        pdf_path: str,
        output_dir: str,
        prefix: str = "page",
        dpi: int = 200,
        start_page: int = 1,
        end_page: int = None
    ) -> List[Dict[str, Any]]:
        """
        Convert PDF to individual page images with proper naming

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save images
            prefix: Filename prefix (e.g., "2026_CSAT_Q")
            dpi: Image resolution
            start_page: First page number
            end_page: Last page number (None = all pages)

        Returns:
            List of dicts with page info and paths
        """
        # First, convert all pages
        page_range = None
        if end_page:
            page_range = f"{start_page}-{end_page}"
        elif start_page > 1:
            page_range = f"{start_page}-"

        raw_images = self.convert_pdf_to_images(
            pdf_path, output_dir, dpi, page_range
        )

        # Rename with proper prefix
        results = []
        for idx, img_path in enumerate(sorted(raw_images)):
            page_num = start_page + idx
            new_name = f"{prefix}{page_num:02d}.png"
            new_path = Path(output_dir) / new_name

            # Rename file
            Path(img_path).rename(new_path)

            results.append({
                "page": page_num,
                "path": str(new_path),
                "filename": new_name
            })

        return results


def convert_kice_pdf(
    pdf_path: str,
    year: int,
    exam: str,
    output_base: str = "./output"
) -> List[Dict[str, Any]]:
    """
    Convert KICE math exam PDF to individual question images

    Args:
        pdf_path: Path to PDF file
        year: Exam year (e.g., 2026)
        exam: Exam type (CSAT, KICE6, KICE9)
        output_base: Base output directory

    Returns:
        List of converted image info
    """
    service = CloudConvertService()

    # Create output directory
    output_dir = Path(output_base) / f"{year}_{exam}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert with proper naming
    prefix = f"{year}_{exam}_Q"
    results = service.convert_pdf_per_page(
        pdf_path=pdf_path,
        output_dir=str(output_dir),
        prefix=prefix,
        dpi=200
    )

    print(f"\nConverted {len(results)} pages to {output_dir}")
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python cloudconvert_service.py <pdf_path> <year> <exam>")
        print("Example: python cloudconvert_service.py ./downloads/math.pdf 2026 CSAT")
        sys.exit(1)

    pdf_path = sys.argv[1]
    year = int(sys.argv[2])
    exam = sys.argv[3]

    results = convert_kice_pdf(pdf_path, year, exam)
    for r in results:
        print(f"  {r['filename']}: {r['path']}")
