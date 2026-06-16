import git
import os
from collections import defaultdict
from ..models import GitMetadata

class GitMetadataParser:
    def parse(self, repo_path: str) -> GitMetadata:
        try:
            repo = git.Repo(repo_path)
            
            # This can be slow for large repos, limit to recent commits for MVP
            commits = list(repo.iter_commits('HEAD', max_count=100))
            
            file_authors = {}
            file_change_counts = defaultdict(int)
            
            # Simple approach: iterate recent commits
            for commit in commits:
                for file_path in commit.stats.files.keys():
                    # Only count changes in this recent window
                    file_change_counts[file_path] += 1
                    
                    # Store the first author we see (since we iterate backwards, this is last modifier)
                    if file_path not in file_authors:
                        file_authors[file_path] = f"{commit.author.name} <{commit.author.email}>"
            
            return GitMetadata(
                repository=os.path.basename(os.path.abspath(repo_path)),
                branch=repo.active_branch.name if not repo.head.is_detached else "detached",
                last_commit_sha=repo.head.commit.hexsha,
                file_authors=file_authors,
                file_change_counts=dict(file_change_counts)
            )
        except git.InvalidGitRepositoryError:
            # Not a git repo
            return GitMetadata(
                repository=os.path.basename(os.path.abspath(repo_path)),
                branch="none",
                last_commit_sha="",
                file_authors={},
                file_change_counts={}
            )
