const { defineConfig } = require("cypress");

module.exports = defineConfig({
  env: {
    frontend_url: "http://localhost:3000",
    backend_url: "http://localhost:8000",
  },
  e2e: {
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    viewportHeight: 1080,
    viewportWidth: 1920,
  },
});
