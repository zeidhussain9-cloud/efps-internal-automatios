/**
 * formatter/types/property.ts
 *
 * PURPOSE: TypeScript type definitions for property listings
 */

/**
 * Raw property details as input by user
 */
export interface RawProperty {
  propertyDetails: string;
  googleMapsUrl?: string;
}

/**
 * Community classification, sourced from Google Places data.
 */
export type CommunityType = "Gated" | "Semi-gated";

/**
 * Fields extracted deterministically (via regex/heuristics) from the raw
 * pasted text. Every field is optional: the parser never invents a value —
 * a field that isn't confidently detected is left undefined and rendered
 * blank in the final template.
 */
export interface ParsedProperty {
  propertyType?: "Apartment" | "Villa" | "Independent House";
  bhk?: string;
  bathrooms?: string;
  balcony?: string;
  furnishing?: "Unfurnished" | "Semi-furnished" | "Fully Furnished";
  rent?: string;
  maintenance?: string;
  deposit?: string;
  sqft?: string;
  floor?: string;
  floorTotal?: string;
  availableFrom?: string;
  preferredTenant?: string;
  pets?: "Allowed" | "Not allowed";
  societyName?: string;
  locality?: string;
  googleMapsUrl?: string;
  communityType?: CommunityType;
}

/**
 * Final formatted property listing ready for output
 */
export interface FormattedProperty {
  title: string;
  rent: string;
  maintenance: string;
  deposit: string;
  sqft: string;
  floor: string;
  availableFrom: string;
  preferredTenant: string;
  pets: string;
  community: CommunityType;
  location: string;
  societyName?: string;
  googleMapsUrl?: string;
}

/**
 * Complete formatter output
 */
export interface FormatterOutput {
  success: boolean;
  formatted?: string;
  data?: FormattedProperty;
  errors?: string[];
  timestamp: string;
}
