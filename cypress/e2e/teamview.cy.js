describe('Testing Team View, filter arrangements can see', () => {
    it('Should filter and see arrangements', () => {
        cy.viewport(1920, 1080);
        // Step 1: Proceed to Sally Loh's Account
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('sally.loh@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');

        // Step 2: Access the team view page
        cy.get('[data-cy="my-team"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/team');

        // Step 3: Filter my team's WFH/OOO requests and assert that can view arrangements
        cy.get('[data-cy="team-requests-filter"]').within(() => {
            cy.get('[data-cy="start-date-picker"]').click()
            cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary
            cy.get('[data-cy="apply-filters"]').click()
            cy.request(`http://localhost:8000/arrangements/team/${160008}`)
                .then((response) => {
                    // Log the entire response to debug
                    console.log('Response:', response);

                    expect(response.body).to.have.property('data'); // Check if data property exists
                    const arrangements = response.body.data;

                    // Check if arrangements is an array and has items
                    expect(arrangements).to.be.an('array').and.not.to.be.empty;
                })

        });
    });
})


describe('Testing Team View, check if approved requests works', () => {
    it('Should filter approved requests', () => {
        cy.viewport(1920, 1080);
        // Step 1: Proceed to Rahim Khalid's Account
        cy.visit('http://localhost:3000/login');
        cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg');
        cy.get('[data-cy="password"]').type('password');
        cy.get('[data-cy="submit"]').click();
        cy.url().should('eq', 'http://localhost:3000/home');

        // Step 2: Access the team view page
        cy.get('[data-cy="my-team"]').first().click({ force: true });
        cy.url().should('eq', 'http://localhost:3000/team');

        // Step 3: Filter my team's WFH/OOO requests and assert that can view arrangements
        cy.get('[data-cy="approved-requests-filter"]').within(() => {
            cy.get('[data-cy="start-date-picker"]').click()
            cy.get('.react-datepicker__day--026').click(); // Adjust the day selection as necessary
            cy.get('[data-cy="apply-filters"]').click()
            cy.request(`http://localhost:8000/arrangements/team/${140894}`)
                .then((response) => {
                    // Log the entire response to debug
                    console.log('Response:', response);

                    expect(response.body).to.have.property('data'); // Check if data property exists
                    const arrangements = response.body.data;

                    // Check if arrangements is an array and has items
                    expect(arrangements).to.be.an('array').and.not.to.be.empty;
                })

        });
    });
});


// describe('Testing Team View, filter by status', () => {
//     it('Should filter and see arrangements', () => {
//         // Step 1: Proceed to Sally Loh's Account
//         cy.visit('http://localhost:3000/login');
//         cy.get('[data-cy="email"]').type('sally.loh@allinone.com.sg');
//         cy.get('[data-cy="password"]').type('password');
//         cy.get('[data-cy="submit"]').click();
//         cy.url().should('eq', 'http://localhost:3000/home');

//         // Step 2: Access the team view page
//         cy.get('[data-cy="my-team"]').first().click({ force: true });
//         cy.url().should('eq', 'http://localhost:3000/team');

//         // Step 3: Filter my team's WFH/OOO requests and assert that we can view arrangements
//         cy.get('[data-cy="team-requests-filter"]').within(() => {
//             // Open the status dropdown
//             cy.get('[data-cy="status-select"]').click();

//             // Ensure the dropdown is visible
//             cy.get('ul[role="listbox"]').should('be.visible');

//             // Select the first option in the dropdown (by index 0)
//             cy.get('ul[role="listbox"] li').first().click();  // or you can use .eq(0)

//             // Click anywhere on the body to close the dropdown
//             cy.get('body').click(0, 0);

//             // Apply the filters
//             cy.get('[data-cy="apply-filters"]').click();
//         });

//         // Step 4: Assert that requests are visible after the filter is applied
//         cy.get('[data-cy="team-request-item"]').should('have.length.greaterThan', 0); // Ensure there are requests visible

//         // Optionally, you can verify if the filtered requests are indeed the selected status
//         cy.get('[data-cy="team-request-item"]').each(($item) => {
//             cy.wrap($item).find('[data-cy="request-status"]').should('contain', 'Pending approval'); // Assuming first option is "Pending approval"
//         });
//     });
// });