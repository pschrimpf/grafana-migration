from src.Page import Page
from src.Variable import Variable

class Dashboard:

    def __init__(self, conversionService, json):
        self.conversionService = conversionService
        self.name = ''
        self.description = ''
        self.pages = []
        self.variables = []

        self.parseGrafana(json)

    def parseGrafana(self, json):
        self.name = json['dashboard']['title']
        self.parseTemplates(json['dashboard']['templating']['list'])
        self.parsePanels(json['dashboard']['panels'])


    # For collapse = true, you have to put rows panels inside the row definition , in panels[ ] section.
    # For collapse = false, you have to put rows panels below the row definition.
    def parsePanels(self, panels):
        page = Page(conversionService=self.conversionService, widgets=[])
        succesivePanels = False

        for panel in panels:
            if panel['type'] == 'row':
                if succesivePanels:
                    self.pages.append(page)
                    succesivePanels = False
                    page = Page(conversionService=self.conversionService, widgets=[])

                page.name = panel['title']
                if 'collapsed' in panel and panel['collapsed']:
                    for nestedPanel in panel['panels']:
                        page.addWidget(nestedPanel)
                    self.pages.append(page)
                    page = Page(conversionService=self.conversionService, widgets=[])
                else:
                    succesivePanels = True
            else:
                page.addWidget(panel)

        ## Edge cases ##
        # If last row is not collapsed don't forget to add last row's panels
        if succesivePanels:
            self.pages.append(page)
        # Don't forget to add any panel that don't belong to a row at the end of Grafana dashboard to the last NR page
        elif page.widgets:
            if self.pages:
                self.pages[-1].addWidgets(page.widgets)
            ## in case no rows in the grafana dashboard
            else:
                self.pages.append(Page(conversionService=self.conversionService, name=self.name, description='', widgets=page.widgets))

    def parseTemplates(self, templatingList):
        for template in templatingList:
            self.variables.append(Variable(self.conversionService, template))
        

    def toJSON(self):
        return {
            "name": self.name,
            "description": self.description,
            "permissions": "PUBLIC_READ_WRITE",
            "pages": list(map(lambda page: page.toJSON(), self.pages)),
            "variables": list(map(lambda variable: variable.toJSON(), self.variables))
        }
    
    @staticmethod
    def getVariables(json):
        variables = list()
        if 'templating' in json['dashboard'] and 'list' in json['dashboard']['templating']:
            variablesList = json['dashboard']['templating']['list']
            for variableObj in variablesList:
                variables.append(f'${variableObj["name"]}')
        return variables
