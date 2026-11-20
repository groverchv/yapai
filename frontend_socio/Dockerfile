# Portal socio — SvelteKit adapter-node
FROM node:26-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build && npm prune --omit=dev

FROM node:26-alpine
WORKDIR /app
ENV NODE_ENV=production PORT=3000
COPY --from=build /app/build ./build
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/node_modules ./node_modules
USER node
EXPOSE 3000
# PUBLIC_API_BASE se lee en runtime: ej. https://api.tudominio.com/api/v1
CMD ["node", "build"]
