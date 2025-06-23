# You can skip this step. It's not yet working.
# Have Loren associate your email to secretmanager if you are testing.
# So far, the secretmanager might only work within cloud/run.
# https://model.earth/localsite/start/steps/github-token

from google.colab import auth
# auth.authenticate_user()

!pip install google-cloud-secret-manager
from google.cloud import secretmanager
import os
project_id = "207223955365" # modelearth-run-models-1
secret_name = "github-token-run-models-1"

auth.authenticate_user(clear_output=True, project_id=project_id)

def get_shared_secret(project_id, secret_name):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    print(name)
    return response.payload.data.decode("UTF-8")

# Usage
try:
    GITHUB_TOKEN = get_shared_secret("modelearth-run-models-1", "github-token-run-models-1")
    print(GITHUB_TOKEN)
except Exception as e:
    print("Please ensure you have access to the shared secret")