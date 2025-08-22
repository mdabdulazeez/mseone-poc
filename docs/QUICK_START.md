# DevOps PoC - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.8+
- Azure CLI (for infrastructure setup)
- Access to Azure subscription

### 1. Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# Verify installation
python -c "import fastapi, strawberry, azure.cosmos, azure.storage.blob; print('✅ All dependencies installed')"
```

### 2. Environment Setup
```bash
# Copy environment template
cp env.example .env

# Edit .env with your Azure details
# (Already populated from terminal session)
```

### 3. Test Configuration
```bash
# Test configuration loading
python -c "from config.settings import get_settings; print('✅ Config loaded successfully')"
```

### 4. Start the API
```bash
# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### GraphQL Playground
Open: http://localhost:8000/graphql

#### Sample Queries

**Get API Status:**
```graphql
query {
  status
  version
  health
}
```

**Create a Project:**
```graphql
mutation {
  createProject(input: {
    name: "DevOps Platform PoC"
    description: "Proof of concept for DevOps platform capabilities"
    owner: "devops-team"
    team: "platform"
    priority: "HIGH"
    tags: ["poc", "devops", "azure"]
  }) {
    id
    name
    status
    created_at
  }
}
```

**List Projects:**
```graphql
query {
  projects(
    filter: { status: "PLANNING" }
    pagination: { limit: 10, offset: 0, sort_by: "created_at", sort_order: "desc" }
  ) {
    id
    name
    description
    status
    owner
    team
    priority
    created_at
  }
}
```

**Get Project Statistics:**
```graphql
query {
  projectStats
}
```

## 🔍 Testing Azure Integration

### 1. Test Cosmos DB Connection
The API will automatically test Cosmos DB connectivity on startup. Check logs for:
```
✅ Cosmos DB connection successful. Container: projects
```

### 2. Test Azure Storage Connection
The API will automatically test Azure Storage connectivity on startup. Check logs for:
```
✅ Azure Storage connection successful. Container: api-results
```

### 3. Verify Data Persistence
After creating/updating projects, check Azure Blob Storage for API result logs:
- Container: `api-results`
- Files: `project-creation-{id}-{timestamp}.json`

## 🐛 Troubleshooting

### Common Issues

#### 1. Module Not Found
```bash
# Error: ModuleNotFoundError: No module named 'pydantic_settings'
# Solution: Install dependencies
pip install -r requirements.txt
```

#### 2. Azure Connection Failed
```bash
# Check .env file has correct values
# Verify Azure services are running
# Check network connectivity
```

#### 3. Cosmos DB Container Not Found
```bash
# The API will automatically create the container
# Check Azure portal for container creation
```

### Debug Mode
```bash
# Start with debug logging
LOG_LEVEL=DEBUG uvicorn main:app --reload
```

## 📊 Monitoring

### Health Endpoints
- `/health` - Service health status
- `/` - API information
- `/graphql` - GraphQL playground

### Logs
- Check console output for connection status
- Azure services log to console with emoji indicators
- Structured logging with timestamps

## 🔐 Security Notes

- `.env` file contains sensitive information - never commit to version control
- Azure AD authentication is configured but not yet implemented
- CORS is open for development - restrict for production
- All Azure operations use secure connections

## 🚀 Next Steps

1. **Test the API** with sample queries above
2. **Implement Azure AD authentication** (next priority)
3. **Add comprehensive testing**
4. **Containerize and deploy to Azure**
5. **Implement Logic App orchestration**

## 📞 Support

- Check logs for detailed error messages
- Verify Azure service status in Azure portal
- Ensure all environment variables are set correctly
- Test individual Azure services separately if needed

---

**Status**: ✅ Ready for testing | **Progress**: 70% Complete | **Next**: Azure AD Auth
