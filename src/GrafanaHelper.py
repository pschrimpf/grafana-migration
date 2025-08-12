import re

def convertGrafanaQuery(query):
    if query.startswith('label_values'):
        return convertLabelValues(query)
    else:
        return None

def normalizeQuery(query):
    # Remove new line characters
    normalizedQuery = query.replace('\r', "")
    normalizedQuery = normalizedQuery.replace('\n', "")
    
    # Translate Grafana Variables in New Relic Variables
    normalizedQuery = re.sub(r"\$\{?([A-Za-z0-9-_]+)\}?", r'{{\1}}', normalizedQuery)
    
    return normalizedQuery

def finalVariableNormalization(query):
    return re.sub(r"\'?\"?(\{\{[A-Za-z0-9-_]+\}\})\'?\"?", r'\1', query)

def convertLabelFilters(filterArgs):
    convertedFilter = ''
    allFilters = re.findall(r'(.+?=".+?")[,\s]?', filterArgs)
    if allFilters:
      convertedFilter = ' AND '.join(allFilters)
    else:
      print(f"Unknwon filter: {filterArgs}")
          
    return convertedFilter

# label_values([[metricName][{filterAttribute=filterValue[, ...]}]],label_name)
def convertLabelValues(query):
    convertedQuery = None
    match = re.search(r'label_values\((.+)\)', query)
    if match:
        functionArgs = match.group(1)
        
        metricName = None
        filter = None
        labelName = ''
        if ',' in functionArgs:
          if '{' in functionArgs and '}' in functionArgs:
            if functionArgs.startswith('{'):
                # label_values({filter, ...}, label_name)
                match = re.search(r'{(.+)},(.+)', functionArgs)
                filterArgs = match.group(1)
                labelName = match.group(2)                
                
            # label_values(metricName{filter, ...}, label_name)
            else:
                # label_values(metricName{filter, ...}, label_name)
                match = re.search(r'(.+){(.+)},(.+)', functionArgs)
                metricName = match.group(1)
                filterArgs = match.group(2)
                labelName = match.group(3)
        
            filter = convertLabelFilters(filterArgs)
                
          else:
            # label_values(metricName, label_name)
            args = functionArgs.split(', ')
            metricName = args[0].strip()
            labelName = args[1].strip()
            convertedQuery =  f"FROM Metric SELECT unqiques({labelName}) WHERE metricName = '{metricName}'"
        else:
            # label_values(label_name)
            labelName = functionArgs
    
    convertedQuery = f"FROM Metric SELECT uniques({labelName})"
    if metricName or filter:
        convertedQuery += (" WHERE ")
        
        if metricName:
            convertedQuery += f"metricName = '{metricName}'"
        
        if filter:
            if metricName:
                convertedQuery += " AND "
            
            convertedQuery += filter
    
    return normalizeQuery(convertedQuery)