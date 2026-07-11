# ============================================================
# MedVisionAI Frontend — Dockerfile
# Uses Vite dev server for development hot-reload
# ============================================================

FROM node:20-alpine

WORKDIR /app

# Install dependencies first (layer cache optimisation)
COPY package.json package-lock.json* ./
RUN npm install

# Copy source
COPY . .

EXPOSE 5173

# --host makes Vite listen on all interfaces inside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
