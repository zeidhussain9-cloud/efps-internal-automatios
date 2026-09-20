/**
 * formatter/types/formatter.ts
 *
 * PURPOSE: TypeScript type definitions for formatter configuration
 */

/**
 * Formatter configuration
 */
export interface FormatterConfig {
  apiKey?: string;
  model?: string;
  maxRetries?: number;
  timeout?: number;
}

/**
 * Formatting rule
 */
export interface FormattingRule {
  field: string;
  pattern?: RegExp;
  transformer: (value: string) => string;
}

/**
 * Standardization rules collection
 */
export interface StandardizationRules {
  furnishing: FormattingRule[];
  monetary: FormattingRule[];
  bathroom: FormattingRule[];
  [key: string]: FormattingRule[];
}
