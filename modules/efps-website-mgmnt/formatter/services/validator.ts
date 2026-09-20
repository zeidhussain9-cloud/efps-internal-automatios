/**
 * formatter/services/validator.ts
 *
 * PURPOSE: Input validation for the EasyFind Formatter
 *
 * RESPONSIBILITY:
 * - Validate empty input
 * - Validate Google Maps URL format
 * - Check for missing property details
 */

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

/**
 * Validates the formatter input
 */
export function validateInput(propertyDetails: string, googleMapsUrl?: string): ValidationResult {
  const errors: string[] = [];

  // 1. Validate empty input
  if (!propertyDetails || propertyDetails.trim().length === 0) {
    errors.push("Property details cannot be empty");
  }

  // 2. Validate Google Maps URL if provided
  if (googleMapsUrl && !isValidGoogleMapsUrl(googleMapsUrl)) {
    errors.push("Invalid Google Maps URL");
  }

  // 3. Check for missing property details (basic heuristic)
  if (propertyDetails && propertyDetails.trim().length < 10) {
    errors.push("Property details are too short to be valid");
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validates BHK value
 */
export function validateBHK(bhk: string): { valid: boolean; error?: string } {
  const bhkNum = parseFloat(bhk);
  if (isNaN(bhkNum) || bhkNum <= 0 || bhkNum > 10) {
    return { valid: false, error: "Invalid BHK value" };
  }
  return { valid: true };
}

/**
 * Validates monetary amount
 */
export function validateAmount(amount: string): { valid: boolean; error?: string } {
  const cleanAmount = amount.replace(/[₹,kL\s]/gi, "");
  const num = parseFloat(cleanAmount);
  if (isNaN(num) || num < 0) {
    return { valid: false, error: "Invalid amount" };
  }
  return { valid: true };
}

/**
 * Validates furnishing status
 */
export function validateFurnishing(furnishing: string): { valid: boolean; error?: string } {
  const validStatuses = ["unfurnished", "semi-furnished", "fully furnished"];
  if (!validStatuses.includes(furnishing.toLowerCase())) {
    return { valid: false, error: "Invalid furnishing status" };
  }
  return { valid: true };
}

/**
 * Validates floor information
 */
export function validateFloor(floor: string): { valid: boolean; error?: string } {
  if (!floor || floor.trim().length === 0) {
    return { valid: false, error: "Floor information is missing" };
  }
  return { valid: true };
}

/**
 * Internal helper to validate Google Maps URL
 */
function isValidGoogleMapsUrl(url: string): boolean {
  try {
    const parsedUrl = new URL(url);
    const validHosts = ["maps.google.com", "www.google.com", "goo.gl", "maps.app.goo.gl"];
    return validHosts.some((host) => parsedUrl.hostname.includes(host));
  } catch {
    return false;
  }
}
