describe('Testing delegation (Happy path)', () => {
    it('Should create a request and then have it approved by a manager', () => {
        // Step 1: Login as Rahim and create a WFH request
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');

        // Navigate to create request page
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');

        // Fill in the form and submit
        cy.get('[name="reason"]').type('Working on project X');
        cy.get('[data-cy="wfhType"]').click();
        cy.get('li[data-value="full"]').click();
        cy.get('[data-cy="start-datepicker"]').click();
        cy.get('.react-datepicker__day--026').click();
        cy.get('[data-cy="submit-request"]').click();

        // Capture the latest request arrangement_id
        cy.request('http://localhost:8000/arrangements/personal/140894').then((response) => {
            expect(response.body).to.have.property('data');
            const arrangements = response.body.data;
            const latestRequest = arrangements.reduce((latest, current) =>
                new Date(current.update_datetime) > new Date(latest.update_datetime) ? current : latest
            );
            cy.wrap(latestRequest.arrangement_id).as('latestArrangementId');
        });

        // Step 2: Log out and log in as Derek
        cy.get('[data-cy="logout"]').click();
        cy.url().should('eq', 'http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('Derek.Tan@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');

        // Step 3: Access the review requests page to see if the request exists
        cy.get('[data-cy="review-team-requests"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/review-requests');

        cy.request(`http://localhost:8000/arrangements/subordinates/${140001}`)
            .then((response) => {
                // Log the entire response to debug
                console.log('Response:', response);

                expect(response.body).to.have.property('data'); // Check if data property exists
                const arrangements = response.body.data;

                // Check if arrangements is an array and has items
                expect(arrangements).to.be.an('array').and.not.to.be.empty;
            })

        // Step 4: Access the delegation page
        cy.get('[data-cy="delegation"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/delegate');
        cy.get('[data-cy="Delegate-A-Manager"]').click();

        // Step 5: Choose a delegatee
        cy.get('[data-cy="select-peer-dropdown"]').should('be.visible').click();
        cy.get('[role="option"]').first().click();
        cy.get('[data-cy="delegate-manager-button"]').click();
        // Confirm the approval action with an alert or message assertion
        cy.get('.MuiSnackbar-root .MuiAlert-message', { timeout: 20000 })
            .should('be.visible')
            .and('contain', "Request to delegate peer manager sent");

        // Step 6: Proceed to Eric Loh's Account
        cy.get('[data-cy="logout"]').click();
        cy.url().should('eq', 'http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('eric.loh@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');

        // Step 7: Access the delegation page
        cy.get('[data-cy="delegation"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/delegate');
        cy.get('[data-cy="accept-delegation"]').click();
        // Confirm the approval action with an alert or message assertion
        cy.get('.MuiSnackbar-root .MuiAlert-message', { timeout: 20000 })
            .should('be.visible')
            .and('contain', "Delegation request accepted successfully!");



    })
})