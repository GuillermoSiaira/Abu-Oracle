FROM node:18-alpine AS builder

WORKDIR /app

# Copiamos package.json y lockfiles
COPY package*.json ./

# Instalamos dependencias
RUN npm install

# Copiamos todo el código
COPY . .

# 🔥 PASAMOS LA VARIABLE AL BUILD DE NEXT
ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=$OPENAI_API_KEY

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
