# ============================================================
# MedVisionAI Frontend — Production Dockerfile
# Stage 1: Build Vite app → dist/
# Stage 2: Serve dist/ with nginx, listening on Railway's $PORT
# ============================================================

# ── Stage 1: Build ────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies (cached layer)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build
# VITE_API_URL is passed as a build arg so it's baked into the JS bundle
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

COPY . .
RUN npm run build

# ── Stage 2: Serve ────────────────────────────────────────────
FROM nginx:stable-alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx template (uses ${PORT} placeholder)
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Railway injects PORT; nginx Docker image runs envsubst on /etc/nginx/templates/*.template
# and writes the result to /etc/nginx/conf.d/ at startup automatically.

EXPOSE 3000

# Default PORT if not injected (Railway always injects it)
ENV PORT=3000

CMD ["nginx", "-g", "daemon off;"]
