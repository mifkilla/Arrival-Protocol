# Phase 18 Task 2: REST API Specification

## Task

Implement a complete REST API using FastAPI for a todo-list task manager.

## Data Model

Each task has the following fields:

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| id | integer | auto | auto-increment from 1 | read-only |
| title | string | yes | - | min 1 char, max 200 chars |
| description | string | no | "" | max 2000 chars |
| priority | string | no | "medium" | one of: "low", "medium", "high", "critical" |
| status | string | no | "todo" | one of: "todo", "in_progress", "done", "cancelled" |
| due_date | string | no | null | format: YYYY-MM-DD |
| tags | list[string] | no | [] | list of strings |
| created_at | string | auto | ISO timestamp | read-only |
| updated_at | string | auto | ISO timestamp | read-only |

## Endpoints

### CRUD Operations

| Method | Path | Description |
|--------|------|-------------|
| POST | /tasks | Create a new task |
| GET | /tasks/{id} | Get a single task by ID |
| PUT | /tasks/{id} | Update a task (full replace) |
| DELETE | /tasks/{id} | Delete a task |
| GET | /tasks | List all tasks (with filtering, sorting, pagination) |

### Query Parameters for GET /tasks

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 20 | Max items per page (1-100) |
| offset | int | 0 | Skip N items |
| status | string | - | Filter by status |
| priority | string | - | Filter by priority |
| tags | string | - | Filter by tag (comma-separated, any match) |
| sort | string | "id" | Sort field (any task field) |
| order | string | "asc" | Sort direction: "asc" or "desc" |
| search | string | - | Case-insensitive substring search in title and description |

### Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | Deleted (no content) |
| 404 | Task not found |
| 422 | Validation error |

### Response Format

Single task:
```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "priority": "medium",
  "status": "todo",
  "due_date": "2026-03-01",
  "tags": ["personal", "shopping"],
  "created_at": "2026-02-26T12:00:00Z",
  "updated_at": "2026-02-26T12:00:00Z"
}
```

Task list:
```json
{
  "tasks": [...],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

## Constraints

- In-memory storage (Python dict, no database)
- Auto-incrementing integer IDs starting from 1
- Proper Pydantic models for input validation
- Complete error handling
- Python type hints throughout
