# Sentinel ADK Deployment Guide

This guide walks you through deploying the Sentinel ADK application to Google Cloud Run using the `agents-cli`.

## Prerequisites

1. **Google Cloud Platform (GCP) Project**: Ensure you have an active GCP project with billing enabled.
2. **Google Cloud CLI (`gcloud`)**: Installed and initialized.
3. **`agents-cli`**: Installed locally.

## 1. Setup GCP Credentials

First, authenticate with Google Cloud using your CLI:

```bash
gcloud auth login
gcloud config set project <YOUR_PROJECT_ID>
gcloud auth application-default login
```

Ensure the required APIs are enabled for your project:
```bash
gcloud services enable run.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com
```

## 2. Configure Secrets in Secret Manager

Since we do not deploy our `.env` file, we must manage API keys securely using GCP Secret Manager.

Create the secrets for your environment variables:
```bash
gcloud secrets create GEMINI_API_KEY --replication-policy="automatic"
gcloud secrets create GEMINI_API_KEY_DEV --replication-policy="automatic"
gcloud secrets create GEMINI_API_KEY_PROD --replication-policy="automatic"
gcloud secrets create ALPACA_KEY --replication-policy="automatic"
gcloud secrets create ALPACA_SECRET --replication-policy="automatic"
```

Add the actual secret values:
```bash
echo -n "your-gemini-key" | gcloud secrets versions add GEMINI_API_KEY --data-file=-
echo -n "your-dev-key" | gcloud secrets versions add GEMINI_API_KEY_DEV --data-file=-
echo -n "your-prod-key" | gcloud secrets versions add GEMINI_API_KEY_PROD --data-file=-
echo -n "your-alpaca-key" | gcloud secrets versions add ALPACA_KEY --data-file=-
echo -n "your-alpaca-secret" | gcloud secrets versions add ALPACA_SECRET --data-file=-
```

## 3. Verify Deployment Configuration

We use `deployment_config.yaml` to define the Cloud Run settings.
It should look like this:

```yaml
service_name: sentinel-adk
region: us-central1
memory: 2Gi
env_vars:
  - GEMINI_API_KEY
  - GEMINI_API_KEY_DEV
  - GEMINI_API_KEY_PROD
  - ALPACA_KEY
  - ALPACA_SECRET
```

## 4. Run a Dry Run

Before deploying for real, run a dry-run to ensure the configuration parses correctly:

```bash
agents-cli deploy --dry-run
```

## 5. Deploy to Cloud Run

Deploy the service to Cloud Run using the CLI. The CLI will automatically package the ADK backend (along with its MCP subprocesses) and deploy it:

```bash
agents-cli deploy
```

## 6. Post-Deployment

1. Once the deployment completes, the CLI will output the Cloud Run Service URL.
2. The deployed container uses the default compute service account. You must grant it permission to read the secrets you just created:
```bash
# Get your default compute service account
SERVICE_ACCOUNT=$(gcloud iam service-accounts list \
  --filter="displayName:Compute Engine default service account" \
  --format="value(email)")

# Grant Secret Accessor role to the project
gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```
3. Visit the URL to verify that the ADK API endpoints and Dev UI are actively running.
