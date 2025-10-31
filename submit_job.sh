#!/bin/bash

# Usage:
# ./submit_job.sh <workspace-name> <resource-group> <subscription-id>

# Check if all arguments are provided
if [ $# -ne 3 ]; then
    echo "❌ Error: Missing required arguments"
    echo "Usage: ./submit_job.sh <workspace-name> <resource-group> <subscription-id>"
    exit 1
fi

# Input variables
WORKSPACE_NAME=$1
RESOURCE_GROUP=$2
SUBSCRIPTION_ID=$3

# Echo inputs
echo "📦 Workspace Name: $WORKSPACE_NAME"
echo "🧾 Resource Group: $RESOURCE_GROUP"
echo "📄 Subscription ID: $SUBSCRIPTION_ID"

# Check .env
if [ ! -f .env ]; then
  echo "❌ .env file not found. Exiting."
  exit 1
fi

# Load environment variables from .env
set -o allexport
source .env
set +o allexport

# Validate required environment variables
required_vars=("AZURE_OPENAI_API_KEY" "AZURE_OPENAI_ENDPOINT" "AZURE_OPENAI_MODEL" "AZURE_OPENAI_API_VERSION")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Error: Missing required environment variables:"
    printf '  - %s\n' "${missing_vars[@]}"
    exit 1
fi

# Check if job.yml exists
if [ ! -f job.yml ]; then
  echo "❌ job.yml not found in the azureml directory. Exiting."
  exit 1
fi

# Create temporary job file with env vars injected
TEMP_JOB_FILE="job_temp.yml"
cp job.yml "$TEMP_JOB_FILE"

echo "🛠️ Injecting environment variables into $TEMP_JOB_FILE"

cat <<EOL >> "$TEMP_JOB_FILE"

environment_variables:
  AZURE_OPENAI_API_KEY: "$AZURE_OPENAI_API_KEY"
  AZURE_OPENAI_ENDPOINT: "$AZURE_OPENAI_ENDPOINT"
  AZURE_OPENAI_MODEL: "$AZURE_OPENAI_MODEL"
  AZURE_OPENAI_API_VERSION: "$AZURE_OPENAI_API_VERSION"
  HUGGINGFACE_TOKEN: "$HUGGINGFACE_TOKEN"
  HUGGINGFACE_MODEL_NAME: "$HUGGINGFACE_MODEL_NAME"
  HUGGINGFACE_MODEL_PATH: "$HUGGINGFACE_MODEL_PATH"
  WANDB_API_KEY: "$WANDB_API_KEY"
EOL

# Submit the job
echo "🚀 Submitting Azure ML job..."
if az ml job create \
  --file "$TEMP_JOB_FILE" \
  --workspace-name "$WORKSPACE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --subscription "$SUBSCRIPTION_ID"; then
    echo "✅ Job submission completed successfully."
else
    echo "❌ Job submission failed."
    rm "$TEMP_JOB_FILE"
    exit 1
fi

# Clean up
rm "$TEMP_JOB_FILE"