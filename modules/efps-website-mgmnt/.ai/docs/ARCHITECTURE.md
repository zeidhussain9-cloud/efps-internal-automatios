# System Architecture

This project is a modern web application built using **React**, **TypeScript**, and **TanStack Start**. It leverages **Tailwind CSS 4** for styling and **Lucide React** for iconography.

## Core Technologies

| Technology | Purpose |
| :--- | :--- |
| **React 19** | Frontend UI library |
| **TanStack Start** | Full-stack React framework with built-in routing |
| **TypeScript** | Static typing for improved developer experience and safety |
| **Tailwind CSS 4** | Utility-first CSS framework for styling |
| **Vite** | Build tool and development server |

## Directory Structure

- `src/routes/`: Contains the application's routing logic and main page components.
- `src/components/`: Reusable UI components.
- `src/components/ui/`: Low-level UI primitives (e.g., buttons, inputs).
- `src/lib/`: Utility functions and external service integrations.
- `src/styles.css`: Global styles and Tailwind CSS configuration.
- `public/`: Static assets like images and fonts.

## Key Integrations

### Lead Capture System
The application uses a client-side lead capture system that submits data to **Google Forms**.
- **Implementation**: Forms use `POST` requests in `no-cors` mode to submit data to specific Google Form entry IDs.
- **Components**: `LeadForm.tsx` (main contact section) and `ContactForm.tsx` (hero section).
- **Service Logic**: Located in `src/lib/submitLead.ts`.

### Maps Integration
- **Google Maps Embed**: Uses a clean Place API embed URL to show the office location in Koramangala, Bangalore.

## Performance Optimization
- **Asset Compression**: The Open Graph image (`og-image.jpg`) is optimized to ~170KB to ensure fast social sharing previews.
- **Metadata Consolidation**: All SEO and social metadata is managed through the TanStack Router root layout (`src/routes/__root.tsx`) to ensure a single source of truth.

## Key Design Patterns

- **Component-Based Architecture**: UI is broken down into small, reusable components.
- **Route-Based Data Fetching**: Leveraging TanStack Router for efficient data management.
- **Utility-First Styling**: Using Tailwind CSS for consistent and rapid UI development.
- **Mobile-First Design**: Responsive layouts that work across all device sizes.
