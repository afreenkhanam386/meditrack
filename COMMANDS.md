# MediTrack — Full Deployment Commands
# EC2 Instance : afreen-crud-storage-2026
# EC2 Public IP: 16.112.118.42
# S3 Bucket    : portfolio-server
# App URL      : http://16.112.118.42

# ══════════════════════════════════════
# STEP 1 — LOCAL MACHINE (before EC2)
# ══════════════════════════════════════

# 1a. Init git repo locally
git init
git add .
git commit -m "Initial MediTrack project"

# 1b. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/meditrack.git
git branch -M main
git push -u origin main


# ══════════════════════════════════════
# STEP 2 — RDS DATABASE SETUP
# ══════════════════════════════════════

# Connect to your RDS instance from your local machine or EC2
mysql -h YOUR_RDS_ENDPOINT -u admin -p

# Once inside MySQL, run:
source init_db.sql
# OR paste the SQL manually from init_db.sql


# ══════════════════════════════════════
# STEP 3 — EC2 INSTANCE SETUP
# ══════════════════════════════════════

# 3a. SSH into your EC2
ssh -i your-key.pem ubuntu@16.112.118.42

# 3b. Update packages and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git nginx -y

# 3c. Clone your GitHub repo
git clone https://github.com/YOUR_USERNAME/meditrack.git
cd meditrack

# 3d. Create virtual environment and install packages
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3e. Create your .env file (NEVER commit this)
nano .env
# Add the following lines:
#   DB_HOST=your-rds-endpoint.amazonaws.com
#   DB_USER=admin
#   DB_PASSWORD=yourpassword
#   DB_NAME=meditrack


# ══════════════════════════════════════
# STEP 4 — TEST FLASK DEV SERVER
# ══════════════════════════════════════

source venv/bin/activate
flask run --host=0.0.0.0 --port=5000
# Visit: http://16.112.118.42:5000  (open port 5000 in security group temporarily)
# Press Ctrl+C when done testing


# ══════════════════════════════════════
# STEP 5 — GUNICORN TEST
# ══════════════════════════════════════

source venv/bin/activate
gunicorn --workers 3 --bind unix:/home/ubuntu/meditrack/meditrack.sock app:app
# Check that meditrack.sock file was created:
ls -la /home/ubuntu/meditrack/meditrack.sock
# Press Ctrl+C when confirmed


# ══════════════════════════════════════
# STEP 6 — SYSTEMD SERVICE
# ══════════════════════════════════════

# 6a. Copy the service file
sudo cp meditrack.service /etc/systemd/system/meditrack.service

# 6b. Enable and start
sudo systemctl daemon-reload
sudo systemctl start meditrack
sudo systemctl enable meditrack

# 6c. Check it's running
sudo systemctl status meditrack

# 6d. View live logs
journalctl -u meditrack -f


# ══════════════════════════════════════
# STEP 7 — NGINX REVERSE PROXY
# ══════════════════════════════════════

# 7a. Check nothing is already on port 80
sudo ss -tlnp | grep :80

# 7b. Copy nginx config
sudo cp meditrack.nginx.conf /etc/nginx/sites-available/meditrack

# 7c. Enable the site
sudo ln -s /etc/nginx/sites-available/meditrack /etc/nginx/sites-enabled/

# 7d. Remove default site to avoid conflict
sudo rm -f /etc/nginx/sites-enabled/default

# 7e. Test config syntax
sudo nginx -t

# 7f. Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx


# ══════════════════════════════════════
# STEP 8 — VERIFY
# ══════════════════════════════════════

# App should now be live at:
# http://16.112.118.42   (no port number)

# Check gunicorn service status
sudo systemctl status meditrack

# Check nginx status
sudo systemctl status nginx

# Nginx error log
sudo tail -f /var/log/nginx/meditrack_error.log

# App log
journalctl -u meditrack -f


# ══════════════════════════════════════
# STEP 9 — REBOOT TEST
# ══════════════════════════════════════

sudo reboot
# Wait ~30 seconds, then visit http://YOUR_EC2_PUBLIC_IP again
# App must come back automatically — no manual steps


# ══════════════════════════════════════
# USEFUL DEBUG COMMANDS
# ══════════════════════════════════════

# Restart app after code changes:
sudo systemctl restart meditrack

# Pull latest code from GitHub:
cd /home/ubuntu/meditrack
git pull origin main
sudo systemctl restart meditrack

# Check socket file exists:
ls -la /home/ubuntu/meditrack/meditrack.sock

# Check port 80 listener:
sudo ss -tlnp | grep :80

# Full nginx error log:
sudo cat /var/log/nginx/meditrack_error.log

# Gunicorn process check:
ps aux | grep gunicorn


# ══════════════════════════════════════
# STEP 10 — S3 BUCKET (portfolio-server)
# ══════════════════════════════════════

# Install AWS CLI on EC2 (if not already installed)
sudo apt install awscli -y

# Configure AWS credentials (run once)
aws configure
# Enter: Access Key, Secret Key, region (e.g. ap-south-1), output format: json

# Upload a file to your S3 bucket
aws s3 cp /home/ubuntu/meditrack/app.py s3://portfolio-server/meditrack/app.py

# Upload entire project folder to S3 (backup)
aws s3 sync /home/ubuntu/meditrack/ s3://portfolio-server/meditrack/ --exclude "venv/*" --exclude ".env"

# List files in your bucket
aws s3 ls s3://portfolio-server/

# Download from S3 back to EC2 (restore)
aws s3 sync s3://portfolio-server/meditrack/ /home/ubuntu/meditrack/

# Make a file publicly accessible (optional)
aws s3 cp /home/ubuntu/meditrack/init_db.sql s3://portfolio-server/meditrack/init_db.sql --acl public-read
