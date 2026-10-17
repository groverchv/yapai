# Portal socio/kiosco/terminal — SvelteKit adapter-node
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production PORT=3000
COPY --from=build /app/build ./build
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/node_modules ./node_modules
EXPOSE 3000
# PUBLIC_API_BASE se lee en runtime: ej. https://api.tudominio.com/api/v1
CMD ["node", "build"]
