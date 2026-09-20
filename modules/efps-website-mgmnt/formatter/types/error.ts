/**
 * formatter/types/error.ts
 *
 * PURPOSE: Custom error type definitions
 */

/**
 * Base formatter error
 */
export class FormatterError extends Error {
  constructor(
    message: string,
    public code: string = "FORMATTER_ERROR",
  ) {
    super(message);
    this.name = "FormatterError";
  }
}

/**
 * Validation error
 */
export class ValidationError extends FormatterError {
  constructor(message: string) {
    super(message, "VALIDATION_ERROR");
    this.name = "ValidationError";
  }
}

/**
 * API integration error
 */
export class APIIntegrationError extends FormatterError {
  constructor(
    message: string,
    public service: string,
  ) {
    super(message, "API_ERROR");
    this.name = "APIIntegrationError";
  }
}

/**
 * Parse error
 */
export class ParseError extends FormatterError {
  constructor(message: string) {
    super(message, "PARSE_ERROR");
    this.name = "ParseError";
  }
}
