# Archimedes Runbook

This runbook explains how to set up, run, test, and deploy Archimedes without Docker on the local machine.

Current decision: use real Cosmos DB immediately. Local in-memory storage is now only a fallback for emergency debugging.

Deployment path:

1. Phase A: Local app with real Cosmos  
   FastAPI local + Streamlit local + Cosmos DB + mock KB or real KB
2. Phase B: Local app with more Azure services  
   FastAPI local + Streamlit local + Cosmos DB + Azure OpenAI + optional Foundry IQ
3. Phase C: Hosted dev  
   Deploy FastAPI to Azure Container Apps. Keep Streamlit local or deploy it separately.
4. Phase D: Demo deployment  
   Deploy both backend and frontend to Azure. Use real Foundry IQ for at least part of the demo. Keep mock mode as fallback.

## 1. Current Implementation Status

What works now:

- FastAPI app entry point: `src/api/main.py`
- Streamlit frontend entry point: `frontend/app.py`
- Local in-memory fallback storage: `src/api/storage.py`
- Mock knowledge base adapter: `src/archimedes/tools/mock_foundry_iq.py`
- Foundry IQ / Azure AI Search style adapter: `src/archimedes/tools/foundry_iq.py`
- Cosmos storage client implementation: `src/archimedes/storage/cosmos_client.py`
- Cosmos runtime selection via `ARCHIMEDES_API_STORAGE_BACKEND=cosmos`
- Demo flow and re-reasoning tests are passing.

Important behavior:

- FastAPI defaults to in-memory storage unless `ARCHIMEDES_API_STORAGE_BACKEND=cosmos` is set.
- Cosmos DB serverless was already provisioned in backlog task P0-T06b.
- In Cosmos mode, startup validates/creates the database and required containers if they do not already exist.
- Cosmos containers use `/session_id` as the partition key.

## 2. Prerequisites

Install locally:

- Python 3.11 or newer
- Git
- Azure CLI, for Cosmos and hosted deployment steps
- Git Bash or another Bash-compatible terminal

You do not need Docker for the local phases.

Confirm tools:

```bash
python --version
git --version
az version
```

## 3. Repository Layout

Key paths:

```text
src/api/main.py                         FastAPI app
frontend/app.py                         Streamlit UI
frontend/api_client.py                  Streamlit API client
src/api/storage.py                      local in-memory storage
src/archimedes/storage/cosmos_client.py Cosmos storage client
src/archimedes/tools/foundry_iq.py      KB retrieval adapter
src/archimedes/tools/mock_foundry_iq.py mock KB adapter
docs/archimedes-build-backlog.md        roadmap and phase status
requirements.txt                        Python dependencies
pytest.ini                              test config
```

## 4. One-Time Local Setup

From the repo root:

```bash
cd /d/Work/Challenges/Microsoft-Agents-League/src/archemedes
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Set `PYTHONPATH` for this shell:

```bash
export PYTHONPATH=src
```

Run the tests:

```bash
pytest
```

Expected result at the time this runbook was written:

```text
81 passed, 1 skipped
```

## 5. Environment Files

Start from the sample:

```bash
cp .env.example .env
```

For the fastest real-Cosmos path, use:

```dotenv
ARCHIMEDES_ENV=dev
ARCHIMEDES_API_URL=http://localhost:8000/api/v1

# Use real Cosmos immediately.
ARCHIMEDES_API_STORAGE_BACKEND=cosmos
ARCHIMEDES_API_COSMOS_ENDPOINT=https://<cosmos-account>.documents.azure.com:443/
ARCHIMEDES_API_COSMOS_DATABASE_NAME=archimedes

# Prefer managed identity/Azure CLI auth locally. Use this only if key auth is required.
ARCHIMEDES_API_COSMOS_KEY=

# Keep KB mock on until Foundry IQ/Azure AI Search is ready.
USE_MOCK_KB=true

# Mock KB mode does not need a real Foundry endpoint.
ARCHIMEDES_API_VALIDATE_REQUIRED_ENV=false
FOUNDRY_PROJECT_ENDPOINT=
DEFAULT_ARCHITECTURE_MODEL=gpt-4.1
AZURE_OPENAI_ENDPOINT=

COSMOS_ENDPOINT=https://<cosmos-account>.documents.azure.com:443/
COSMOS_DATABASE_NAME=archimedes
COSMOS_KEY=
```

Notes:

- `ARCHIMEDES_API_URL` is read by the Streamlit frontend.
- `ARCHIMEDES_API_STORAGE_BACKEND=cosmos` makes FastAPI use `CosmosStorageClient`.
- `USE_MOCK_KB=true` makes `FoundryIQRetriever` use the fixture-backed mock adapter.
- `ARCHIMEDES_API_VALIDATE_REQUIRED_ENV=false` allows FastAPI to start without `FOUNDRY_PROJECT_ENDPOINT`.
- FastAPI settings use the `ARCHIMEDES_API_` prefix for app settings such as `ARCHIMEDES_API_VALIDATE_REQUIRED_ENV`.
- Cosmos endpoint can be supplied as either `ARCHIMEDES_API_COSMOS_ENDPOINT` or `COSMOS_ENDPOINT`.
- Cosmos database can be supplied as either `ARCHIMEDES_API_COSMOS_DATABASE_NAME` or `COSMOS_DATABASE_NAME`.

## 6. Phase A: Local FastAPI + Streamlit With Real Cosmos

Architecture:

```text
Browser -> Streamlit local :8501 -> FastAPI local :8000 -> Cosmos DB + mock KB
```

This is the default path for the project now.

### 6.0 Use Existing Cosmos DB

Backlog task P0-T06b already provisioned the core Azure resources:

```text
Resource group:        arch-dev-rg-eus
Cosmos DB account:    arch-dev-cosmos-eus-06102215
Storage account:      archdevsteus06102215
Container Apps env:   arch-dev-acaenv-eus
App Insights:         arch-dev-ai-eus
Key Vault:            arch-dev-kv-eus-06102215
Region:               eastus
Cosmos database name: archimedes
```

Log in and select the subscription:

```bash
az login
az account show
az account set --subscription "<subscription-id-or-name>"
```

Set shell variables for the existing Cosmos account:

```bash
rg="arch-dev-rg-eus"
loc="eastus"
cosmos="arch-dev-cosmos-eus-06102215"
db="archimedes"

cosmosEndpoint=$(az cosmosdb show \
  --name "$cosmos" \
  --resource-group "$rg" \
  --query documentEndpoint \
  --output tsv
)
```

You do not need to create the Cosmos account again. FastAPI startup will validate/create the required database containers:

```text
architecture_sessions
versioned_artifacts
claims_evidence
change_events
diffs
```

All containers use partition key:

```text
/session_id
```

Authentication options:

- Preferred local option: Azure CLI / `DefaultAzureCredential`
- Fastest option if RBAC is not ready: Cosmos key via `ARCHIMEDES_API_COSMOS_KEY`

If using key auth:

```bash
cosmosKey=$(az cosmosdb keys list \
  --name "$cosmos" \
  --resource-group "$rg" \
  --query primaryMasterKey \
  --output tsv
)
```

### 6.1 Start FastAPI

Open terminal 1:

```bash
cd /d/Work/Challenges/Microsoft-Agents-League/src/archemedes
source .venv/Scripts/activate
export PYTHONPATH=src
export USE_MOCK_KB=true
export ARCHIMEDES_API_VALIDATE_REQUIRED_ENV=false
export ARCHIMEDES_API_STORAGE_BACKEND=cosmos
export ARCHIMEDES_API_COSMOS_ENDPOINT="$cosmosEndpoint"
export ARCHIMEDES_API_COSMOS_DATABASE_NAME=archimedes

# Use this only if managed identity / Azure CLI auth is not configured.
# export ARCHIMEDES_API_COSMOS_KEY="$cosmosKey"

python -m uvicorn api.main:app --app-dir src --reload --host 127.0.0.1 --port 8000
```

Validate:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/health
```

Expected status:

```text
status = ok
service = archimedes-api
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

### 6.2 Start Streamlit

Open terminal 2:

```bash
cd /d/Work/Challenges/Microsoft-Agents-League/src/archemedes
source .venv/Scripts/activate
export ARCHIMEDES_API_URL=http://127.0.0.1:8000/api/v1
streamlit run frontend/app.py --server.port 8501
```

Open:

```text
http://localhost:8501
```

### 6.3 Smoke Test Through API

Create a session:

```bash
session_json=$(curl -sS -X POST http://127.0.0.1:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "business_need": "Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability.",
    "title": "Fraud Detection Demo"
  }')

session_id=$(printf '%s' "$session_json" | python -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo "$session_id"
```

Send a message:

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/v1/sessions/${session_id}/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability."
  }'
```

Check pipeline:

```bash
curl -sS "http://127.0.0.1:8000/api/v1/sessions/${session_id}/pipeline/status"
```

Confirm Cosmos persistence:

```bash
az cosmosdb sql query \
  --account-name "$cosmos" \
  --resource-group "$rg" \
  --database-name "$db" \
  --container-name architecture_sessions \
  --query "SELECT * FROM c WHERE c.session_id = '${session_id}'"

az cosmosdb sql query \
  --account-name "$cosmos" \
  --resource-group "$rg" \
  --database-name "$db" \
  --container-name versioned_artifacts \
  --query "SELECT c.stage, c.version FROM c WHERE c.session_id = '${session_id}'"
```

### 6.4 Demo Message Sequence

Use this order for a stable local demo:

1. `Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability.`
2. `Extract requirements: 10K TPS, PCI-DSS, 99.95% availability.`
3. `real-time stream event latency tps fraud pattern detection`
4. `Generate architecture options for the 10K TPS fraud workload.`
5. `Run Socratic review on the options.`
6. `Generate the ADR for the recommended option.`
7. `Generate the HLD for the selected option.`
8. `Run the mini WAF review.`
9. `Actually, make it 100K TPS and multi-region active-active.`

Expected highlights:

- Pattern detection identifies `real_time_streaming`.
- Options include 3 or more architecture options.
- Socratic review and evidence audit artifacts are produced.
- ADR, HLD, WAF, and final evidence audit artifacts are produced.
- Requirement change creates impacted/stable stage lists.
- Impacted artifacts regenerate as v2 where v1 existed.
- Diff endpoints can compare v1 and v2.

### 6.5 Diff API Example

Create a diff after a change produced v2:

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/v1/sessions/${session_id}/diffs" \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "options_generation",
    "before_version": 1,
    "after_version": 2
  }'
```

List diffs:

```bash
curl -sS "http://127.0.0.1:8000/api/v1/sessions/${session_id}/diffs?stage=options_generation"
```

## 7. Phase B: Add Azure OpenAI / Foundry IQ Locally

Architecture target:

```text
Browser -> Streamlit local :8501 -> FastAPI local :8000 -> Cosmos DB + Azure OpenAI + optional Foundry IQ
```

Cosmos is already active from Phase A. This phase turns on real model and retrieval services.

### 7.1 Azure Login

```bash
az login
az account show
az account set --subscription "<subscription-id-or-name>"
```

### 7.2 Recommended Azure Resources

Minimum resources:

- Azure OpenAI or Azure AI Foundry project/model deployment
- Optional Azure AI Search / Foundry IQ knowledge source

### 7.3 Azure OpenAI / Foundry Environment

Set local environment variables:

```bash
export FOUNDRY_PROJECT_ENDPOINT="https://<your-foundry-project-endpoint>"
export DEFAULT_ARCHITECTURE_MODEL="<your-model-deployment-name>"
export AZURE_OPENAI_ENDPOINT="https://<your-azure-openai-resource>.openai.azure.com/"
```

The current lightweight Foundry client uses:

```text
FOUNDRY_PROJECT_ENDPOINT
DEFAULT_ARCHITECTURE_MODEL
```

It imports `azure.identity.DefaultAzureCredential`, so install Azure identity support before using that path:

```bash
pip install azure-identity
```

### 7.4 Real KB / Foundry IQ Style Retrieval

Mock mode:

```bash
export USE_MOCK_KB=true
```

Real retrieval mode:

```bash
export USE_MOCK_KB=false
export ARCH_SEARCH_ENDPOINT="https://<search-service>.search.windows.net"
export ARCH_SEARCH_API_KEY="<search-api-key>"
export ARCH_KB_INDEX=archimedes-arch-idx
export ARCH_KB_NAME=azure-architecture-kb
export ARCH_KB_VERSION=v1
```

Alternative endpoint variable:

```bash
export ARCH_SEARCH_SERVICE_NAME="<search-service-name>"
```

Use either `ARCH_SEARCH_ENDPOINT` or `ARCH_SEARCH_SERVICE_NAME`.

Keep this as the Phase B acceptance test:

1. Start FastAPI locally.
2. Create a session.
3. Confirm a document appears in `architecture_sessions`.
4. Run one or more stages.
5. Confirm artifacts appear in `versioned_artifacts`.
6. Trigger a requirement change.
7. Confirm change events and v2 artifacts are persisted.

## 8. Phase C: Hosted Dev

Architecture target:

```text
Browser -> Streamlit local :8501 -> hosted FastAPI on Azure Container Apps -> Azure services
```

Since Docker is unavailable locally, use an Azure-side source build or remote build path.

### 8.1 Prepare Azure CLI

```bash
az login
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
```

### 8.2 Use Existing Container Apps Environment

```bash
rg="arch-dev-rg-eus"
loc="eastus"
envName="arch-dev-acaenv-eus"
cosmos="arch-dev-cosmos-eus-06102215"
db="archimedes"

cosmosEndpoint=$(az cosmosdb show \
  --name "$cosmos" \
  --resource-group "$rg" \
  --query documentEndpoint \
  --output tsv
)

az containerapp env show \
  --name "$envName" \
  --resource-group "$rg"
```

### 8.3 Deploy FastAPI Without Local Docker

Preferred no-Docker path:

```bash
appName="archimedes-api-dev"

az containerapp up \
  --name "$appName" \
  --resource-group "$rg" \
  --location "$loc" \
  --environment "$envName" \
  --source . \
  --ingress external \
  --target-port 8000
```

If Azure source build cannot infer the Python app, add a startup command in Container Apps:

```text
python -m uvicorn api.main:app --app-dir src --host 0.0.0.0 --port 8000
```

Set app environment variables:

```bash
az containerapp update \
  --name "$appName" \
  --resource-group "$rg" \
  --set-env-vars \
    ARCHIMEDES_API_VALIDATE_REQUIRED_ENV=false \
    USE_MOCK_KB=true \
    ARCHIMEDES_API_STORAGE_BACKEND=cosmos \
    ARCHIMEDES_API_COSMOS_ENDPOINT="$cosmosEndpoint" \
    ARCHIMEDES_API_COSMOS_DATABASE_NAME="archimedes"
```

If using Cosmos key auth, store it as a secret:

```bash
az containerapp secret set \
  --name "$appName" \
  --resource-group "$rg" \
  --secrets cosmos-key="$cosmosKey"

az containerapp update \
  --name "$appName" \
  --resource-group "$rg" \
  --set-env-vars ARCHIMEDES_API_COSMOS_KEY=secretref:cosmos-key
```

For Azure-backed mode, set real values instead:

```bash
az containerapp update \
  --name "$appName" \
  --resource-group "$rg" \
  --set-env-vars \
    ARCHIMEDES_API_VALIDATE_REQUIRED_ENV=true \
    USE_MOCK_KB=false \
    ARCHIMEDES_API_STORAGE_BACKEND=cosmos \
    ARCHIMEDES_API_COSMOS_ENDPOINT="$cosmosEndpoint" \
    ARCHIMEDES_API_COSMOS_DATABASE_NAME="archimedes" \
    FOUNDRY_PROJECT_ENDPOINT="https://<foundry-project-endpoint>" \
    DEFAULT_ARCHITECTURE_MODEL="<model-deployment>" \
    ARCH_SEARCH_ENDPOINT="https://<search-service>.search.windows.net" \
    ARCH_KB_INDEX="archimedes-arch-idx"
```

Use Container Apps secrets for keys:

```bash
az containerapp secret set \
  --name "$appName" \
  --resource-group "$rg" \
  --secrets arch-search-api-key="<search-api-key>"

az containerapp update \
  --name "$appName" \
  --resource-group "$rg" \
  --set-env-vars ARCH_SEARCH_API_KEY=secretref:arch-search-api-key
```

Get the hosted API URL:

```bash
apiFqdn=$(az containerapp show \
  --name "$appName" \
  --resource-group "$rg" \
  --query properties.configuration.ingress.fqdn \
  --output tsv
)

echo "https://${apiFqdn}/api/v1"
```

Validate:

```bash
curl "https://${apiFqdn}/health"
curl "https://${apiFqdn}/api/v1/health"
```

### 8.4 Point Local Streamlit at Hosted FastAPI

```bash
cd /d/Work/Challenges/Microsoft-Agents-League/src/archemedes
source .venv/Scripts/activate
export ARCHIMEDES_API_URL="https://${apiFqdn}/api/v1"
streamlit run frontend/app.py --server.port 8501
```

## 9. Phase D: Demo Deployment

Architecture target:

```text
Browser -> hosted Streamlit -> hosted FastAPI -> Cosmos DB + Azure OpenAI + Foundry IQ
```

Keep mock mode available as a fallback:

```text
USE_MOCK_KB=true
```

### 9.1 Backend

Use the Phase C FastAPI deployment. For a real demo, set:

```text
ARCHIMEDES_API_VALIDATE_REQUIRED_ENV=true
USE_MOCK_KB=false
FOUNDRY_PROJECT_ENDPOINT=<real endpoint>
DEFAULT_ARCHITECTURE_MODEL=<real deployment>
ARCH_SEARCH_ENDPOINT=<real Azure AI Search endpoint>
ARCH_SEARCH_API_KEY=<secretref>
ARCH_KB_INDEX=<real index>
```

Cosmos settings are required:

```text
ARCHIMEDES_API_STORAGE_BACKEND=cosmos
ARCHIMEDES_API_COSMOS_ENDPOINT=<real endpoint>
ARCHIMEDES_API_COSMOS_DATABASE_NAME=archimedes
```

### 9.2 Frontend

Option 1: Keep Streamlit local for the demo:

```bash
export ARCHIMEDES_API_URL="https://${apiFqdn}/api/v1"
streamlit run frontend/app.py --server.port 8501
```

Option 2: Deploy Streamlit separately to Container Apps without local Docker:

```bash
uiAppName="archimedes-ui-dev"

az containerapp up \
  --name "$uiAppName" \
  --resource-group "$rg" \
  --location "$loc" \
  --environment "$envName" \
  --source . \
  --ingress external \
  --target-port 8501
```

If Azure source build cannot infer Streamlit startup, set the startup command:

```text
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
```

Set frontend env:

```bash
az containerapp update \
  --name "$uiAppName" \
  --resource-group "$rg" \
  --set-env-vars ARCHIMEDES_API_URL="https://${apiFqdn}/api/v1"
```

Get frontend URL:

```bash
uiFqdn=$(az containerapp show \
  --name "$uiAppName" \
  --resource-group "$rg" \
  --query properties.configuration.ingress.fqdn \
  --output tsv
)

echo "https://${uiFqdn}"
```

### 9.3 Demo Checklist

Before recording or presenting:

```bash
pytest
curl "https://${apiFqdn}/health"
curl "https://${apiFqdn}/api/v1/health/ready"
```

In the UI:

1. Create a new session with the 10K TPS fraud prompt.
2. Run intake and requirements.
3. Run pattern detection with the message:
   `real-time stream event latency tps fraud pattern detection`
4. Generate options.
5. Run Socratic review.
6. Generate ADR.
7. Generate HLD.
8. Run mini WAF review.
9. Submit change:
   `Actually, make it 100K TPS and multi-region active-active.`
10. Show impacted vs stable stages.
11. Show v2 artifacts.
12. Show options/HLD diffs.

Fallback plan:

1. If Foundry IQ or Azure AI Search is unavailable, set `USE_MOCK_KB=true`.
2. Restart the backend.
3. Continue the demo using mock KB evidence.

## 10. Useful API Endpoints

Health:

```text
GET /health
GET /api/v1/health
GET /api/v1/health/ready
```

Sessions:

```text
POST /api/v1/sessions
GET  /api/v1/sessions/{session_id}
POST /api/v1/sessions/{session_id}/messages
GET  /api/v1/sessions/{session_id}/pipeline/status
```

Artifacts:

```text
GET /api/v1/sessions/{session_id}/artifacts/{stage}/latest
GET /api/v1/sessions/{session_id}/artifacts/{stage}?version=1
GET /api/v1/sessions/{session_id}/artifacts/{stage}/diff?v1=1&v2=2
```

Evidence:

```text
GET /api/v1/sessions/{session_id}/claims
GET /api/v1/sessions/{session_id}/evidence
```

Changes and diffs:

```text
POST /api/v1/sessions/{session_id}/changes/preview-impact
POST /api/v1/sessions/{session_id}/changes
GET  /api/v1/sessions/{session_id}/changes/{change_event_id}
POST /api/v1/sessions/{session_id}/changes/{change_event_id}/rereason
POST /api/v1/sessions/{session_id}/diffs
GET  /api/v1/sessions/{session_id}/diffs
GET  /api/v1/sessions/{session_id}/diffs/{diff_id}
```

## 11. Troubleshooting

### FastAPI fails with missing `FOUNDRY_PROJECT_ENDPOINT`

For local mock mode:

```bash
export ARCHIMEDES_API_VALIDATE_REQUIRED_ENV=false
```

For Azure-backed mode:

```bash
export FOUNDRY_PROJECT_ENDPOINT="https://<your-foundry-project-endpoint>"
```

### FastAPI fails while connecting to Cosmos

Check required settings:

```bash
echo "$ARCHIMEDES_API_STORAGE_BACKEND"
echo "$ARCHIMEDES_API_COSMOS_ENDPOINT"
echo "$ARCHIMEDES_API_COSMOS_DATABASE_NAME"
```

Expected:

```text
ARCHIMEDES_API_STORAGE_BACKEND=cosmos
ARCHIMEDES_API_COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/
ARCHIMEDES_API_COSMOS_DATABASE_NAME=archimedes
```

If RBAC / `DefaultAzureCredential` is not ready, use key auth:

```bash
export ARCHIMEDES_API_COSMOS_KEY="$cosmosKey"
```

If the SDK is missing:

```bash
pip install azure-cosmos azure-identity
```

### Streamlit cannot reach backend

Check:

```bash
echo "$ARCHIMEDES_API_URL"
curl http://127.0.0.1:8000/api/v1/health
```

Set:

```bash
export ARCHIMEDES_API_URL=http://127.0.0.1:8000/api/v1
```

### Pattern detection fails

The deterministic pattern detector needs signal words. For the fraud demo, use:

```text
real-time stream event latency tps fraud pattern detection
```

### Port already in use

Find processes:

```bash
netstat -ano | grep ':8000'
netstat -ano | grep ':8501'
```

Use another port:

```bash
python -m uvicorn api.main:app --app-dir src --reload --port 8010
export ARCHIMEDES_API_URL=http://127.0.0.1:8010/api/v1
streamlit run frontend/app.py --server.port 8502
```

### Real KB retrieval fails

Check:

```bash
echo "$USE_MOCK_KB"
echo "$ARCH_SEARCH_ENDPOINT"
echo "$ARCH_SEARCH_SERVICE_NAME"
echo "$ARCH_SEARCH_API_KEY"
echo "$ARCH_KB_INDEX"
```

Fallback:

```bash
export USE_MOCK_KB=true
```

### Container Apps source deployment fails

Use this checklist:

1. Confirm the Container Apps extension is current:
   `az extension add --name containerapp --upgrade`
2. Confirm app starts locally with the exact startup command.
3. Confirm `requirements.txt` contains runtime dependencies.
4. Configure the startup command in Container Apps:
   `python -m uvicorn api.main:app --app-dir src --host 0.0.0.0 --port 8000`
5. Check logs:

```bash
az containerapp logs show \
  --name "$appName" \
  --resource-group "$rg" \
  --follow
```

## 12. Cleanup

Stop local processes with `Ctrl+C` in each terminal.

Do not delete `arch-dev-rg-eus`; it contains the shared resources provisioned in P0-T06b.

To remove only the hosted app instances created during this runbook:

```bash
az containerapp delete --name "$appName" --resource-group "$rg" --yes
az containerapp delete --name "$uiAppName" --resource-group "$rg" --yes
```

## 13. Acceptance Criteria By Phase

Phase A:

- `pytest` passes.
- FastAPI health endpoint returns `ok`.
- Streamlit loads locally.
- New session can be created.
- Session appears in Cosmos `architecture_sessions`.
- Artifacts appear in Cosmos `versioned_artifacts`.
- Demo flow produces artifacts.
- Requirement change produces impacted/stable stages and v2 artifacts.

Phase B:

- Azure login works locally.
- Cosmos containers exist.
- Real model credentials are configured.
- Optional real KB retrieval works, or mock KB fallback is enabled.
- Sessions, artifacts, change events, claims/evidence, and diffs persist to Cosmos.

Phase C:

- FastAPI is reachable from a public Container Apps URL.
- Local Streamlit can call the hosted FastAPI URL.
- Health and session APIs work.

Phase D:

- Backend and frontend are both hosted or frontend is intentionally local.
- Real Foundry IQ / KB is used for at least part of the demo.
- Mock KB fallback is documented and tested.
- 10K TPS demo and 100K TPS multi-region re-reasoning flow can be shown end to end.
