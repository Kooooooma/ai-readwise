---
description: Common development commands for ai-readwise project
---

# Common Development Commands

// turbo-all

## Backend

1. Run syntax check on Python files:
```
.\venv\Scripts\python.exe -m py_compile backend\*.py
```

2. Start the backend server:
```
python .\app.py
```

3. Check backend imports:
```
.\venv\Scripts\python.exe -c "from backend import api, services, translation_service"
```

## Frontend

1. Build the frontend:
```
cd frontend && npm run build
```

2. Type check the frontend:
```
cd frontend && npx tsc --noEmit
```

3. Run development server:
```
cd frontend && npm run dev
```

## File Operations

1. List directory contents:
```
Get-ChildItem -Path <path>
```

2. Read file contents:
```
Get-Content -Path <file>
```

## Testing

1. Test a specific Python module:
```
.\venv\Scripts\python.exe -c "import <module>; print('OK')"
```
