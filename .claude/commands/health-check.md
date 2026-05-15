# Server Health Check

Verifies that the FastAPI server is running and responding correctly.

## Quick command

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -Method GET
```

Or with curl:
```bash
curl http://127.0.0.1:8000/health
```

## Expected response

```json
{ "status": "ok" }
```

## If the server is not responding

1. Start the server:
   ```
   py -m uvicorn main:app --reload
   ```

2. Check that no other process is using port 8000:
   ```powershell
   netstat -ano | findstr :8000
   ```

3. Make sure dependencies are installed:
   ```
   pip install -r requirements.txt
   ```

4. Verify that `.env` has `ANTHROPIC_API_KEY` defined (no extra quotes).

## Available endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Server status |
| POST | `/analyze` | Analyze a CSV/Excel file |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc documentation |