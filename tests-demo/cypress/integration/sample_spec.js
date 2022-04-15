Cypress.on('uncaught:exception', (err, runnable) => {
    // prevent Cypress from crashing on script errors from page under test
    return false
})

describe('The RaptorMaps Public Site', () => {
    it('The Jobs page can navigate to the Technology page', () => {
        var technology_link_id = '#menu-item-6777'

        cy.visit('https://raptormaps.com/jobs/')
        cy.get(technology_link_id).click()
        cy.url().should('eq', 'https://raptormaps.com/rmtechnology/')
    })

    it('The API section of the Technology page shows the expected elements', () => {
        cy.visit('https://raptormaps.com/rmtechnology/')

        var expected_text = "Raptor Maps easily integrates software solutions through our API. Clients can use the API to push or pull data between tools, maximizing the value of both tools while increasing data output and analysis. Our API can integrate with leading analytics tools used in asset monitoring dashboards and SCADA systems, including Power BI, SAP, and Power Factors.",
            expected_title = "API Integration",
            expected_img_src = "https://raptormaps.com/wp-content/uploads/2019/09/Raptor-Maps-API.png",
            expected_button_target = "https://docs.raptormaps.com/reference#reference-getting-started";
        cy.get('#tech-api').scrollIntoView()

        cy.get('h1').contains(expected_title).should('be.inViewport')
        cy.get('p').contains(expected_text).should('be.inViewport')
        cy.get('.et_pb_row_12').find('img').should('have.attr', 'src', expected_img_src).should('be.inViewport')
        cy.get('a').contains('KNOWLEDGE HUB').should('be.inViewport')
            .should('have.attr', 'href', expected_button_target).should('be.inViewport')
    })

    it('The Knowledge Hub button should open the expected page in a new tab', () => {
        cy.visit('https://raptormaps.com/rmtechnology/')
        var button = cy.get('a').contains('KNOWLEDGE HUB')

        // we check that the button would open a new tab, and then alter it to open in the same tab to simplify test logic
        button.should('have.attr', 'target', '_blank')
        button.invoke('removeAttr', 'target')
        button.click()

        cy.url().should('eq', 'https://docs.raptormaps.com/reference/reference-getting-started#reference-getting-started')
    })

    it('The solar_farms API endpoint page should have the expected elements', () => {
        // mobile-size viewport affects how this page works
        cy.viewport(1500, 1000)

        cy.visit('https://docs.raptormaps.com/reference/reference-getting-started#reference-getting-started')

        cy.get('span').contains('Solar Farm Endpoints').parents('a').click()
        cy.get('a').contains('api/v2/solar_farms').click()

        var form_elements = ['Your Request History', 'Query Params', 'Responses']
        form_elements.forEach(element => {
            cy.get('header>strong').contains(element).should('be.inViewport')
        })
        cy.get('h1').contains('/api/v2/solar_farms').should('be.inViewport')
        cy.get('p').contains('Warning: Use https://docs.raptormaps.com/v3.0/reference#search_solar_farms_by_name Endpoint to retrieve all solar farms that you have access to view in a particular organization').should('be.inViewport')
    })
})
