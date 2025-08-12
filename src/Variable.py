from src.Item import Item

class Variable:

    def __init__(self, conversionService):
        self.conversionService = conversionService
        self.name = ""
        self.items = None
        self.defaultValues = []
        self.nrqlQuery = None
        self.options = {}
        self.title = ""
        self.type = "STRING"
        self.isMultiSelection = False
        self.replacementStrategy = "STRING"
        
        
    def __init__(self, conversionService, template):
        self.conversionService = conversionService
        self.name = template['name']
        self.items = []
        self.replacementStrategy = "STRING"
        
        if 'options' in template and len(template['options']) > 0:
            for option in template['options']:
                self.items.append(Item(option))
        
        # Default Value
        if 'current' in template and 'value' in template['current']:
            if template['multi'] == True:
                self.defaultValues = [] # TODO Multi Default Values
            else:
                self.defaultValues = [
                    {
                        "value": {
                            "string": template['current']['value']
                        }
                    }
                ]
                
                if template['current']['value'].isnumeric():
                    self.replacementStrategy = "NUMBER"
        else:
            self.defaultValues = []
       
        # if something
        #self.options = {
        #    "excluded": 
        #    "showApplyAction":
        #}
        #else
        self.options = {
            "ignoreTimeRange": True,
            "excluded": False,
            "showApplyAction": False
        }
        if 'label' in template: 
            self.title = template['label']
        elif 'description' in template:
            self.title = template['description']
        else:
            self.title = ''
        
        self.nrqlQuery = None
        
        # Variable Type
        if len(self.items) > 0:
            self.type = 'ENUM'
        elif template['type'] == 'custom':
            self.type = 'STRING'
        elif template['type'] == 'query':
            self.type = "NRQL"
            self.nrqlQuery = {
                    "accountIds": [int(self.conversionService.accountId)],
                    "query": self.conversionService.convertQuery(template['query']['query'], range=range)
                }
            
        self.isMultiSelection = template['multi']

    def toJSON(self):
        return {
            "name": self.name,
            "items": list(map(lambda item: item.toJSON(), self.items)),
            "defaultValues": self.defaultValues,
            "nrqlQuery": self.nrqlQuery,
            "options": self.options,
            "title": self.title,
            "type": self.type,
            "isMultiSelection": self.isMultiSelection,
            "replacementStrategy": self.replacementStrategy,
        }
