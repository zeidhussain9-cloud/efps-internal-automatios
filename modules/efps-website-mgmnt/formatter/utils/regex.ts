/**
 * formatter/utils/regex.ts
 *
 * PURPOSE: Regular expressions for parsing and validation
 *
 * RESPONSIBILITY:
 * - Define regex patterns for common formats
 * - Provide reusable patterns
 * - Enable consistent parsing
 */

// Pattern for BHK extraction
// Matches: "2BHK", "2 BHK", "2-BHK", "2"
export const BHK_PATTERN = /^(\d+)\s*-?\s*BHK$/i;

// Pattern for INR amount extraction
// Matches: "40000", "₹40000", "₹40k", "₹1.2L"
export const INR_PATTERN = /^₹?([0-9.,kKlL]+)$/;

// Pattern for Google Maps URL
// Matches: https://maps.google.com/..., https://goo.gl/maps/...
export const GOOGLE_MAPS_URL_PATTERN =
  /https?:\/\/(maps\.google\.com|goo\.gl|maps\.app\.goo\.gl)\/[^\s]+/i;

// Pattern for floor format
// Matches: "4/4", "2/10", "G", "1"
export const FLOOR_PATTERN = /^([0-9]+|[GG]|[Gg]round)\/?([0-9]+)?$/;

// TODO: Add more regex patterns as needed
// - Phone number pattern
// - Email pattern
// - Locality pattern
// - Society name pattern
