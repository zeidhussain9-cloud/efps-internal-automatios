/**
 * formatter/services/standardizer.ts
 *
 * PURPOSE: Field standardization according to EasyFind SOP
 *
 * RESPONSIBILITY:
 * - Normalize furnishing status
 * - Format monetary values (INR)
 * - Standardize bathroom/balcony counts
 * - Format dates and preferences
 */

/**
 * Normalizes furnishing status
 * Returns: Unfurnished, Semi-furnished, Fully Furnished
 */
export function standardizeFurnishing(furnishing: string): string {
  const f = furnishing.toLowerCase();
  if (f.includes("semi")) return "Semi-furnished";
  if (f.includes("fully") || f.includes("full")) return "Fully Furnished";
  if (f.includes("un")) return "Unfurnished";
  return "Semi-furnished"; // Default to semi-furnished as per common property types
}

/**
 * Formats monetary values to EasyFind standard (₹40k, ₹1.2L)
 */
export function formatMonetaryValue(amount: string | number): string {
  const num = typeof amount === "string" ? parseFloat(amount.replace(/[₹,kL\s]/gi, "")) : amount;
  if (isNaN(num)) return "₹-";

  if (num >= 100000) {
    const lakhs = num / 100000;
    return `₹${Number.isInteger(lakhs) ? lakhs : parseFloat(lakhs.toFixed(2))}L`;
  } else if (num >= 1000) {
    const k = num / 1000;
    return `₹${Number.isInteger(k) ? k : parseFloat(k.toFixed(1))}k`;
  }
  return `₹${num}`;
}

/**
 * Standardizes bathroom counts
 */
export function standardizeBathrooms(count: string | number): string {
  const num = typeof count === "string" ? parseInt(count, 10) : count;
  if (isNaN(num)) return "1 bathroom";
  return `${num} bathroom${num > 1 ? "s" : ""}`;
}

/**
 * Capitalizes tenant preferences
 */
export function capitalizeTenantPreference(preference: string): string {
  const p = preference.toLowerCase();
  if (p.includes("family")) return "Family";
  if (p.includes("bachelor")) return "Bachelors";
  if (p.includes("anyone")) return "Anyone";
  return "Anyone";
}

/**
 * Standardizes "Available from" date
 */
export function standardizeAvailableFrom(date: string): string {
  if (!date || date.toLowerCase().includes("ready") || date.toLowerCase().includes("immediate")) {
    return "Ready to Occupy";
  }
  return date;
}
