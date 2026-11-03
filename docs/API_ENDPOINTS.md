# SailPoint Identity Security Cloud (ISC) - API Endpoint Reference

This document details all REST API endpoints utilized by the **SailPoint AD Provisioning Test Automation Framework**. It covers HTTP methods, request headers, query parameters, request body schemas, response payloads, and architectural nuances.

---

## 1. Global Request Standards

### Base URL
All requests are routed against the tenant's API host:
```text
https://<tenant>.api.identitynow.com
```

### Standard Request Headers
```http
Authorization: Bearer <OAUTH_ACCESS_TOKEN>
Content-Type: application/json
Accept: application/json
```

---

## 2. Authentication Endpoint

### `POST /oauth/token`
Obtains a short-lived OAuth 2.0 Bearer access token using Client Credentials (PAT).

* **URL**: `https://<tenant>.api.identitynow.com/oauth/token`
* **Method**: `POST`
* **Content-Type**: `application/x-www-form-urlencoded`
* **Request Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `grant_type` | `string` | Yes | Fixed value: `client_credentials` |
  | `client_id` | `string` | Yes | Personal Access Token Client ID |
  | `client_secret` | `string` | Yes | Personal Access Token Client Secret |

* **Sample Response (HTTP 200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 43199,
    "scope": "sp:scopes:default sp:scopes:all",
    "tenant_id": "eu-partner28",
    "pod": "eu-central-1"
  }
  ```

---

## 3. Identity Endpoints

### 3.1 Search Identities (`POST /v3/search`)
Performs full-text queries against SailPoint's Elasticsearch index across names, emails, and IDs.

* **URL**: `/v3/search?limit=25`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "indices": ["identities"],
    "query": {
      "query": "name:*Elijah* OR displayName:*Elijah* OR email:*Elijah* OR id:\"97894aec40784510955c1fa5817492cc\""
    }
  }
  ```
* **Sample Response (HTTP 200 OK)**:
  ```json
  [
    {
      "id": "97894aec40784510955c1fa5817492cc",
      "name": "Elijah Novak",
      "displayName": "Elijah Novak",
      "email": "elijah.novak@example.com",
      "inactive": false,
      "identityProfile": {
        "id": "9eb84d1b108d4df99aaed9b13f395eb5",
        "name": "Truist Employee Profile"
      },
      "source": {
        "id": "fc85e64ba2fa408d8edfec30348aa661",
        "name": "AD_Demo_Source"
      },
      "attributes": {
        "department": "Engineering",
        "cloudLifecycleState": "skp"
      },
      "accounts": [
        {
          "id": "824d01f92fb14b15bfafe67e8676f9e6",
          "name": "Elijah Novak",
          "sourceId": "fc85e64ba2fa408d8edfec30348aa661",
          "sourceName": "AD_Demo_Source"
        }
      ]
    }
  ]
  ```

### 3.2 Direct Live Identity Lookup (`GET /beta/identities/{id}`)
Fetches the real-time identity record directly from the transactional database, completely bypassing Elasticsearch sync lag.

* **URL**: `/beta/identities/{identity_id}`
* **Method**: `GET`
* **Sample Response (HTTP 200 OK)**:
  ```json
  {
    "id": "97894aec40784510955c1fa5817492cc",
    "name": "Elijah Novak",
    "alias": "Elijah Novak",
    "emailAddress": "elijah.novak@example.com",
    "lifecycleState": {
      "stateName": "skp",
      "manuallyUpdated": true
    },
    "identityStatus": "ACTIVE",
    "isProtected": false,
    "attributes": {
      "firstname": "Elijah",
      "lastname": "Novak",
      "department": "Engineering",
      "cloudLifecycleState": "skp",
      "cloudAuthoritativeSource": "fc85e64ba2fa408d8edfec30348aa661"
    },
    "created": "2026-11-03T13:34:28.188Z",
    "modified": "2026-11-03T21:53:18.296Z"
  }
  ```

---

## 4. Lifecycle State Engine

### `POST /v3/identities/{id}/set-lifecycle-state`
Applies an immediate lifecycle state transition to an identity. Triggers lifecycle event policies (e.g., AD account creation, disablement, entitlement revocation).

* **URL**: `/v3/identities/{identity_id}/set-lifecycle-state`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "lifecycleStateTechnicalName": "skp"
  }
  ```
* **Sample Response (HTTP 200 OK / 202 Accepted)**:
  ```json
  {
    "accountActivityId": "3942bade5f2b418eae032195886c4567"
  }
  ```
  *(Returns `accountActivityId` used to track asynchronous provisioning execution)*.

### Configured Lifecycle State Technical Names
| Technical Name | Display Name | Scenario Use Case | Target AD Outcome |
| :--- | :--- | :--- | :--- |
| `active` | Active | Scenario 1 & 2 (Create / Enable) | Create & enable AD account |
| `loa` | Leave of Absence | Scenario 6 (LOA) / Scenario 3 (Disable)| Suspend access; disable account |
| `skp` | Sabbatical (SKP) | Scenario 7 (Sabbatical - SKP) | Suspend account; retain attributes |
| `ear` | Emergency Access Removal | Scenario 8 (EAR) | Immediately disable account & revoke rights |
| `terminated` | Terminated | Scenario 5 (Employment Termination) | Deprovision/remove account & revoke all access |

---

## 5. Identity Profiles

### 5.1 List Identity Profiles (`GET /v3/identity-profiles`)
* **URL**: `/v3/identity-profiles?limit=50`
* **Method**: `GET`
* **Sample Response Item**:
  ```json
  {
    "id": "9eb84d1b108d4df99aaed9b13f395eb5",
    "name": "Truist Employee Profile",
    "authoritativeCluster": {
      "id": "fc85e64ba2fa408d8edfec30348aa661",
      "name": "AD_Demo_Source"
    },
    "identityCount": 50
  }
  ```

### 5.2 Retrieve Lifecycle States for Profile (`GET /v3/identity-profiles/{id}/lifecycle-states`)
* **URL**: `/v3/identity-profiles/{profile_id}/lifecycle-states`
* **Method**: `GET`
* **Sample Response (HTTP 200 OK)**:
  ```json
  [
    { "id": "state-01", "name": "Active", "technicalName": "active", "enabled": true },
    { "id": "state-02", "name": "SKP", "technicalName": "skp", "enabled": true },
    { "id": "state-03", "name": "EAR", "technicalName": "ear", "enabled": true },
    { "id": "state-04", "name": "LOA", "technicalName": "loa", "enabled": true },
    { "id": "state-05", "name": "Terminated", "technicalName": "terminated", "enabled": true }
  ]
  ```

---

## 6. Sources Management

### 6.1 List Sources (`GET /v3/sources`)
* **URL**: `/v3/sources?limit=50`
* **Method**: `GET`
* **Sample Response Item**:
  ```json
  {
    "id": "fc85e64ba2fa408d8edfec30348aa661",
    "name": "AD_Demo_Source",
    "type": "DelimitedFile",
    "authoritative": true,
    "connector": "delimited-file-angularsc"
  }
  ```

### 6.2 Get Source Details (`GET /v3/sources/{id}`)
* **URL**: `/v3/sources/{source_id}`
* **Method**: `GET`
* **Sample Response Item**:
  ```json
  {
    "id": "fc85e64ba2fa408d8edfec30348aa661",
    "name": "AD_Demo_Source",
    "features": ["DIRECT_PERMISSIONS", "DISCOVER_SCHEMA", "NO_RANDOM_ACCESS"]
  }
  ```

---

## 7. Account Operations

### 7.1 Filter Accounts by Identity (`GET /v3/accounts`)
* **URL**: `/v3/accounts?filters=identityId eq "{identity_id}"`
* **Method**: `GET`
* **Sample Response Item**:
  ```json
  [
    {
      "id": "8073b11a8b1a41fc926814cc43a4cb21",
      "name": "Ava Ellis",
      "nativeIdentity": "user005",
      "sourceId": "fc85e64ba2fa408d8edfec30348aa661",
      "sourceName": "AD_Demo_Source",
      "disabled": false,
      "locked": false,
      "created": "2026-11-03T13:34:14.857Z",
      "modified": "2026-11-03T13:34:14.985Z"
    }
  ]
  ```

### 7.2 Get Single Account Details (`GET /v3/accounts/{id}`)
* **URL**: `/v3/accounts/{account_id}`
* **Method**: `GET`
* **Returns**: Full representation including raw source feed attributes (`firstName`, `lastName`, `department`, `employeeStatus`, `disabled`, `lifecycleState`).

### 7.3 Enable Account (`POST /v3/accounts/{id}/enable`)
* **URL**: `/v3/accounts/{account_id}/enable`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "forceProvisioning": false
  }
  ```

### 7.4 Disable Account (`POST /v3/accounts/{id}/disable`)
* **URL**: `/v3/accounts/{account_id}/disable`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "forceProvisioning": false
  }
  ```

### 7.5 Create Account (`POST /v3/accounts`)
* **URL**: `/v3/accounts`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "sourceId": "fc85e64ba2fa408d8edfec30348aa661",
    "attributes": {
      "sAMAccountName": "elijah.novak",
      "displayName": "Elijah Novak",
      "mail": "elijah.novak@example.com"
    }
  }
  ```

---

## 8. Roles & Access Requests

### 8.1 Search Roles (`POST /v3/search`)
* **URL**: `/v3/search?limit=25`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "indices": ["roles"],
    "query": {
      "query": "name:*Analyst*"
    }
  }
  ```

### 8.2 Submit Access Request (`POST /v3/access-requests`)
* **URL**: `/v3/access-requests`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "requestedFor": ["97894aec40784510955c1fa5817492cc"],
    "requestType": "GRANT_ACCESS",
    "requestedItems": [
      {
        "type": "ROLE",
        "id": "2c91808457d1f11e0157d2a58b680124",
        "comment": "Automated AD Role Provisioning Test"
      }
    ]
  }
  ```

### 8.3 Check Access Request Status (`GET /v3/access-request-status`)
* **URL**: `/v3/access-request-status?filters=requestedFor.id eq "{identity_id}"`
* **Method**: `GET`

---

## 9. Provisioning Task Inspection

### `GET /beta/account-activities/{id}`
Inspects the asynchronous downstream provisioning engine activity created when a lifecycle state change or account update is enqueued.

* **URL**: `/beta/account-activities/{account_activity_id}`
* **Method**: `GET`
* **Sample Response (HTTP 200 OK)**:
  ```json
  {
    "id": "3942bade5f2b418eae032195886c4567",
    "name": "IdentityAttributeUpdate",
    "stage": "COMPLETED",
    "completionStatus": "SUCCESS",
    "type": "IdentityAttributeUpdate",
    "created": "2026-11-03T21:53:17.000Z",
    "modified": "2026-11-03T21:53:23.000Z",
    "sources": "AD_Demo_Source"
  }
  ```

---

## 10. Key Architecture Note: Search Index vs Core Database

```text
[POST /set-lifecycle-state]
       |
       v
+-------------------------------+
| Live Relational Database      |  <-- Synchronous update (immediately updated)
| GET /beta/identities/{id}     |  <-- Returns {'stateName': 'skp', 'manuallyUpdated': true}
+-------------------------------+
       |
       |  Asynchronous Ingestion Worker (takes 10-30 seconds)
       v
+-------------------------------+
| Elasticsearch Search Index    |  <-- Stale during first 10-30 seconds!
| POST /v3/search               |  <-- Still returned old state ('loa')
+-------------------------------+
```

**Rule enforced by framework**:
* For identity discovery across thousands of users, use `POST /v3/search`.
* For immediate post-provisioning verification, **always query `GET /beta/identities/{id}` directly** to prevent false negative test failures.

