describe('Testing login page', () => {

  // Test case 1
  it('should stay in the same page if the fields are not filled in fully', () => {
    cy.visit('http://localhost:3000/login')
    cy.get('[data-cy="email"]').type('bobby')
    cy.get('[data-cy="submit"]').click()
    cy.url().should('eq', 'http://localhost:3000/login');
  })

  // Test case 2
  it('should stay in the same page if the fields are not filled in fully', () => {
    cy.visit('http://localhost:3000/login')
    cy.get('[data-cy="email"]').type('bobby@gmail.com')
    cy.get('[data-cy="submit"]').click()
    cy.url().should('eq', 'http://localhost:3000/login');
  })

  // Test case 3
  it('should stay in the same page if the fields are not filled with correct user input', () => {
    cy.visit('http://localhost:3000/login')
    cy.get('[data-cy="email"]').type('bobby@gmail.com')
    cy.get('[data-cy="password"]').type('password')
    cy.get('[data-cy="submit"]').click()
    cy.url().should('eq', 'http://localhost:3000/login');
  })

  // Test case 4
  it('should change to the homepage if the fields are filled with correct user input', () => {
    cy.visit('http://localhost:3000/login')
    cy.get('[data-cy="email"]').type('Rahim.Khalid@allinone.com.sg')
    cy.get('[data-cy="password"]').type('password')
    cy.get('[data-cy="submit"]').click()
    cy.url().should('eq', 'http://localhost:3000/home');
  })

  // Test case 5
  it('should change to the homepage if the fields are filled with correct user input, with lowercased email', () => {
    cy.visit('http://localhost:3000/login')
    cy.get('[data-cy="email"]').type('rahim.khalid@allinone.com.sg')
    cy.get('[data-cy="password"]').type('password')
    cy.get('[data-cy="submit"]').click()
    cy.url().should('eq', 'http://localhost:3000/home');
  })

})