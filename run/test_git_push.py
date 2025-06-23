# notebook.ipynb

# Add this to the beginning of your notebook as a cell:
import os
import requests
from google.cloud import secretmanager

# Get the GitHub token from Secret Manager
def get_github_token():
    key = os.environ.get('GITHUB_KEY_MODELEARTH', None)
    if key:
        return key
    else:
        raise ValueError("GITHUB_KEY_MODELEARTH environment variable not set")

# Set the token as an environment variable for the upload function
GITHUB_TOKEN = get_github_token()


def upload_reports_to_github(repo, token, report_path, branch='main', commit_message='Reports from Run Models colab'):
    
    # Upload all files from the report folder to GitHub repository.

    # Args:
    #    repo (str): GitHub repository in the format 'username/repo'
    #    token (str): GitHub personal access token
    #    branch (str): Branch to push to (default: 'main')
    #    commit_message (str): Commit message (can include {report_file_count} placeholder)
    
    # First, set up the report folder and get file count
    report_file_count = len(list(report_path.glob("**/*")))  # Count all files in the report folder

    # Format the commit message with the file count if needed
    if "{report_file_count}" in commit_message:
        commit_message = commit_message.format(report_file_count=report_file_count)

    print(f"Preparing to push {report_file_count} reports to: {repo}")

    # GitHub API endpoint for getting the reference
    api_url = f"https://api.github.com/repos/{repo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # Get the current reference (SHA) of the branch
        ref_response = requests.get(f"{api_url}/git/refs/heads/{branch}", headers=headers)
        ref_response.raise_for_status()
        ref_sha = ref_response.json()["object"]["sha"]

        # Get the current commit to which the branch points
        commit_response = requests.get(f"{api_url}/git/commits/{ref_sha}", headers=headers)
        commit_response.raise_for_status()
        base_tree_sha = commit_response.json()["tree"]["sha"]

        # Create a new tree with all the files in the report folder
        new_tree = []

        
        for file_path in report_path.glob("**/*"):
            if file_path.is_file():
                # Calculate the path relative to the report folder
                relative_path = file_path.relative_to(report_path)
                github_path = f"reports/{relative_path}"

                # Read file content and encode as base64
                with open(file_path, "rb") as f:
                    content = f.read()

                # Add the file to the new tree
                new_tree.append({
                    "path": github_path,
                    "mode": "100644",  # File mode (100644 for regular file)
                    "type": "blob",
                    "content": content.decode('utf-8', errors='replace')
                })

        # Create a new tree with the new files
        new_tree_response = requests.post(
            f"{api_url}/git/trees",
            headers=headers,
            json={
                "base_tree": base_tree_sha,
                "tree": new_tree
            }
        )
        new_tree_response.raise_for_status()
        new_tree_sha = new_tree_response.json()["sha"]

        # Create a new commit
        new_commit_response = requests.post(
            f"{api_url}/git/commits",
            headers=headers,
            json={
                "message": commit_message,
                "tree": new_tree_sha,
                "parents": [ref_sha]
            }
        )
        new_commit_response.raise_for_status()
        new_commit_sha = new_commit_response.json()["sha"]

        # Update the reference to point to the new commit
        update_ref_response = requests.patch(
            f"{api_url}/git/refs/heads/{branch}",
            headers=headers,
            json={"sha": new_commit_sha}
        )
        update_ref_response.raise_for_status()

        print(f"Successfully pushed {report_file_count} files to GitHub repository: {repo}")
        print(f"Branch: {branch}")
        print(f"Commit message: {commit_message}")
        return True

    except Exception as e:
        print(f"Error uploading files to GitHub: {e}")
        return False

# Test the upload function
if __name__ == "__main__":
    from pathlib import Path

    # Example usage
    repo = "Abivishaq/modelearth-notebook-results"  # Replace with your GitHub repo
    report_path = Path("temp_dir/reports")  # Path to the reports folder
    print(type(report_path))
    # upload_reports_to_github(repo, GITHUB_TOKEN, report_path)