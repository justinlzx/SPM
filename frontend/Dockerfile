# Use an official Node runtime as the base image
FROM node:20-alpine as build

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install git before npm install
RUN apk add --no-cache git

# Install dependencies
RUN git config --global url."git@github.com:".insteadOf git://github.com/

RUN npm ci

# Copy the rest of the application code
COPY . .

# Build the app
RUN npm run build --verbose

# Use nginx to serve the static files
FROM nginx:alpine

# Copy the build output to replace the default nginx contents.
COPY --from=build /app/build /usr/share/nginx/html

# Copy the nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]