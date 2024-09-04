# Use a lightweight web server as the base image
FROM nginx:alpine

# Copy the website files to the appropriate directory in the container
COPY . /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# The default command will start Nginx
CMD ["nginx", "-g", "daemon off;"]
