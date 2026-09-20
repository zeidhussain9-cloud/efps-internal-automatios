/**
 * formatter/services/googlePlaces.ts
 *
 * PURPOSE: Resolve a Google Maps URL into structured place data
 *   (place name, locality, place type) that the formatter engine
 *   can use to fill the society / location / community fields.
 *
 * URL FORMATS HANDLED (in priority order):
 *   1. Long URL with Place ID in data param  – google.com/maps/place/Name/@lat,lng,Xz/data=…1sChIJ…
 *   2. Long URL without Place ID (place name in path) – google.com/maps/place/Name/@…
 *   3. Coords-only URL   – google.com/maps/@lat,lng,Xz
 *   4. Search / query    – google.com/maps/search/query or ?q=query
 *   5. Short URLs        – maps.app.goo.gl/X  or  goo.gl/maps/X
 *      → followed via HTTP redirect to recover the long URL, then re-parsed
 */

import axios from "axios";

export interface GooglePlacesResult {
  placeName: string;
  locality: string;
  placeType: string;
}

// ─────────────────────────────────────────────────────────────────
// Regex helpers
// ─────────────────────────────────────────────────────────────────

/** Extract the Place ID embedded in the Google Maps `data=` parameter.
 *  The Place ID starts with "ChIJ" and is encoded as "1s<placeId>!".  */
function extractPlaceId(url: string): string | null {
  // data=…!1sChIJxxxxxxx!…
  const dataMatch = url.match(/[!&]1s(ChIJ[^!&]+)/);
  if (dataMatch) return decodeURIComponent(dataMatch[1]);

  // Explicit place_id= query param (rare but exists in embed URLs)
  const paramMatch = url.match(/[?&]place_id=([A-Za-z0-9_-]+)/);
  if (paramMatch) return paramMatch[1];

  return null;
}

/** Extract the human-readable place name from the /place/<Name>/ path segment. */
function extractPlaceNameFromPath(url: string): string | null {
  const m = url.match(/\/place\/([^/@?]+)/);
  if (!m) return null;
  try {
    return decodeURIComponent(m[1].replace(/\+/g, " ")).trim();
  } catch {
    return m[1].replace(/\+/g, " ").trim();
  }
}

/** Extract lat/lng from a Google Maps URL (used as last-resort geocode). */
function extractLatLng(url: string): { lat: string; lng: string } | null {
  const m = url.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
  return m ? { lat: m[1], lng: m[2] } : null;
}

/** Extract a text search query from ?q= or /search/ path. */
function extractSearchQuery(url: string): string | null {
  const qParam = url.match(/[?&]q=([^&]+)/);
  if (qParam) return decodeURIComponent(qParam[1]);

  const searchPath = url.match(/\/search\/([^/@?]+)/);
  if (searchPath) {
    try {
      return decodeURIComponent(searchPath[1].replace(/\+/g, " ")).trim();
    } catch {
      return searchPath[1].replace(/\+/g, " ").trim();
    }
  }

  return null;
}

// ─────────────────────────────────────────────────────────────────
// Short URL resolution
// ─────────────────────────────────────────────────────────────────

/** Follow HTTP redirects on a short URL and return the final long URL. */
async function resolveShortUrl(shortUrl: string): Promise<string> {
  try {
    // Use maxRedirects: 10 and capture the final URL from the response
    const response = await axios.get(shortUrl, {
      maxRedirects: 10,
      validateStatus: () => true, // never throw on status code
      headers: {
        "User-Agent":
          "Mozilla/5.0 (compatible; EasyFind-Formatter/1.0; +https://easyfindprops.com)",
      },
    });

    // axios stores the final URL in response.request.res.responseUrl (Node.js)
    const finalUrl: string =
      (response.request as { res?: { responseUrl?: string } })?.res?.responseUrl ?? shortUrl;

    return finalUrl && finalUrl !== shortUrl ? finalUrl : shortUrl;
  } catch {
    return shortUrl;
  }
}

// ─────────────────────────────────────────────────────────────────
// Places API helpers
// ─────────────────────────────────────────────────────────────────

function getLocalityFromComponents(
  components: Array<{ types: string[]; long_name: string }>,
): string {
  if (!components) return "Unknown";
  const order = ["sublocality_level_1", "sublocality", "locality"];
  for (const type of order) {
    const c = components.find((c) => c.types.includes(type));
    if (c) return c.long_name;
  }
  return "Unknown";
}

function getLocalityFromNewComponents(
  components: Array<{ componentType: string; longText: string }> | undefined,
): string {
  if (!components) return "Unknown";
  const order = ["sublocality_level_1", "sublocality", "locality"];
  for (const type of order) {
    const c = components.find((c) => c.componentType === type);
    if (c) return c.longText;
  }
  return "Unknown";
}

/** Look up a Place by ID using Places API (New), with legacy API fallback. */
async function lookupByPlaceId(
  placeId: string,
  apiKey: string,
): Promise<GooglePlacesResult | null> {
  // Places API (New)
  try {
    const { data } = await axios.get(`https://places.googleapis.com/v1/places/${placeId}`, {
      headers: {
        "X-Goog-Api-Key": apiKey,
        "X-Goog-FieldMask": "displayName,addressComponents,types",
      },
    });
    if (data?.displayName) {
      return {
        placeName: data.displayName.text ?? "Landmark",
        placeType: data.types?.[0] ?? "unknown",
        locality: getLocalityFromNewComponents(data.addressComponents),
      };
    }
  } catch {
    // fall through to legacy
  }

  // Places API (Legacy)
  try {
    const { data } = await axios.get(
      `https://maps.googleapis.com/maps/api/place/details/json?place_id=${placeId}&fields=name,address_components,types&key=${apiKey}`,
    );
    if (data.status === "OK" && data.result) {
      return {
        placeName: data.result.name ?? "Landmark",
        placeType: data.result.types?.[0] ?? "unknown",
        locality: getLocalityFromComponents(data.result.address_components),
      };
    }
  } catch {
    // fall through
  }

  return null;
}

/** Text-search a query using Places API (New), with legacy / Geocoding fallbacks. */
async function lookupByTextQuery(
  query: string,
  apiKey: string,
): Promise<GooglePlacesResult | null> {
  // Places API (New) – searchText
  try {
    const { data } = await axios.post(
      "https://places.googleapis.com/v1/places:searchText",
      { textQuery: query },
      {
        headers: {
          "X-Goog-Api-Key": apiKey,
          "X-Goog-FieldMask": "places.displayName,places.addressComponents,places.types",
        },
      },
    );
    if (data.places?.length) {
      const p = data.places[0];
      return {
        placeName: p.displayName?.text ?? "Landmark",
        placeType: p.types?.[0] ?? "unknown",
        locality: getLocalityFromNewComponents(p.addressComponents),
      };
    }
  } catch {
    // fall through
  }

  // Geocoding API fallback
  try {
    const { data } = await axios.get(
      `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(query)}&key=${apiKey}`,
    );
    if (data.status === "OK" && data.results?.[0]) {
      const r = data.results[0];
      return {
        placeName: r.formatted_address.split(",")[0].trim(),
        placeType: r.types?.[0] ?? "unknown",
        locality: getLocalityFromComponents(r.address_components),
      };
    }
  } catch {
    // fall through
  }

  return null;
}

/** Reverse-geocode a lat/lng using Geocoding API. */
async function lookupByLatLng(
  lat: string,
  lng: string,
  apiKey: string,
): Promise<GooglePlacesResult | null> {
  try {
    const { data } = await axios.get(
      `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${apiKey}`,
    );
    if (data.status === "OK" && data.results?.[0]) {
      const r = data.results[0];
      return {
        placeName: r.formatted_address.split(",")[0].trim(),
        placeType: r.types?.[0] ?? "unknown",
        locality: getLocalityFromComponents(r.address_components),
      };
    }
  } catch {
    // fall through
  }
  return null;
}

// ─────────────────────────────────────────────────────────────────
// Main export
// ─────────────────────────────────────────────────────────────────

const FALLBACK: GooglePlacesResult = {
  placeName: "Landmark",
  locality: "Unknown",
  placeType: "unknown",
};

/**
 * Resolve a Google Maps URL into place name, locality, and place type.
 * Returns a safe fallback (never throws) so the formatter can always
 * continue even when the Maps API is unavailable.
 */
export async function resolveGoogleMapsLocation(
  googleMapsUrl: string,
): Promise<GooglePlacesResult> {
  const apiKey = process.env.GOOGLE_PLACES_API_KEY;
  if (!apiKey) {
    console.error("GOOGLE_PLACES_API_KEY is not set – skipping location resolution");
    return FALLBACK;
  }

  try {
    // Step 1: resolve short URLs to their canonical long form
    let url = googleMapsUrl;
    const isShort =
      url.includes("maps.app.goo.gl") ||
      url.includes("goo.gl/maps") ||
      url.includes("goo.gl/");
    if (isShort) {
      url = await resolveShortUrl(url);
    }

    // Step 2: try Place ID (most authoritative)
    const placeId = extractPlaceId(url);
    if (placeId) {
      const result = await lookupByPlaceId(placeId, apiKey);
      if (result) return result;
    }

    // Step 3: try the place name from the URL path as a text search
    const pathName = extractPlaceNameFromPath(url);
    if (pathName) {
      const result = await lookupByTextQuery(pathName, apiKey);
      if (result) return result;
    }

    // Step 4: try an explicit text query (?q= or /search/)
    const query = extractSearchQuery(url);
    if (query) {
      const result = await lookupByTextQuery(query, apiKey);
      if (result) return result;
    }

    // Step 5: reverse-geocode lat/lng as last resort
    const coords = extractLatLng(url);
    if (coords) {
      const result = await lookupByLatLng(coords.lat, coords.lng, apiKey);
      if (result) return result;
    }

    return FALLBACK;
  } catch (error) {
    console.error(
      "Google Places Error:",
      error instanceof Error ? error.message : String(error),
    );
    return FALLBACK;
  }
}

// ─────────────────────────────────────────────────────────────────
// Legacy stubs (kept for backward compatibility)
// ─────────────────────────────────────────────────────────────────

export async function detectSociety(
  placeName: string,
  _placeType: string,
): Promise<{ isSociety: boolean; societyName?: string }> {
  const indicators = [
    "apartment", "society", "complex", "residency", "heights",
    "gardens", "villas", "habitat", "enclave", "estates",
    "square", "park", "arcade", "tower", "terrace",
    "meadows", "greens", "woods", "grove", "layout",
  ];
  const isSociety = indicators.some((kw) => placeName.toLowerCase().includes(kw));
  return { isSociety, societyName: isSociety ? placeName : undefined };
}

export function getLocality(_placeName: string, _placeType: string): string {
  return "Unknown"; // use the async flow
}

export function initializeGooglePlacesClient(): void {
  // no-op for axios-based implementation
}
