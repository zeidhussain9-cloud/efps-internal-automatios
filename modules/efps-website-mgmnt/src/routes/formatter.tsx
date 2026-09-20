import { createFileRoute } from "@tanstack/react-router";
import { useState, useRef } from "react";
import { Helmet } from "react-helmet-async";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import {
  Clipboard,
  Trash2,
  Wand2,
  Loader2,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
} from "lucide-react";
import type { FormatterResponse } from "../../formatter/types/api";

export const Route = createFileRoute("/formatter")({
  component: FormatterPage,
});

function FormatterPage() {
  const [input, setInput] = useState("");
  const [output, setOutput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const outputRef = useRef<HTMLTextAreaElement>(null);

  const handleFormat = async () => {
    if (!input.trim()) return;

    setIsLoading(true);
    setError(null);
    setCopied(false);

    try {
      // Extract Google Maps URL if present
      const mapsUrlRegex =
        /https?:\/\/(?:www\.)?(?:google\.com\/maps|goo\.gl\/maps|maps\.app\.goo\.gl)\/\S+/;
      const match = input.match(mapsUrlRegex);
      const googleMapsUrl = match ? match[0] : undefined;

      // Prepare payload
      const payload = {
        propertyDetails: input,
        googleMapsUrl,
      };

      const response = await fetch("/api/formatter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result: FormatterResponse = await response.json();

      if (result.success) {
        setOutput(result.data.formattedProperty || "");
      } else {
        setError(result.error?.message || "An error occurred during formatting");
      }
    } catch (err) {
      setError("Failed to connect to the formatter service. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!output) return;
    try {
      await navigator.clipboard.writeText(output);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      setError("Failed to copy to clipboard");
    }
  };

  const handleClear = () => {
    setInput("");
    setOutput("");
    setError(null);
    setCopied(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <Helmet>
        <title>EasyFind | Property Formatter</title>
      </Helmet>

      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <a href="/" className="p-2 hover:bg-gray-200 rounded-full transition-colors">
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </a>
            <h1 className="text-2xl font-bold text-gray-900">EasyFind Formatter</h1>
          </div>
          <div className="text-xs font-medium text-gray-500 bg-gray-200 px-2 py-1 rounded">
            Internal Tool
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6">
          {/* Input Section */}
          <div className="bg-white shadow rounded-lg p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Paste Property Details (including Google Maps URL)
            </label>
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Paste everything here: property details, maps link, WhatsApp messages..."
              className="min-h-[250px] font-sans text-sm resize-y"
              disabled={isLoading}
            />

            <div className="mt-4 flex flex-wrap gap-3">
              <Button
                onClick={handleFormat}
                disabled={isLoading || !input.trim()}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Wand2 className="w-4 h-4" />
                )}
                Format Property
              </Button>

              <Button
                variant="outline"
                onClick={handleClear}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Clear
              </Button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Output Section */}
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Formatted Output</label>
              {output && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                  className={`flex items-center gap-2 ${copied ? "text-green-600" : "text-gray-600"}`}
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Clipboard className="w-4 h-4" />
                      Copy Output
                    </>
                  )}
                </Button>
              )}
            </div>
            <Textarea
              ref={outputRef}
              value={output}
              readOnly
              placeholder="Standardized output will appear here..."
              className="min-h-[300px] font-mono text-sm bg-gray-50 resize-y"
            />
          </div>
        </div>

        <footer className="mt-12 text-center text-gray-400 text-xs">
          EasyFind Inventory Engine &copy; {new Date().getFullYear()}
        </footer>
      </div>
    </div>
  );
}
