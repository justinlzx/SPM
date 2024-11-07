// eslint.config.js
import globals from "globals";
import js from "@eslint/js";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import typescript from "@typescript-eslint/eslint-plugin";
import typescriptParser from "@typescript-eslint/parser";

export default [
  {
    files: ["**/*.{js,mjs,cjs,jsx,ts,tsx}"],
    languageOptions: {
      globals: {
        ...globals.builtin,
        ...globals.browser,
        ...globals.node,
      },
      parser: typescriptParser,
      parserOptions: {
        ecmaVersion: "latest",
        ecmaFeatures: {
          jsx: true,
        },
        sourceType: "module",
      },
    },
    plugins: {
      react: {
        version: "18.3.1",
      },
      "react-hooks": reactHooks,
      "@typescript-eslint": typescript,
    },
    rules: {
      ...js.configs.recommended.rules,
      // ...react.configs.recommended.rules,
      ...typescript.configs.recommended.rules,
      // "@typescript-eslint/no-unused-vars": "off",
      "react/jsx-key": "off",
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
];
