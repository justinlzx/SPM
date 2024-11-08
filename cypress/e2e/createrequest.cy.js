describe('Testing requests page', () => {

    // Test case 1 (Happy Path non recurring)
    it('(Non recurring) Form should be created', () => {
        cy.visit('http://localhost:3000/login')
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg')
        cy.get('[data-cy="password"]').type('password')
        cy.get('[data-cy="submit"]').click()
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
        cy.get('.MuiSnackbar-root .MuiAlert-message', { timeout: 10000 })
            .should('be.visible')
            .and('contain', 'Your request was successfully submitted!');
    })

    // Test case 2 (Happy Path with recurring)
    it('(Recurring) Form should be created', () => {
        cy.visit('http://localhost:3000/login')
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg')
        cy.get('[data-cy="password"]').type('password')
        cy.get('[data-cy="submit"]').click()
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');
        // Fill in the form
        cy.get('[name="reason"]').type('Working on project X recurringly');

        // Interact with Material-UI select for WFH Type
        cy.get('[data-cy="wfhType"]').click(); // Open the dropdown
        cy.get('li[data-value="full"]').click(); // Select "Full-day" option

        // Interact with Material-UI select for Schedule Type
        cy.get('[data-cy = "scheduleType"]').click() // Open the dropdown
        cy.get('li[data-value="recurring"]').click(); // Select "recurring" option

        // Open the date picker input
        cy.get('[data-cy="start-datepicker-recurring"]').click(); // Click the custom input for the date picker

        // Select a specific future date (ensure the date class matches your DatePicker setup)
        cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary

        cy.get('[data-cy="submit-request"]').click();
        cy.get('.MuiSnackbar-root .MuiAlert-message', { timeout: 10000 })
            .should('be.visible')
            .and('contain', 'Your request was successfully submitted!');
    })

    // // Test case 3 (Submitting w Reason but no WFH type)
    it('Form should throw error message --> No WFH type', () => {
        cy.visit('http://localhost:3000/login')
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg')
        cy.get('[data-cy="password"]').type('password')
        cy.get('[data-cy="submit"]').click()
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');
        // Fill in the form
        cy.get('[name="reason"]').type('Working on project X');

        // Open the date picker input
        cy.get('[data-cy="start-datepicker"]').click(); // Click the custom input for the date picker

        // Select a specific future date (ensure the date class matches your DatePicker setup)
        cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary
        cy.get('[data-cy="submit-request"]').click();

        // Assert the error message is shown for WFH type
        cy.get('input[name="wfhType"]').then(($input) => {
            // Check if the error message is displayed
            cy.get('.MuiFormHelperText-root').should('contain', 'You must select AM, PM, or Full-day');
        });
    })

    // // Test case 4 (Submitting w no reason but with WFH type)
    it('Form should throw error --> No reason', () => {
        cy.visit('http://localhost:3000/login')
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg')
        cy.get('[data-cy="password"]').type('password')
        cy.get('[data-cy="submit"]').click()
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');

        // Interact with Material-UI select for WFH Type
        cy.get('[data-cy="wfhType"]').click(); // Open the dropdown
        cy.get('li[data-value="full"]').click(); // Select "Full-day" option

        // Open the date picker input
        cy.get('[data-cy="start-datepicker"]').click(); // Click the custom input for the date picker

        // Select a specific future date (ensure the date class matches your DatePicker setup)
        cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary
        cy.get('[data-cy="submit-request"]').click();

        // Assert the error message is shown for the reason field
        cy.get('.MuiFormHelperText-root').should('contain', 'Reason is required');
    });

    // // Test case 5 (Submitting w reason, WFH type but no proper date)
    it('Form should throw error --> No proper date', () => {
        cy.visit('http://localhost:3000/login')
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg')
        cy.get('[data-cy="password"]').type('password')
        cy.get('[data-cy="submit"]').click()
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');
        // Fill in the form
        cy.get('[name="reason"]').type('Working on project X');

        // Interact with Material-UI select for WFH Type
        cy.get('[data-cy="wfhType"]').click(); // Open the dropdown
        cy.get('li[data-value="full"]').click(); // Select "Full-day" option
        cy.get('[data-cy="submit-request"]').click();

        // Assert the error message is shown for the date field
        cy.get('.MuiFormHelperText-root').should('contain', 'Start date must be at least 1 day from today');
    });

    // // Test case 6 (Submitting w no reason, no WFH type and no proper date)
    it('Form should throw error --> No reason, No WFH type and no proper date', () => {
        cy.visit('http://localhost:3000/login')
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg')
        cy.get('[data-cy="password"]').type('password')
        cy.get('[data-cy="submit"]').click()
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');
        cy.get('[data-cy="submit-request"]').click()
        cy.url().should('eq', 'http://localhost:3000/create-request');
        // Assert the error message is shown for the reason field
        cy.get('.MuiFormHelperText-root').should('contain', 'Reason is required');
        // Assert the error message is shown for WFH type
        cy.get('input[name="wfhType"]').then(($input) => {
            // Check if the error message is displayed
            cy.get('.MuiFormHelperText-root').should('contain', 'You must select AM, PM, or Full-day');
        });
        // Assert the error message is shown for the date field
        // cy.get('.MuiFormHelperText-root').should('contain', 'Start date must be at least 1 day from today');
    })

    // // Test case 7 (Submitting w reason, no WFH type and no proper date)
    it('Form should throw error --> no WFH type, no proper date', () => {
        cy.visit('http://localhost:3000/login')
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg')
        cy.get('[data-cy="password"]').type('password')
        cy.get('[data-cy="submit"]').click()
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');
        // Fill in the form
        cy.get('[name="reason"]').type('Working on project X');
        cy.get('[data-cy="submit-request"]').click();
        cy.url().should('eq', 'http://localhost:3000/create-request');
        // Assert the error message is shown for WFH type
        cy.get('input[name="wfhType"]').then(($input) => {
            // Check if the error message is displayed
            cy.get('.MuiFormHelperText-root').should('contain', 'You must select AM, PM, or Full-day');
        });
        // // Assert the error message is shown for the date field
        // cy.get('.MuiFormHelperText-root').should('contain', 'Start date must be at least 1 day from today');
    })

    // // Test case 8 (Submitting w no reason, with valid WFH type but no proper date)
    it('Form should throw error --> No reason, no proper date', () => {
        cy.visit('http://localhost:3000/login')
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg')
        cy.get('[data-cy="password"]').type('password')
        cy.get('[data-cy="submit"]').click()
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');
        // Interact with Material-UI select for WFH Type
        cy.get('[data-cy="wfhType"]').click(); // Open the dropdown
        cy.get('li[data-value="full"]').click(); // Select "Full-day" option
        cy.get('[data-cy="submit-request"]').click();
        cy.url().should('eq', 'http://localhost:3000/create-request');
        // Assert the error message is shown for the reason field
        cy.get('.MuiFormHelperText-root').should('contain', 'Reason is required');
        // // Assert the error message is shown for the date field
        // cy.get('.MuiFormHelperText-root').should('contain', 'Start date must be at least 1 day from today');
    })

    // // Test case 9 (Submitting w no reason, no WFH type but with proper date)
    it('Form should throw error --> no reason, no WFH type', () => {
        cy.visit('http://localhost:3000/login')
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg')
        cy.get('[data-cy="password"]').type('password')
        cy.get('[data-cy="submit"]').click()
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');
        // Open the date picker input
        cy.get('[data-cy="start-datepicker"]').click(); // Click the custom input for the date picker

        // Select a specific future date (ensure the date class matches your DatePicker setup)
        cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary
        cy.get('[data-cy="submit-request"]').click();
        cy.url().should('eq', 'http://localhost:3000/create-request');
        // Assert the error message is shown for the reason field
        cy.get('.MuiFormHelperText-root').should('contain', 'Reason is required');
        // Assert the error message is shown for WFH type
        cy.get('input[name="wfhType"]').then(($input) => {
            // Check if the error message is displayed
            cy.get('.MuiFormHelperText-root').should('contain', 'You must select AM, PM, or Full-day');
        });
    })

    // // Test case 10 (Clicking Cancel button should return to homepage)
    it('Cancel button should return to homepage', () => {
        cy.visit('http://localhost:3000/login')
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg')
        cy.get('[data-cy="password"]').type('password')
        cy.get('[data-cy="submit"]').click()
        cy.url().should('eq', 'http://localhost:3000/home');
        cy.get('[data-cy="create-request"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/create-request');
        cy.get('[data-cy="cancel"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');

    })

})