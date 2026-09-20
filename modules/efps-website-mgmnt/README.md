# EasyFind Property Solutions

EasyFind Property Solutions is a property services website for Bangalore covering rentals, property sales, property management, NRI assistance, and investment advisory.

The project also includes an internal property formatter at `/formatter` for turning raw listing details, WhatsApp messages, and Google Maps links into a standardized listing format.

**Live app**: Not published yet. Use the Replit Preview while developing.

## Development

You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
npm install
npm run dev
```

The development server listens on port 5000 and includes the formatter API.

## Available routes

- `/` — EasyFind landing page and contact form
- `/formatter` — Internal property formatter
- `/api/formatter/health` — Formatter API health check

## Optional configuration

Add `GOOGLE_PLACES_API_KEY` as an environment variable to enable location resolution from Google Maps URLs. The main site and deterministic formatter work without additional secrets.

## Production

```sh
npm run build
npm run start
```

The production server serves the built site and formatter API together.
