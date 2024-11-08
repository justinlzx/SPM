const delegator_manager_id = 171014;
const delegator_manager_email = "narong.pillai@allinone.com.sg";
const delegator_manager_name = "Narong Pillai";
const delegatee_manager_id = 171029;
const delegatee_manager_email = "chandra.kong@allinone.com.sg";
const delegatee_manager_name = "Chandra Kong";
const subordinate_id = 171010;
const subordinate_email = "rithy.saad@allinone.com.sg";

describe("Testing delegation (Happy path) w Cancel", () => {
  it("Should create a request and then have it approved by a manager, then cancel to test other functions", () => {
    // Step 1: Login as Rithy Saad and create a WFH request
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
    cy.request("http://localhost:8000/arrangements/personal/140894").then(
      (response) => {
        expect(response.body).to.have.property("data");
        const arrangements = response.body.data;
        const latestRequest = arrangements.reduce((latest, current) =>
          new Date(current.update_datetime) > new Date(latest.update_datetime)
            ? current
            : latest
        );
        cy.wrap(latestRequest.arrangement_id).as("latestArrangementId");
      }
    );

    // Step 2: Log out and log in as Narong Pillai
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(delegator_manager_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 3: Access the review requests page to see if the request exists
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.request(
      `http://localhost:8000/arrangements/subordinates/${delegator_manager_id}`
    ).then((response) => {
      // Log the entire response to debug
      console.log("Response:", response);

      expect(response.body).to.have.property("data"); // Check if data property exists
      const arrangements = response.body.data;

      // Check if arrangements is an array and has items
      expect(arrangements).to.be.an("array").and.not.to.be.empty;
    });

    // Step 4: Access the delegation page
    cy.get('[data-cy="delegation"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/delegate");
    cy.get('[data-cy="Delegate-A-Manager"]').click();

    // Step 5: Choose a delegatee
    cy.get('[data-cy="select-peer-dropdown"]').should("be.visible").click();
    cy.get('[role="option"]').first().click();
    cy.get('[data-cy="delegate-manager-button"]').click();
    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "Request to delegate peer manager sent");

    // Step 6: Proceed to Chandra Kong's Account
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(delegatee_manager_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 7: Access the delegation page
    cy.get('[data-cy="delegation"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/delegate");
    cy.get('[data-cy="accept-delegation"]').click();
    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "Delegation request accepted successfully!");

    // Step 8: Access the review requests page to see if requests exist
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.request(
      `http://localhost:8000/arrangements/subordinates/${delegatee_manager_id}`
    ).then((response) => {
      // Log the entire response to debug
      console.log("Response:", response);

      expect(response.body).to.have.property("data"); // Check if data property exists
      const arrangements = response.body.data;

      // Check if arrangements is an array and has items
      expect(arrangements).to.be.an("array").and.not.to.be.empty;
    });

    // Step 9: Log out and log in as Rithy Saad to check if delegations have been accepted
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(delegator_manager_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");
    cy.get('[data-cy="delegation"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/delegate");
    // Check if there is a row with "Accepted" status in the delegations table
    cy.get("table").each(() => {
      // Find the row with Delegation Status "Accepted"
      cy.contains("tr", "Accepted").within(() => {
        // Check that the delegated manager name is "Chandra Kong"
        cy.get("td").eq(1).should("have.text", delegatee_manager_name);

        // Verify the Delegation Status column has "Accepted"
        cy.get("td").eq(3).should("have.text", "Accepted");
      });
    });

    // Step 10: Click on the cancel button
    cy.get('[data-cy="cancel-delegation-button"]').click();
    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "Delegation canceled successfully.");
  });
});

describe("Testing delegation Reject delegation request", () => {
  it("Should create a request and delegatee rejects it", () => {
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

    // Step 2: Log out and log in as Narong Pillai
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(delegator_manager_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 3: Access the review requests page to see if the request exists
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.request(
      `http://localhost:8000/arrangements/subordinates/${delegator_manager_id}`
    ).then((response) => {
      // Log the entire response to debug
      console.log("Response:", response);

      expect(response.body).to.have.property("data"); // Check if data property exists
      const arrangements = response.body.data;

      // Check if arrangements is an array and has items
      expect(arrangements).to.be.an("array").and.not.to.be.empty;
    });

    // Step 4: Access the delegation page
    cy.get('[data-cy="delegation"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/delegate");
    cy.get('[data-cy="Delegate-A-Manager"]').click();

    // Step 5: Choose a delegatee
    cy.get('[data-cy="select-peer-dropdown"]').should("be.visible").click();
    cy.get('[role="option"]').eq(2).click(); //chooses the third option
    cy.get('[data-cy="delegate-manager-button"]').click();
    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "Request to delegate peer manager sent");

    // Step 6: Proceed to Chandra Kong's Account
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(delegatee_manager_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 7: Access the delegation page
    cy.get('[data-cy="delegation"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/delegate");
    cy.get('[data-cy="reject-delegation"]').click();
    cy.get('[data-cy="RejectDelegationModal"]')
      .click()
      .type("I am also going on holiday, delegate someone else!");
    cy.get('[data-cy="RejectDelegationModalConfirm"]').click();
  });
});

describe("Testing delegation cancelling the reject delegation request and then accepting it", () => {
  it("Should create a delegate request, want to reject but then changed mind and accepts it", () => {
    // Step 1: Login as Rithy Saad and create a WFH request
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

    // Step 2: Log out and log in as Narong Pillai
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(delegator_manager_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 3: Access the review requests page to see if the request exists
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.request(
      `http://localhost:8000/arrangements/subordinates/${delegator_manager_id}`
    ).then((response) => {
      // Log the entire response to debug
      console.log("Response:", response);

      expect(response.body).to.have.property("data"); // Check if data property exists
      const arrangements = response.body.data;

      // Check if arrangements is an array and has items
      expect(arrangements).to.be.an("array").and.not.to.be.empty;
    });

    // Step 4: Access the delegation page
    cy.get('[data-cy="delegation"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/delegate");
    cy.get('[data-cy="Delegate-A-Manager"]').click();

    // Step 5: Choose a delegatee
    cy.get('[data-cy="select-peer-dropdown"]').should("be.visible").click();
    cy.get('[role="option"]').eq(2).click(); //chooses the third option
    cy.get('[data-cy="delegate-manager-button"]').click();
    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "Request to delegate peer manager sent");

    // Step 6: Proceed to Chandra Kong's Account
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type(delegatee_manager_email);
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 7: Access the delegation page, Reject, type something in, then cancel
    cy.get('[data-cy="delegation"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/delegate");
    cy.get('[data-cy="reject-delegation"]').click();
    cy.get('[data-cy="RejectDelegationModal"]')
      .click()
      .type("I am also going on holiday, delegate someone else!");
    cy.get('[data-cy="RejectDelegationModalCancel"]').click();

    cy.url().should("eq", "http://localhost:3000/delegate");
    cy.get('[data-cy="accept-delegation"]').click();
    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "Delegation request accepted successfully!");

    // Step 8: Access the review requests page to see if requests exist
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.request(
      `http://localhost:8000/arrangements/subordinates/${delegatee_manager_id}`
    ).then((response) => {
      // Log the entire response to debug
      console.log("Response:", response);

      expect(response.body).to.have.property("data"); // Check if data property exists
      const arrangements = response.body.data;

      // Check if arrangements is an array and has items
      expect(arrangements).to.be.an("array").and.not.to.be.empty;
    });

    // Step 9: Log out and log in as Derek to check if delegations have been accepted
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type("Derek.Tan@allinone.com.sg");
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");
    cy.get('[data-cy="delegation"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/delegate");
    // Check if there is a row with "Accepted" status in the delegations table
    cy.get("table").within(() => {
      // Find the row with Delegation Status "Accepted"
      cy.contains("tr", "Accepted").within(() => {
        // Check that the delegated manager name is "Eric Loh" (or the expected manager name)
        cy.get("td").eq(1).should("have.text", "Sally Loh");

        // Verify the Delegation Status column has "Accepted"
        cy.get("td").eq(3).should("have.text", "Accepted");
      });
    });

    // Step 9: Click on the cancel button
    cy.get('[data-cy="cancel-delegation-button"]').click();
    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "Delegation canceled successfully.");
  });
});

describe("Testing delegation by accessing it through the button in the homepage", () => {
  it("Should create a request via homepage and then have it approved by a manager", () => {
    // Step 1: Login as Jack Goh and create a WFH request via accessing the create form thru the homepage
    cy.visit("http://localhost:3000/login");
    cy.get('[data-cy="email"]').type("jack.goh@allinone.com.sg");
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Navigate to create request page
    cy.get('[data-cy="home-page-create-request-button"]').click();
    cy.url().should("eq", "http://localhost:3000/create-request");

    // Fill in the form and submit
    cy.get('[name="reason"]').type("Working on project X");
    cy.get('[data-cy="wfhType"]').click();
    cy.get('li[data-value="full"]').click();
    cy.get('[data-cy="start-datepicker"]').click();
    cy.get(".react-datepicker__day--026").click();
    cy.get('[data-cy="submit-request"]').click();

    // Capture the latest request arrangement_id
    cy.request("http://localhost:8000/arrangements/personal/160076").then(
      (response) => {
        expect(response.body).to.have.property("data");
        const arrangements = response.body.data;
        const latestRequest = arrangements.reduce((latest, current) =>
          new Date(current.update_datetime) > new Date(latest.update_datetime)
            ? current
            : latest
        );
        cy.wrap(latestRequest.arrangement_id).as("latestArrangementId");
      }
    );

    // Step 2: Log out and log in as Sally Loh
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type("Sally.loh@allinone.com.sg");
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 3: Access the review requests page to see if the request exists
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.request(
      `http://localhost:8000/arrangements/subordinates/${160008}`
    ).then((response) => {
      // Log the entire response to debug
      console.log("Response:", response);

      expect(response.body).to.have.property("data"); // Check if data property exists
      const arrangements = response.body.data;

      // Check if arrangements is an array and has items
      expect(arrangements).to.be.an("array").and.not.to.be.empty;
    });

    // Step 4: Access the delegation page from the homepage
    cy.get('[data-cy="home"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/home");
    cy.get('[data-cy="delegation"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/delegate");
    cy.get('[data-cy="Delegate-A-Manager"]').click();

    // Step 5: Choose a delegatee
    cy.get('[data-cy="select-peer-dropdown"]').should("be.visible").click();
    cy.get('[role="option"]').eq(2).click(); //chooses the third option
    cy.get('[data-cy="delegate-manager-button"]').click();
    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "Request to delegate peer manager sent");

    // Step 6: Proceed to Ernst Sim's Account
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type("ernst.sim@allinone.com.sg");
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");

    // Step 7: Access the delegation page, Reject, type something in, then cancel
    cy.get('[data-cy="delegation"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/delegate");
    cy.get('[data-cy="reject-delegation"]').click();
    cy.get('[data-cy="RejectDelegationModal"]')
      .click()
      .type(
        "I am also going on holiday, delegate someone else! Meh, nevermind I changed my mind."
      );
    cy.get('[data-cy="RejectDelegationModalCancel"]').click();

    cy.url().should("eq", "http://localhost:3000/delegate");
    cy.get('[data-cy="accept-delegation"]').click();
    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "Delegation request accepted successfully!");

    // Step 8: Access the review requests page to see if requests exist
    cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/review-requests");

    cy.request(
      `http://localhost:8000/arrangements/subordinates/${180001}`
    ).then((response) => {
      // Log the entire response to debug
      console.log("Response:", response);

      expect(response.body).to.have.property("data"); // Check if data property exists
      const arrangements = response.body.data;

      // Check if arrangements is an array and has items
      expect(arrangements).to.be.an("array").and.not.to.be.empty;
    });

    // Step 9: Log out and log in as Sally to check if delegations have been accepted
    cy.get('[data-cy="logout"]').click();
    cy.url().should("eq", "http://localhost:3000/login");
    cy.get('[data-cy="email"]').type("sally.loh@allinone.com.sg");
    cy.get('[data-cy="password"]').type("password");
    cy.get('[data-cy="submit"]').click();
    cy.url().should("eq", "http://localhost:3000/home");
    cy.get('[data-cy="delegation"]').first().click({ force: true });
    cy.url().should("eq", "http://localhost:3000/delegate");
    // Check if there is a row with "Accepted" status in the delegations table
    cy.get("table").within(() => {
      // Find the row with Delegation Status "Accepted"
      cy.contains("tr", "Accepted").within(() => {
        // Check that the delegated manager name is "Eric Loh" (or the expected manager name)
        cy.get("td").eq(1).should("have.text", "Ernst Sim");

        // Verify the Delegation Status column has "Accepted"
        cy.get("td").eq(3).should("have.text", "Accepted");
      });
    });

    // Step 9: Click on the cancel button
    cy.get('[data-cy="cancel-delegation-button"]').click();
    // Confirm the approval action with an alert or message assertion
    cy.get(".MuiSnackbar-root .MuiAlert-message", { timeout: 20000 })
      .should("be.visible")
      .and("contain", "Delegation canceled successfully.");
  });
});
