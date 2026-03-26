FROM nginx:alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/gateway.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
