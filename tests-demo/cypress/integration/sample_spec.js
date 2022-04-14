Cypress.on('uncaught:exception', (err, runnable) => {
  // returning false here prevents Cypress from
  // failing the test
  return false
})

describe('The RaptorMaps Public Site', () => {
  it('The Jobs page can navigate to the Technology page', () => {
    var technology_link_id = '#menu-item-6777'

    cy.visit('https://raptormaps.com/jobs/')
    cy.get(technology_link_id).click()
    cy.url().should('eq', 'https://raptormaps.com/rmtechnology/')
  })
  it('', () => {
    cy.url().should('eq', 'https://raptormaps.com/rmtechnology/')

    var expected_text = "Raptor Maps easily integrates software solutions through our API. Clients can use the API to push or pull data between tools, maximizing the value of both tools while increasing data output and analysis. Our API can integrate with leading analytics tools used in asset monitoring dashboards and SCADA systems, including Power BI, SAP, and Power Factors.",
        expected_title = "API Integration",
        expected_img_src = "https://raptormaps.com/wp-content/uploads/2019/09/Raptor-Maps-API.png",
        expected_button_contents = "KNOWLEDGE HUB",
        expected_button_target = "https://docs.raptormaps.com/reference/reference-getting-started#reference-getting-started";
    cy.get('#tech-api').scrollIntoView()
  })
})
