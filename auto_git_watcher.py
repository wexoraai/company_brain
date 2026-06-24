import time
import subprocess
import os
import logging
from watchfiles import watch

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("GitAutoWatcher")

logger.info("Initializing Git Auto Watcher...")

# Excluded folders / extensions
EXCLUDED_PATHS = [".git", "__pycache__", "company_brain.db", "temp_downloads", "uploads"]
EXCLUDED_EXT = [".db", ".pyc", ".log", ".tmp"]

def is_ignored(path: str) -> bool:
    """Check if the changed file path should be ignored."""
    parts = os.path.normpath(path).split(os.sep)
    for part in parts:
        if part in EXCLUDED_PATHS:
            return True
    ext = os.path.splitext(path)[1].lower()
    if ext in EXCLUDED_EXT:
        return True
    return False

def push_changes(change_details: str):
    """Commits and pushes changes to GitHub."""
    logger.info(f"Change detected: {change_details}")
    try:
        # Add all files (respecting .gitignore)
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit changes
        commit_msg = f"Auto-commit: updates detected at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        # Push changes to GitHub
        result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Successfully pushed updates to GitHub.")
        else:
            logger.error(f"Git push failed: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git process warning (possibly no changes to commit): {e}")
    except Exception as e:
        logger.error(f"Error executing git auto-push: {e}")

def main():
    logger.info("Watching workspace for changes. Pushes will be triggered automatically.")
    
    # Watch the current directory
    for changes in watch('.'):
        has_valid_changes = False
        change_desc = []
        
        for change_type, path in changes:
            if not is_ignored(path):
                has_valid_changes = True
                change_desc.append(f"{change_type.name}: {os.path.basename(path)}")
        
        if has_valid_changes:
            logger.info(f"Triggering auto-push for: {', '.join(change_desc)}")
            push_changes(", ".join(change_desc))

if __name__ == "__main__":
    main()
