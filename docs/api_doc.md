# Expense Tracker API Documentation

## Base URL

```
https://<server_url+port>/api/v1
```

## Authentication

All endpoints (except registration and login) require JWT authentication via the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

## Common Response Format

```json
{
  "data": {} // Response data
}
```

## Error Response Format

```json
{
  "detail": {
    "message": "Human readable error message",
    "details": {} // Additional error details
  }
}
```

---

## Health Check Endpoints

### GET /health

Check if the API server is running.

**Response (200 OK):**

```json
{
  "data": {
    "status": "ok"
  }
}
```

---

## Users Endpoints

### POST /users/register

Register a new user account.

**Request Body:**

```json
{
  "email": "john.doe@example.com",
  "password": "securePassword123",
  "username": "John"
}
```

**Response (201 Created):**

```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "username": "John",
      "created_at": "2025-07-29T10:30:00Z",
      "updated_at": "2025-07-29T10:30:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid input data
- `409 Conflict`: Email already exists

---

### POST /users/login

Authenticate user and get JWT token.

**Request Body:**

```json
{
  "email": "john.doe@example.com",
  "password": "securePassword123"
}
```

**Response (200 OK):**

```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "username": "John",
      "created_at": "2025-07-29T10:30:00Z",
      "updated_at": "2025-07-29T10:30:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Invalid credentials

---

### POST /users/refresh

Obtain a new JWT access token using a valid refresh token.

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**

```json
{
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid or missing refresh token
- `401 Unauthorized`: Expired or invalid refresh token

---

### GET /users/me

Get current user profile information.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**

```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "username": "John",
      "created_at": "2025-07-29T10:30:00Z",
      "updated_at": "2025-07-29T10:30:00Z"
    }
  }
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid or expired token

---

## Groups Endpoints

### POST /groups

Create a new expense group.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Request Body:**

```json
{
  "name": "Weekend Trip to Paris",
  "description": "Expenses for our weekend getaway to Paris"
}
```

**Response (201 Created):**

```json
{
  "data": {
    "group": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Weekend Trip to Paris",
      "description": "Expenses for our weekend getaway to Paris",
      "created_by": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-07-29T10:30:00Z",
      "updated_at": "2025-07-29T10:30:00Z",
      "member_count": 1
    }
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Invalid or expired token

---

### GET /groups

List all groups for the authenticated user.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**

- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Response (200 OK):**

```json
{
  "data": {
    "groups": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Weekend Trip to Paris",
        "description": "Expenses for our weekend getaway to Paris",
        "created_by": "550e8400-e29b-41d4-a716-446655440000",
        "created_at": "2025-07-29T10:30:00Z",
        "updated_at": "2025-07-29T10:30:00Z",
        "member_count": 3,
        "user_role": "admin"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "pages": 1
    }
  }
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid or expired token

---

### GET /groups/{group_id}

Get detailed information about a specific group.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `group_id`: UUID of the group

**Response (200 OK):**

```json
{
  "data": {
    "group": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Weekend Trip to Paris",
      "description": "Expenses for our weekend getaway to Paris",
      "created_by": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-07-29T10:30:00Z",
      "updated_at": "2025-07-29T10:30:00Z",
      "member_count": 3,
      "user_role": "admin"
    }
  }
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: User is not a member of this group
- `404 Not Found`: Group not found

---

### PUT /groups/{group_id}

Update group information.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `group_id`: UUID of the group

**Request Body:**

```json
{
  "name": "Weekend Trip to Paris - Updated",
  "description": "Updated description for our Paris trip"
}
```

**Response (200 OK):**

```json
{
  "data": {
    "group": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Weekend Trip to Paris - Updated",
      "description": "Updated description for our Paris trip",
      "created_by": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-07-29T10:30:00Z",
      "updated_at": "2025-07-29T11:30:00Z",
      "member_count": 3
    }
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: Only group admin can update group
- `404 Not Found`: Group not found

---

### GET /groups/{group_id}/members

Get paginated list of group members.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `group_id`: UUID of the group

**Query Parameters:**

- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Response (200 OK):**

```json
{
  "data": {
    "members": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "john.doe@example.com",
        "username": "John",
        "role": "admin"
      },
      {
        "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "email": "jane.smith@example.com",
        "username": "Jane",
        "role": "member"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 2,
      "pages": 1
    }
  }
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: User is not a member of this group
- `404 Not Found`: Group not found

---

### POST /groups/{group_id}/members

Add a new member to the group.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `group_id`: UUID of the group

**Request Body:**

```json
{
  "email": "new.member@example.com",
  "role": "member"
}
```

**Response (201 Created):**

```json
{
  "data": {
    "member": {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "email": "new.member@example.com",
      "username": "New",
      "role": "member"
    }
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid email or user already in group
- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: Only group admin can add members
- `404 Not Found`: Group or user not found

### PUT /groups/{group_id}/members/{user_id}/role

Update a member's role in a group (e.g., from "member" to "admin").

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `group_id`: UUID of the group
- `user_id`: UUID of the member

**Request Body:**

```json
{
  "role": "admin" // or "member"
}
```

**Response (200 OK)**

---

### DELETE /groups/{group_id}/members/{user_id}

Remove a member from a group.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `group_id`: UUID of the group
- `user_id`: UUID of the member to remove

**Response (200 OK)**

---

### DELETE /groups/{group_id}

Delete a group (only allowed by admin).

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `group_id`: UUID of the group

**Response (200 OK):**

---

## Expenses Endpoints

### POST /groups/{group_id}/expenses

Create a new expense.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Request Body:**

```json
{
  "title": "Dinner at Le Bernardin",
  "amount": 285.5,
  "payer_id": "550e8400-e29b-41d4-a716-446655440000",
  "category": "Food",
  "date": "2025-07-28",
  "is_payer_included": true,
  "participants_id": ["6ba7b810-9dad-11d1-80b4-00c04fd430c8"]
}
```

**Response (201 Created):**

```json
{
  "data": {
    "expense": {
      "id": "987fcdeb-51a2-4d3c-8765-123456789abc",
      "group_id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Dinner at Le Bernardin",
      "amount": 285.5,
      "payer": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "John",
        "email": "john.doe@example.com"
      },
      "category": "Food",
      "date": "2025-07-28",
      "created_at": "2025-07-29T12:30:00Z",
      "updated_at": "2025-07-29T12:30:00Z",
      "participants": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "username": "John",
          "email": "john.doe@example.com"
        },
        {
          "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
          "username": "Jane",
          "email": "jane.smith@example.com"
        }
      ]
    }
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid input data or participants not in group
- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: User is not a member of the group

---

### GET /groups/{group_id}/expenses

List expenses with filtering options.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**

- `category` (optional): Filter by category (Food, Transport, Accommodation, Entertainment, Other)
- `payer_id` (optional): Filter by payer UUID
- `date_from` (optional): Start date filter (YYYY-MM-DD)
- `date_to` (optional): End date filter (YYYY-MM-DD)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Response (200 OK):**

```json
{
  "data": {
    "expenses": [
      {
        "id": "987fcdeb-51a2-4d3c-8765-123456789abc",
        "group_id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Dinner at Le Bernardin",
        "amount": 285.5,
        "payer": {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "username": "John",
          "email": "john.doe@example.com"
        },
        "category": "Food",
        "date": "2025-07-28",
        "created_at": "2025-07-29T12:30:00Z",
        "participants": [
          {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "username": "John",
            "email": "john.doe@example.com"
          },
          {
            "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "username": "Jane",
            "email": "jane.smith@example.com"
          }
        ]
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "pages": 1
    }
  }
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid or expired token

---

### GET /groups/{group_id}/expenses/{expense_id}

Get detailed information about a specific expense.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `expense_id`: UUID of the expense

**Response (200 OK):**

```json
{
  "data": {
    "expense": {
      "id": "987fcdeb-51a2-4d3c-8765-123456789abc",
      "group_id": "123e4567-e89b-12d3-a456-426614174000",
      "group_name": "Weekend Trip to Paris",
      "title": "Dinner at Le Bernardin",
      "amount": 285.5,
      "category": "Food",
      "date": "2025-07-28",
      "created_at": "2025-07-29T12:30:00Z",
      "updated_at": "2025-07-29T12:30:00Z",
      "payer": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "John",
        "email": "john.doe@example.com"
      },
      "participants": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "username": "John",
          "email": "john.doe@example.com"
        },
        {
          "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
          "username": "Jane",
          "email": "jane.smith@example.com"
        }
      ]
    }
  }
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: User is not a member of the expense's group
- `404 Not Found`: Expense not found

---

### PUT /groups/{group_id}/expenses/{expense_id}

Update an existing expense.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `expense_id`: UUID of the expense

**Request Body:**

```json
{
  "title": "Updated Dinner at Le Bernardin",
  "amount": 300.0,
  "category": "Food",
  "payer_id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2025-07-28",
  "is_payer_included": true,
  "participants_id": [
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  ]
}
```

**Response (200 OK):**

```json
{
  "data": {
    "expense": {
      "id": "987fcdeb-51a2-4d3c-8765-123456789abc",
      "group_id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Updated Dinner at Le Bernardin",
      "amount": 300.0,
      "payer": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "John",
        "email": "john.doe@example.com"
      },
      "category": "Food",
      "date": "2025-07-28",
      "created_at": "2025-07-29T12:30:00Z",
      "updated_at": "2025-07-29T13:30:00Z",
      "participants": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "username": "John",
          "email": "john.doe@example.com"
        },
        {
          "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
          "username": "Jane",
          "email": "jane.smith@example.com"
        }
      ]
    }
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: User is not a member of the expense's group
- `404 Not Found`: Expense not found

---

### DELETE /groups/{group_id}/expenses/{expense_id}

Delete an expense (soft delete).

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `expense_id`: UUID of the expense

**Response (200 OK):**

```json
{
  "data": {}
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: User is not a member of the expense's group
- `404 Not Found`: Expense not found

---

### GET /groups/{group_id}/members/{user_id}/balance

Get a user’s balance in a group (share per expense + total owed).

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `group_id`: UUID of the group
- `user_id`: UUID of the user

**Response (200 OK):**

```json
{
  "data": {
    "user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "net_balance": 342.75,
    "expenses": {
      "987fcdeb-51a2-4d3c-8765-123456789abc": 142.75,
      "888fcdeb-51a2-4d3c-8765-123456789def": 200.0
    }
  }
}
```

---

## Sync Endpoints

### POST /sync/bulk

Perform bulk synchronization operations.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Request Body:**

```json
{
  "changes": [
    {
      "type": "create",
      "entity": "expense",
      "entity_id": "987fcdeb-51a2-4d3c-8765-123456789abc",
      "data": {
        // id and group_id should be the same as the server
        "group_id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Coffee Shop",
        "amount": 15.5,
        "payer_id": "550e8400-e29b-41d4-a716-446655440000",
        "category": "Food",
        "date": "2025-07-29",
        "is_payer_included": true,
        "participants_id": ["550e8400-e29b-41d4-a716-446655440000"]
      },
      "timestamp": "2025-07-29T14:30:00Z"
    },
    {
      "type": "update",
      "entity": "expense",
      "entity_id": "987fcdeb-51a2-4d3c-8765-123456789abc",
      "data": {
        "group_id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Updated Restaurant Bill",
        "amount": 320.0,
        "payer_id": "550e8400-e29b-41d4-a716-446655440000",
        "category": "Food",
        "date": "2025-07-29",
        "is_payer_included": true,
        "participants_id": ["550e8400-e29b-41d4-a716-446655440000"]
      },
      "timestamp": "2025-07-29T14:35:00Z"
    },
    {
      "type": "delete",
      "entity": "expense",
      "entity_id": "456fcdeb-51a2-4d3c-8765-123456789xyz",
      "timestamp": "2025-07-29T14:40:00Z"
    },
    {
      "type": "create",
      "entity": "group",
      "entity_id": "789e4567-e89b-12d3-a456-426614174111",
      "data": {
        "name": "College Reunion Trip",
        "description": "Expenses for our college reunion weekend"
      },
      "timestamp": "2025-07-29T14:45:00Z"
    },
    {
      "type": "update",
      "entity": "group",
      "entity_id": "123e4567-e89b-12d3-a456-426614174000",
      "data": {
        "name": "Updated Paris Trip",
        "description": "Updated description for our amazing Paris adventure"
      },
      "timestamp": "2025-07-29T14:50:00Z"
    },
    {
      "type": "delete",
      "entity": "group",
      "entity_id": "abc4567-e89b-12d3-a456-426614174222",
      "timestamp": "2025-07-29T14:55:00Z"
    }
  ]
}
```

**Response (202 Accepted):**

```json
{
  "data": {
    "operation_id": "bulk-sync-456"
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid operation format
- `401 Unauthorized`: Invalid or expired token

---

### GET /sync/status/{operation_id}

Check the status of a sync operation.

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**

- `operation_id`: UUID of the sync operation

**Response (200 OK):**

```json
{
  "data": {
    "operation_id": "bulk-sync-456",
    "status": "completed",
    "created_at": "2025-07-29T14:40:00Z",
    "completed_at": "2025-07-29T14:40:15Z",
    "notifications": ["", ""]
  }
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid or expired token
- `404 Not Found`: Operation not found

---

## Sync Endpoints (v2 - WebSocket Based)

Version 2 introduces a WebSocket-based bulk sync endpoint that replaces the request/response plus polling model of v1 (`POST /sync/bulk` + `GET /sync/status/{operation_id}`) with a single persistent connection for the whole operation.

### Base URL (v2)

```
https://<server_url+port>/api/v2
```

### WebSocket Endpoint

```
GET ws(s)://<server_url+port>/api/v2/sync/bulk/ws?token=<JWT>
```

Notes:
- The `token` query parameter MUST contain a valid JWT access token (same format as Authorization header in v1).
- The connection is accepted only after token validation. Missing / invalid tokens cause the server to send an error frame then close.
- Payload is sent once by the client after the connection is established (no streaming changes yet).
- The server currently responds with an `ack` message immediately, then a `completed` (or `error`) message when processing finishes.

### Client -> Server First Message

Immediately after `101 Switching Protocols` (i.e., after `websocket.accept()`), the client must send a JSON object matching the `SyncBulkRequest` schema:

```json
{
  "changes": [
    {
      "type": "create",             // create | update | delete
      "entity": "expense",          // expense | group
      "entity_id": "987fcdeb-51a2-4d3c-8765-123456789abc", // UUID
      "data": {                      // Required for create/update, omitted for delete
        "group_id": "123e4567-e89b-12d3-a456-426614174000", // create expense only
        "title": "Coffee",
        "amount": 5.75,
        "payer_id": "550e8400-e29b-41d4-a716-446655440000",
        "category": "Food",         // Food | Transport | Accommodation | Entertainment | Other
        "date": "2025-08-01",
        "is_payer_included": true,
        "participants_id": ["550e8400-e29b-41d4-a716-446655440000"]
      },
      "timestamp": "2025-08-01T10:30:00Z"
    }
  ]
}
```

### Server -> Client Message Types

1. Acknowledgement (always first if validation passes):

```json
{
  "type": "ack",
  "operation_id": "2b6d8f0e-3f6a-4e9d-b7a2-4b2b9d9c1ef2",
  "status": "started",
  "created_at": "2025-08-01T10:30:01.123456+00:00"
}
```

2. Completion (success path):

```json
{
  "type": "completed",
  "operation_id": "2b6d8f0e-3f6a-4e9d-b7a2-4b2b9d9c1ef2",
  "status": "completed",
  "completed_at": "2025-08-01T10:30:02.456789+00:00",
  "notifications": [
    "expense:987fcdeb-51a2-4d3c-8765-123456789abc:created"
  ]
}
```

3. Error (validation / auth / processing error):

```json
{
  "type": "error",
  "operation_id": "2b6d8f0e-3f6a-4e9d-b7a2-4b2b9d9c1ef2",
  "status": "failed",
  "error": "Invalid token"
}
```

### Close Codes Used

| Code | Meaning |
|------|---------|
| 4401 | Missing token |
| 4403 | Invalid token |
| 4400 | Invalid payload (JSON / schema validation) |
| 1011 | Internal server error during processing |

Normal successful completion closes with the default normal closure code (1000).

### Differences vs v1

- Single persistent connection instead of separate HTTP request + polling.
- Immediate acknowledgement eliminates need for `202 Accepted` polling pattern.
- `operation_id` still provided for correlation (UUID generated server-side).
- Currently only one bulk request per connection (no streaming multiple batches yet).

### Error Handling Semantics

- Schema validation failures occur before `ack` and result in an `error` then close.
- Processing errors after `ack` produce an `error` message then close with code 1011.
- If the client disconnects early, the operation is aborted (idempotent—no partial commits guaranteed only at application layer; refer to service implementation for transactional guarantees).


---

## User Roles

### Group Roles

- **admin**: Can update group info, add/remove members, manage all expenses
- **member**: Can view group info, add expenses, edit own expenses

---

## HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `202 Accepted`: Request accepted for processing
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or invalid
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate email)
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

---
