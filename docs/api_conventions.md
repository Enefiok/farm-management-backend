# API Conventions

This document defines the standard conventions for all API endpoints in the Farm Management Platform. Both frontend and backend developers must adhere to these rules to ensure consistency, data integrity, and seamless integration.

## 1. General Rules
- **Format:** All requests and responses must be `application/json` (except file uploads).
- **Naming:** JSON keys must use `snake_case` to match Django/Python conventions (e.g., `event_date`, `unit_price`).
- **Character Encoding:** UTF-8.

## 2. Data Types & Serialization (Critical)
- **Money and Quantities:** All `Decimal` fields (prices, totals, quantities) **must be serialized as strings** (e.g., `"15000.00"`, `"93.50"`). This prevents JavaScript floating-point precision loss.
- **Dates and Times:** 
  - `event_date`: The date the farm activity actually occurred (user-chosen). Format: `YYYY-MM-DD`.
  - `entry_timestamp`: The exact moment the system received the record (system-set, read-only). Format: ISO 8601 (e.g., `2026-10-14T16:00:00Z`).
- **Booleans:** Standard JSON `true` or `false`.

## 3. Standard Error Response Format
All validation and business logic errors must follow this exact structure. The backend `custom_exception_handler` enforces this.

**Validation Error Example:**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Please correct the highlighted fields.",
    "fields": {
      "quantity": ["Quantity must be greater than zero."],
      "event_date": ["This field is required."]
    }
  }
}