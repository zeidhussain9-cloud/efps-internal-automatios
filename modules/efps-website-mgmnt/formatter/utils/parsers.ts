/**
 * formatter/utils/parsers.ts
 *
 * PURPOSE: Utility functions for parsing values
 */

import { parseMonetary } from "../services/propertyParser";

/**
 * Parse INR amount from string
 *
 * EXAMPLES:
 * "₹40k" → 40000
 * "₹1.2L" → 120000
 * "40000" → 40000
 */
export function parseINR(str: string): number {
  const result = parseMonetary(str);
  if (result === undefined) throw new Error(`Could not parse INR value: "${str}"`);
  return result;
}

/**
 * Parse BHK from string
 *
 * EXAMPLES:
 * "2BHK" → 2
 * "2 BHK" → 2
 * "2" → 2
 */
export function parseBHK(str: string): number {
  const match = str.match(/(\d+(?:\.\d+)?)\s*(?:BHK)?/i);
  if (!match) throw new Error(`Could not parse BHK value: "${str}"`);
  return parseFloat(match[1]);
}

/**
 * Extract Google Maps URL from text
 */
export function extractGoogleMapsUrl(text: string): string | null {
  const mapsUrlRegex =
    /https?:\/\/(?:www\.)?(?:google\.com\/maps|goo\.gl\/maps|maps\.app\.goo\.gl)\/\S+/;
  const match = text.match(mapsUrlRegex);
  return match ? match[0] : null;
}
