import requests
import json
import src.utils.constants as constants
import src.GrafanaHelper as GrafanaHelper
import browser_cookie3
import os
import re


class PromQL2NrqlService:

    def __init__(self, config, variables):

        self.accountId = config['api']['accountId']
        self.grafanaVariables = variables

        # Create local cache to store queries, this will speed up testing
        self.cache = self.loadCache()

        # Login to New Relic
        # Use an API key if provided, else get a new session
        token = os.getenv('NEW_RELIC_API_TOKEN')
        self.session = requests.Session()
        if token:
            self.token = token
        else:
            self.token = None
            self.authenticate(config, self.session)


    def loadCache(self):
        try:
            f = open(constants.CACHE_FILE_NAME, "r")
            content = json.load(f)
        except FileNotFoundError: #code to run if error occurs
            content = {}

        return content

    def saveCache(self):
        data = json.dumps(self.cache)
        f = open(constants.CACHE_FILE_NAME,"w")
        f.write(data)
        f.close()

    def convertQuery(self, query, range=True, clean=True):
        convertedQuery = GrafanaHelper.convertGrafanaQuery(query)
        if convertedQuery is None:
            convertedQuery = self.convertPromQLQuery(query)
        
        return GrafanaHelper.finalVariableNormalization(convertedQuery)

    def convertPromQLQuery(self, query, range=True, clean=True):
        custom_headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json"
        }
        if self.token:
            custom_headers['Api-Key'] = self.token

         # Variable handling, e.g. 
        #promql = promql.replace("${top}", "10")
        #query = re.sub(r'\$\{(.+?)\}', r'$\1', query)
        #promql = re.sub(r'(?<=\{)(.*?)(?=\})', self.removeVariables, query)
        promql = GrafanaHelper.normalizeQuery(query)
        
        # +++ Ugly Workaround - Part 1 +++
        ### Variables not working as topk first parameter
        yep_topk_with_var = None
        match = re.search(r'topk\(\s*(\{\{\s*[A-Za-z0-9-_]+\s*\}\})\s*,', promql)
        if match:
            yep_topk_with_var = match.group(1)
            promql = re.sub(r'topk\(\s*(\{\{\s*.[A-Za-z0-9-_]+)\s*\}\}\s*,', 'topk(1337,', promql)
            
        ### Rate function specifying rate value per variable
        yep_rate_with_interval = None
        match = re.search(r'rate\(.+\[(\{\{.+\}\})\]\)', promql)
        if match:
           yep_rate_with_interval = match.group(1)
           promql = promql.replace(yep_rate_with_interval, '15m')
           print("WARNING: TIMESERIES with variable threshold value not supported. Defaulting to 15m")

        ### PromQL absent function not supported
        #### https://prometheus.io/docs/prometheus/latest/querying/functions/#absent
        yep_absent_query = None
        match = re.search(r'.*(absent)\(([A-Za-z0-9-_]+).*', promql)
        if match:
            yep_absent_query = match.group(2)
            promql = promql.replace(match.group(1), '')
        
        #if promql not in self.cache:
        nrql = self.session.post(constants.PROMQL_TRANSLATE_URL, headers=custom_headers, json={
            "promql": promql,
            "account_id": self.accountId,
            "isRange": range,
            "startTime": "null",
            "endTime": "null",
            "step": 30
        })

        if nrql.status_code == 200:
            # Remove `Facet Dimensions()`
            newNrql = self.removeDimensions(nrql.json()['nrql'])
            # +++ Ugly workaround - Part 2 +++
            if yep_topk_with_var:
                newNrql = newNrql.replace('LIMIT 1337', f"LIMIT {yep_topk_with_var}")
                
            if yep_absent_query:
                regExSearchTerm = r'SELECT (.*?' + yep_absent_query + '.*?) FROM Metric WHERE '
                newNrql = re.sub(regExSearchTerm, 'SELECT count(1) FROM Metric WHERE metricName = \'' + yep_absent_query + '\' AND ', newNrql)
                
                
            #if yep_rate_with_interval:
            #    newNrql = newNrql.replace('TIMESERIES 900000', f"TIMESERIES {yep_rate_with_interval}")         
            self.cache[promql] = newNrql
            
        else:
            # Print the error to console
            print('{}:\n    {}'.format(nrql.json()['message'], promql))
            # print('{}:\n    {}'.format(nrql.json(), promql))
            self.cache[promql] = promql

        return self.cache[promql]

    def authenticate(self,configuration, session):
        self.session.hooks = {
            'response': lambda r, *args, **kwargs: r.raise_for_status()
        }
        if configuration['auth']['ssoEnabled']:
            browser = configuration['auth']['sso']['browserCookie'] 
            if browser == 'Chrome':
                cookies = browser_cookie3.chrome(domain_name='.newrelic.com')
            elif browser == 'Opera':
                cookies = browser_cookie3.opera(domain_name='.newrelic.com')
            elif browser == 'FireFox':
                cookies = browser_cookie3.firefox(domain_name='.newrelic.com')
            elif browser == 'Edge':
                cookies = browser_cookie3.edge(domain_name='.newrelic.com')
            
            for cookie in cookies:
                if cookie.domain == '.newrelic.com':  # remove .blog.newreli.com and other domains
                    self.session.cookies[cookie.name] = cookie.value
        else:
            login_data = {
                "login[email]": configuration['auth']['nonSso']['username'],
                "login[password]": configuration['auth']['nonSso']['password']
            }
            self.session.post(constants.LOGIN_URL, data = login_data)
    
    @staticmethod
    def removeDimensions(nrqlQuery):
        pattern = re.compile(" facet dimensions\(\)", re.IGNORECASE)
        return pattern.sub("", nrqlQuery)