# Deployment Checklist for Bible Study Generator

## Pre-Deployment Setup

### ☐ 1. Google Cloud Project
- [ ] Create GCP project: `bs-gen-project`
- [ ] Enable Cloud Build API
- [ ] Enable Cloud Run API
- [ ] Enable Google Drive API

### ☐ 2. OAuth 2.0 Credentials
- [ ] Configure OAuth consent screen
- [ ] Add test user: john@1421.me
- [ ] Create OAuth 2.0 Client ID
- [ ] Add redirect URI: `https://bs-gen.1421.me/auth/callback`
- [ ] Save Client ID and Client Secret

### ☐ 3. API Keys
- [ ] Get Anthropic API key from console.anthropic.com
- [ ] Get OpenAI API key from platform.openai.com (optional)
- [ ] Test API keys locally

### ☐ 4. Google Drive Setup
- [ ] Verify Bible_Studies folder exists: `1HGQyFgOlIcQZ-RqQKUGq_URmXQeY6TMz`
- [ ] Upload test sermon transcripts (.txt files)
- [ ] Name files with "## 01, 02, 03..." prefix for sorting

---

## Deployment Steps

### ☐ 5. Push to GitHub
```bash
# Set up GitHub remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/bs-gen.git
git push -u origin main
```

### ☐ 6. Initial Cloud Run Deployment
```bash
# Set project
gcloud config set project bs-gen-project

# Build and push image
gcloud builds submit --tag gcr.io/bs-gen-project/bs-gen

# Deploy to Cloud Run
gcloud run deploy bs-gen \
    --image gcr.io/bs-gen-project/bs-gen \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --timeout 900 \
    --max-instances 10
```

### ☐ 7. Set Environment Variables in Cloud Run
Via Console (easier):
1. Go to console.cloud.google.com/run
2. Click service: `bs-gen`
3. Click "Edit & Deploy New Revision"
4. Go to "Variables & Secrets" tab
5. Add all variables from `.env.example`:
   - ANTHROPIC_API_KEY
   - OPENAI_API_KEY
   - GOOGLE_CLIENT_ID
   - GOOGLE_CLIENT_SECRET
   - GOOGLE_DRIVE_FOLDER_ID
   - ALLOWED_EMAIL
   - SESSION_SECRET_KEY (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
   - APP_URL=https://bs-gen.1421.me
   - ENVIRONMENT=production
6. Click "Deploy"

### ☐ 8. Configure Custom Domain
```bash
gcloud run domain-mappings create \
    --service bs-gen \
    --domain bs-gen.1421.me \
    --region us-central1
```

Then update DNS records at your domain registrar with the records provided by Cloud Run.

### ☐ 9. Setup Continuous Deployment (Optional)
1. Go to console.cloud.google.com/cloud-build/triggers
2. Click "Create Trigger"
3. Name: Deploy bs-gen
4. Event: Push to branch
5. Branch: `^main$`
6. Configuration: Cloud Build configuration file (cloudbuild.yaml)
7. Click "Create"

---

## Post-Deployment Testing

### ☐ 10. Test Authentication
- [ ] Visit https://bs-gen.1421.me
- [ ] Click "Sign in with Google"
- [ ] Verify you can log in with john@1421.me
- [ ] Verify other emails are rejected

### ☐ 11. Test File Selection
- [ ] Click "Select .txt files from Google Drive"
- [ ] Verify sermon transcript files appear
- [ ] Select 2-3 test files
- [ ] Verify files display in "Selected Files" section

### ☐ 12. Test Study Guide Generation
- [ ] Fill in Series Title: "Test Series"
- [ ] Select Target Audience: "Mixed"
- [ ] Select Model: "Claude 3.5 Haiku" (cheaper for testing)
- [ ] Click "Generate Study Guide"
- [ ] Wait for completion (should take 2-5 minutes for 3 sermons)
- [ ] Verify success modal appears
- [ ] Click "Open in Google Drive"
- [ ] Verify file exists in Bible_Studies folder
- [ ] Review generated content for quality

### ☐ 13. Test Production Model
- [ ] Repeat test with "Claude Sonnet 4.5"
- [ ] Compare quality to Haiku output
- [ ] Verify theological soundness and formatting

---

## Monitoring & Maintenance

### ☐ 14. Setup Monitoring
- [ ] Check Cloud Run logs: `gcloud run logs read bs-gen --region=us-central1`
- [ ] Monitor API usage on Anthropic Console
- [ ] Monitor Cloud Run costs in GCP Billing

### ☐ 15. Regular Checks
- [ ] Weekly: Check API credit balance
- [ ] Monthly: Review GCP billing
- [ ] As needed: Update environment variables for new features

---

## Troubleshooting Commands

```bash
# View logs
gcloud run logs read bs-gen --region=us-central1 --limit=50

# Check service status
gcloud run services describe bs-gen --region=us-central1

# Update environment variable
gcloud run services update bs-gen \
    --region us-central1 \
    --set-env-vars "KEY=value"

# Redeploy (trigger new deployment)
gcloud run deploy bs-gen \
    --image gcr.io/bs-gen-project/bs-gen \
    --region us-central1

# Check domain mapping
gcloud run domain-mappings describe bs-gen.1421.me --region=us-central1
```

---

## Quick Reference

**Service URL**: https://bs-gen.1421.me
**GCP Project**: bs-gen-project
**Service Name**: bs-gen
**Region**: us-central1
**Drive Folder ID**: 1HGQyFgOlIcQZ-RqQKUGq_URmXQeY6TMz
**Authorized Email**: john@1421.me

---

## Success Criteria

✅ Application accessible at https://bs-gen.1421.me
✅ OAuth login works for john@1421.me
✅ Can select sermon files from Google Drive
✅ Study guides generate successfully
✅ Output saves to Google Drive Bible_Studies folder
✅ No console errors or failed requests
✅ Generation completes within 15 minutes

---

Ready to deploy! 🚀
