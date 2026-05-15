# Batch Analysis of a Folder

Analyzes all `.csv` and `.xlsx` files in a folder and consolidates the results.

## Prerequisites

- Server running at `http://127.0.0.1:8000`
- Files with a valid text column (`comentarios`, `comment`, `text`, etc.)

## PowerShell script

```powershell
$folder  = "example_file"   # Change to your folder
$top_k   = 10
$results = @()

Get-ChildItem -Path $folder -Include "*.csv","*.xlsx" -Recurse | ForEach-Object {
    Write-Host "Analyzing: $($_.Name)"
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/analyze" `
            -Method POST `
            -Body @{ file_path = $_.FullName; top_k = $top_k.ToString() }
        $data = $response.Content | ConvertFrom-Json
        $results += [PSCustomObject]@{
            file                  = $_.Name
            total_comments        = $data.total_comentarios
            summary               = $data.resumen_general.Substring(0, [Math]::Min(120, $data.resumen_general.Length)) + "..."
            issues_count          = $data.problemas_detectados.Count
            recommendations_count = $data.recomendaciones_accionables.Count
        }
    } catch {
        Write-Warning "Error in $($_.Name): $_"
        $results += [PSCustomObject]@{ file = $_.Name; error = $_.ToString() }
    }
}

# Display consolidated summary
$results | Format-Table -AutoSize

# Save to JSON
$results | ConvertTo-Json -Depth 5 | Out-File "batch_results.json" -Encoding UTF8
Write-Host "Results saved to batch_results.json"
```

## Python script (alternative)

```python
import httpx, json
from pathlib import Path

FOLDER = "example_file"
API    = "http://127.0.0.1:8000/analyze"
TOP_K  = 10

results = []
for path in Path(FOLDER).rglob("*"):
    if path.suffix.lower() not in {".csv", ".xlsx"}:
        continue
    print(f"Analyzing: {path.name}")
    try:
        r = httpx.post(API, data={"file_path": str(path), "top_k": TOP_K}, timeout=120)
        r.raise_for_status()
        results.append({"file": path.name, **r.json()})
    except Exception as e:
        results.append({"file": path.name, "error": str(e)})

Path("batch_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
print(f"Results: batch_results.json ({len(results)} files)")
```

## Notes

- Recommended `top_k`: 10–20 for medium datasets, 5 for small datasets (<50 comments)
- Each file analysis may take 10–30 seconds depending on Claude API response time
- Per-file errors are logged without stopping the batch