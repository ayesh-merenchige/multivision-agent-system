FROM node:20-alpine AS deps
WORKDIR /srv/frontend
COPY package.json ./
RUN npm install --no-audit --no-fund

FROM node:20-alpine AS builder
WORKDIR /srv/frontend
COPY --from=deps /srv/frontend/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /srv/frontend
ENV NODE_ENV=production
COPY --from=builder /srv/frontend/.next ./.next
COPY --from=builder /srv/frontend/node_modules ./node_modules
COPY --from=builder /srv/frontend/package.json ./package.json
COPY --from=builder /srv/frontend/next.config.mjs ./next.config.mjs

EXPOSE 3000
CMD ["npm", "start"]
