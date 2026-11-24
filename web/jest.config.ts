import type { Config } from "jest";
import nextJest from "next/jest.js";

const createJestConfig = nextJest({ dir: "./" });

const config: Config = {
  coverageProvider: "v8",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "^server-only$": "<rootDir>/jest.server-only.ts",
  },
  testPathIgnorePatterns: ["/node_modules/", "/e2e/", "/.next/"],
  // Never let a run saturate the machine (CLAUDE.md guardrail): the harness also passes --maxWorkers=1
  maxWorkers: 1,
};

export default createJestConfig(config);
