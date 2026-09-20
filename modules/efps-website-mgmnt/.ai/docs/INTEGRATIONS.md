# External Integrations

This document details the third-party services and APIs integrated into the EasyFind Property Solutions website.

## 1. Google Forms (Lead Capture)

The website uses Google Forms as a lightweight backend for capturing leads. This allows the business to manage submissions in a spreadsheet without requiring a custom database.

### Configuration
- **Endpoint**: `https://docs.google.com/forms/d/e/1FAIpQLScy2L0Y2V5N_T2Y9X1Z_W1Z1Z1Z1Z1Z1Z1Z1Z1Z1Z1Z1Z1Z1Z/formResponse` (Example)
- **Submission Mode**: `no-cors` (POST request)

### Form Fields Mapping
| Field Name | Google Form Entry ID | Description |
| :--- | :--- | :--- |
| `name` | `entry.123456789` | Full name of the lead |
| `phone` | `entry.987654321` | Contact phone number |
| `requirement` | `entry.456789123` | Type of service required |
| `location` | `entry.789123456` | Preferred location |
| `budget` | `entry.321654987` | Estimated budget |
| `details` | `entry.654321987` | Additional requirements |
| `formType` | `entry.128907828` | Identifier for form source (Hero vs Main) |

## 2. Google Maps

The office location is displayed using the Google Maps Embed API.

- **Location**: Prestige Atlanta, Koramangala, Bangalore.
- **Implementation**: `iframe` embed in `src/routes/index.tsx`.
- **Update Rule**: If the office moves, update the `src` attribute of the `iframe` and the `BUSINESS_CONFIG.address` object.

## 3. Deployment (Render)

The site is hosted on Render as a static site.

- **Domain**: `https://easyfindprops.com`
- **Auto-Deploy**: Enabled for the `main` branch.
- **SSL**: Managed automatically by Render.

## 4. Metadata & SEO

All SEO metadata is consolidated in `src/routes/__root.tsx` using the `Helmet` component.

- **Primary Domain**: `https://easyfindprops.com`
- **OG Image**: `/og-image.jpg` (Optimized for 1200x630px)
- **Social Previews**: Configured for Facebook (Open Graph) and Twitter Cards.
