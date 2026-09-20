/**
 * formatter/services/communityDetector.ts
 *
 * PURPOSE: Community classification for the EasyFind Formatter
 *
 * RESPONSIBILITY:
 * - Determine if a property is in a Gated or Semi-gated community
 * - Use Google Places data as the primary source
 * - Apply business rules from EasyFind SOP
 */

/**
 * Keywords that indicate a gated/organised residential society.
 * Matched case-insensitively against the resolved place name.
 */
const GATED_KEYWORDS = [
  // Generic society words
  "apartment", "apartments",
  "society", "societies",
  "complex",
  "residency", "residences", "residence",
  "residential",
  // Common suffix words in Indian society names
  "heights",
  "gardens", "garden",
  "villas", "villa",
  "enclave",
  "estates", "estate",
  "habitat",
  "square",
  "park",
  "arcade",
  "tower", "towers",
  "terrace", "terraces",
  "meadows",
  "greens",
  "woods",
  "grove",
  "layout",
  "nagar",          // planned colonies
  "county",
  "county",
  "avenue",
  "panorama",
  "pride",
  "prestige",
  "brigade",
  "sobha",
  "purva",
  "godrej",
  "tata",
  "lodha",
  "mantri",
  "salarpuria",
];

/**
 * Google Places `types` values that indicate a gated premise.
 */
const GATED_PLACE_TYPES = [
  "premise",
  "neighborhood",
  "sublocality_level_1",
  "establishment",
];

/**
 * Detects community type based on Google Places data.
 *
 * Gated  → place name or type signals an organised residential society
 * Semi-gated → everything else (independent house on a street, etc.)
 */
export function detectCommunityType(placeName: string, placeType: string): "Gated" | "Semi-gated" {
  const name = (placeName ?? "").toLowerCase();
  const type = (placeType ?? "").toLowerCase();

  const isGated =
    GATED_KEYWORDS.some((kw) => name.includes(kw)) ||
    GATED_PLACE_TYPES.some((t) => type.includes(t));

  return isGated ? "Gated" : "Semi-gated";
}

/**
 * Returns true when the resolved place name looks like a residential society
 * (as opposed to a landmark, road, or neighbourhood name).
 * Used to decide whether to show the society name in the listing footer.
 */
export function isSocietyName(placeName: string): boolean {
  if (!placeName || placeName === "Landmark") return false;
  const name = placeName.toLowerCase();
  return GATED_KEYWORDS.some((kw) => name.includes(kw));
}
