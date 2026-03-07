FROM oven/bun:latest AS builder

WORKDIR /app

COPY package*.json ./
RUN bun install

COPY . .

EXPOSE 5173