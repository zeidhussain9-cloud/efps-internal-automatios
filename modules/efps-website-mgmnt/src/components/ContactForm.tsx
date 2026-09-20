import React, { useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { NAVY, GOLD } from "@/routes/index";
import { submitLead } from "@/lib/submitLead";

// Hero "Talk to Our Expert" form — compact 3-field lead capture.
// State is fully local; this component never reads from or writes to any
// other form's state.
const ContactForm: React.FC<{ onPrivacyClick: () => void }> = ({ onPrivacyClick }) => {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [requirement, setRequirement] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [succeeded, setSucceeded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    const trimmedName = name.trim();
    const digits = phone.replace(/\D/g, "");
    if (!trimmedName) {
      setError("Please enter your name.");
      return;
    }
    if (digits.length !== 10) {
      setError("Please enter a valid 10-digit mobile number.");
      return;
    }
    if (!requirement) {
      setError("Please select a requirement.");
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      const res = await submitLead({
        name: trimmedName,
        phone: `+91 ${digits}`,
        requirement,
        source: "Website Hero Form",
      });
      if (res.success) {
        setSucceeded(true);
        setName("");
        setPhone("");
        setRequirement("");
      } else {
        setError(res.error || "Something went wrong. Please try again or call us.");
      }
    } catch (err) {
      console.error("Hero form submission failed:", err);
      setError("Something went wrong. Please try again or call us.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputBase =
    "w-full rounded-lg border bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-gold/80 focus:ring-2 focus:ring-brand-gold/30 disabled:opacity-60";

  if (succeeded) {
    return (
      <div
        className="rounded-2xl bg-white p-8 text-center shadow-xl border border-brand-border"
        role="status"
        aria-live="polite"
      >
        <div
          className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full"
          style={{ background: "#ECFDF5", color: "#059669" }}
        >
          <CheckCircle2 size={30} />
        </div>
        <h3 className="text-lg font-bold text-brand-navy">Thank you! We'll call you shortly.</h3>
        <p className="mt-2 text-sm text-gray-500">
          Our team will reach out on the number you shared.
        </p>
        <button
          type="button"
          onClick={() => setSucceeded(false)}
          className="mt-6 rounded-lg bg-brand-gold hover:bg-brand-gold-soft hover:scale-[1.02] active:scale-[0.98] transition-all px-5 py-2 text-sm font-semibold text-brand-navy"
        >
          Send another enquiry
        </button>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl md:p-7 mx-auto border border-brand-border"
      aria-label="Talk to our expert"
    >
      <h3 className="mb-5 text-lg font-bold text-brand-navy">Talk to Our Expert</h3>

      <div className="space-y-4">
        <div>
          <label htmlFor="hero-name" className="mb-1.5 block text-xs font-semibold text-gray-600">
            Name <span className="text-red-500">*</span>
          </label>
          <input
            id="hero-name"
            type="text"
            autoComplete="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={(e) => setName(e.target.value.trim())}
            disabled={isSubmitting}
            className={inputBase}
            style={{ borderColor: "#E5E7EB" }}
          />
        </div>

        <div>
          <label htmlFor="hero-phone" className="mb-1.5 block text-xs font-semibold text-gray-600">
            Phone Number <span className="text-red-500">*</span>
          </label>
          <div className="flex items-stretch gap-2">
            <span
              className="inline-flex items-center rounded-lg border px-3 text-sm font-semibold text-gray-700"
              style={{ borderColor: "#E5E7EB", background: "#F8F9FB" }}
            >
              +91
            </span>
            <input
              id="hero-phone"
              type="tel"
              inputMode="numeric"
              autoComplete="tel-national"
              maxLength={10}
              placeholder="10-digit mobile"
              value={phone}
              onChange={(e) => {
                const val = e.target.value.replace(/\D/g, "").slice(0, 10);
                if (val !== phone) setPhone(val);
              }}
              disabled={isSubmitting}
              className={inputBase}
              style={{ borderColor: "#E5E7EB" }}
            />
          </div>
        </div>

        <div>
          <label
            htmlFor="hero-requirement"
            className="mb-1.5 block text-xs font-semibold text-gray-600"
          >
            Requirement <span className="text-red-500">*</span>
          </label>
          <select
            id="hero-requirement"
            value={requirement}
            onChange={(e) => setRequirement(e.target.value)}
            disabled={isSubmitting}
            className={inputBase}
            style={{ borderColor: "#E5E7EB" }}
          >
            <option value="">Select...</option>
            <option>Looking to Rent</option>
            <option>Looking to Buy</option>
            <option>Looking to Sell</option>
            <option>Property Management</option>
            <option>Investment Advisory</option>
          </select>
        </div>

        {error && (
          <p className="text-sm font-medium text-red-600" role="alert">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-lg py-3.5 text-base font-bold shadow-md transition-all bg-brand-gold hover:bg-brand-gold-soft hover:-translate-y-0.5 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-70 disabled:hover:translate-y-0 text-brand-navy"
        >
          {isSubmitting ? "Sending..." : "Get a Call Back"}
        </button>
        <p className="text-center text-xs leading-relaxed text-gray-500">
          By submitting, you agree to our{" "}
          <button
            type="button"
            onClick={onPrivacyClick}
            className="font-semibold text-brand-navy underline decoration-brand-gold underline-offset-2"
          >
            Privacy Policy
          </button>
          .
        </p>
      </div>
    </form>
  );
};

export default ContactForm;
