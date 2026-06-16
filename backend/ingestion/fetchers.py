import os
import requests
import zipfile
import tempfile
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class GitHubFetcher:
    """Fetches a GitHub repository without cloning it, by downloading its zip archive."""
    
    @contextmanager
    def fetch_as_temp_dir(self, repo_url: str):
        """
        Downloads a GitHub repo zipball and extracts it to a temporary directory.
        Yields the path to the extracted directory.
        Automatically cleans up when the context manager exits.
        """
        # Parse github URL to get owner and repo
        # Example: https://github.com/thecodeblood/codelens-ekos -> owner: thecodeblood, repo: codelens-ekos
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
            
        owner = parts[-2]
        repo = parts[-1]
        
        if repo.endswith(".git"):
            repo = repo[:-4]
            
        api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/main"
        
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Use token if available
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
            
        logger.info(f"Downloading repository zip from {api_url}")
        
        response = requests.get(api_url, headers=headers, stream=True)
        
        # Fallback to master branch if main is not found
        if response.status_code == 404:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/master"
            logger.info(f"'main' branch not found, trying 'master': {api_url}")
            response = requests.get(api_url, headers=headers, stream=True)
            
        if response.status_code != 200:
            raise Exception(f"Failed to fetch GitHub repository. Status code: {response.status_code}. Response: {response.text}")

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "repo.zip")
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Extracting zip to {temp_dir}")
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            # The zipball usually contains a single root directory (e.g. owner-repo-sha)
            # We want to yield the path to that root directory.
            contents = os.listdir(extract_dir)
            if len(contents) == 1 and os.path.isdir(os.path.join(extract_dir, contents[0])):
                yield os.path.join(extract_dir, contents[0])
            else:
                yield extract_dir


class WebFetcher:
    """Fetches text content from a public web page."""
    
    def fetch_text(self, url: str) -> str:
        headers = {
            "User-Agent": "CodeLens-EKOS-Ingestion-Bot/1.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch web page. Status code: {response.status_code}")
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Kill all script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        return text


class PDFFetcher:
    """Extracts text from a local PDF file."""
    
    def extract_text(self, file_path: str) -> str:
        try:
            doc = fitz.open(file_path)
            text_blocks = []
            for page in doc:
                text_blocks.append(page.get_text())
            doc.close()
            return "\n".join(text_blocks)
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise
