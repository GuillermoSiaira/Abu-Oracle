FROM node:18-alpine

WORKDIR /app

# Copiamos package.json
COPY package*.json ./

# Instalamos dependencias
RUN npm install

# Copiamos el resto del código
COPY . .

# ⬅️ ESTO ES LO QUE FALTA (MUY IMPORTANTE)
RUN npm run build

EXPOSE 3000

# ⬅️ Producción: ejecuta el build ya generado
CMD ["npm", "run", "start"]
