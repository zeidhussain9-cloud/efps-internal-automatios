/**
 * formatter/services/sanitizer.ts
 *
 * PURPOSE: Input sanitization for the EasyFind Formatter
 *
 * RESPONSIBILITY:
 * - Normalize whitespace
 * - Clean up Unicode characters
 * - Remove duplicate blank lines
 * - Preserve Google Maps URLs exactly
 */

/**
 * Sanitizes the raw property input
 */
export function sanitizeInput(input: string): string {
  if (!input) return "";

  // 1. Identify and preserve Google Maps URLs
  const mapsUrlRegex =
    /https?:\/\/(?:www\.)?(?:google\.com\/maps|goo\.gl\/maps|maps\.app\.goo\.gl)\/\S+/g;
  const urls: string[] = [];
  let sanitized = input.replace(mapsUrlRegex, (match) => {
    urls.push(match);
    return `__GOOGLE_MAPS_URL_${urls.length - 1}__`;
  });

  // 2. Normalize whitespace and newlines
  sanitized = sanitized
    .replace(/\r\n/g, "\n") // Normalize line endings
    .replace(/[ \t]+/g, " ") // Normalize horizontal whitespace
    .replace(/\n{3,}/g, "\n\n") // Remove excessive blank lines
    .trim();

  // 3. Clean up Unicode (basic normalization)
  sanitized = sanitized.normalize("NFKC");

  // 4. Restore Google Maps URLs
  urls.forEach((url, index) => {
    sanitized = sanitized.replace(`__GOOGLE_MAPS_URL_${index}__`, url);
  });

  return sanitized;
}

/**
 * Sanitizes the formatted output for safety
 */
export function sanitizeOutput(output: string): string {
  if (!output) return "";

  return output
    .replace(/[<>]/g, "") // Basic HTML tag stripping for safety
    .trim();
}
