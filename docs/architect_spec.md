## JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FlashSoft Architect Plan",
  "type": "object",
  "additionalProperties": false,
  "required": ["metadata", "components"],
  "properties": {
    "metadata": {
      "type": "object",
      "additionalProperties": false,
      "required": ["spec", "created_at", "architect"],
      "properties": {
        "spec": { "type": "string", "minLength": 1 },
        "created_at": { "type": "string", "format": "date-time" },
        "architect": { "type": "string", "minLength": 1 },
        "version": { "type": "string", "minLength": 1 },
        "assumptions": {
          "type": "array",
          "items": { "type": "string", "minLength": 1 }
        }
      }
    },
    "components": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/definitions/component"
      }
    },
    "notes": {
      "type": "string"
    }
  },
  "definitions": {
    "component": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "id",
        "description",
        "responsibilities",
        "dependencies",
        "files",
        "acceptance_tests"
      ],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^[a-z0-9_\\-]+$",
          "minLength": 1
        },
        "description": { "type": "string", "minLength": 1 },
        "responsibilities": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string", "minLength": 1 }
        },
        "dependencies": {
          "type": "array",
          "items": { "type": "string", "minLength": 1 },
          "uniqueItems": true,
          "default": []
        },
        "files": {
          "type": "array",
          "minItems": 1,
          "items": {
            "$ref": "#/definitions/fileDescriptor"
          }
        },
        "acceptance_tests": {
          "type": "array",
          "minItems": 1,
          "items": {
            "$ref": "#/definitions/acceptanceTest"
          }
        }
      }
    },
    "fileDescriptor": {
      "type": "object",
      "additionalProperties": false,
      "required": ["path", "description"],
      "properties": {
        "path": {
          "type": "string",
          "pattern": "^[^\\0]+$",
          "minLength": 1
        },
        "description": { "type": "string", "minLength": 1 },
        "type": {
          "type": "string",
          "enum": ["code", "config", "test", "doc", "asset", "script", "other"]
        },
        "generated": { "type": "boolean" }
      }
    },
    "acceptanceTest": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "description", "success_criteria"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^[a-z0-9_\\-]+$",
          "minLength": 1
        },
        "description": { "type": "string", "minLength": 1 },
        "target_files": {
          "type": "array",
          "items": { "type": "string", "minLength": 1 },
          "uniqueItems": true
        },
        "success_criteria": { "type": "string", "minLength": 1 }
      }
    }