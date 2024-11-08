// eslint.config.js
import js from '@eslint/js';
import prettier from 'eslint-config-prettier';

export default [
    js.configs.recommended,
    prettier,
    {
        files: ['**/*.{js,jsx,ts,tsx}'],
        rules: {
            // Add your custom rules here
            'no-unused-vars': 'warn',
            'no-console': 'warn',
        },
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'module',
            jsx: true,
        },
    },
];