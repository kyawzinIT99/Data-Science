# Modal Deployment Guide

This document explains how to deploy the heavy data analysis tasks (forecasting, segmentation, agent swarm) to Modal for distributed execution.

## 1. Prerequisites

1.  **Modal Account**: Create an account at [modal.com](https://modal.com).
2.  **Install Modal**:
    ```bash
    pip install modal
    ```
3.  **Setup Modal**:
    ```bash
    modal setup
    ```

## 2. Security Setup (Secrets)

To run the agent analysis, Modal needs access to your OpenAI API key. We use Modal Secrets for this.

1.  Go to the [Modal Secrets Dashboard](https://modal.com/secrets).
2.  Create a new secret named `openai-api-key`.
3.  Add an environment variable:
    - Key: `OPENAI_API_KEY`
    - Value: `your-openai-api-key-here`

## 3. Deployment

Once the secret is created, deploy the app:

```bash
cd backend
modal deploy modal_app.py
```

This will build the container image and deploy the remote functions.

## 4. Enable in the App

Update your `backend/.env` file:

```env
MODAL_ENABLED=true
MODAL_APP_NAME=ai-data-analysis
```

Restart your backend server. The app will now automatically offload heavy tasks to Modal using **persistent volumes** for maximum performance and reliability with large datasets.

## How it Works (Persistence)

1.  **Sync Layer**: The app checks if your data file (e.g., a 100MB CSV) already exists on the Modal Volume.
2.  **Streaming Upload**: If not, it streams the file to the persistent cloud volume once.
3.  **Cloud Execution**: Future analysis runs (forecasting, segmentation) read directly from that persistent volume, making them significantly faster and more stable than traditional byte-transfer methods.

## Troubleshooting

-   **Check Logs**: Run `modal app logs ai-data-analysis`.
-   **Clear Storage**: If you need to clear the cloud storage, use `modal volume delete data-analysis-storage`.
-   **Fallback**: If Modal fails or is disabled, the app will automatically fall back to local processing (using your local machine's resources).
