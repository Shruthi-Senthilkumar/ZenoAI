import os
import httpx
import json
from dotenv import load_dotenv
from sqlmodel import Session, select

load_dotenv()

class GitHubConnector:
    def __init__(self):
        self.default_owner = os.getenv("GITHUB_OWNER", "test-user")
        self.default_repo = os.getenv("GITHUB_REPO", "test-repo")

    def _get_connected_token(self, student_id: str) -> tuple[str, str] | tuple[None, None]:
        """Looks up the real, decrypted OAuth token for a student who's
        connected via /auth/github (backend/routes/auth.py). Returns
        (token, github_username) or (None, None) if not connected —
        callers fall back to the mock path on None, same as an
        explicitly-omitted token always has.

        Import is local, not top-level: avoids a circular import
        (backend.database <-> connectors at package-init time) and
        keeps this connector importable even in contexts that don't
        need the DB (e.g. a future test double).
        """
        from backend.database import Student, engine
        from backend.logic.crypto import decrypt_token

        with Session(engine) as session:
            student = session.exec(select(Student).where(Student.id == student_id)).first()
            if student is None or not student.github_token_encrypted:
                return None, None
            token = decrypt_token(student.github_token_encrypted)
            return token, student.github_username

    def get_latest_commit(self, student_id: str, token: str = None) -> dict:
        """
        Retrieves the latest commit of the student's repository from GitHub API.
        If offline, rate-limited, or unauthorized, returns a simulated mock commit
        containing a sample meta.json file.

        `token` is normally left unset by callers — this method looks up the
        student's real, connected OAuth token itself (if they've been
        through /auth/github/authorize) rather than requiring every call
        site to plumb it through manually. Passing `token` explicitly still
        works, for tests or a future multi-account scenario.

        Repo selection is still a known gap: a connected student's token
        lets us call the API as them, but nothing yet lets them pick
        *which* repo to poll — GITHUB_OWNER/GITHUB_REPO stay the
        configured default until a repo-picker exists. Out of scope for
        this pass; flagging rather than silently hardcoding around it.
        """
        owner = self.default_owner
        repo = self.default_repo

        if token is None:
            token, _ = self._get_connected_token(student_id)

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
                
                if raw_url and "raw.githubusercontent.com/mock" not in raw_url:
                    try:
                        with httpx.Client() as client:
                            response = client.get(raw_url)
                            if response.status_code == 200:
                                return response.json()
                    except Exception as e:
                        print(f"Error fetching raw file content: {e}")
                
                patch_content = f.get("patch")
                if patch_content:
                    try:
                        return json.loads(patch_content)
                    except Exception:
                        pass
        return None

github_connector = GitHubConnector()