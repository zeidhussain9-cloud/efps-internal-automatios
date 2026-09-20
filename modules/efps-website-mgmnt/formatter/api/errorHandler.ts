/**
 * formatter/api/errorHandler.ts
 *
 * PURPOSE: Centralized error handling for the API layer
 */

import { FormatterErrorResponse } from "../types/api";

/**
 * Handle API errors and format response
 */
export function handleApiError(error: unknown): {
  statusCode: number;
  response: FormatterErrorResponse;
} {
  let statusCode = 500;
  let code = "INTERNAL_SERVER_ERROR";
  let message = "An unexpected error occurred";

  if (error instanceof Error) {
    message = error.message;

    // Custom error handling based on error name or properties if available
    if (error.name === "ValidationError") {
      statusCode = 400;
      code = "VALIDATION_ERROR";
    } else if (error.name === "APIIntegrationError") {
      statusCode = 502;
      code = "API_INTEGRATION_ERROR";
    } else if (error.name === "ParseError") {
      statusCode = 422;
      code = "PARSE_ERROR";
    }
  }

  return {
    statusCode,
    response: {
      success: false,
      error: {
        code,
        message,
      },
    },
  };
}

/**
 * Formats an error response directly
 */
export function formatErrorResponse(
  statusCode: number,
  code: string,
  message: string,
): { statusCode: number; response: FormatterErrorResponse } {
  return {
    statusCode,
    response: {
      success: false,
      error: {
        code,
        message,
      },
    },
  };
}
