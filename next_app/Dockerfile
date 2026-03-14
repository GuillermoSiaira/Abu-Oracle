FROM node:18-alpine AS builder

WORKDIR /app

# Copiamos package.json y lockfiles
COPY package*.json ./

# Instalamos dependencias
RUN npm install

# Copiamos todo el código
COPY . .

# 🔥 PASAMOS LAS VARIABLES AL BUILD DE NEXT
ARG OPENAI_API_KEY
ARG NEXT_PUBLIC_ABU_URL
ARG NEXT_PUBLIC_LILLY_URL
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV NEXT_PUBLIC_ABU_URL=$NEXT_PUBLIC_ABU_URL
ENV NEXT_PUBLIC_LILLY_URL=$NEXT_PUBLIC_LILLY_URL

ENV NODE_OPTIONS=--max_old_space_size=2048

# 🔥 AHORA SÍ: build sin romper
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

EXPOSE 3000

CMD ["npm", "run", "start"]
