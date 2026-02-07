"""
Supabase Storage Service
Uploads images to Supabase Storage for direct public URLs
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class SupabaseStorageService:
    """Upload and manage files in Supabase Storage"""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.bucket_name = "problem-images-v2"

        if not self.url or not self.service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY required")

    def create_bucket_if_not_exists(self) -> bool:
        """Create storage bucket if it doesn't exist"""
        headers = {
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json"
        }

        # Check if bucket exists
        check_url = f"{self.url}/storage/v1/bucket/{self.bucket_name}"
        response = requests.get(check_url, headers=headers)

        if response.status_code == 200:
            print(f"Bucket '{self.bucket_name}' already exists")
            return True

        # Create bucket
        create_url = f"{self.url}/storage/v1/bucket"
        data = {
            "id": self.bucket_name,
            "name": self.bucket_name,
            "public": True,
            "file_size_limit": 10485760  # 10MB
        }

        response = requests.post(create_url, headers=headers, json=data)

        if response.status_code in [200, 201]:
            print(f"Created bucket '{self.bucket_name}'")
            return True
        else:
            print(f"Failed to create bucket: {response.text}")
            return False

    def upload_image(self, local_path: str, remote_path: str = None) -> dict:
        """
        Upload image to Supabase Storage

        Args:
            local_path: Path to local image file
            remote_path: Optional path in bucket (default: filename)

        Returns:
            dict with success status and public URL
        """
        local_path = Path(local_path)

        if not local_path.exists():
            return {"success": False, "error": f"File not found: {local_path}"}

        # Use filename if no remote path specified
        if not remote_path:
            remote_path = local_path.name

        # Determine content type
        ext = local_path.suffix.lower()
        content_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        content_type = content_types.get(ext, "application/octet-stream")

        # Upload file
        upload_url = f"{self.url}/storage/v1/object/{self.bucket_name}/{remote_path}"

        headers = {
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": content_type,
            "x-upsert": "true"  # Overwrite if exists
        }

        with open(local_path, "rb") as f:
            file_data = f.read()

        response = requests.post(upload_url, headers=headers, data=file_data)

        if response.status_code in [200, 201]:
            # Generate public URL
            public_url = f"{self.url}/storage/v1/object/public/{self.bucket_name}/{remote_path}"
            return {
                "success": True,
                "url": public_url,
                "path": remote_path
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }

    def upload_problem_images(self, output_dir: str = "./output") -> list:
        """
        Upload all problem images from output directory

        Args:
            output_dir: Directory containing problem images

        Returns:
            List of upload results
        """
        output_path = Path(output_dir)

        if not output_path.exists():
            print(f"Output directory not found: {output_path}")
            return []

        # Find all PNG files (including subdirectories)
        images = list(output_path.glob("**/*.png"))

        if not images:
            print("No PNG images found")
            return []

        print(f"Found {len(images)} images to upload")

        # Create bucket first
        self.create_bucket_if_not_exists()

        results = []
        for idx, img_path in enumerate(images, 1):
            print(f"Uploading [{idx}/{len(images)}]: {img_path.name}")

            result = self.upload_image(str(img_path))
            result["filename"] = img_path.name
            results.append(result)

            if result["success"]:
                print(f"  [OK] {result['url']}")
            else:
                print(f"  [FAIL] {result.get('error', 'Unknown error')}")

        success_count = sum(1 for r in results if r["success"])
        print(f"\nUploaded {success_count}/{len(images)} images")

        return results

    def get_public_url(self, remote_path: str) -> str:
        """Get public URL for a file in storage"""
        return f"{self.url}/storage/v1/object/public/{self.bucket_name}/{remote_path}"


def upload_and_update_database():
    """Upload images and update database with new URLs"""
    from supabase import create_client

    storage = SupabaseStorageService()

    # Create bucket first
    storage.create_bucket_if_not_exists()

    # Connect to Supabase database
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

    # Get all problems with local image paths
    response = supabase.table("problems").select("problem_id,problem_image_url,question_no").execute()
    problems = response.data

    if not problems:
        print("No problems found in database")
        return

    print(f"Found {len(problems)} problems in database")

    updated = 0
    for problem in problems:
        problem_id = problem["problem_id"]
        local_path = problem.get("problem_image_url", "")

        # Skip if already a public URL
        if local_path and local_path.startswith("http"):
            print(f"Skipping {problem_id}: already has public URL")
            continue

        # Build local file path
        if local_path:
            # Convert Windows path to proper format
            local_path = local_path.replace("\\", "/")
            full_path = Path(local_path)
        else:
            # Guess path from question number
            q_no = problem.get("question_no")
            if q_no:
                full_path = Path(f"./output/2026_CSAT_PROBLEM/page_{q_no:03d}.png")
            else:
                print(f"Skipping {problem_id}: no image path or question number")
                continue

        if not full_path.exists():
            print(f"Skipping {problem_id}: file not found - {full_path}")
            continue

        # Upload to Supabase Storage
        remote_path = f"{problem_id}.png"
        result = storage.upload_image(str(full_path), remote_path)

        if result["success"]:
            public_url = result["url"]

            # Update database with public URL
            try:
                supabase.table("problems").update({
                    "problem_image_url": public_url
                }).eq("problem_id", problem_id).execute()

                print(f"[OK] {problem_id} -> {public_url}")
                updated += 1
            except Exception as e:
                print(f"[FAIL] {problem_id}: DB update failed - {e}")
        else:
            print(f"[FAIL] {problem_id}: upload failed - {result.get('error')}")

    print(f"\nUpdated {updated}/{len(problems)} problems with Supabase Storage URLs")


if __name__ == "__main__":
    upload_and_update_database()
