# Super Manager API Documentation

## Overview

Super Manager is an intelligent AI-powered assistant for personal and professional task management. This document provides comprehensive API documentation for integrating with the Super Manager backend.

## Base URL

- **Production**: `https://super-manager-api.onrender.com`
- **Development**: `http://localhost:8000`

## Authentication

All API requests (except health checks) require authentication via Bearer token.

```http
Authorization: Bearer <your-api-token>
```

## Rate Limiting

- **Default**: 100 requests per minute
- **Authenticated users**: 200 requests per minute
- Rate limit headers are included in all responses

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per window |
| `X-RateLimit-Remaining` | Remaining requests in current window |
| `X-RateLimit-Reset` | Timestamp when the rate limit resets |

---

## Endpoints

### Health Check

Check if the API is running and healthy.

```http
GET /api/health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "cache": "healthy",
    "ai": "healthy"
  }
}
```

---

### Chat / Conversation

Send a message to the AI assistant and receive a response.

```http
POST /api/chat
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User's message (1-50000 chars) |
| `conversation_id` | string | No | ID of existing conversation |
| `context` | object | No | Additional context |

**Example Request:**

```json
{
  "message": "Schedule a meeting with John tomorrow at 2 PM",
  "conversation_id": "conv_abc123"
}
```

**Response:**

```json
{
  "response": "I've scheduled a meeting with John for tomorrow at 2:00 PM. Would you like me to send a calendar invite?",
  "conversation_id": "conv_abc123",
  "message_id": "msg_xyz789",
  "actions": [
    {
      "type": "meeting_scheduled",
      "data": {
        "title": "Meeting with John",
        "time": "2025-01-16T14:00:00Z",
        "participants": ["john@example.com"]
      }
    }
  ],
  "metadata": {
    "processing_time_ms": 523,
    "model": "llama-3.3-70b-versatile"
  }
}
```

---

### Send Email

Send an email through the AI assistant.

```http
POST /api/email/send
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | string | Yes | Recipient email address |
| `subject` | string | Yes | Email subject |
| `body` | string | Yes | Email content |
| `cc` | string[] | No | CC recipients |
| `bcc` | string[] | No | BCC recipients |

**Example Request:**

```json
{
  "to": "client@example.com",
  "subject": "Meeting Follow-up",
  "body": "Thank you for meeting with me today..."
}
```

**Response:**

```json
{
  "success": true,
  "message_id": "email_abc123",
  "sent_at": "2025-01-15T10:30:00Z"
}
```

---

### Create Meeting

Schedule a new meeting.

```http
POST /api/meetings
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Meeting title |
| `participants` | string[] | Yes | Participant emails |
| `start_time` | string | Yes | ISO 8601 datetime |
| `duration_minutes` | number | No | Duration (default: 60) |
| `description` | string | No | Meeting description |

**Example Request:**

```json
{
  "title": "Project Review",
  "participants": ["alice@example.com", "bob@example.com"],
  "start_time": "2025-01-20T10:00:00Z",
  "duration_minutes": 45,
  "description": "Weekly project status review"
}
```

**Response:**

```json
{
  "meeting_id": "meet_xyz789",
  "meeting_link": "https://meet.jitsi.si/supermanager-xyz789",
  "calendar_event_id": "cal_abc123",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Create Task

Create a new task.

```http
POST /api/tasks
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Task title |
| `description` | string | No | Task description |
| `priority` | string | No | `low`, `medium`, `high`, `urgent` |
| `due_date` | string | No | ISO 8601 datetime |
| `tags` | string[] | No | Task tags |

**Example Request:**

```json
{
  "title": "Complete API documentation",
  "description": "Write comprehensive docs for all endpoints",
  "priority": "high",
  "due_date": "2025-01-20T17:00:00Z",
  "tags": ["documentation", "api"]
}
```

**Response:**

```json
{
  "task_id": "task_abc123",
  "status": "pending",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### List Tasks

Retrieve tasks with optional filtering.

```http
GET /api/tasks
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (`pending`, `completed`, `in_progress`) |
| `priority` | string | Filter by priority |
| `limit` | number | Max results (default: 50) |
| `offset` | number | Pagination offset |

**Response:**

```json
{
  "tasks": [
    {
      "task_id": "task_abc123",
      "title": "Complete API documentation",
      "status": "pending",
      "priority": "high",
      "due_date": "2025-01-20T17:00:00Z"
    }
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

---

### Search (Web/Information)

Perform a web search.

```http
POST /api/search
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `num_results` | number | No | Number of results (default: 5) |
| `safe_search` | boolean | No | Enable safe search (default: true) |

**Response:**

```json
{
  "results": [
    {
      "title": "Search Result Title",
      "url": "https://example.com/article",
      "snippet": "Brief description of the result..."
    }
  ],
  "query": "your search query",
  "total_results": 5
}
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": true,
  "error_id": "abc12345",
  "code": "VALIDATION_ERROR",
  "message": "User-friendly error message",
  "category": "validation",
  "timestamp": "2025-01-15T10:30:00Z",
  "recoverable": true
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `AUTH_REQUIRED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Permission denied |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `EXTERNAL_API_ERROR` | 502 | External service failure |
| `DATABASE_ERROR` | 503 | Database unavailable |
| `TIMEOUT` | 504 | Request timeout |

---

## WebSocket API

For real-time updates, connect to the WebSocket endpoint:

```
wss://super-manager-api.onrender.com/ws
```

### Events

| Event | Description |
|-------|-------------|
| `message` | New chat message received |
| `task_update` | Task status changed |
| `meeting_reminder` | Upcoming meeting reminder |
| `notification` | General notification |

### Example (JavaScript)

```javascript
const ws = new WebSocket('wss://super-manager-api.onrender.com/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['tasks', 'meetings']
}));
```

---

## SDKs and Libraries

### JavaScript/TypeScript

```bash
npm install @supermanager/sdk
```

```javascript
import { SuperManager } from '@supermanager/sdk';

const sm = new SuperManager({
  apiKey: 'your-api-key'
});

const response = await sm.chat('Schedule a meeting');
```

### Python

```bash
pip install supermanager
```

```python
from supermanager import SuperManager

sm = SuperManager(api_key="your-api-key")
response = sm.chat("Schedule a meeting")
```

---

## Changelog

### v1.0.0 (2025-01-15)
- Initial release
- Chat/conversation API
- Email integration
- Meeting scheduling
- Task management
- Web search

---

## Support

- **Documentation**: https://docs.supermanager.ai
- **Issues**: https://github.com/supermanager/api/issues
- **Email**: support@supermanager.ai
