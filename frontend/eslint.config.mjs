import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({ baseDirectory: import.meta.dirname });

/** @type {import("eslint").Linter.Config[]} */
const config = [...compat.extends("next/core-web-vitals")];
export default config;
