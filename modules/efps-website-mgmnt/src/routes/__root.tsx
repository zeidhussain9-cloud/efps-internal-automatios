import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Outlet, Link, createRootRouteWithContext, useRouter } from "@tanstack/react-router";
import { Helmet, HelmetProvider } from "react-helmet-async";

import "../styles.css";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Page not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          This page didn't load
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Something went wrong on our end. You can try refreshing or head back home.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Try again
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Go home
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <HelmetProvider>
      <QueryClientProvider client={queryClient}>
        <Helmet>
          <meta charSet="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>EasyFind Property Solutions | Bangalore's Trusted Property Partner</title>
          <meta
            name="description"
            content="Find, Own, and Manage property in Bangalore. Professional rental services, property management, and investment advisory with 4.9★ rating."
          />
          <meta name="author" content="EasyFind Property Solutions" />
          <meta
            property="og:title"
            content="EasyFind Property Solutions | Bangalore's Trusted Property Partner"
          />
          <meta
            property="og:description"
            content="Find, Own, and Manage property in Bangalore. Professional rental services, property management, and investment advisory with 4.9★ rating."
          />
          <meta property="og:type" content="website" />
          <meta property="og:url" content="https://easyfindprops.com" />
          <meta property="og:image" content="https://easyfindprops.com/og-image.jpg" />
          <meta property="og:image:width" content="1200" />
          <meta property="og:image:height" content="630" />
          <meta name="twitter:card" content="summary_large_image" />
          <meta
            name="twitter:title"
            content="EasyFind Property Solutions | Bangalore's Trusted Property Partner"
          />
          <meta
            name="twitter:description"
            content="Find, Own, and Manage property in Bangalore. Professional rental services, property management, and investment advisory with 4.9★ rating."
          />
          <meta name="twitter:image" content="https://easyfindprops.com/og-image.jpg" />

          <link rel="icon" href="/easyfind-logo.webp" type="image/webp" />
          <link rel="canonical" href="https://easyfindprops.com" />
          <link rel="preconnect" href="https://fonts.googleapis.com" />
          <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
          <link
            rel="stylesheet"
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap"
          />
        </Helmet>
        <Outlet />
      </QueryClientProvider>
    </HelmetProvider>
  );
}
