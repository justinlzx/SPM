const manager_id = 170166;
const manager_email = "david.yap@allinone.com.sg";
const subordinate_id = 171014;
const subordinate_email = "narong.pillai@allinone.com.sg";

describe("Testing withdraw request", () => {
  it("Should create a request and then have it approved by a manager, and then withdraw request", () => {
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

    // Step 4: Log out and log in as Rahim again
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(subordinate_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 5: Go to wfh-schedule and withdraw
    cy.get('[data-cy="my-wfh-schedule"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/wfh-schedule");

    cy.request(
      `http://localhost:8000/arrangements/personal/${subordinate_id}`
    ).then((response) => {
      // Log the entire response to debug
      console.log("Response:", response);

      expect(response.body).to.have.property("data"); // Check if data property exists
      const arrangements = response.body.data;

      // Check if arrangements is an array and has items
      expect(arrangements).to.be.an("array").and.not.to.be.empty;

      // Find the latest arrangement using reduce
      const latestRequest = arrangements.reduce((latest, current) => {
        return new Date(current.update_datetime) >
          new Date(latest.update_datetime)
          ? current
          : latest;
      });

      // Get the arrangement_id of the latest request
      const latestArrangementId = latestRequest.arrangement_id;

      // Click the withdraw button
      cy.get(`[data-cy="withdraw-button-${latestArrangementId}"]`).click();

      // Type something in the withdraw textbox
      cy.get('[data-cy="withdrawal-reason"]')
        .click()
        .type("i dont want anymore");

      // Click the yes button
      cy.get('[data-cy="yes-button"]').click();

      // Add assertions to verify the cancel action was successful
      cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
        .should("be.visible")
        .and(
          "contain",
          "Withdrawal Request has been sent to your manager for review."
        );
    });
  });
});

describe("Testing withdraw request, when withdrawing, press no", () => {
  it("Should create a request and then have it approved by a manager, then attempt to withdraw but change his mind and press no", () => {
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

    // Step 4: Log out and log in as Rahim again
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(subordinate_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 5: Go to wfh-schedule and withdraw
    cy.get('[data-cy="my-wfh-schedule"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/wfh-schedule");

    cy.request(
      `http://localhost:8000/arrangements/personal/${subordinate_id}`
    ).then((response) => {
      // Log the entire response to debug
      console.log("Response:", response);

      expect(response.body).to.have.property("data"); // Check if data property exists
      const arrangements = response.body.data;

      // Check if arrangements is an array and has items
      expect(arrangements).to.be.an("array").and.not.to.be.empty;

      // Find the latest arrangement using reduce
      const latestRequest = arrangements.reduce((latest, current) => {
        return new Date(current.update_datetime) >
          new Date(latest.update_datetime)
          ? current
          : latest;
      });

      // Get the arrangement_id of the latest request
      const latestArrangementId = latestRequest.arrangement_id;

      // Click the withdraw button
      cy.get(`[data-cy="withdraw-button-${latestArrangementId}"]`).click();

      // Type something in the withdraw textbox
      cy.get('[data-cy="withdrawal-reason"]')
        .click()
        .type("actually i changed my mind");

      // Click the yes button
      cy.get('[data-cy="no-button"]').click();

      // Add assertions to verify the cancel action was successful
      cy.url().should("eq", "http://localhost:3000/wfh-schedule");
    });
  });
});

describe("Testing withdraw request, Manager should approve withdrawal too", () => {
  it("Should create a request and then have it approved by a manager, and then withdraw request, with manager approval now", () => {
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

    // Step 3: Access the review requests page and approve Narong Pillai's request
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

    // Step 4: Log out and log in as Narong Pillai again
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(subordinate_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 5: Go to wfh-schedule and withdraw
    cy.get('[data-cy="my-wfh-schedule"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/wfh-schedule");

    cy.request(
      `http://localhost:8000/arrangements/personal/${subordinate_id}`
    ).then((response) => {
      // Log the entire response to debug
      console.log("Response:", response);

      expect(response.body).to.have.property("data"); // Check if data property exists
      const arrangements = response.body.data;

      // Check if arrangements is an array and has items
      expect(arrangements).to.be.an("array").and.not.to.be.empty;

      // Find the latest arrangement using reduce
      const latestRequest = arrangements.reduce((latest, current) => {
        return new Date(current.update_datetime) >
          new Date(latest.update_datetime)
          ? current
          : latest;
      });

      // Get the arrangement_id of the latest request
      const latestArrangementId = latestRequest.arrangement_id;

      // Click the withdraw button
      cy.get(`[data-cy="withdraw-button-${latestArrangementId}"]`).click();

      // Type something in the withdraw textbox
      cy.get('[data-cy="withdrawal-reason"]')
        .click()
        .type("i dont want anymore");

      // Click the yes button
      cy.get('[data-cy="yes-button"]').click();

      // Add assertions to verify the cancel action was successful
      cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
        .should("be.visible")
        .and(
          "contain",
          "Withdrawal Request has been sent to your manager for review."
        );

      // Step 6: Log out and log in as David Yap
      cy.get('[data-cy="logout"]').click();
      cy.url().should("eq", "http://localhost:3000/login");
      cy.get('[data-cy="email"]').type(manager_email);
      cy.get('[data-cy="password"]').type("password");
      cy.get('[data-cy="submit"]').click();
      cy.url().should("eq", "http://localhost:3000/home");

      // Step 7: Access the review requests page and approve Rahim's withdrawal request
      cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
      cy.url().should("eq", "http://localhost:3000/review-requests");

      cy.get("@latestArrangementId").then((latestArrangementId) => {
        // Wait until the approve button for the specific request is available
        cy.get(`[data-cy="withdraw-button-${latestArrangementId}"]`, {
          timeout: 10000,
        })
          .should("be.visible")
          .click();
      });

      // Confirm the approval action with an alert or message assertion
      cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
        .should("be.visible")
        .and("contain", "WFH Request successfully updated to 'withdrawn'");
    });
  });
});

describe("Testing withdraw request, Manager should reject withdrawal", () => {
  it("Should create a request and then have it approved by a manager, and then withdraw request, with manager approval now", () => {
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

    // Step 4: Log out and log in as Narong Pillai again
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(subordinate_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 5: Go to wfh-schedule and withdraw
    cy.get('[data-cy="my-wfh-schedule"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/wfh-schedule");

    cy.request(
      `http://localhost:8000/arrangements/personal/${subordinate_id}`
    ).then((response) => {
      // Log the entire response to debug
      console.log("Response:", response);

      expect(response.body).to.have.property("data"); // Check if data property exists
      const arrangements = response.body.data;

      // Check if arrangements is an array and has items
      expect(arrangements).to.be.an("array").and.not.to.be.empty;

      // Find the latest arrangement using reduce
      const latestRequest = arrangements.reduce((latest, current) => {
        return new Date(current.update_datetime) >
          new Date(latest.update_datetime)
          ? current
          : latest;
      });

      // Get the arrangement_id of the latest request
      const latestArrangementId = latestRequest.arrangement_id;

      // Click the withdraw button
      cy.get(`[data-cy="withdraw-button-${latestArrangementId}"]`).click();

      // Type something in the withdraw textbox
      cy.get('[data-cy="withdrawal-reason"]')
        .click()
        .type("i dont want anymore");

      // Click the yes button
      cy.get('[data-cy="yes-button"]').click();

      // Add assertions to verify the cancel action was successful
      cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
        .should("be.visible")
        .and(
          "contain",
          "Withdrawal Request has been sent to your manager for review."
        );

      // Step 6: Log out and log in as David Yap
      cy.get('[data-cy="logout"]').click();
      cy.url().should("eq", "http://localhost:3000/login");
      cy.get('[data-cy="email"]').type(manager_email);
      cy.get('[data-cy="password"]').type("password");
      cy.get('[data-cy="submit"]').click();
      cy.url().should("eq", "http://localhost:3000/home");

      // Step 7: Access the review requests page and reject Rahim's withdrawal request
      cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
      cy.url().should("eq", "http://localhost:3000/review-requests");

      cy.get("@latestArrangementId").then((latestArrangementId) => {
        // Wait until the approve button for the specific request is available
        cy.get(`[data-cy="reject-button-${latestArrangementId}"]`, {
          timeout: 10000,
        })
          .should("be.visible")
          .click();
      });

      cy.get('[data-cy="rejection-modal"]').click().type("No you must WFH");
      cy.get('[data-cy="reject-modal-button"]').click();

      // Confirm the approval action with an alert or message assertion
      cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
        .should("be.visible")
        .and("contain", "WFH Request successfully updated to 'rejected'");
    });
  });
});
