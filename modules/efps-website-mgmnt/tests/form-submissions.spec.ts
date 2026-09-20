import { test, expect } from "@playwright/test";

test.describe("Independent Lead Form Submissions", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the local home page
    await page.goto("/");
  });

  test("should submit the Hero Form successfully and verify exactly one network request is made", async ({
    page,
  }) => {
    // Keep track of requests made to the Google Form endpoint
    let googleFormRequestCount = 0;
    let requestPayload: string | null = null;

    // Intercept Google Form submissions to prevent test pollution and verify payloads
    await page.route("**/formResponse", async (route) => {
      googleFormRequestCount++;
      requestPayload = route.request().postData();
      await route.fulfill({
        status: 200,
        contentType: "text/html",
        body: "Mock Google Form Submission Succeeded",
      });
    });

    // Locate the Hero form via its unique aria-label
    const heroForm = page.locator('form[aria-label="Talk to our expert"]');
    await expect(heroForm).toBeVisible();

    // Fill out the Hero form fields
    await heroForm.locator("#hero-name").fill("Hero Tester");
    await heroForm.locator("#hero-phone").fill("9876543210");
    await heroForm.locator("#hero-requirement").selectOption("Looking to Buy");

    // Before submission, confirm success message is not shown
    await expect(page.locator('text="Thank you! We\'ll call you shortly."')).toHaveCount(0);

    // Submit the Hero form
    await heroForm.locator('button[type="submit"]').click();

    // Wait for the Hero form's success UI to appear
    const successCard = page.locator('div[role="status"]');
    await expect(successCard).toBeVisible();
    await expect(
      successCard.locator('h3:has-text("Thank you! We\'ll call you shortly.")'),
    ).toBeVisible();

    // Verify exactly 1 network request was made
    expect(googleFormRequestCount).toBe(1);

    // Verify payload contents and source
    expect(requestPayload).not.toBeNull();
    const decodedPayload = decodeURIComponent(requestPayload!.replace(/\+/g, " "));
    expect(decodedPayload).toContain("Hero Tester");
    expect(decodedPayload).toContain("+91 9876543210");
    expect(decodedPayload).toContain("Looking to Buy");
    expect(decodedPayload).toContain("Website Hero Form");

    // IMPORTANT: Verify the Bottom Form remains fully independent
    // Ensure the Bottom form fields are still empty and it has not entered success state
    const bottomForm = page.locator("#lead-form form");
    await expect(bottomForm).toBeVisible();
    await expect(bottomForm.locator('input[placeholder="Name"]')).toHaveValue("");
    await expect(bottomForm.locator('input[placeholder="Phone Number"]')).toHaveValue("");
  });

  test("should submit the Bottom Form successfully and verify exactly one network request is made", async ({
    page,
  }) => {
    // Keep track of requests made to the Google Form endpoint
    let googleFormRequestCount = 0;
    let requestPayload: string | null = null;

    // Intercept Google Form submissions to prevent test pollution and verify payloads
    await page.route("**/formResponse", async (route) => {
      googleFormRequestCount++;
      requestPayload = route.request().postData();
      await route.fulfill({
        status: 200,
        contentType: "text/html",
        body: "Mock Google Form Submission Succeeded",
      });
    });

    // Locate the Bottom form container
    const bottomFormContainer = page.locator("#lead-form");
    await expect(bottomFormContainer).toBeVisible();

    const bottomForm = bottomFormContainer.locator("form");
    await expect(bottomForm).toBeVisible();

    // Fill out the Bottom form fields
    await bottomForm.locator('input[placeholder="Name"]').fill("Bottom Tester");
    await bottomForm.locator('input[placeholder="Phone Number"]').fill("9876543211");
    await bottomForm.locator("select").selectOption("Looking to Rent");
    await bottomForm.locator('input[placeholder="Preferred Location"]').fill("Koramangala");
    await bottomForm.locator('input[placeholder="Budget"]').fill("50k");
    await bottomForm
      .locator('textarea[placeholder="Additional Details"]')
      .fill("Need 2BHK flat with high ROI or clean balcony");

    // Before submission, confirm success message is not shown on Bottom form
    await expect(
      bottomFormContainer.locator('text="Thank you! We\'ll call you shortly."'),
    ).toHaveCount(0);

    // Submit the Bottom form
    await bottomForm.locator('button[type="submit"]').click();

    // Wait for the Bottom form's success message to appear
    const bottomSuccessMsg = bottomFormContainer.locator(
      'text="Thank you! We\'ll call you shortly."',
    );
    await expect(bottomSuccessMsg).toBeVisible();

    // Verify exactly 1 network request was made
    expect(googleFormRequestCount).toBe(1);

    // Verify payload contents, extra fields, and source
    expect(requestPayload).not.toBeNull();
    const decodedPayload = decodeURIComponent(requestPayload!.replace(/\+/g, " "));
    expect(decodedPayload).toContain("Bottom Tester");
    expect(decodedPayload).toContain("+91 9876543211");
    expect(decodedPayload).toContain("Looking to Rent");
    expect(decodedPayload).toContain("Koramangala");
    expect(decodedPayload).toContain("50k");
    expect(decodedPayload).toContain("Need 2BHK flat with high ROI or clean balcony");
    expect(decodedPayload).toContain("Website Bottom Enquiry Form");

    // IMPORTANT: Verify the Hero Form remains fully independent
    // Ensure the Hero form fields are still empty/default and it has not entered success state
    const heroForm = page.locator('form[aria-label="Talk to our expert"]');
    await expect(heroForm).toBeVisible();
    await expect(heroForm.locator("#hero-name")).toHaveValue("");
    await expect(heroForm.locator("#hero-phone")).toHaveValue("");
    await expect(heroForm.locator("#hero-requirement")).toHaveValue("");
  });

  test("should allow both forms to be submitted in the same session without state crosstalk", async ({
    page,
  }) => {
    // Intercept Google Form submissions
    let heroFormRequests = 0;
    let bottomFormRequests = 0;

    await page.route("**/formResponse", async (route) => {
      const payload = route.request().postData() || "";
      const decodedPayload = decodeURIComponent(payload.replace(/\+/g, " "));

      if (decodedPayload.includes("Website Hero Form")) {
        heroFormRequests++;
      } else if (decodedPayload.includes("Website Bottom Enquiry Form")) {
        bottomFormRequests++;
      }

      await route.fulfill({
        status: 200,
        contentType: "text/html",
        body: "Mock Google Form Submission Succeeded",
      });
    });

    // 1. Submit the Hero Form
    const heroForm = page.locator('form[aria-label="Talk to our expert"]');
    await heroForm.locator("#hero-name").fill("Session Hero User");
    await heroForm.locator("#hero-phone").fill("9999999999");
    await heroForm.locator("#hero-requirement").selectOption("Property Management");
    await heroForm.locator('button[type="submit"]').click();

    // Verify Hero Form goes into success state
    const heroSuccessCard = page.locator('div[role="status"]');
    await expect(heroSuccessCard).toBeVisible();

    // 2. Bottom Form remains interactive and editable
    const bottomFormContainer = page.locator("#lead-form");
    const bottomForm = bottomFormContainer.locator("form");
    await expect(bottomForm).toBeVisible();

    await bottomForm.locator('input[placeholder="Name"]').fill("Session Bottom User");
    await bottomForm.locator('input[placeholder="Phone Number"]').fill("8888888888");
    await bottomForm.locator("select").selectOption("Investment Advisory");
    await bottomForm.locator('button[type="submit"]').click();

    // Verify Bottom Form goes into success state as well
    const bottomSuccessMsg = bottomFormContainer.locator(
      'text="Thank you! We\'ll call you shortly."',
    );
    await expect(bottomSuccessMsg).toBeVisible();

    // 3. Confirm network counts are correct (exactly 1 for each)
    expect(heroFormRequests).toBe(1);
    expect(bottomFormRequests).toBe(1);
  });
});
