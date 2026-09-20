/**
 * formatter/utils/constants.ts
 *
 * PURPOSE: Application constants and configuration values
 *
 * RESPONSIBILITY:
 * - Define furnishing options
 * - Define tenant preferences
 * - Define pet policies
 * - Define formatting patterns
 * - Define error messages
 */

// Furnishing options (standardized)
export const FURNISHING_OPTIONS = {
  UNFURNISHED: "Unfurnished",
  SEMI_FURNISHED: "Semi-furnished",
  FULLY_FURNISHED: "Fully Furnished",
} as const;

// Tenant preferences
export const TENANT_PREFERENCES = {
  ANYONE: "Anyone",
  FAMILY: "Family",
  BACHELOR: "Bachelor",
} as const;

// Pet policies
export const PET_POLICIES = {
  ALLOWED: "Allowed",
  NOT_ALLOWED: "Not allowed",
} as const;

// Community types
export const COMMUNITY_TYPES = {
  GATED: "Gated",
  SEMI_GATED: "Semi-gated",
} as const;

// TODO: Add more constants as needed
// - Currency symbols
// - Number formatting patterns
// - Error codes
// - API endpoints
// - Timeout values
