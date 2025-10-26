# Bible Study Generator (bs-gen)

Transform sermon transcripts into comprehensive Bible study guides using AI.

## Overview

This web application uses Anthropic Claude AI (or OpenAI GPT) to generate structured, theologically sound Bible study guides from sermon transcripts stored in Google Drive. The generated guides are automatically saved back to your Google Drive.

## Features

- **Google OAuth Authentication** - Secure login with your Google account
- **Google Drive Integration** - Select sermon transcripts directly from your Drive
- **Multiple AI Models** - Choose between Claude Sonnet 4.5, Claude Haiku 3.5, or GPT-4o
- **Comprehensive Study Guides** - Each session includes:
  - Session title and key scripture passage
  - Summary/overview (350-500 words)
  - Discussion questions (5-7, progressively deeper)
  - Personal reflection prompts
  - Application challenges
  - Leader notes with prayers, facilitation tips, and resources
- **Auto-save to Drive** - Generated guides automatically saved to your Bible_Studies folder
- **Target Audience Support** - Customize for New Christians, Mature Believers, or Mixed groups

## Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **AI**: Anthropic Claude API, OpenAI API
- **Cloud**: Google Cloud Run
- **Storage**: Google Drive
- **Auth**: Google OAuth 2.0

---

## Prerequisites

1. **Google Cloud Platform Account** - [Sign up here](https://cloud.google.com/)
2. **Anthropic API Key** - [Get one here](https://console.anthropic.com/)
3. **OpenAI API Key** (optional) - [Get one here](https://platform.openai.com/)
4. **Domain** - bs-gen.1421.me (or your custom domain)

---

## Setup Instructions

### Part 1: Google Cloud Project Setup

#### 1.1 Create a New GCP Project

```bash
# Install gcloud CLI if you haven't already
# https://cloud.google.com/sdk/docs/install

# Login to Google Cloud
gcloud auth login

# Create a new project
gcloud projects create bs-gen-project --name="Bible Study Generator"

# Set as active project
gcloud config set project bs-gen-project

# Enable required APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    drive.googleapis.com
```

#### 1.2 Create OAuth 2.0 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (`bs-gen-project`)
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Configure Consent Screen**:
   - User Type: **External**
   - App name: **Bible Study Generator**
   - User support email: `john@1421.me`
   - Developer contact: `john@1421.me`
   - Add scopes:
     - `.../auth/userinfo.email`
     - `.../auth/userinfo.profile`
     - `.../auth/drive`
   - Add test users: `john@1421.me`
   - Save and continue

5. Go back to **Credentials** tab
6. Click **Create Credentials** → **OAuth 2.0 Client ID**
7. Application type: **Web application**
8. Name: **Bible Study Generator**
9. Authorized redirect URIs:
   - `https://bs-gen.1421.me/auth/callback`
   - `http://localhost:8080/auth/callback` (for local testing)
10. Click **Create**
11. **Save the Client ID and Client Secret** - you'll need these!

### Part 2: Local Development Setup

#### 2.1 Clone and Setup

```bash
# Clone the repository
cd ~/code_projects/bs-gen

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2.2 Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# OpenAI API (optional)
OPENAI_API_KEY=sk-xxxxx

# Google OAuth (from step 1.2)
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx

# Google Drive
GOOGLE_DRIVE_FOLDER_ID=1HGQyFgOlIcQZ-RqQKUGq_URmXQeY6TMz

# Authentication
ALLOWED_EMAIL=john@1421.me

# Session Security (generate a random key)
SESSION_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Application
APP_URL=http://localhost:8080
ENVIRONMENT=development
```

#### 2.3 Run Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run the app
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Open browser to http://localhost:8080
```

### Part 3: Deploy to Google Cloud Run

#### 3.1 Build and Deploy

```bash
# Set your project ID
export PROJECT_ID=bs-gen-project
export REGION=us-central1
export SERVICE_NAME=bs-gen

# Submit build to Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --timeout 900 \
    --max-instances 10 \
    --set-env-vars ENVIRONMENT=production
```

#### 3.2 Set Environment Variables in Cloud Run

```bash
# Set all required environment variables
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --set-env-vars "ANTHROPIC_API_KEY=your_key_here" \
    --set-env-vars "OPENAI_API_KEY=your_key_here" \
    --set-env-vars "GOOGLE_CLIENT_ID=your_client_id" \
    --set-env-vars "GOOGLE_CLIENT_SECRET=your_client_secret" \
    --set-env-vars "GOOGLE_DRIVE_FOLDER_ID=1HGQyFgOlIcQZ-RqQKUGq_URmXQeY6TMz" \
    --set-env-vars "ALLOWED_EMAIL=john@1421.me" \
    --set-env-vars "SESSION_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
    --set-env-vars "APP_URL=https://bs-gen.1421.me"
```

Or set them via the Cloud Console:
1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on your service (`bs-gen`)
3. Click **Edit & Deploy New Revision**
4. Go to **Variables & Secrets** tab
5. Add each environment variable
6. Click **Deploy**

#### 3.3 Configure Custom Domain

```bash
# Map your custom domain
gcloud run domain-mappings create \
    --service $SERVICE_NAME \
    --domain bs-gen.1421.me \
    --region $REGION

# Follow the instructions to verify domain ownership and update DNS records
```

**DNS Configuration:**
- Add the DNS records provided by Cloud Run to your domain registrar
- It may take a few minutes to several hours for DNS to propagate

#### 3.4 Update OAuth Redirect URIs

1. Go back to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Credentials**
2. Edit your OAuth 2.0 Client ID
3. Update **Authorized redirect URIs** to include:
   - `https://bs-gen.1421.me/auth/callback`
4. Save changes

### Part 4: Continuous Deployment (Optional)

#### 4.1 Connect GitHub Repository

```bash
# Push to GitHub
git remote add origin https://github.com/yourusername/bs-gen.git
git push -u origin main
```

#### 4.2 Setup Cloud Build Trigger

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click **Create Trigger**
3. Name: `Deploy bs-gen`
4. Event: **Push to branch**
5. Source: Connect your GitHub repository
6. Branch: `^main$`
7. Configuration: **Cloud Build configuration file**
8. Location: `/cloudbuild.yaml` (create this file - see below)
9. Click **Create**

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/bs-gen', '.']

  # Push the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/bs-gen']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'bs-gen'
      - '--image'
      - 'gcr.io/$PROJECT_ID/bs-gen'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'

images:
  - 'gcr.io/$PROJECT_ID/bs-gen'
```

Now every push to `main` will automatically deploy to Cloud Run!

---

## Usage

### 1. Login

1. Navigate to `https://bs-gen.1421.me`
2. Click **Sign in with Google**
3. Authenticate with your Google account (`john@1421.me`)

### 2. Upload Sermon Transcripts

Upload your sermon transcripts to Google Drive as `.txt` files. Name them with a prefix for proper ordering:

```
## 01 - Introduction to Faith.txt
## 02 - Walking with God.txt
## 03 - Prayer and Worship.txt
```

### 3. Generate Study Guide

1. Enter **Series Title** (e.g., "Walking in Faith")
2. Select **Target Audience** (New Christians, Mature Believers, or Mixed)
3. Choose **AI Model**:
   - **Claude Sonnet 4.5** - Best quality (recommended for production)
   - **Claude 3.5 Haiku** - Faster, lower cost (good for testing)
   - **GPT-4o** - Alternative option
4. Click **Select .txt files from Google Drive**
5. Select up to 8 sermon transcript files
6. Click **Generate Study Guide**
7. Wait 5-15 minutes (keep page open)
8. Study guide will be automatically saved to your Google Drive `Bible_Studies` folder

### 4. Access Generated Guide

- Click **Open in Google Drive** from the success modal
- Or find it in your Drive at: `Bible_Studies/{Series Title}_Study_Guide.md`

---

## Cost Estimates

### AI API Costs (per study guide with 6 sermons)

| Model | Input | Output | Total per Guide |
|-------|-------|--------|-----------------|
| Claude Sonnet 4.5 | $0.07 | $0.36 | **$0.43** |
| Claude 3.5 Haiku | $0.02 | $0.10 | **$0.12** |
| GPT-4o | $0.06 | $0.24 | **$0.30** |

### Google Cloud Run Costs

- **Free tier**: 2 million requests/month, 360,000 GB-seconds/month
- **Typical usage**: ~$0-5/month for personal use
- **With moderate usage** (10 guides/month): ~$5-10/month total

---

## Troubleshooting

### OAuth Error: "redirect_uri_mismatch"

**Solution**: Ensure your OAuth redirect URI exactly matches your APP_URL:
- Local: `http://localhost:8080/auth/callback`
- Production: `https://bs-gen.1421.me/auth/callback`

### Error: "Access denied. Only john@1421.me is authorized"

**Solution**: Ensure you're logging in with the correct Google account specified in `ALLOWED_EMAIL`.

### Generation fails midway

**Solution**:
- Check API key is valid and has sufficient credits
- Increase Cloud Run timeout (currently 15 minutes)
- Try a smaller batch of sermons
- Partial results may be saved with "_PARTIAL_ERROR" suffix

### No .txt files showing in picker

**Solution**:
- Ensure sermon transcripts are uploaded to Google Drive
- Verify files have `.txt` extension
- Check OAuth has granted Drive access

---

## Project Structure

```
bs-gen/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app and routes
│   ├── auth.py              # Google OAuth logic
│   ├── drive.py             # Google Drive operations
│   ├── generator.py         # AI study guide generation
│   └── templates/
│       ├── login.html       # Login page
│       └── index.html       # Main app interface
├── static/
│   ├── css/
│   │   └── style.css        # Styling
│   └── js/
│       └── app.js           # Frontend logic
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

---

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest
```

### Code Style

```bash
# Install formatters
pip install black isort

# Format code
black .
isort .
```

---

## Security Notes

- OAuth credentials are stored in Cloud Run environment variables (not in code)
- Session cookies are signed with SECRET_KEY and expire after 7 days
- Only authorized email (`john@1421.me`) can access the application
- All API calls use HTTPS
- Drive access is scoped to authenticated user only

---

## Support

For issues or questions:
- Check this README first
- Review error messages in Cloud Run logs: `gcloud run logs read bs-gen --region=us-central1`
- Contact: john@1421.me

---

## License

Private project - All rights reserved.

---

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Anthropic Claude](https://www.anthropic.com/)
- Deployed on [Google Cloud Run](https://cloud.google.com/run)
