Cypress.on('uncaught:exception', (err, runnable) => {
    // prevent Cypress from crashing on script errors from page under test
    return false
})

describe('The RaptorMaps Public Site', () => {
    beforeEach(() => {
        // mobile-size viewport affects how this site works
        cy.viewport(1500, 1000)
    })

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

    it('The API endpoint tester works properly', () => {
        cy.visit('https://docs.raptormaps.com/reference/apiv2solar_farms')

        cy.get('#APIAuth-Authentication-Token').type('WyIyMDA3IiwiJDUkcm91bmRzPTUzNTAwMCQ4czdkZ0lyZkxRalN1TXlkJHZJbXJPMzFVdERYZDFlTDRZTmdDaHJwUjBhRmIydW0vampvQWYzTE1iUzYiXQ.Yk-w_w.dGRb3xdsG6TgzOTHYdhh0eSmHWk')

        var org_id_label = cy.get('div.form-group>div.Param-left7tTo9KK0E0kY>div.Param-header3wXBpbDTP1O6>label').contains('org_id')
        org_id_label.parents().get('div.form-group').find('input').type('228')
        cy.get('button').contains('Try It!').click()

        cy.get('button.APIResponse-copyButton1Wx_vGKSR6nt').realClick()
        cy.window().then((win) => {
            win.navigator.clipboard.readText().then((text) => {
                var response = JSON.parse(text),
                    postman = null;
                response.solar_farms.forEach(farm => {
                    if (farm.name == 'Test Postman Routes - QA Team') {
                        postman = farm
                    }
                })
                expect(postman.uuid).to.eq('8bb07ba1-2661-4f89-8dca-4292c378e665');
            });
        });
    })
})
