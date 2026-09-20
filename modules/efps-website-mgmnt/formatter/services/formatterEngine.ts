/**
 * formatter/services/formatterEngine.ts
 *
 * Core orchestration for the EasyFind formatter.
 */

import { validateInput } from "./validator";
import { sanitizeInput } from "./sanitizer";
import { resolveGoogleMapsLocation } from "./googlePlaces";
import { detectCommunityType, isSocietyName } from "./communityDetector";
import { parseProperty } from "./propertyParser";
import { formatWithTemplate } from "./templateFormatter";
import { ParsedProperty } from "../types/property";

export type FormatterInput = {
  propertyDetails: string;
  googleMapsUrl?: string;
};

export type ResolvedPlaceInfo = {
  placeName?: string;
  locality?: string;
  placeType?: string;
  community?: string;
  googleMapsUrl?: string;
};

export type FormatterResult = {
  success: boolean;
  formattedText?: string;
  errors?: string[];
  resolvedPlace?: ResolvedPlaceInfo | null;
};

/**
 * Orchestrates the complete property formatting pipeline
 */
export async function formatProperty(input: FormatterInput): Promise<FormatterResult> {
  try {
    // 1. Validate Input
    const validation = validateInput(input.propertyDetails, input.googleMapsUrl);
    if (!validation.isValid) {
      return { success: false, errors: validation.errors };
    }

    // 2. Sanitize Input
    const sanitizedDetails = sanitizeInput(input.propertyDetails);

    // 3. Parse property fields deterministically from the raw text
    const parsed: ParsedProperty = parseProperty(sanitizedDetails);

    // 4. Resolve Google Maps (if provided) — authoritative source for
    //    society name, locality, and community type
    let resolvedPlace = null;
    let community: "Gated" | "Semi-gated" = "Semi-gated";
    if (input.googleMapsUrl) {
      resolvedPlace = await resolveGoogleMapsLocation(input.googleMapsUrl);
      community = detectCommunityType(resolvedPlace.placeName, resolvedPlace.placeType);
      parsed.locality = resolvedPlace.locality !== "Unknown" ? resolvedPlace.locality : undefined;
      parsed.societyName = isSocietyName(resolvedPlace.placeName)
        ? resolvedPlace.placeName
        : undefined;
    }
    parsed.communityType = community;
    parsed.googleMapsUrl = input.googleMapsUrl;

    // 5. Template Formatting (deterministic, no AI)
    const formattedText = formatWithTemplate(parsed);

    return {
      success: true,
      formattedText,
      resolvedPlace: {
        ...resolvedPlace,
        community,
        googleMapsUrl: input.googleMapsUrl,
      },
    };
  } catch (error: unknown) {
    console.error("Formatter Engine Error:", error);
    return {
      success: false,
      errors: [
        error instanceof Error ? error.message : "An unexpected error occurred during formatting",
      ],
    };
  }
}

/**
 * Validates if the output is a non-empty string
 */
export function validateFormattedOutput(output: string): boolean {
  return typeof output === "string" && output.trim().length > 0;
}
