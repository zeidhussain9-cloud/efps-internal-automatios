/**
 * formatter/api/formatter.handler.ts
 *
 * PURPOSE: Main formatter endpoint handler
 */

import { FormatterRequest, FormatterResponse } from "../types/api";
import { formatProperty } from "../services/formatterEngine";
import { validateFormatterRequest } from "./validators";
import { handleApiError, formatErrorResponse } from "./errorHandler";

/**
 * Main formatter handler function
 *
 * Flow:
 * Request → Validate → formatterEngine → JSON Response
 */
export async function formatPropertyHandler(
  request: { body: unknown },
  response: {
    status: (code: number) => { json: (data: FormatterResponse) => void };
    json: (data: FormatterResponse) => void;
  },
): Promise<void> {
  try {
    // 1. Validate request payload
    const validation = validateFormatterRequest(request.body);
    if (!validation.valid) {
      const { statusCode, response: errorResponse } = formatErrorResponse(
        400,
        "VALIDATION_ERROR",
        validation.errors?.join(", ") || "Invalid request",
      );
      response.status(statusCode).json(errorResponse);
      return;
    }

    const payload = request.body as FormatterRequest;

    // 2. Call formatter engine
    const result = await formatProperty({
      propertyDetails: payload.propertyDetails,
      googleMapsUrl: payload.googleMapsUrl,
    });

    // 3. Handle engine failure
    if (!result.success) {
      const { statusCode, response: errorResponse } = formatErrorResponse(
        500,
        "FORMATTER_ENGINE_ERROR",
        result.errors?.join(", ") || "Formatting failed",
      );
      response.status(statusCode).json(errorResponse);
      return;
    }

    // 4. Return success response
    response.status(200).json({
      success: true,
      data: {
        formattedProperty: result.formattedText || "",
        parsedData: (result.resolvedPlace as Record<string, unknown>) || {},
      },
    });
  } catch (error: unknown) {
    // 5. Centralized error handling
    const { statusCode, response: errorResponse } = handleApiError(error);
    response.status(statusCode).json(errorResponse);
  }
}

/**
 * Health check endpoint
 */
export async function healthCheck(
  _request: unknown,
  response: {
    status: (code: number) => { json: (data: unknown) => void };
    json: (data: unknown) => void;
  },
): Promise<void> {
  response.status(200).json({
    success: true,
    data: {
      status: "ok",
      module: "formatter",
      timestamp: new Date().toISOString(),
    },
  });
}
