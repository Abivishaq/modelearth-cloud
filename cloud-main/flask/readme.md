Flask Hosting and Jupyter Notebook Setup on Google
Cloud
Prepared by: Prem Chand Reddy Gopidinne

1. Google Cloud VM Setup
• Log in to Google Cloud Console.
• Navigate to: Compute Engine → VM Instances → Create Instance.
Instance Settings:
Setting Value
Name flask-server
Machine type e2-micro (Free Tier eligible)
Boot disk Ubuntu 22.04 LTS
Firewall Check Allow HTTP and Allow HTTPS
Click Create to launch the instance.

2. SSH into VM Instance
In the Google Cloud Console → VM Instances → Click SSH on your instance.
This opens the Linux terminal of your VM.

3. Install Essential Software
In the SSH terminal:
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y

4. Set Up Flask Application

# Create a project directory
mkdir flask_app
cd flask_app
# Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate
# Install Flask and Gunicorn
pip install flask gunicorn
# Create a basic Flask app
nano app.py

Paste inside app.py:
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
return "Flask app is running on Google Cloud!"
if __name__ == "__main__":
app.run(host="0.0.0.0", port=8080)

Save and close (Ctrl + O, Enter, Ctrl + X).

5. Run Flask App
source venv/bin/activate
python app.py

Flask server will start on port 8080.

6. Open Port 8080 (Firewall Rule)
Go to VPC Network → Firewall Rules → Create Firewall Rule.
Set:
Field Value
Name allow-8080
Direction Ingress
Action Allow
Source 0.0.0.0/0
Protocols and ports tcp:8080
Save the rule.
Now your Flask app is accessible at:
http://<your-external-ip>:8080

7. Install Jupyter Notebook
Still inside the VM terminal:
source ~/flask_app/venv/bin/activate
pip install jupyter

8. Launch Jupyter Notebook
Start Jupyter server:
jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root

A token will be generated in the terminal output.

9. Open Port 8888 (Firewall Rule)
Create another firewall rule:
Field Value
Name allow-8888
Direction Ingress
Action Allow
Source 0.0.0.0/0
Protocols and ports tcp:8888
Save.
Now Jupyter Notebook is accessible at:
http://<your-external-ip>:8888
Login using the token.

10. Clone GitHub Repository
cd ~/flask_app
git clone https://github.com/ModelEarth/realitystream.git

11. Open and Run .ipynb File
In Jupyter Notebook:
Navigate to: realitystream/models/
Open Run-Models-bkup.ipynb.
Run the notebook cells.
This runs the backup model notebook on the cloud server!