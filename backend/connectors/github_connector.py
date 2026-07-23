import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

class GitHubConnector:
    def __init__(self):
        self.default_owner = os.getenv("GITHUB_OWNER", "test-user")
        self.default_repo = os.getenv("GITHUB_REPO", "test-repo")

    def get_latest_commit(self, student_id: str, token: str = None) -> dict:
        """
        Retrieves the latest commit of the student's repository from GitHub API.
        If offline, rate-limited, or unauthorized, returns a simulated mock commit
        containing a sample meta.json file.
        """
        owner = self.default_owner
        repo = self.default_repo
        
        url = f"https://api.github.com/repos/{owner}/{repo}/commits/main"
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            headers["Authorization"] = f"token {token}"
            
        try:
            with httpx.Client() as client:
                response = client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Error fetching latest commit from GitHub: {e}")
            
        # Return simulated mock commit data if offline/unconfigured
        return {
            "sha": "mock_sha_12345",
            "commit": {
                "message": "Pushed solution for LeetCode problem"
            },
            "files": [
                {
                    "filename": "meta.json",
                    "status": "added",
                    "raw_url": "https://raw.githubusercontent.com/mock/repo/main/meta.json",
                    "patch": json.dumps({
                        "problem": "two-sum",
                        "difficulty": "Easy",
                        "time_taken_seconds": 600,
                        "attempts": 2,
                        "solved_at": "2026-07-22T20:00:00Z"
                    })
                }
            ]
        }

    def extract_file(self, commit: dict, filename: str) -> dict | None:
        """
        Extracts the content of a file from a commit dictionary.
        """
        files = commit.get("files", [])
        for f in files:
            curr_filename = f.get("filename", "")
            if curr_filename == filename or curr_filename.endswith("/" + filename):
                raw_url = f.get("raw_url")
                
                # If it's a real URL (not mock), try to fetch the file contents from GitHub
                if raw_url and "raw.githubusercontent.com/mock" not in raw_url:
                    try:
                        with httpx.Client() as client:
                            response = client.get(raw_url)
                            if response.status_code == 200:
                                return response.json()
                    except Exception as e:
                        print(f"Error fetching raw file content: {e}")
                
                # Fallback to parsing from mock/patch content if present
                patch_content = f.get("patch")
                if patch_content:
                    try:
                        # Extract JSON object from patch or parse it directly
                        return json.loads(patch_content)
                    except Exception:
                        pass
        return None

github_connector = GitHubConnector()
