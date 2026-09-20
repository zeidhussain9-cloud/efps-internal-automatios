# Use Node.js 20 alpine as the base image
FROM node:20-alpine

# Set working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install all dependencies (required for tsx and typescript build)
RUN npm ci

# Copy the rest of the application source files
COPY . .

# Build the front-end SPA static assets (produces the dist/ folder)
RUN npm run build

# Set the environment variable for production
ENV NODE_ENV=production
ENV PORT=3000

# Expose the default port
EXPOSE 3000

# Start the Express server which serves the client SPA and /api endpoints
CMD ["npm", "run", "start"]
