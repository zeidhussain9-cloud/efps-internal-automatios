/**
 * formatter/services/templateFormatter.ts
 *
 * PURPOSE: Deterministic, rule-based rendering of a ParsedProperty into the
 * exact EasyFind listing template. No AI/LLM call is involved — this is the
 * final step of the formatter pipeline and always produces the same output
 * for the same input.
 *
 * RESPONSIBILITY:
 * - Preserve field order exactly (see formatter/prompts/formatting-rules.md).
 * - Never invent a value: a field left `undefined` by the parser renders
 *   as a blank value rather than a guess.
 */

import { ParsedProperty } from "../types/property";

const FINISH_LINE = `*${"=".repeat(34)}*`;

function buildTitle(parsed: ParsedProperty): string {
  const parts: string[] = [];

  if (parsed.furnishing) parts.push(parsed.furnishing);
  if (parsed.bhk) parts.push(parsed.bhk);
  if (parsed.propertyType && parsed.propertyType !== "Apartment") {
    parts.push(parsed.propertyType);
  }

  let title = parts.join(" ");

  const withParts: string[] = [];
  if (parsed.bathrooms) withParts.push(parsed.bathrooms);
  if (parsed.balcony) withParts.push(parsed.balcony);

  if (withParts.length > 0) {
    title = title ? `${title} with ${withParts.join(" & ")}` : `With ${withParts.join(" & ")}`;
  }

  return title;
}

function line(label: string, value?: string): string {
  return `${label} : ${value ?? ""}`.trimEnd();
}

/**
 * Renders the final EasyFind listing text from parsed + resolved fields.
 */
export function formatWithTemplate(parsed: ParsedProperty): string {
  const lines: string[] = [];

  const title = buildTitle(parsed);
  if (title) lines.push(title);

  lines.push("");
  lines.push(line("Rent", parsed.rent));
  lines.push(line("Maintenance", parsed.maintenance));
  lines.push(line("Deposit", parsed.deposit));
  lines.push(line("Sqft", parsed.sqft));
  lines.push(
    line(
      "Floor",
      parsed.floor && parsed.floorTotal ? `${parsed.floor}/${parsed.floorTotal}` : parsed.floor,
    ),
  );
  lines.push(line("Available from", parsed.availableFrom));
  lines.push(line("Preferred tenant", parsed.preferredTenant));
  lines.push(line("Pets", parsed.pets));
  lines.push(line("Community", parsed.communityType));
  lines.push(line("Location", parsed.locality));

  const footer: string[] = [""];
  if (parsed.societyName) footer.push(`*${parsed.societyName}*`);
  if (parsed.googleMapsUrl) footer.push(parsed.googleMapsUrl);
  footer.push("");
  footer.push(FINISH_LINE);

  return [...lines, ...footer].join("\n");
}
