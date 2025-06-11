import os
import tempfile
import subprocess
import requests
import json
from flask import Flask, render_template, request, jsonify
from google.cloud import secretmanager
import git
import papermill as pm
import nbformat
from nbconvert import HTMLExporter
import shutil
from pathlib import Path
import time

app = Flask(__name__)

# Configuration
SOURCE_REPO_URL = "https://github.com/Abivishaq/modelearth-notebook.git"
# TARGET_REPO = "datascape/RealityStream2025"
TARGET_REPO = "Abivishaq/modelearth-notebook-results"
NOTEBOOK_PATH = "notebook.ipynb"



# Get the GitHub token from Secret Manager
def get_github_token():
    # key = os.environ.get('GITHUB_KEY_MODELEARTH', None)
    # if key:
    #     return key
    # else:
    #     raise ValueError("GITHUB_KEY_MODELEARTH environment variable not set")
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{os.environ.get('GOOGLE_CLOUD_PROJECT')}/secrets/github-token/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


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

@app.route('/')
def home():
    return render_template('page_xy.html')

@app.route('/run-notebook', methods=['POST'])
def run_notebook():
    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone the source repository
            repo = git.Repo.clone_from(SOURCE_REPO_URL, temp_dir)
            reports_dir = os.path.join(temp_dir, 'reports')
            os.makedirs(reports_dir)
            
            # Path to the notebook in the cloned repo
            notebook_file = os.path.join(temp_dir, NOTEBOOK_PATH)
            
            # parameters for the notebook
            parameters = request.get_json()
            if not parameters:
                parameters = {}
            # Execute the notebook
            output_path = os.path.join(reports_dir, 'output.ipynb')
            pm.execute_notebook(
                notebook_file,
                output_path,
                parameters={"reports_dir":reports_dir, "parameters": parameters}
            )
            
            # Read the executed notebook
            with open(output_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)
            
            # Convert to HTML for display
            html_exporter = HTMLExporter()
            html_data, resources = html_exporter.from_notebook_node(nb)

            # Upload reports to GitHub
            github_token = get_github_token()
            date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            upload_success = upload_reports_to_github(
                TARGET_REPO,
                github_token,
                Path(reports_dir),
                branch='main',
                commit_message='Reports from Run Models colab - {}'.format(date_str)
            )
            if not upload_success:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to upload reports to GitHub'
                }), 500
            # print("Reports uploaded successfully to GitHub")
            
            # The notebook execution will trigger the upload_reports_to_github function
            # which is defined in the notebook itself
            
            return jsonify({
                'status': 'success',
                'message': 'Notebook executed successfully'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook from GitHub to update when the repo changes"""
    try:
        payload = request.json
        if 'ref' in payload and payload['ref'] == 'refs/heads/main':
            # Pull the latest changes
            subprocess.run(["git", "pull"], cwd="/app")
            return jsonify({'status': 'success'})
        return jsonify({'status': 'no action'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)