/**
 * formatter/api/validators.ts
 *
 * PURPOSE: Request validation for the API layer
 */

import { FormatterRequest } from "../types/api";

/**
 * Validate formatter request payload
 */
export function validateFormatterRequest(payload: unknown): {
  valid: boolean;
  errors?: string[];
} {
  const errors: string[] = [];

  if (!payload || typeof payload !== "object") {
    return { valid: false, errors: ["Invalid request payload"] };
  }

  const request = payload as Partial<FormatterRequest>;

  // 1. Validate propertyDetails
  if (!request.propertyDetails || typeof request.propertyDetails !== "string") {
    errors.push("propertyDetails is required and must be a string");
  } else if (request.propertyDetails.trim().length === 0) {
    errors.push("propertyDetails cannot be empty");
  }

  // 2. Validate googleMapsUrl if provided
  if (request.googleMapsUrl !== undefined) {
    if (typeof request.googleMapsUrl !== "string") {
      errors.push("googleMapsUrl must be a string");
    } else if (request.googleMapsUrl.trim().length > 0 && !isValidUrl(request.googleMapsUrl)) {
      errors.push("googleMapsUrl must be a valid URL");
    }
  }

  return {
    valid: errors.length === 0,
    errors: errors.length > 0 ? errors : undefined,
  };
}

/**
 * Internal helper to validate URL
 */
function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}
