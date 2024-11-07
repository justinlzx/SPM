

describe('Testing Department Overview Page', () => {
    it('Should filter and show a graph', () => {
        // Step 1: Proceed to Sally Loh's Account
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('sally.loh@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');

        // Step 2: Access the department overview page
        cy.get('[data-cy="department-overview"]').first().click({ force: true });


        // Step 3: Choose the department
        cy.get('[data-cy="stats-department"]').click(); // Open the dropdown
        cy.get('[role="listbox"]') // Material-UI dropdown uses role="listbox" for the menu
            .should('be.visible') // Ensure the dropdown is visible
            .wait(500)  // Optional: wait for 500ms to allow dropdown to fully load
            .contains('HR') // Find the HR option
            .click({ force: true }); // Click on HR option

        // Step 4: Select the desired date in the date input
        cy.get('[data-cy="date-department"]')
            .type('2024-10-10'); // Enter the date in YYYY-MM-DD format

        // Step 5: Confirm the selection and filter the data
        cy.get('[data-cy="go-button"]').click();
        cy.url().should('eq', 'http://localhost:3000/department-overview');

        // Step 6: Assert that the chart container is visible
        cy.get('[data-cy="chart-container"]').should('be.visible');  // Ensure chart container is visible

        // Step 7: Check if the chart is visible or the message is displayed
        cy.get('[data-cy="chart-container"]').within(() => {
            // Assert that the chart (Canvas element) is visible if data is available
            cy.get('canvas').should('be.visible');  // Check that chart is rendered
        })
    })
})



describe('Testing Department Overview Page, no data to be seen', () => {
    it('Should filter, but no results, so show "No arrangements made for the selected date"', () => {
        // Step 1: Proceed to Sally Loh's Account
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('sally.loh@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');

        // Step 2: Access the department overview page
        cy.get('[data-cy="department-overview"]').first().click({ force: true });


        // Step 3: Choose the department
        cy.get('[data-cy="stats-department"]').click(); // Open the dropdown
        cy.get('[role="listbox"]') // Material-UI dropdown uses role="listbox" for the menu
            .should('be.visible') // Ensure the dropdown is visible
            .wait(500)  // Optional: wait for 500ms to allow dropdown to fully load
            .contains('Sales') // Find the HR option
            .click({ force: true }); // Click on HR option

        // Step 4: Select the desired date in the date input
        cy.get('[data-cy="date-department"]')
            .type('2024-10-10'); // Enter the date in YYYY-MM-DD format

        // Step 5: Confirm the selection and filter the data
        cy.get('[data-cy="go-button"]').click();
        cy.url().should('eq', 'http://localhost:3000/department-overview');

        // Step 6: Assert that the chart container is visible
        cy.get('[data-cy="chart-container"]').should('be.visible');  // Ensure chart container is visible

        // Step 7: Check if the chart is visible or the message is displayed
        cy.get('[data-cy="chart-container"]').within(() => {
            // Assert that the message is shown if no data is available
            cy.contains('No arrangements made for the selected date').should('exist')
        })
    })
})

describe('Testing Department Overview Page, no data to be seen, so try again for another date and department', () => {
    it('Should filter, but no results, so show "No arrangements made for the selected date", click refresh and reselect', () => {
        // Step 1: Proceed to Sally Loh's Account
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('sally.loh@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');

        // Step 2: Access the department overview page
        cy.get('[data-cy="department-overview"]').first().click({ force: true });


        // Step 3: Choose the department
        cy.get('[data-cy="stats-department"]').click(); // Open the dropdown
        cy.get('[role="listbox"]') // Material-UI dropdown uses role="listbox" for the menu
            .should('be.visible') // Ensure the dropdown is visible
            .wait(500)  // Optional: wait for 500ms to allow dropdown to fully load
            .contains('Sales') // Find the HR option
            .click({ force: true }); // Click on HR option

        // Step 4: Select the desired date in the date input
        cy.get('[data-cy="date-department"]')
            .type('2024-10-10'); // Enter the date in YYYY-MM-DD format

        // Step 5: Confirm the selection and filter the data
        cy.get('[data-cy="go-button"]').click();
        cy.url().should('eq', 'http://localhost:3000/department-overview');

        // Step 6: Assert that the chart container is visible
        cy.get('[data-cy="chart-container"]').should('be.visible');  // Ensure chart container is visible

        // Step 7: Check if the chart is visible or the message is displayed
        cy.get('[data-cy="chart-container"]').within(() => {
            // Assert that the message is shown if no data is available
            cy.contains('No arrangements made for the selected date').should('exist')
        })

        // Step 8: Click on the refresh button
        cy.get('[data-cy="department-refresh-button"]').click();

        // Step 9: Choose the department
        cy.get('[data-cy="stats-department"]').click(); // Open the dropdown
        cy.get('[role="listbox"]') // Material-UI dropdown uses role="listbox" for the menu
            .should('be.visible') // Ensure the dropdown is visible
            .wait(500)  // Optional: wait for 500ms to allow dropdown to fully load
            .contains('Engineering') // Find the HR option
            .click({ force: true }); // Click on HR option

        // Step 10: Select the desired date in the date input
        cy.get('[data-cy="date-department"]')
            .type('2024-10-16'); // Enter the date in YYYY-MM-DD format

        // Step 11: Confirm the selection and filter the data
        cy.get('[data-cy="go-button"]').click();
        cy.url().should('eq', 'http://localhost:3000/department-overview');

        // Step 12: Assert that the chart container is visible
        cy.get('[data-cy="chart-container"]').should('be.visible');  // Ensure chart container is visible

        // Step 13: Check if the chart is visible or the message is displayed
        cy.get('[data-cy="chart-container"]').within(() => {
            // Assert that the chart (Canvas element) is visible if data is available
            cy.get('canvas').should('be.visible');  // Check that chart is rendered
        })

    })
})




describe('Testing Department Overview Page (Trying out with Derek Tan)', () => {
    it('Should filter and show a graph', () => {
        // Step 1: Proceed to Sally Loh's Account
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('derek.tan@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');

        // Step 2: Access the department overview page
        cy.get('[data-cy="department-overview"]').first().click({ force: true });


        // Step 3: Choose the department
        cy.get('[data-cy="stats-department"]').click(); // Open the dropdown
        cy.get('[role="listbox"]') // Material-UI dropdown uses role="listbox" for the menu
            .should('be.visible') // Ensure the dropdown is visible
            .wait(500)  // Optional: wait for 500ms to allow dropdown to fully load
            .contains('HR') // Find the HR option
            .click({ force: true }); // Click on HR option

        // Step 4: Select the desired date in the date input
        cy.get('[data-cy="date-department"]')
            .type('2024-10-10'); // Enter the date in YYYY-MM-DD format

        // Step 5: Confirm the selection and filter the data
        cy.get('[data-cy="go-button"]').click();
        cy.url().should('eq', 'http://localhost:3000/department-overview');

        // Step 6: Assert that the chart container is visible
        cy.get('[data-cy="chart-container"]').should('be.visible');  // Ensure chart container is visible

        // Step 7: Check if the chart is visible or the message is displayed
        cy.get('[data-cy="chart-container"]').within(() => {
            // Assert that the chart (Canvas element) is visible if data is available
            cy.get('canvas').should('be.visible');  // Check that chart is rendered
        })
    })
})


describe('Testing Department Overview Page (Trying out with Jack Sim, he wants to view every department for 5th August 2024)', () => {
    it('Should filter and show a graph', () => {
        // Step 1: Proceed to Sally Loh's Account
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('jack.sim@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');

        // Step 2: Access the department overview page
        cy.get('[data-cy="department-overview"]').first().click({ force: true });


        // Step 3: Choose the department
        cy.get('[data-cy="stats-department"]').click(); // Open the dropdown
        cy.get('[role="listbox"]') // Material-UI dropdown uses role="listbox" for the menu
            .should('be.visible') // Ensure the dropdown is visible
            .wait(500)  // Optional: wait for 500ms to allow dropdown to fully load
            .contains('All') // Find the HR option
            .click({ force: true }); // Click on HR option

        // Step 4: Select the desired date in the date input
        cy.get('[data-cy="date-department"]')
            .type('2024-08-05'); // Enter the date in YYYY-MM-DD format

        // Step 5: Confirm the selection and filter the data
        cy.get('[data-cy="go-button"]').click();
        cy.url().should('eq', 'http://localhost:3000/department-overview');

        // Step 6: Assert that the chart container is visible
        cy.get('[data-cy="chart-container"]').should('be.visible');  // Ensure chart container is visible

        // Step 7: Check if the chart is visible or the message is displayed
        cy.get('[data-cy="chart-container"]').within(() => {
            // Assert that the chart (Canvas element) is visible if data is available
            cy.get('canvas').should('be.visible');  // Check that chart is rendered
        })
    })
})