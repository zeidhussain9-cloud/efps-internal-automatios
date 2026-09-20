# Formatting Rules for EasyFind Formatter

## Status
🚧 **PLACEHOLDER** - To be referenced from repo's SOP

## Purpose
This file documents the standardized formatting rules that the formatter will apply to raw property details.

## TODO
- [ ] Transcribe rules from `docs/EasyFind_Property_Formatter_SOP.md`
- [ ] Add examples for each rule
- [ ] Document edge cases
- [ ] Define error handling for invalid inputs

## Reference Documentation
The authoritative source for formatting rules is:
**`docs/EasyFind_Property_Formatter_SOP.md`**

## Key Rules (Summary)

### Furnishing Standardization
- Unfurnished
- Semi-furnished
- Fully Furnished

### Monetary Value Format
- ₹40k (for 40,000)
- ₹1.2L (for 120,000)
- ₹12L (for 1,200,000)

### Field Order
1. Property Title
2. Rent
3. Maintenance
4. Deposit
5. Sqft
6. Floor
7. Available from
8. Preferred tenant
9. Pets
10. Community (Gated/Semi-gated)
11. Location (locality only)
12. Society Name or Landmark
13. Google Maps Link
14. Finish Line

## Implementation Notes
These rules will be used by:
- `formatter/services/standardizer.ts`
- `formatter/services/aiFormatter.ts`
- `formatter/services/validator.ts`
