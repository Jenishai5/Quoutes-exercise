# Frontend: nginx serves index.html and proxies /api/* to the backend container.
FROM nginx:alpine

# Replace the default nginx site config with ours.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Drop the static HTML into nginx's web root.
COPY index.html /usr/share/nginx/html/index.html

EXPOSE 80
