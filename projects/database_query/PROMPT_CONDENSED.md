# Database Query Tool - Quick Reference

## JSON API Format (PostgreSQL)

### Basic Structure
```json
{
  "table": "table_name",
  "select": ["field1", "field2"]  // or "*"
}
```

## Essential Tables

**employees**: `id`, `first_name`, `last_name`, `email`, `department_id`, `position`, `manager_id`, `is_active`
**departments**: `id`, `department_name`, `department_code`, `manager_id`, `is_active`
**projects**: `id`, `project_name`, `client_name`, `start_date`, `end_date`, `budget`, `status`, `pm_id`
**project_assignments**: `id`, `project_id`, `employee_id`, `role_in_project`, `allocation_percentage`, `is_active`
**certifications**: `id`, `name`, `category`, `level`, `provider`, `is_active`
**employee_certifications**: `id`, `employee_id`, `certification_id`, `certification_name`, `issue_date`, `expiry_date`, `is_active`
**assessments**: `id`, `employee_id`, `assessment_date`, `overall_score`, `technical_score`, `soft_skills_score`, `status`
**skills**: `id`, `Skill`, `is_active`
**employee_skills**: `id`, `employee_id`, `skill_id`, `proficiency_level`, `years_experience`

## Foreign Keys
- employees.department_id → departments.id
- employees.manager_id → employees.id
- employee_certifications.employee_id → employees.id
- employee_certifications.certification_id → certifications.id
- project_assignments.project_id → projects.id
- project_assignments.employee_id → employees.id
- projects.pm_id → employees.id

## Enums
- **CertificationCategory**: "CLOUD", "PROJECT", "SECURITY", "DEVELOPMENT", "DATABASE", "BUSINESS", "CUSTOM"
- **CertificationLevel**: "FOUNDATION", "ASSOCIATE", "PROFESSIONAL", "EXPERT"

## Common Operations

**Filters**:
- `"where": {"field": "value"}` - equality
- `"where": {"field": {"operator": ">", "value": 100}}` - comparison
- `"whereIn": {"field": ["val1", "val2"]}` - IN clause
- `"whereLike": {"field": "pattern%"}` - pattern match
- `"whereNull": ["field"]` - NULL check

**Joins**:
```json
"join": [{
  "table": "other_table",
  "first": "table1.column",
  "second": "table2.column"
}]
```

**Aggregations**:
- `"count": "*"` or `"count": {"alias": "field"}`
- `"sum": "field"`, `"avg": "field"`, `"min": "field"`, `"max": "field"`
- `"groupBy": "field"` or `"groupBy": ["field1", "field2"]`

**Ordering & Limits**:
- `"orderBy": "field"` or `"orderBy": ["field", "desc"]`
- `"limit": 10`, `"offset": 20`

## Examples

### 1. Simple SELECT
Query: "List all active employees"
```json
{
  "table": "employees",
  "select": ["id", "first_name", "last_name", "email"],
  "where": {"is_active": true}
}
```

### 2. JOIN
Query: "Employees with their departments"
```json
{
  "table": "employees",
  "select": ["employees.first_name", "employees.last_name", "departments.department_name"],
  "join": [{
    "table": "departments",
    "first": "employees.department_id",
    "second": "departments.id"
  }],
  "where": {"employees.is_active": true}
}
```

### 3. Aggregation
Query: "Count employees per department"
```json
{
  "table": "employees",
  "select": ["department_id"],
  "count": {"employee_count": "*"},
  "groupBy": "department_id",
  "where": {"is_active": true}
}
```

### 4. Certifications
Query: "Employees with AWS certifications"
```json
{
  "table": "employee_certifications",
  "select": ["employees.first_name", "employees.last_name", "employee_certifications.certification_name", "employee_certifications.expiry_date"],
  "join": [{
    "table": "employees",
    "first": "employee_certifications.employee_id",
    "second": "employees.id"
  }],
  "whereLike": {"certification_name": "AWS%"},
  "where": {"employee_certifications.is_active": true}
}
```

### 5. Projects
Query: "Active projects with budgets over 100k"
```json
{
  "table": "projects",
  "select": ["project_name", "client_name", "budget", "status"],
  "where": {
    "is_active": true,
    "budget": {"operator": ">", "value": 100000}
  },
  "orderBy": ["budget", "desc"]
}
```

## Important Rules

1. **Exact names**: Use table/column names exactly as shown above
2. **Valid joins**: Only join tables with FK relationships
3. **PostgreSQL only**: Use PostgreSQL syntax and functions
4. **SELECT only**: No INSERT/UPDATE/DELETE operations
5. **Enum values**: Must match exactly (case-sensitive)

## Common Errors to Avoid

❌ Wrong table name: `"employes"` → ✅ `"employees"`
❌ Wrong column: `"dept"` → ✅ `"department_id"`
❌ Missing join: Referencing columns from unjoined tables
❌ Invalid enum: `"cloud"` → ✅ `"CLOUD"` (uppercase)
❌ Wrong FK: Joining unrelated tables

## Full Documentation
For complete schema and advanced features, see: `/home/mverde/src/taal/json_api/PROMPT.md`
