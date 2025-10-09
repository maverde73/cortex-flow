# Built-in Libraries Reference

Cortex-Flow includes several built-in libraries ready to use in your workflows.

## Table of Contents

1. [REST API Library](#rest-api-library)
2. [Filesystem Library](#filesystem-library)
3. [Future Libraries](#future-libraries)

---

## REST API Library

**Location**: `libraries/rest_api/`
**Capabilities Required**: `network_access`

### Functions

#### `http_get`

Make an HTTP GET request.

**Parameters:**
- `url` (string, required): URL to request
- `headers` (dict, optional): Request headers
- `params` (dict, optional): Query parameters
- `timeout` (integer, optional): Request timeout in seconds (default: 30)

**Example:**
```json
{
  "agent": "library",
  "library_name": "rest_api",
  "function_name": "http_get",
  "function_params": {
    "url": "https://api.github.com/repos/cortex-flow/cortex-flow",
    "headers": {
      "Accept": "application/vnd.github.v3+json"
    }
  }
}
```

#### `http_post`

Make an HTTP POST request.

**Parameters:**
- `url` (string, required): URL to request
- `json_data` (dict, optional): JSON data to send
- `data` (dict, optional): Form data to send
- `headers` (dict, optional): Request headers
- `timeout` (integer, optional): Request timeout in seconds (default: 30)

**Example:**
```json
{
  "agent": "library",
  "library_name": "rest_api",
  "function_name": "http_post",
  "function_params": {
    "url": "https://api.example.com/webhook",
    "json_data": {
      "event": "workflow_complete",
      "status": "success"
    },
    "headers": {
      "X-API-Key": "secret-key"
    }
  }
}
```

#### `http_put`

Make an HTTP PUT request.

**Parameters:**
- `url` (string, required): URL to request
- `json_data` (dict, optional): JSON data to send
- `data` (dict, optional): Form data to send
- `headers` (dict, optional): Request headers
- `timeout` (integer, optional): Request timeout in seconds (default: 30)

**Example:**
```json
{
  "agent": "library",
  "library_name": "rest_api",
  "function_name": "http_put",
  "function_params": {
    "url": "https://api.example.com/resource/123",
    "json_data": {
      "name": "Updated Name",
      "status": "active"
    }
  }
}
```

#### `http_delete`

Make an HTTP DELETE request.

**Parameters:**
- `url` (string, required): URL to request
- `headers` (dict, optional): Request headers
- `timeout` (integer, optional): Request timeout in seconds (default: 30)

**Example:**
```json
{
  "agent": "library",
  "library_name": "rest_api",
  "function_name": "http_delete",
  "function_params": {
    "url": "https://api.example.com/resource/123",
    "headers": {
      "Authorization": "Bearer token123"
    }
  }
}
```

#### `http_request`

Make a generic HTTP request with any method.

**Parameters:**
- `method` (string, required): HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)
- `url` (string, required): URL to request
- `json_data` (dict, optional): JSON data to send
- `data` (dict, optional): Form data to send
- `headers` (dict, optional): Request headers
- `params` (dict, optional): Query parameters
- `timeout` (integer, optional): Request timeout in seconds (default: 30)

**Example:**
```json
{
  "agent": "library",
  "library_name": "rest_api",
  "function_name": "http_request",
  "function_params": {
    "method": "PATCH",
    "url": "https://api.example.com/resource/123",
    "json_data": {
      "field": "new_value"
    }
  }
}
```

---

## Filesystem Library

**Location**: `libraries/filesystem/`
**Capabilities Required**: `filesystem_read`, `filesystem_write`

### Configuration

Default allowed paths:
- `/tmp`
- `./data`
- `./output`

Maximum file size: 10MB

### Functions

#### `read_file`

Read contents of a text file.

**Parameters:**
- `path` (string, required): Path to the file
- `encoding` (string, optional): File encoding (default: "utf-8")

**Example:**
```json
{
  "agent": "library",
  "library_name": "filesystem",
  "function_name": "read_file",
  "function_params": {
    "path": "./data/config.txt"
  }
}
```

#### `write_file`

Write content to a text file.

**Parameters:**
- `path` (string, required): Path to the file
- `content` (string, required): Content to write
- `encoding` (string, optional): File encoding (default: "utf-8")
- `append` (boolean, optional): Append to existing file (default: false)

**Example:**
```json
{
  "agent": "library",
  "library_name": "filesystem",
  "function_name": "write_file",
  "function_params": {
    "path": "./output/report.txt",
    "content": "Analysis complete: {analysis_output}",
    "append": false
  }
}
```

#### `list_files`

List files in a directory.

**Parameters:**
- `path` (string, required): Directory path
- `pattern` (string, optional): File pattern to match (default: "*")
- `recursive` (boolean, optional): Search recursively (default: false)

**Example:**
```json
{
  "agent": "library",
  "library_name": "filesystem",
  "function_name": "list_files",
  "function_params": {
    "path": "./data",
    "pattern": "*.json",
    "recursive": true
  }
}
```

#### `file_exists`

Check if a file exists.

**Parameters:**
- `path` (string, required): Path to check

**Example:**
```json
{
  "agent": "library",
  "library_name": "filesystem",
  "function_name": "file_exists",
  "function_params": {
    "path": "./data/input.csv"
  }
}
```

#### `delete_file`

Delete a file.

**Parameters:**
- `path` (string, required): Path to the file to delete

**Example:**
```json
{
  "agent": "library",
  "library_name": "filesystem",
  "function_name": "delete_file",
  "function_params": {
    "path": "./tmp/temporary_file.txt"
  }
}
```

#### `create_directory`

Create a directory.

**Parameters:**
- `path` (string, required): Directory path to create
- `parents` (boolean, optional): Create parent directories if needed (default: true)

**Example:**
```json
{
  "agent": "library",
  "library_name": "filesystem",
  "function_name": "create_directory",
  "function_params": {
    "path": "./output/reports/2024",
    "parents": true
  }
}
```

#### `read_json`

Read and parse a JSON file.

**Parameters:**
- `path` (string, required): Path to the JSON file

**Example:**
```json
{
  "agent": "library",
  "library_name": "filesystem",
  "function_name": "read_json",
  "function_params": {
    "path": "./data/config.json"
  }
}
```

#### `write_json`

Write data to a JSON file.

**Parameters:**
- `path` (string, required): Path to the JSON file
- `data` (any, required): Data to write as JSON
- `indent` (integer, optional): JSON indentation (default: 2)

**Example:**
```json
{
  "agent": "library",
  "library_name": "filesystem",
  "function_name": "write_json",
  "function_params": {
    "path": "./output/results.json",
    "data": {
      "status": "complete",
      "results": "{analysis_output}"
    },
    "indent": 2
  }
}
```

---

## Future Libraries

These libraries are planned for future releases:

### Email Library

Send email notifications from workflows.

**Planned Functions:**
- `send_email`: Send plain text or HTML emails
- `send_with_attachment`: Send emails with file attachments
- `send_bulk`: Send emails to multiple recipients

### Database Library

Connect to and query databases.

**Planned Functions:**
- `query`: Execute SQL queries
- `insert`: Insert records
- `update`: Update records
- `delete`: Delete records
- `transaction`: Execute transactions

### Cloud Storage Library

Interact with cloud storage services.

**Planned Functions:**
- `upload_to_s3`: Upload files to AWS S3
- `download_from_s3`: Download files from AWS S3
- `upload_to_gcs`: Upload files to Google Cloud Storage
- `download_from_gcs`: Download files from Google Cloud Storage

### Social Media Library

Post to social media platforms.

**Planned Functions:**
- `post_to_twitter`: Post tweets
- `post_to_linkedin`: Post to LinkedIn
- `post_to_slack`: Send Slack messages

### Data Processing Library

Common data processing operations.

**Planned Functions:**
- `csv_to_json`: Convert CSV to JSON
- `json_to_csv`: Convert JSON to CSV
- `transform_data`: Apply transformations
- `validate_schema`: Validate data against schema

## Creating Custom Libraries

To add your own libraries, see [Creating Libraries](creating-libraries.md).

## Complete Workflow Example

Here's a workflow that uses multiple built-in libraries:

```json
{
  "name": "api_to_file_workflow",
  "description": "Fetch data from API and save to file",
  "nodes": [
    {
      "id": "check_existing",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "file_exists",
      "function_params": {
        "path": "./data/cache.json"
      }
    },
    {
      "id": "fetch_fresh",
      "agent": "library",
      "library_name": "rest_api",
      "function_name": "http_get",
      "function_params": {
        "url": "https://api.example.com/data",
        "headers": {
          "Accept": "application/json"
        }
      }
    },
    {
      "id": "save_data",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "write_json",
      "function_params": {
        "path": "./data/cache.json",
        "data": "{fetch_fresh_output}"
      },
      "depends_on": ["fetch_fresh"]
    },
    {
      "id": "create_report_dir",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "create_directory",
      "function_params": {
        "path": "./reports/{timestamp}"
      },
      "depends_on": ["save_data"]
    },
    {
      "id": "analyze",
      "agent": "analyst",
      "instruction": "Analyze this data: {fetch_fresh_output}",
      "depends_on": ["fetch_fresh"]
    },
    {
      "id": "save_analysis",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "write_file",
      "function_params": {
        "path": "./reports/{timestamp}/analysis.md",
        "content": "{analyze_output}"
      },
      "depends_on": ["create_report_dir", "analyze"]
    }
  ],
  "conditional_edges": [
    {
      "from_node": "check_existing",
      "conditions": [
        {
          "field": "node_outputs.check_existing",
          "operator": "equals",
          "value": "true",
          "next_node": "END"
        }
      ],
      "default": "fetch_fresh"
    }
  ],
  "parameters": {
    "timestamp": "2024_01_15_1430"
  }
}
```

## Next Steps

- [Using libraries in workflows](using-in-workflows.md)
- [Creating custom libraries](creating-libraries.md)
- [API Reference](api-reference.md)