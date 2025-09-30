# Multi-stage Dockerfile for MBTI Travel Frontend

# Build stage
FROM node:20.19.0-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Build application
ARG BUILD_MODE=production
ENV NODE_ENV=production
RUN npm run build:${BUILD_MODE}

# Production stage
FROM nginx:1.25-alpine AS production

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache curl

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy security headers configuration
COPY --from=builder /app/dist/_headers /etc/nginx/conf.d/security-headers.conf

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 && \
    chown -R nextjs:nodejs /usr/share/nginx/html && \
    chown -R nextjs:nodejs /var/cache/nginx && \
    chown -R nextjs:nodejs /var/log/nginx && \
    chown -R nextjs:nodejs /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nextjs:nodejs /var/run/nginx.pid

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]