/**
 * submitLead.ts
 *
 * Primary: Formspree — real JSON response, email notification, dashboard.
 * Fallback: Google Forms (no-cors) — blind fire, used when VITE_FORMSPREE_ID
 *           is not set. Preserves existing behavior until Formspree activates.
 *
 * To activate Formspree:
 *   1. Create a free account at https://formspree.io
 *   2. Create a form named "EasyFind Lead Form"
 *   3. Copy the 8-character Form ID (e.g. xpwzabcd)
 *   4. In Render dashboard → easyfind-website → Environment:
 *      Add key: VITE_FORMSPREE_ID  value: your_form_id
 *   5. Trigger a new deploy
 *   6. Test: submit hero form → confirm email arrives in inbox
 */

export interface LeadData {
  name: string;
  phone: string;
  requirement: string;
  location?: string;
  budget?: string;
  details?: string;
  source: string;
}

export interface SubmitResult {
  success: boolean;
  error?: string;
}

const FORMSPREE_ID = import.meta.env["VITE_FORMSPREE_ID"] as string | undefined;

// ── ACTUAL VALUES FROM THE CURRENT CODEBASE ───────────────────────────────
const GOOGLE_FORMS_URL =
  "https://docs.google.com/forms/d/e/1FAIpQLSeyRnYIMCl3ouDgMfGkZBK57ccIeIk6e6nlYmoZubRaoLdOsA/formResponse";
// ────────────────────────────────────────────────────────────────────────────

export async function submitLead(data: LeadData): Promise<SubmitResult> {
  if (FORMSPREE_ID) {
    return submitViaFormspree(data);
  }
  return submitViaGoogleForms(data);
}

async function submitViaFormspree(data: LeadData): Promise<SubmitResult> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);

  try {
    const response = await fetch(`https://formspree.io/f/${FORMSPREE_ID}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        name: data.name,
        phone: data.phone,
        requirement: data.requirement,
        preferred_location: data.location ?? "",
        budget: data.budget ?? "",
        additional_details: data.details ?? "",
        source: data.source,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (response.ok) {
      return { success: true };
    }

    const json = (await response.json().catch(() => ({}))) as { error?: string };
    return {
      success: false,
      error: json.error ?? `Submission failed (${response.status}). Please try again.`,
    };
  } catch (err) {
    clearTimeout(timeout);
    if (err instanceof Error && err.name === "AbortError") {
      return { success: false, error: "Request timed out. Please try again." };
    }
    return { success: false, error: "Network error. Please check your connection and try again." };
  }
}

async function submitViaGoogleForms(data: LeadData): Promise<SubmitResult> {
  // No-cors fallback — cannot verify success, assumes success on fire.
  const body = new URLSearchParams({
    "entry.647419092": data.name,
    "entry.1504466253": data.phone,
    "entry.1645082311": data.requirement,
    "entry.616237414": data.location ?? "",
    "entry.1733021043": data.budget ?? "",
    "entry.1656301094": data.details ?? "",
    "entry.128907828": data.source,
  });

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);

  try {
    await fetch(GOOGLE_FORMS_URL, {
      method: "POST",
      mode: "no-cors",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
      signal: controller.signal,
    });
    clearTimeout(timeout);
    return { success: true };
  } catch (err) {
    clearTimeout(timeout);
    if (err instanceof Error && err.name === "AbortError") {
      return { success: false, error: "Submission timed out. Please try again." };
    }
    return { success: false, error: "Network error. Please try again." };
  }
}
