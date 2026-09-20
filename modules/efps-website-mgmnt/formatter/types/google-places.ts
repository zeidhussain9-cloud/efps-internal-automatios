/**
 * formatter/types/google-places.ts
 *
 * PURPOSE: TypeScript type definitions for Google Places API
 */

/**
 * Google Places API place details
 */
export interface GooglePlaceDetails {
  placeId: string;
  name: string;
  address: string;
  placeType: string[];
  location: { lat: number; lng: number };
}

/**
 * Extracted location information from Google Maps
 */
export interface LocationInfo {
  placeName: string;
  locality: string;
  isSociety: boolean;
  googleMapsUrl?: string;
}
