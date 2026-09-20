/**
 * formatter/types/api.ts
 *
 * PURPOSE: TypeScript type definitions for API requests and responses
 */

/**
 * Formatter API request body
 */
export interface FormatterRequest {
  propertyDetails: string;
  googleMapsUrl?: string;
}

/**
 * Formatter API success response
 */
export interface FormatterSuccessResponse {
  success: true;
  data: {
    formattedProperty: string;
    parsedData: Record<string, unknown>;
  };
}

/**
 * Formatter API error response
 */
export interface FormatterErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
  };
}

/**
 * Combined API response type
 */
export type FormatterResponse = FormatterSuccessResponse | FormatterErrorResponse;
