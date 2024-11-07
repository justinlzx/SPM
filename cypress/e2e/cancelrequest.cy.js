describe('Testing My WFH Schedule page', () => {
    // Test case 1 (Happy Path non-recurring, Cancel)
    it('(Non-recurring) Form should be created, should be visible and easily withdrawn', () => {
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');

        // Fill in the form
        cy.get('[name="reason"]').type('Working on project X');

        // Interact with Material-UI select for WFH Type
        cy.get('[data-cy="wfhType"]').click(); // Open the dropdown
        cy.get('li[data-value="full"]').click(); // Select "Full-day" option

        // Open the date picker input
        cy.get('[data-cy="start-datepicker"]').click(); // Click the custom input for the date picker

        // Select a specific future date (ensure the date class matches your DatePicker setup)
        cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary

        cy.get('[data-cy="submit-request"]').click();

        // After submitting the request, go to My WFH Schedule
        cy.get('[data-cy="my-wfh-schedule"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/wfh-schedule');

        cy.request(`http://localhost:8000/arrangements/personal/${140894}`)
            .then((response) => {
                // Log the entire response to debug
                console.log('Response:', response);

                expect(response.body).to.have.property('data'); // Check if data property exists
                const arrangements = response.body.data;

                // Check if arrangements is an array and has items
                expect(arrangements).to.be.an('array').and.not.to.be.empty;

                // Find the latest arrangement using reduce
                const latestRequest = arrangements.reduce((latest, current) => {
                    return new Date(current.update_datetime) > new Date(latest.update_datetime) ? current : latest;
                });

                // Get the arrangement_id of the latest request
                const latestArrangementId = latestRequest.arrangement_id;

                // Click the cancel button
                cy.get(`[data-cy="cancel-button-${latestArrangementId}"]`).click();

                // Click the yes button
                cy.get('[data-cy="yes-button"]').click()


                // Add assertions to verify the cancel action was successful
                cy.get('.MuiSnackbar-root .MuiAlert-message', { timeout: 20000 })
                    .should('be.visible')
                    .and('contain', 'Your WFH request has been successfully cancelled!');
            });

    });
});

describe('Testing My WFH Schedule page', () => {
    // Test case 1 (Happy Path non-recurring, Cancel but then press No)
    it('(Non-recurring) Form should be created, should be visible and easily withdrawn', () => {
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');

        // Fill in the form
        cy.get('[name="reason"]').type('Working on project X');

        // Interact with Material-UI select for WFH Type
        cy.get('[data-cy="wfhType"]').click(); // Open the dropdown
        cy.get('li[data-value="full"]').click(); // Select "Full-day" option

        // Open the date picker input
        cy.get('[data-cy="start-datepicker"]').click(); // Click the custom input for the date picker

        // Select a specific future date (ensure the date class matches your DatePicker setup)
        cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary

        cy.get('[data-cy="submit-request"]').click();

        // After submitting the request, go to My WFH Schedule
        cy.get('[data-cy="my-wfh-schedule"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/wfh-schedule');

        cy.request(`http://localhost:8000/arrangements/personal/${140894}`)
            .then((response) => {
                // Log the entire response to debug
                console.log('Response:', response);

                expect(response.body).to.have.property('data'); // Check if data property exists
                const arrangements = response.body.data;

                // Check if arrangements is an array and has items
                expect(arrangements).to.be.an('array').and.not.to.be.empty;

                // Find the latest arrangement using reduce
                const latestRequest = arrangements.reduce((latest, current) => {
                    return new Date(current.update_datetime) > new Date(latest.update_datetime) ? current : latest;
                });

                // Get the arrangement_id of the latest request
                const latestArrangementId = latestRequest.arrangement_id;

                // Click the cancel button
                cy.get(`[data-cy="cancel-button-${latestArrangementId}"]`).click();

                // Click the yes button
                cy.get('[data-cy="no-button"').click()


                // Should be same page
                cy.url().should('eq', 'http://localhost:3000/wfh-schedule');
            });

    });
});



describe('Testing My WFH Schedule page, Filter Function (Status Filter)', () => {
    // Test case 1 (Happy Path non-recurring, Cancel but then press No)
    it('(Non-recurring) Form should be created, should be visible and easily withdrawn', () => {
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');

        // Fill in the form
        cy.get('[name="reason"]').type('Working on project X');

        // Interact with Material-UI select for WFH Type
        cy.get('[data-cy="wfhType"]').click(); // Open the dropdown
        cy.get('li[data-value="full"]').click(); // Select "Full-day" option

        // Open the date picker input
        cy.get('[data-cy="start-datepicker"]').click(); // Click the custom input for the date picker

        // Select a specific future date (ensure the date class matches your DatePicker setup)
        cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary

        cy.get('[data-cy="submit-request"]').click();

        // After submitting the request, go to My WFH Schedule
        cy.get('[data-cy="my-wfh-schedule"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/wfh-schedule');

        cy.request(`http://localhost:8000/arrangements/personal/${140894}`)
            .then((response) => {
                // Log the entire response to debug
                console.log('Response:', response);

                expect(response.body).to.have.property('data'); // Check if data property exists
                const arrangements = response.body.data;

                // Check if arrangements is an array and has items
                expect(arrangements).to.be.an('array').and.not.to.be.empty;
            })

        // Click on the department filter
        cy.get('[data-cy="status-select"]').click(); // Open the status dropdown
        cy.get('ul[role="listbox"]').should('be.visible'); // Ensure the dropdown is visible

        // Select "Pending approval" (exact match)
        cy.get('ul[role="listbox"] li').contains('Pending approval').click(); // Click on "Pending approval"


        // Click on an element to close the dropdown
        cy.get('body').click(0, 0); // Click anywhere on the body to close the dropdown
        // Click the Apply Filters button
        cy.get('[data-cy="apply-filters"]').click(); // Ensure you have the correct data-cy for the Apply Filters button

        // Assertions after applying filters
        // Verify that the displayed requests are filtered correctly
        cy.get('[data-cy="request-item"]').should('have.length.greaterThan', 0); // Check that there are visible requests

    });
});

describe('Testing My WFH Schedule page, Filter Function (Status Filter, Multiple)', () => {
    // Test case 1 (Happy Path non-recurring, Cancel but then press No)
    it('(Non-recurring) Form should be created, should be visible and easily withdrawn', () => {
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');

        // Fill in the form
        cy.get('[name="reason"]').type('Working on project X');

        // Interact with Material-UI select for WFH Type
        cy.get('[data-cy="wfhType"]').click(); // Open the dropdown
        cy.get('li[data-value="full"]').click(); // Select "Full-day" option

        // Open the date picker input
        cy.get('[data-cy="start-datepicker"]').click(); // Click the custom input for the date picker

        // Select a specific future date (ensure the date class matches your DatePicker setup)
        cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary

        cy.get('[data-cy="submit-request"]').click();

        // After submitting the request, go to My WFH Schedule
        cy.get('[data-cy="my-wfh-schedule"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/wfh-schedule');

        cy.request(`http://localhost:8000/arrangements/personal/${140894}`)
            .then((response) => {
                // Log the entire response to debug
                console.log('Response:', response);

                expect(response.body).to.have.property('data'); // Check if data property exists
                const arrangements = response.body.data;

                // Check if arrangements is an array and has items
                expect(arrangements).to.be.an('array').and.not.to.be.empty;
            })

        // Click on the department filter
        cy.get('[data-cy="status-select"]').click(); // Open the status dropdown
        cy.get('ul[role="listbox"]').should('be.visible'); // Ensure the dropdown is visible

        // Select "Pending approval" (exact match)
        cy.get('ul[role="listbox"] li').contains('Pending approval').click(); // Click on "Pending approval"

        // Select "Pending approval" (exact match)
        cy.get('ul[role="listbox"] li').contains('Pending withdrawal').click(); // Click on "Pending withdrawal"


        // Click on an element to close the dropdown
        cy.get('body').click(0, 0); // Click anywhere on the body to close the dropdown
        // Click the Apply Filters button
        cy.get('[data-cy="apply-filters"]').click(); // Ensure you have the correct data-cy for the Apply Filters button

        // Assertions after applying filters
        // Verify that the displayed requests are filtered correctly
        cy.get('[data-cy="request-item"]').should('have.length.greaterThan', 0); // Check that there are visible requests

    });
});

describe('Testing My WFH Schedule page, Filter Function (Status Filter, Multiple, Clear Filters)', () => {
    // Test case 1 (Happy Path non-recurring, Cancel but then press No)
    it('(Non-recurring) Form should be created, should be visible and easily withdrawn', () => {
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');

        // Fill in the form
        cy.get('[name="reason"]').type('Working on project X');

        // Interact with Material-UI select for WFH Type
        cy.get('[data-cy="wfhType"]').click(); // Open the dropdown
        cy.get('li[data-value="full"]').click(); // Select "Full-day" option

        // Open the date picker input
        cy.get('[data-cy="start-datepicker"]').click(); // Click the custom input for the date picker

        // Select a specific future date (ensure the date class matches your DatePicker setup)
        cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary

        cy.get('[data-cy="submit-request"]').click();

        // After submitting the request, go to My WFH Schedule
        cy.get('[data-cy="my-wfh-schedule"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/wfh-schedule');

        cy.request(`http://localhost:8000/arrangements/personal/${140894}`)
            .then((response) => {
                // Log the entire response to debug
                console.log('Response:', response);

                expect(response.body).to.have.property('data'); // Check if data property exists
                const arrangements = response.body.data;

                // Check if arrangements is an array and has items
                expect(arrangements).to.be.an('array').and.not.to.be.empty;
            });

        // Click on the status filter
        cy.get('[data-cy="status-select"]').click(); // Open the status dropdown
        cy.get('ul[role="listbox"]').should('be.visible'); // Ensure the dropdown is visible

        // Select "Pending approval"
        cy.get('ul[role="listbox"] li').contains('Pending approval').click(); // Click on "Pending approval"

        // Select "Pending withdrawal"
        cy.get('ul[role="listbox"] li').contains('Pending withdrawal').click(); // Click on "Pending withdrawal"

        // Click on an element to close the dropdown
        cy.get('body').click(0, 0); // Click anywhere on the body to close the dropdown

        // Click the Clear Filters button
        cy.get('[data-cy="clear-filters"]').click(); // Ensure you have the correct data-cy for the Clear Filters button

        // Assertions after clearing filters
        // Check if the status filter is reset, meaning it should show all requests (or specific message for no filters)
        cy.get('[data-cy="status-select"]').find('input').should('have.value', ''); // Assuming the input value should be empty

        // Additionally, check that the displayed requests include expected items
        cy.get('[data-cy="request-item"]').should('have.length.greaterThan', 0); // Ensure requests are displayed
    });
});


describe('Testing My WFH Schedule page, Filter Function (Status Filter FAILURE)', () => {
    // Test case 1 (Happy Path non-recurring, Cancel but then press No)
    it('(Non-recurring) Form should be created, should be visible and easily withdrawn', () => {
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');

        // Fill in the form
        cy.get('[name="reason"]').type('Working on project X');

        // Interact with Material-UI select for WFH Type
        cy.get('[data-cy="wfhType"]').click(); // Open the dropdown
        cy.get('li[data-value="full"]').click(); // Select "Full-day" option

        // Open the date picker input
        cy.get('[data-cy="start-datepicker"]').click(); // Click the custom input for the date picker

        // Select a specific future date (ensure the date class matches your DatePicker setup)
        cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary

        cy.get('[data-cy="submit-request"]').click();

        // After submitting the request, go to My WFH Schedule
        cy.get('[data-cy="my-wfh-schedule"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/wfh-schedule');

        cy.request(`http://localhost:8000/arrangements/personal/${140894}`)
            .then((response) => {
                // Log the entire response to debug
                console.log('Response:', response);

                expect(response.body).to.have.property('data'); // Check if data property exists
                const arrangements = response.body.data;

                // Check if arrangements is an array and has items
                expect(arrangements).to.be.an('array').and.not.to.be.empty;
            })

        // Click on the department filter
        cy.get('[data-cy="status-select"]').click(); // Open the status dropdown
        cy.get('ul[role="listbox"]').should('be.visible'); // Ensure the dropdown is visible

        // Select "Pending approval" (exact match)
        cy.get('ul[role="listbox"] li').contains('Cancelled').click(); // Click on "Cancelled"


        // Click on an element to close the dropdown
        cy.get('body').click(0, 0); // Click anywhere on the body to close the dropdown
        // Click the Apply Filters button
        cy.get('[data-cy="apply-filters"]').click(); // Ensure you have the correct data-cy for the Apply Filters button

        // Assertions after applying filters
        // Verify that the displayed requests are filtered correctly
        cy.get('[data-cy="request-item"]').should('have.length.greaterThan', 0); // Check that there are visible requests

    });
});

describe('Testing My WFH Schedule page, Filter Function (Status Filter FAILURE), Clear Filters', () => {
    // Test case 1 (Happy Path non-recurring, Cancel but then press No)
    it('(Non-recurring) Form should be created, should be visible and easily withdrawn', () => {
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');

        // Fill in the form
        cy.get('[name="reason"]').type('Working on project X');

        // Interact with Material-UI select for WFH Type
        cy.get('[data-cy="wfhType"]').click(); // Open the dropdown
        cy.get('li[data-value="full"]').click(); // Select "Full-day" option

        // Open the date picker input
        cy.get('[data-cy="start-datepicker"]').click(); // Click the custom input for the date picker

        // Select a specific future date (ensure the date class matches your DatePicker setup)
        cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary

        cy.get('[data-cy="submit-request"]').click();

        // After submitting the request, go to My WFH Schedule
        cy.get('[data-cy="my-wfh-schedule"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/wfh-schedule');

        cy.request(`http://localhost:8000/arrangements/personal/${140894}`)
            .then((response) => {
                // Log the entire response to debug
                console.log('Response:', response);

                expect(response.body).to.have.property('data'); // Check if data property exists
                const arrangements = response.body.data;

                // Check if arrangements is an array and has items
                expect(arrangements).to.be.an('array').and.not.to.be.empty;
            })

        // Click on the department filter
        cy.get('[data-cy="status-select"]').click(); // Open the status dropdown
        cy.get('ul[role="listbox"]').should('be.visible'); // Ensure the dropdown is visible

        // Select "Pending approval" (exact match)
        cy.get('ul[role="listbox"] li').contains('Cancelled').click(); // Click on "Cancelled"


        // Click on an element to close the dropdown
        cy.get('body').click(0, 0); // Click anywhere on the body to close the dropdown
        // Click the Apply Filters button
        cy.get('[data-cy="apply-filters"]').click(); // Ensure you have the correct data-cy for the Apply Filters button

        // Assertions after applying filters
        // Verify that the displayed requests are filtered correctly
        cy.get('[data-cy="request-item"]').should('have.length.greaterThan', 0); // Check that there are visible requests

        // Click the Clear Filters button
        cy.get('[data-cy="clear-filters"]').click(); // Ensure you have the correct data-cy for the Clear Filters button

        // Assertions after applying filters
        // Verify that the displayed requests are filtered correctly
        cy.get('[data-cy="request-item"]').should('have.length.greaterThan', 0); // Check that there are visible requests

    });
});