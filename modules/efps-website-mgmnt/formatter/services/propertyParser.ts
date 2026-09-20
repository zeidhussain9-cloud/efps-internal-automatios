/**
 * formatter/services/propertyParser.ts
 *
 * PURPOSE: Deterministic (regex/heuristic based) extraction of property
 * fields from raw, freeform pasted text (WhatsApp messages, MagicBricks /
 * Housing.com listings, broker notes, etc).
 *
 * RESPONSIBILITY:
 * - Never invent values. A field that isn't confidently detected in the
 *   text is left `undefined` so the template formatter can render it blank.
 * - Feed the standardizer for consistent display formatting (currency,
 *   furnishing labels, etc).
 */

import { ParsedProperty } from "../types/property";
import { standardizeFurnishing, formatMonetaryValue, standardizeBathrooms } from "./standardizer";

/**
 * Converts a raw captured money string ("40k", "1.7L", "40,000", "170000")
 * into a plain rupee amount, so it can be re-formatted consistently.
 */
function parseMoneyToNumber(raw: string): number | null {
  const cleaned = raw.trim().toLowerCase().replace(/,/g, "");
  const match = cleaned.match(/^(\d+(?:\.\d+)?)\s*(k|l|lakh|lakhs|thousand)?$/);
  if (!match) return null;

  const value = parseFloat(match[1]);
  if (isNaN(value)) return null;

  const unit = match[2];
  if (unit === "k" || unit === "thousand") return value * 1000;
  if (unit === "l" || unit === "lakh" || unit === "lakhs") return value * 100000;
  return value;
}

/**
 * Extracts a labelled monetary value (e.g. "Rent : 40k", "rent Rs.40,000")
 */
function extractMoney(text: string, labels: string[]): string | undefined {
  for (const label of labels) {
    const regex = new RegExp(
      `${label}\\s*[:\\-]?\\s*(?:rs\\.?|inr|₹)?\\s*(\\d[\\d,]*(?:\\.\\d+)?\\s*(?:k|l|lakhs?|thousand)?)`,
      "i",
    );
    const match = text.match(regex);
    if (match) {
      const value = parseMoneyToNumber(match[1]);
      if (value !== null) return formatMonetaryValue(value);
    }
  }
  return undefined;
}

function extractBHK(text: string): string | undefined {
  const match = text.match(/(\d+(?:\.\d+)?)\s*-?\s*bhk/i);
  return match ? `${match[1]} BHK` : undefined;
}

function extractBathrooms(text: string): string | undefined {
  const match = text.match(/(\d+)\s*(?:bathrooms?|toilets?|washrooms?|baths?)\b/i);
  return match ? standardizeBathrooms(match[1]) : undefined;
}

function extractBalcony(text: string): string | undefined {
  const match = text.match(/(\d+)\s*balcon(?:y|ies)/i);
  if (!match) return undefined;
  const num = parseInt(match[1], 10);
  return `${num} balcon${num > 1 ? "ies" : "y"}`;
}

function extractFurnishing(text: string): ParsedProperty["furnishing"] | undefined {
  if (/semi[\s-]?furnished/i.test(text))
    return standardizeFurnishing("semi") as ParsedProperty["furnishing"];
  if (/(?:fully|full)[\s-]?furnished/i.test(text))
    return standardizeFurnishing("fully") as ParsedProperty["furnishing"];
  if (/\bunfurnished\b|\bun-furnished\b|\bbare\s*shell\b/i.test(text))
    return standardizeFurnishing("un") as ParsedProperty["furnishing"];
  return undefined;
}

function extractSqft(text: string): string | undefined {
  // Use [^\S\r\n]* (horizontal whitespace only) so a number on the previous
  // line (e.g. maintenance: 2500) is never mistaken for sqft.
  const match = text.match(/(\d{3,6})[^\S\r\n]*(?:sq\.?[^\S\r\n]?ft\.?|sqft|square[^\S\r\n]*feet|sft)\b/i);
  return match ? match[1] : undefined;
}

function extractFloor(text: string): { floor?: string; floorTotal?: string } {
  // "floor" or common abbreviation "flr"
  const F = "(?:floor|flr)";

  const withTotal = text.match(new RegExp(`(\\d+)(?:st|nd|rd|th)?\\s*${F}\\s*(?:\\/|of|out\\s*of)\\s*(\\d+)`, "i"));
  if (withTotal) return { floor: withTotal[1], floorTotal: withTotal[2] };

  const slashForm = text.match(new RegExp(`${F}\\s*[:\\-]?\\s*(\\d+)\\s*\\/\\s*(\\d+)`, "i"));
  if (slashForm) return { floor: slashForm[1], floorTotal: slashForm[2] };

  const floorOnly = text.match(new RegExp(`(\\d+)(?:st|nd|rd|th)?\\s*${F}\\b`, "i"));
  if (floorOnly) return { floor: floorOnly[1] };

  const labelOnly = text.match(new RegExp(`${F}\\s*[:\\-]\\s*(\\d+)\\b`, "i"));
  if (labelOnly) return { floor: labelOnly[1] };

  return {};
}

function extractAvailableFrom(text: string): string | undefined {
  if (
    /ready\s*to\s*(?:move|occupy)|immediate(?:ly)?\s*available|available\s*immediately/i.test(text)
  ) {
    return "Ready to Occupy";
  }
  const match = text.match(
    /available\s*(?:from)?\s*[:-]?\s*([0-3]?\d[a-z]*\s+[a-z]+(?:\s+\d{2,4})?)/i,
  );
  return match ? match[1].trim() : undefined;
}

function extractPreferredTenant(text: string): string | undefined {
  if (/family\s*preferred|families?\s*only|preferred\s*tenant\s*[:-]?\s*family/i.test(text))
    return "Family";
  if (/bachelors?\s*(?:allowed|preferred|only)?/i.test(text)) return "Bachelors";
  if (/company\s*lease/i.test(text)) return "Company Lease";
  if (/anyone|no\s*preference/i.test(text)) return "Anyone";
  return undefined;
}

function extractPets(text: string): ParsedProperty["pets"] | undefined {
  if (/no\s*pets|pets?\s*not\s*allowed|pet\s*free/i.test(text)) return "Not allowed";
  if (/pets?\s*(?:allowed|friendly|ok|welcome)/i.test(text)) return "Allowed";
  return undefined;
}

function extractPropertyType(text: string): ParsedProperty["propertyType"] | undefined {
  if (/\bvilla\b/i.test(text)) return "Villa";
  if (/independent\s*house|independent\s*home/i.test(text)) return "Independent House";
  if (/\bapartment\b|\bflat\b/i.test(text)) return "Apartment";
  return undefined;
}

/**
 * Exposed so formatter/utils/parsers.ts can re-use the money parser.
 * Converts "40k" / "1.7L" / "40,000" → plain number (rupees), or null.
 */
export function parseMonetary(raw: string): number | null {
  return parseMoneyToNumber(raw);
}

/**
 * Parses raw sanitized property text into structured fields.
 * Google Places-sourced fields (societyName, locality, communityType) are
 * merged in separately by the formatter engine.
 */
export function parseProperty(rawText: string): ParsedProperty {
  const text = rawText || "";
  const { floor, floorTotal } = extractFloor(text);

  return {
    propertyType: extractPropertyType(text),
    bhk: extractBHK(text),
    bathrooms: extractBathrooms(text),
    balcony: extractBalcony(text),
    furnishing: extractFurnishing(text),
    rent: extractMoney(text, ["rent"]),
    maintenance: extractMoney(text, ["maintenance", "maint\\.?"]),
    deposit: extractMoney(text, ["deposit", "security\\s*deposit", "advance", "dep"]),
    sqft: extractSqft(text),
    floor,
    floorTotal,
    availableFrom: extractAvailableFrom(text),
    preferredTenant: extractPreferredTenant(text),
    pets: extractPets(text),
  };
}
