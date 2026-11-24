# Docket web (Next.js) for on-prem deployments. On Vercel this file is not used.
FROM node:22-slim AS build
RUN corepack enable && corepack prepare pnpm@10.18.0 --activate
WORKDIR /srv/web
COPY web/package.json web/pnpm-lock.yaml web/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY web ./
RUN pnpm build

FROM node:22-slim
RUN corepack enable && corepack prepare pnpm@10.18.0 --activate
WORKDIR /srv/web
ENV NODE_ENV=production
COPY --from=build /srv/web ./
EXPOSE 3000
CMD ["pnpm", "exec", "next", "start", "-p", "3000"]
