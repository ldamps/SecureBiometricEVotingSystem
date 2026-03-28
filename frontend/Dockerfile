# --- Stage 1: Build the React app ---
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# --- Stage 2: Serve with Nginx ---
FROM nginx:alpine

# Generate a self-signed SSL certificate for HTTPS
RUN apk add --no-cache openssl \
 && mkdir -p /etc/nginx/ssl \
 && openssl req -x509 -nodes -days 365 \
      -newkey rsa:2048 \
      -keyout /etc/nginx/ssl/selfsigned.key \
      -out    /etc/nginx/ssl/selfsigned.crt \
      -subj   "/C=GB/ST=Aberdeen/L=Aberdeen/O=SecureBiometricEVoting/CN=localhost"

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
