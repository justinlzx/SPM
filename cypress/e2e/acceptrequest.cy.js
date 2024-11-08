const manager_id = 170166;
const manager_email = "david.yap@allinone.com.sg";
const subordinate_id = 171014;
const subordinate_email = "narong.pillai@allinone.com.sg";

describe("Testing accept request", () => {
  it("Should create a request and then have it approved by a mid-level manager", () => {
    // Step 1: Login as Narong Pillai and create a WFH request
    cy.visit("http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(subordinate_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Navigate to create request page
    cy.get('[data-cy="create-request"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/create-request");

    // Fill in the form and submit
    cy.get('[name="reason"]').type("Working on project X");
    cy.get('[data-cy="wfhType"]').click();
    cy.get('li[data-value="full"]').click();
    cy.get('[data-cy="start-datepicker"]').click();
    cy.get(".react-datepicker__day--026").click();
    cy.get('[data-cy="submit-request"]').click();

    // Capture the latest request arrangement_id
    cy.request(
      `http://localhost:8000/arrangements/personal/${subordinate_id}`
    ).then((response) => {
      expect(response.body).to.have.property("data");
      const arrangements = response.body.data;
      const latestRequest = arrangements.reduce((latest, current) =>
        new Date(current.update_datetime) > new Date(latest.update_datetime)
          ? current
          : latest
      );
      cy.wrap(latestRequest.arrangement_id).as("latestArrangementId");
    });

    // Step 2: Log out and log in as David Yap
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(manager_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 3: Access the review requests page and approve Rahim's request
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.get("@latestArrangementId").then((latestArrangementId) => {
      // Wait until the approve button for the specific request is available
      cy.get(`[data-cy="approve-button-${latestArrangementId}"]`, {
        timeout: 10000,
      })
        .should("be.visible")
        .click();
    });

    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "WFH Request successfully updated to 'approved'");
  });
});

describe("Testing reject request", () => {
  it("Should create a request and then have it rejected by a manager", () => {
    // Step 1: Login as Rahim and create a WFH request
    cy.visit("http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(subordinate_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Navigate to create request page
    cy.get('[data-cy="create-request"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/create-request");

    // Fill in the form and submit
    cy.get('[name="reason"]').type("Working on project X");
    cy.get('[data-cy="wfhType"]').click();
    cy.get('li[data-value="full"]').click();
    cy.get('[data-cy="start-datepicker"]').click();
    cy.get(".react-datepicker__day--026").click();
    cy.get('[data-cy="submit-request"]').click();

    // Capture the latest request arrangement_id
    cy.request(
      `http://localhost:8000/arrangements/personal/${subordinate_id}`
    ).then((response) => {
      expect(response.body).to.have.property("data");
      const arrangements = response.body.data;
      const latestRequest = arrangements.reduce((latest, current) =>
        new Date(current.update_datetime) > new Date(latest.update_datetime)
          ? current
          : latest
      );
      cy.wrap(latestRequest.arrangement_id).as("latestArrangementId");
    });

    // Step 2: Log out and log in as Derek
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(manager_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 3: Access the review requests page and approve Rahim's request
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.get("@latestArrangementId").then((latestArrangementId) => {
      // Wait until the reject button for the specific request is available
      cy.get(`[data-cy="reject-button-${latestArrangementId}"]`, {
        timeout: 10000,
      })
        .should("be.visible")
        .click();
    });

    // Reject action with an alert or message assertion
    cy.get('[data-cy="rejection-modal"]').click().type("test");
    cy.get('[data-cy="reject-modal-button"]').click();
    // Confirm the reject action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "WFH Request successfully updated to 'rejected'");
  });
});

describe("Testing reject request, then press cancel, then press approve", () => {
  it("Should create a request and then have it rejected by a manager", () => {
    // Step 1: Login as Rahim and create a WFH request
    cy.visit("http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(subordinate_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Navigate to create request page
    cy.get('[data-cy="create-request"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/create-request");

    // Fill in the form and submit
    cy.get('[name="reason"]').type("Working on project X");
    cy.get('[data-cy="wfhType"]').click();
    cy.get('li[data-value="full"]').click();
    cy.get('[data-cy="start-datepicker"]').click();
    cy.get(".react-datepicker__day--026").click();
    cy.get('[data-cy="submit-request"]').click();

    // Capture the latest request arrangement_id
    cy.request(
      `http://localhost:8000/arrangements/personal/${subordinate_id}`
    ).then((response) => {
      expect(response.body).to.have.property("data");
      const arrangements = response.body.data;
      const latestRequest = arrangements.reduce((latest, current) =>
        new Date(current.update_datetime) > new Date(latest.update_datetime)
          ? current
          : latest
      );
      cy.wrap(latestRequest.arrangement_id).as("latestArrangementId");
    });

    // Step 2: Log out and log in as Derek
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(manager_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 3: Access the review requests page and approve Rahim's request
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.get("@latestArrangementId").then((latestArrangementId) => {
      // Wait until the reject button for the specific request is available
      cy.get(`[data-cy="reject-button-${latestArrangementId}"]`, {
        timeout: 10000,
      })
        .should("be.visible")
        .click();
    });

    // Reject action with an alert or message assertion
    cy.get('[data-cy="rejection-modal"]').click().type("test");
    cy.get('[data-cy="cancel-modal-button"]').click();
    cy.url().should("eq", "http://localhost:3000/review-requests");
  });
});

describe("Testing reject request, then press cancel, then press approve", () => {
  it("Should create a request and then have it rejected by a manager", () => {
    // Step 1: Login as Rahim and create a WFH request
    cy.visit("http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(subordinate_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Navigate to create request page
    cy.get('[data-cy="create-request"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/create-request");

    // Fill in the form and submit
    cy.get('[name="reason"]').type("Working on project X");
    cy.get('[data-cy="wfhType"]').click();
    cy.get('li[data-value="full"]').click();
    cy.get('[data-cy="start-datepicker"]').click();
    cy.get(".react-datepicker__day--026").click();
    cy.get('[data-cy="submit-request"]').click();

    // Capture the latest request arrangement_id
    cy.request(
      `http://localhost:8000/arrangements/personal/${subordinate_id}`
    ).then((response) => {
      expect(response.body).to.have.property("data");
      const arrangements = response.body.data;
      const latestRequest = arrangements.reduce((latest, current) =>
        new Date(current.update_datetime) > new Date(latest.update_datetime)
          ? current
          : latest
      );
      cy.wrap(latestRequest.arrangement_id).as("latestArrangementId");
    });

    // Step 2: Log out and log in as Derek
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(manager_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 3: Access the review requests page and approve Rahim's request
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.get("@latestArrangementId").then((latestArrangementId) => {
      // Wait until the reject button for the specific request is available
      cy.get(`[data-cy="reject-button-${latestArrangementId}"]`, {
        timeout: 10000,
      })
        .should("be.visible")
        .click();
    });

    // Reject action with an alert or message assertion
    cy.get('[data-cy="rejection-modal"]').click().type("test");
    cy.get('[data-cy="cancel-modal-button"]').click();
    cy.url().should("eq", "http://localhost:3000/review-requests");
    // Confirm the approval action with an alert or message assertion
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.get("@latestArrangementId").then((latestArrangementId) => {
      // Wait until the approve button for the specific request is available
      cy.get(`[data-cy="approve-button-${latestArrangementId}"]`, {
        timeout: 10000,
      })
        .should("be.visible")
        .click();
    });

    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "WFH Request successfully updated to 'approved'");
  });
});
