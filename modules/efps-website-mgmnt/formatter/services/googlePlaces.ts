/** Deprecated formatter compatibility surface. Google links remain source links.
 * Paid Google enrichment has been removed. The verified backend Ola geography
 * boundary owns geographic checks; this browser-compatible formatter never
 * receives an API credential or invents building/community identity from a URL.
 */
export interface GooglePlacesResult {
  placeName: string;
  locality: string;
  placeType: string;
}
export async function resolveGoogleMapsLocation(_sourceUrl: string): Promise<GooglePlacesResult> {
  return { placeName: "", locality: "Unknown", placeType: "unknown" };
}
export async function detectSociety(_placeName: string, _placeType: string): Promise<{ isSociety: boolean; societyName?: string }> {
  return { isSociety: false };
}
export function getLocality(_placeName: string, _placeType: string): string { return "Unknown"; }
export function initializeGooglePlacesClient(): void { /* no Google dependency */ }
