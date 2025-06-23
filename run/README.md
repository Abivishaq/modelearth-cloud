# Google Cloud Run with CoLab+GitHub

Our guide provides commands for Google Cloud Run service setup with Flask to execute a Jupyter notebook from a GitHub repository.

- **Cmds for Google Cloud** - Creates a new project ID and enables necessary APIs
- **GitHub integration** - Setting up access tokens and webhooks for repository updates
- **Flask application** - Complete code for a web service with a button to trigger notebook execution
- **Security setup** - Storing GitHub tokens securely in Secret Manager
- **Notebook modification** - Adding the GitHub upload functionality to your notebook
- **Deployment** - Commands to deploy the service to Cloud Run
- **Automatic updates** - Setting up webhooks to update when your GitHub repo changes
- **Service account permissions** - Configuring proper access for secure GitHub interactions

The application creates a simple web interface with a button that, when pressed, will:

- Clone your GitHub repository (Later we'll sync when the repo changes instead.)
- Execute the specified notebook
- Push the resulting files to your target repository

The guide also includes options for setting up scheduled executions if you want the notebook to run automatically at specific intervals.

[Our initial code was vibe-promoted with](https://claude.ai/public/artifacts/a3d76132-45f4-4155-aef8-4870adf64f20): Create commands for creating a Google Cloud Run containing Flask and use the resulting project ID to create a website that executes a .ipynb file that resides in a Github repo. Whenever the repo is updated, update the website. The .ipynb file will be triggered by a button on a page and it will push files to another GitHub repo. Set permissions in Google to allow the push from the Google server to occur. Here's the function we use to push the files. (I provided the upload_reports_to_github function from the last step in our Run Models colab.)


<!--
https://claude.ai/public/artifacts/a3d76132-45f4-4155-aef8-4870adf64f20

Promoted with: Create commands for creating a Google Cloud Run containing Flask and use the resulting project ID to create a website that executes a .ipynb file that resides in a Github repo. Whenever the repo is updated, update the website. The .ipynb file will be triggered by a button on a page and it will push files to another GitHub repo. Set permissions in Google to allow the push from the Google server to occur. Here's the function we use to push the files. (I provided the upload_reports_to_github function from the last step in our Run Models colab.)
-->

## Prerequisites

1. Google Cloud account
2. GitHub account
3. Two GitHub repositories:
   - Source repo: Contains the .ipynb notebook to execute
   - Target repo: Where the generated files will be pushed



## Part 1: Set Up Google Cloud Project

TO DO: Let's add a form here where users can enter their Google ProjectID, GitHub repo+token to populate in the commands.
Let's also creat deployment cmds for [Thundercompute.com](https://www.thundercompute.com)


Initialize gcloud - Open a terminal in the folder where your site will reside. (For example: cloud/run/site)
Optionally, skip diagnostics during init.

    gcloud init --skip-diagnostics


[Install Google Cloud SDK](https://cloud.google.com/sdk/docs/install) if not already installed

If you're returning, choose #3:
3. Switch to and re-initialize existing configuration: [default]
Choose which gmail account (if you have more than 1) - Figure out a cmd to choose all defaults.
Pick the cloud project to use.

(1) Re-initialize with new setting.
(2) Create a new configuration
(3) Switch to and re-initialize existing configuration

If you add a new configuration, name the configuration different from the project.

<!-- modelearth-config -->

You'll be prompted to create a project and it will be set as active.
Here are the equivalent commands;

1. Create a new project - change the name as desired
2. Set the project as active

```
gcloud projects create your-project-id --name="modelearth-run-models"
gcloud config set project your-project-id
```

You'll likely be advised to update Google Cloud CLI components by running:

    gcloud components update


**If this is your initial setup, get your billing account ID**

    gcloud billing accounts list


For the following, you'll be promted to install gcloud Alpha Commands

gcloud alpha billing accounts describe 000000-000000-000000

The above will fail initially, so
associate a billing account to your new "modelearth-run-models" project

    gcloud billing projects link modelearth-run-models --billing-account=BILLING_ACCOUNT_ID

 TODO: If you don't have a billing account yet, fork this repo and document commands to add it here. Send a PR.

Enable required APIs (if first time)

    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable cloudscheduler.googleapis.com
    gcloud services enable secretmanager.googleapis.com



## Part 2: Create GitHub Access Token

Check if you already added the token in GCloud

    gcloud secrets describe github-token

1. In your [GitHub account](https://github.com), navigate to Settings (upper right menu)
2. Navigate to Developer settings (lower left) > Personal access tokens. Choose Fine-grained tokens.
3. Create a new Fine-grained token so you can limit to one repo.
4. Set the permissions to:  
Contents: Read and write  
Deployments: Read and write  
Metadata: Read-only (gets set automatically)


## Part 3: Store GitHub Token in Secret Manager

Commands for [Storing a GitHub Token in Secret Manager](../../localsite/start/steps/github-token) to share

We named the token: github-token-run-models-1

<!-- Since this is account-wide, let's call it github-token-modelearth-run-models 
TO DO: This will need to get sent into Run-Models-bkup.ipynb as a variable.
-->

```bash
# Create a secret for the GitHub token
echo -n "your-github-token" | gcloud secrets create github-token --data-file=-

# Grant the Cloud Run service account access to the secret
gcloud secrets add-iam-policy-binding github-token \
    --member="serviceAccount:your-project-id@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```


## Part 4: Create Flask Application

[Review this flask info from Prem](https://github.com/ModelEarth/cloud/tree/main/cloud-main/flask), and anything useful as you 
Create a directory for your project and set up the following files:

### `Dockerfile`


```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8080

# Run the application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
```

### `requirements.txt`

See local file.


### `app.py`

See local file.



### `page.html`

Page.html contains the button that will run our .ipynb file.

[View page.html](page.html)

## Part 5: Create Modified Notebook 

Create a modified version of your notebook that incorporates the upload function:

TODO: FIx this python that Claude AI created:

See notebook.ipynb


**Execute the upload at the end of the notebook**

TARGET_REPO = "username/target-repo"  # Replace with your target repository
upload_reports_to_github(TARGET_REPO, GITHUB_TOKEN, branch='main', commit_message='Pushed report files from Cloud Run')


## Part 6: Deploy to Cloud Run

```bash
# Build and deploy the application
gcloud builds submit --tag gcr.io/your-project-id/notebook-executor

gcloud run deploy notebook-executor \
  --image gcr.io/your-project-id/notebook-executor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=your-project-id"
```

## Part 7: Set Up GitHub Webhook

1. Go to your source GitHub repository settings
2. Navigate to Webhooks
3. Add a new webhook with the following settings:
   - Payload URL: `https://your-cloud-run-url.run.app/webhook`
   - Content type: `application/json`
   - Secret: (Optional, but recommended for security)
   - Events: Select "Just the push event"

## Part 8: Set Up Service Account Permissions

```bash
# Create a service account for the Cloud Run service
gcloud iam service-accounts create notebook-executor-sa \
  --display-name="Notebook Executor Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:notebook-executor-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Update the Cloud Run service to use this service account
gcloud run services update notebook-executor \
  --service-account="notebook-executor-sa@your-project-id.iam.gserviceaccount.com" \
  --region us-central1
```

## Part 9: (Optional) Set Up Scheduled Execution

If you want to run the notebook on a schedule, you can use Cloud Scheduler:

```bash
# Create a scheduler job
gcloud scheduler jobs create http notebook-executor-scheduler \
  --schedule="0 */6 * * *" \
  --uri="https://your-cloud-run-url.run.app/run-notebook" \
  --http-method=POST \
  --time-zone="America/New_York"
```

## Testing

1. Visit your Cloud Run URL (`https://your-cloud-run-url.run.app`)
2. Click the "Run Notebook" button
3. The notebook will be executed and results will be pushed to the target GitHub repository

## Troubleshooting

- Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=notebook-executor" --limit 50`
- Ensure all API permissions are correctly set
- Verify that the GitHub token has the necessary permissions
- Check the notebook execution logs in Cloud Run
