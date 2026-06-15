FROM node:18-alpine AS builder

WORKDIR /app

# Copiamos package.json y lockfiles
COPY package*.json ./

# Instalamos dependencias
RUN npm install

# Copiamos todo el código
COPY . .

# Variables que se hornean en el bundle cliente (NEXT_PUBLIC_*)
ARG NEXT_PUBLIC_ABU_URL
ARG NEXT_PUBLIC_LILLY_URL
ARG NEXT_PUBLIC_FIREBASE_API_KEY
ARG NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
ARG NEXT_PUBLIC_FIREBASE_PROJECT_ID
ARG NEXT_PUBLIC_APP_URL
ARG NEXT_PUBLIC_OPERATOR_UID

ENV NEXT_PUBLIC_ABU_URL=$NEXT_PUBLIC_ABU_URL
ENV NEXT_PUBLIC_LILLY_URL=$NEXT_PUBLIC_LILLY_URL
ENV NEXT_PUBLIC_FIREBASE_API_KEY=$NEXT_PUBLIC_FIREBASE_API_KEY
ENV NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=$NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
ENV NEXT_PUBLIC_FIREBASE_PROJECT_ID=$NEXT_PUBLIC_FIREBASE_PROJECT_ID
ENV NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL
ENV NEXT_PUBLIC_OPERATOR_UID=$NEXT_PUBLIC_OPERATOR_UID

ENV NODE_OPTIONS=--max_old_space_size=2048

RUN npm run build

# ============================================================
# FASE FINAL — Imagen limpia de producción
# ============================================================

FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# Copiamos lo necesario desde el build
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/data ./data

EXPOSE 3000

CMD ["npm", "run", "start"]
