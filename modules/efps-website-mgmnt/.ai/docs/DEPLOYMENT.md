# Deployment Flow

This application is designed to be deployed on **Render** with automatic synchronization from **GitHub**.

## Build Settings

- **Build Command**: `pnpm build`
- **Publish Directory**: `dist` (or the directory specified in your Vite config)
- **Node Version**: 20+
- **Package Manager**: `pnpm`

## Environment Variables

Ensure the following environment variables are configured in the deployment environment if needed:

- `VITE_API_URL`: Base URL for API requests (if applicable).

## Verification Process

Before considering a deployment successful, verify:

1.  **Build Success**: The Render build log shows no errors.
2.  **Live URL**: The application is accessible at the provided Render URL.
3.  **Functionality**: Core features (e.g., contact forms, navigation) work as expected in the production environment.
4.  **Assets**: All images and fonts load correctly.
