/**
 * formatter/utils/formatters.ts
 *
 * PURPOSE: Utility functions for formatting values
 */

/**
 * Format amount to INR with appropriate suffix
 *
 * EXAMPLES:
 * 40000 → "₹40k"
 * 120000 → "₹1.2L"
 * 1200000 → "₹12L"
 * 10000000 → "₹1Cr"
 */
export function formatINR(amount: number): string {
  if (isNaN(amount)) return "₹-";
  if (amount >= 10000000) {
    const cr = amount / 10000000;
    return `₹${Number.isInteger(cr) ? cr : parseFloat(cr.toFixed(2))}Cr`;
  }
  if (amount >= 100000) {
    const l = amount / 100000;
    return `₹${Number.isInteger(l) ? l : parseFloat(l.toFixed(2))}L`;
  }
  if (amount >= 1000) {
    const k = amount / 1000;
    return `₹${Number.isInteger(k) ? k : parseFloat(k.toFixed(1))}k`;
  }
  return `₹${amount}`;
}

/**
 * Format date to readable format
 */
export function formatDate(date: Date | string): string {
  const d = date instanceof Date ? date : new Date(date);
  if (isNaN(d.getTime())) return String(date);
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

/**
 * Format number with commas (Indian format)
 */
export function formatNumber(num: number): string {
  return num.toLocaleString("en-IN");
}

/**
 * Format string to title case
 */
export function toTitleCase(str: string): string {
  return str.replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.slice(1).toLowerCase());
}
