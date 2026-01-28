# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy the code
COPY . .

# Exposes the Vite door
EXPOSE 5173

# Runs in development mode released for external network
CMD ["npm", "run", "dev", "--", "--host"]