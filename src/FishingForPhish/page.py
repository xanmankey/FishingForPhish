# page.py; a python file adapted from Dr. Choon Lin Tan's and others work found at:
# https://www.sciencedirect.com/science/article/abs/pii/S0020025519300763
# The file functions as a built in example for the module
# (but is not ever called by FishingForPhish.py due to the possibility of a circular import)
# and helps the replicability of the research
# Not all of this is documented, as it wasn't written myself, but instead adapted
# so I don't have a full understanding of the inner-workings of this code yet
from FishingForPhish import startFishing, analyzer, scrape, saveFish
from weka.core.dataset import Instance
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
import operator
import urllib
from urllib.parse import urlparse
import tldextract
from IPy import IP
from urllib3.exceptions import InsecureRequestWarning
import cssutils
import requests
import logging

class pageAnalyzer(analyzer):
    '''A class for scraping page-based features'''

    def __init__(self, features=[], featureNames={
        'NumDots':"numeric",
        'SubdomainLevel':"numeric",
        'PathLevel':"numeric",
        'UrlLength':"numeric",
        'NumDash':"numeric",
        'NumDashInHostname':"numeric",
        'AtSymbol':"numeric",
        'TildeSymbol':"numeric",
        'NumUnderscore':"numeric",
        'NumPercent':"numeric",
        'NumQueryComponents':"numeric",
        'NumAmpersand':"numeric",
        'NumHash':"numeric",
        'NumNumericChars':"numeric",
        'NoHttps':"numeric",
        'RandomString':"numeric",
        'IpAddress':"numeric",
        'DomainInSubdomains':"numeric",
        'DomainInPaths':"numeric",
        'HttpsInHostname':"numeric",
        'HostnameLength':"numeric",
        'PathLength':"numeric",
        'QueryLength':"numeric",
        'DoubleSlashInPath':"numeric",
        'NumSensitiveWords':"numeric",
        'EmbeddedBrandName':"numeric",
        'PctExtHyperlinks':"numeric",
        'PctExtResourceUrls':"numeric",
        'ExtFavicon':"numeric",
        'InsecureForms':"numeric",
        'RelativeFormAction':"numeric",
        'ExtFormAction':"numeric",
        'AbnormalFormAction':"numeric",
        'PctNullSelfRedirectHyperlinks':"numeric",
        'FrequentDomainNameMismatch':"numeric",
        'FakeLinkInStatusBar':"numeric",
        'RightClickDisabled':"numeric",
        'PopUpWindow':"numeric",
        'SubmitInfoToEmail':"numeric",
        'IframeOrFrame':"numeric",
        'MissingTitle':"numeric",
        'ImagesOnlyInForm':"numeric",
        'SubdomainLevelRT':"numeric",
        'UrlLengthRT':"numeric",
        'PctExtResourceUrlsRT':"numeric",
        'AbnormalExtFormActionR':"numeric",
        'ExtMetaScriptLinkRT':"numeric",
        'PctExtNullSelfRedirectHyperlinksRT':"numeric",
        "classVal":"nominal"
    }, **kwargs):
        '''Inherits all previous attributes, adds an optional attribute called pageFeatures
        (although the purpose of the function is to populate the pageFeatures list, so there
        isn't much of a point in passing in a value pageFeatures. If you already have a value,
        I recommend either scraping image data as well
        or creating an instance of the combine class to create datasets of your data)'''
        super().__init__(**kwargs)
        # For each analyzer, it is recommended that you create attributes for features and featureNames
        # You can return them as values instead in the analyze function, but it may be useful for convenience purposes
        self.features = features
        self.featureNames = featureNames
        self.classVal = Instance.missing_value()

    def get_complete_webpage_url(self, saved_actual_url):
        parsed = urlparse(saved_actual_url)

        if saved_actual_url.endswith('/') and '?' not in saved_actual_url:

            complete_webpage_url = saved_actual_url + 'index.html'

        elif parsed.netloc != '' and parsed.path == '':

            complete_webpage_url = saved_actual_url + '/index.html'

        # parsed.path has some string but no filename extension
        elif not saved_actual_url.endswith('/') and parsed.path != '':

            if not saved_actual_url.endswith('.htm') and not saved_actual_url.endswith('.html'):

                complete_webpage_url = saved_actual_url + '.html'
            else:
                complete_webpage_url = saved_actual_url

        return complete_webpage_url

    def analyze(self, url, filename, resources, urlNum):

        # Initialize feature dictionary
        features = {}

        for name in self.featureNames.keys():
            features.update({name:0})

        parsed = urlparse(url)

        # Count number of dots in full URL
        features.update({'NumDots':url.count('.')})

        # Count path level
        if parsed.path != '':

            if parsed.path == '/':
                features.update({'PathLevel':0})
            else:
                parsed_path_list = parsed.path.split('/')
                features.update({'PathLevel':len(parsed_path_list) - 1})

        # no path
        else:
            features.update({'PathLevel':0})

        # Count total characters in URL
        features.update({'UrlLength':len(url)})

        # Count total characters in URL (RT)
        if len(url) < 54:
            features.update({'UrlLengthRT':1})
        elif len(url) >= 54 and len(url) <= 75:
            features.update({'UrlLengthRT':0})
        else:
            features.update({'UrlLengthRT':-1})

        # Count dash symbol in full URL
        features.update({'NumDash':url.count('-')})

        # Count dash symbol in hostname
        features.update({'NumDashInHostname':parsed.netloc.count('-')})

        # Check @ symbol in URL
        if '@' in url:
            features.update({'AtSymbol':1})
        else:
            features.update({'AtSymbol':0})

        # Check tilde symbol in URL
        if '~' in url:
            features.update({'TildeSymbol':1})
        else:
            features.update({'TildeSymbol':0})

        # Count underscore symbol in URL
        features.update({'NumUnderscore':url.count('_')})

        # Count percent symbol in URL
        features.update({'NumPercent':url.count('%')})

        # Count number of query components in URL
        features.update({'NumQueryComponents':parsed.query.count('=')})

        # Count ampersand symbol in URL
        features.update({'NumAmpersand':url.count('&')})

        # Count hash symbol in URL
        features.update({'NumHash':url.count('#')})

        # Count numeric characters in URL
        features.update({'NumNumericChars':sum(char.isdigit() for char in url)})

        # Check no HTTPS
        if parsed.scheme == 'http':
            features.update({'NoHttps':1})
        elif parsed.scheme == 'https':
            features.update({'NoHttps':0})

        # Check random string in URL
        parsed_netloc_str = parsed.netloc

        # check for hostname part
        for token in parsed_netloc_str.replace(
                '.', ' ').replace('-', ' ').split(' '):
            consonant_count = 0

            for char in token.lower():
                if (char != 'a' and char != 'e' and char != 'i' and char != 'o' and char != 'u'):
                    consonant_count += 1
                else:
                    # reset consonant count
                    consonant_count = 0

                # assume 4 consonants is not pronounciable
                if consonant_count == 4:
                    features.update({'RandomString':1})
                    break
                else:
                    features.update({'RandomString':0})

        # continue checking path if no random string found previously
        if features['RandomString'] != 1:

            # check for path part
            for token in parsed.path.replace(
                    '/',
                    ' ').strip().replace(
                    '-',
                    ' ').replace(
                    '_',
                    ' ').replace(
                        '.',
                    ' ').split(' '):
                consonant_count = 0
                possible_random_str = ''

                for char in token.lower():
                    if (char != 'a' and char != 'e' and char !=
                            'i' and char != 'o' and char != 'u'):
                        consonant_count += 1
                        possible_random_str += char
                    else:
                        # reset consonant count
                        consonant_count = 0

                    if consonant_count == 4 and possible_random_str not in [
                            'html', 'xhtml']:
                        features.update({'RandomString':1})
                        break

        base_url_to_be_replaced = 'file:' + urllib.request.pathname2url(resources["dataDir"]) + str(urlNum) + '/'

        url_scheme = parsed.scheme + '://'

        # ext = tldextract.TLDExtract(suffix_list_urls=None, fallback_to_snapshot=False)
        ext = tldextract.TLDExtract(suffix_list_urls=None)
        ext1 = ext(url)
        domain_query = ext1.domain + '.' + ext1.suffix

        if ext1.suffix == '':
            try:
                IP(ext1.domain)
                domain_query = ext1.domain

                features.update({'IpAddress':1})

            except BaseException:
                pass
                features.update({'IpAddress':0})

        # Count level of subdomains
        if ext1.subdomain == '':
            features.update({'SubdomainLevel':0})
        else:
            subdomain_list = ext1.subdomain.split('.')
            features.update({'SubdomainLevel':len(subdomain_list)})

        # Check multiple subdomains (RT)
        if ext1.subdomain == '':
            features.update({'SubdomainLevelRT':1})
        else:
            subdomain_domain_str = ext1.subdomain + '.' + ext1.domain

            if subdomain_domain_str.lower().startswith('www.'):
                # discard 'www.' string
                subdomain_domain_str = subdomain_domain_str[4:]

            if subdomain_domain_str.count('.') <= 1:
                features.update({'SubdomainLevelRT':1})

            elif subdomain_domain_str.count('.') == 2:
                features.update({'SubdomainLevelRT':0})

            else:
                features.update({'SubdomainLevelRT':-1})

        extraction = tldextract.extract(url)
        urlSuffix = extraction.suffix

        # Check TLD or ccTLD used in subdomain part
        if ext1.subdomain == '':
            features.update({'DomainInSubdomains':0})
        else:
            for token in urlSuffix:
                # if token in ext1.subdomain.lower():
                token_location = ext1.subdomain.lower().find(token)
                if token_location != -1:

                    if ext1.subdomain.lower().startswith(token):
                        pass

                    elif ext1.subdomain.lower().endswith(token):
                        if not ext1.subdomain[token_location - 1].isalnum():

                            features.update({'DomainInSubdomains':1})
                            break

                    elif not ext1.subdomain[token_location - 1].isalnum() and not ext1.subdomain[token_location + len(token)].isalnum():

                        features.update({'DomainInSubdomains':1})
                        break

        # Check TLD or ccTLD used in path part
        if parsed.path == '':
            features.update({'DomainInPaths':0})
        else:
            for token in urlSuffix:
                token_location = parsed.path.lower().find(token)

                if token_location != -1:

                    if parsed.path.lower().startswith(token):
                        pass

                    elif parsed.path.lower().endswith(token):
                        if not parsed.path[token_location - 1].isalnum():

                            features.update({'DomainInPaths':1})
                            break

                    elif not parsed.path[token_location - 1].isalnum() and not parsed.path[token_location + len(token)].isalnum():

                        features.update({'DomainInPaths':1})
                        break

        # Check https is obfuscated in hostname
        if 'https' in parsed.netloc.lower():
            features.update({'HttpsInHostname':1})
        else:
            features.update({'HttpsInHostname':0})

        # Count length of hostname
        features.update({'HostnameLength':len(parsed.netloc)})

        # Count length of path
        features.update({'PathLength':len(parsed.path)})

        # Count length of query
        features.update({'QueryLength':len(parsed.query)})

        # Check double slash exist in path
        if '//' in parsed.path:
            features.update({'DoubleSlashInPath':1})

        else:
            features.update({'DoubleSlashInPath':0})

        # Check how many sensitive words occur in URL
        sensitive_word_list = [
            'secure',
            'account',
            'webscr',
            'login',
            'ebayisapi',
            'signin',
            'banking',
            'confirm']
        features.update({'NumSensitiveWords':0})
        for word in sensitive_word_list:
            if word in url.lower():
                features['NumSensitiveWords'] += 1

        caching = False

        if not caching:
            resources["driver"].set_page_load_timeout(120)

            try:
                resources["driver"].get(url)
            except BaseException:
                pass

            # SWITCH OFF ALERTS
            while True:
                try:
                    WebDriverWait(
                        resources["driver"], 3).until(
                        expected_conditions.alert_is_present())

                    # alert = resources["driver"].switch_to_alert()
                    alert = resources["driver"].switch_to.alert
                    alert.dismiss()

                except TimeoutException:
                    break

            total_input_field = 0

            captured_domains = []

            resource_URLs = []
            hyperlink_URLs = []
            meta_script_link_URLs = []
            request_URLs = []
            null_link_count = 0
            original_link_count = 0

            # Extracts main visible text from HTML
            iframe_frame_elems = ''
            iframe_frame_elems = resources["driver"].find_elements(By.TAG_NAME, 'iframe')
            iframe_frame_elems.extend(
                resources["driver"].find_elements(
                    By.TAG_NAME, 'frame'))

            # Check iframe or frame exist
            if len(iframe_frame_elems) > 0:
                features.update({'IframeOrFrame':1})
            else:
                features.update({'IframeOrFrame':0})

            for iframe_frame_elem in iframe_frame_elems:
                iframe_frame_style = iframe_frame_elem.get_attribute(
                    'style').replace(' ', '')
                if iframe_frame_style.find(
                        "visibility:hidden") == -1 and iframe_frame_style.find("display:none") == -1:

                    try:
                        resources["driver"].switch_to.frame(iframe_frame_elem)
                    except BaseException:
                        continue

                    try:
                        input_field_list = resources["driver"].find_elements(
                            By.XPATH, '//input')
                    except BaseException:
                        input_field_list = []

                    total_input_field += len(input_field_list)

                    tag_attrib = ['src', 'href']
                    tag_count = 0
                    link_count = 0

                    # Extract all URLs
                    while tag_count <= 1:
                        elements = resources["driver"].find_elements(
                            By.XPATH, '//*[@' + tag_attrib[tag_count] + ']')
                        if elements:
                            for elem in elements:
                                try:
                                    link = ''
                                    link = elem.get_attribute(
                                        tag_attrib[tag_count])

                                    # Check null link
                                    null_link_detected = False
                                    if tag_count == 1 and elem.get_attribute('outerHTML').lower().startswith('<a') and (
                                        link.startswith('#') or link == '' or link.lower().replace(
                                            ' ', '').startswith('javascript::void(0)')):
                                        null_link_count += 1
                                        null_link_detected = True

                                    # Construct full URL from relative URL (if
                                    # webpage sample is processed offline)
                                    if not link.startswith('http') and not link.startswith(
                                            "javascript"):
                                        # link = base_url + '/' + link    # this is
                                        # for live relative URLs

                                        # link = link.replace(base_url_to_be_replaced, url)

                                        link = link.replace(
                                            base_url_to_be_replaced, url_scheme)
                                        link = link.replace('///', '//')
                                        link = link.replace(
                                            'file://C:/', url)
                                        # link = link.replace('file:///', url_scheme)
                                        link = link.replace(
                                            'file://', url_scheme)

                                        # pass

                                    link_count += 1
                                    original_link_count += 1

                                    # Check null link after constructing full URL
                                    # from local URL (if webpage sample is
                                    # processed offline)
                                    if tag_count == 1 and elem.get_attribute('outerHTML').lower().startswith('<a') and not null_link_detected and (
                                            link == self.get_complete_webpage_url(url, urlNum) or link == self.get_complete_webpage_url(url, urlNum) + '#'):
                                        null_link_count += 1

                                    # print link
                                    # if link not in captured_domains and link !=
                                    # "":
                                    if link != '' and link.startswith('http'):

                                        captured_domains.append(link)

                                        if tag_count == 0:
                                            resource_URLs.append(link)
                                        elif tag_count == 1:
                                            # TODO: missing one hyperlink_URL
                                            if not elem.get_attribute('outerHTML').lower(
                                            ).startswith('<link'):
                                                hyperlink_URLs.append(link)
                                            else:
                                                if elem.get_attribute('rel') in [
                                                'stylesheet', 'shortcut icon', 'icon']:
                                                    resource_URLs.append(link)

                                        # RT
                                        if elem.get_attribute('outerHTML').lower().startswith('<meta') or \
                                                elem.get_attribute('outerHTML').lower().startswith('<script') or \
                                                elem.get_attribute('outerHTML').lower().startswith('<link'):

                                            meta_script_link_URLs.append(link)

                                        elif elem.get_attribute('outerHTML').lower().startswith('<a'):
                                            pass
                                        else:
                                            request_URLs.append(link)

                                except BaseException:
                                    pass

                        tag_count += 1

                    resources["driver"].switch_to.default_content()

            resources["driver"].switch_to.default_content()

            try:
                input_field_list = resources["driver"].find_elements(By.XPATH, '//input')
            except BaseException:
                pass

            total_input_field += len(input_field_list)

            tag_attrib = ['src', 'href']
            tag_count = 0
            link_count = 0

            # Extract all URLs
            while tag_count <= 1:
                elements = ''
                elements = resources["driver"].find_elements(
                    By.XPATH, '//*[@' + tag_attrib[tag_count] + ']')

                for elem in elements:

                    try:
                        link = ''
                        link = elem.get_attribute(tag_attrib[tag_count])

                        # Check null links
                        null_link_detected = False
                        # if tag_count == 1 and (link.startswith('#') or link ==
                        # ''):
                        if tag_count == 1 and elem.get_attribute('outerHTML').lower().startswith('<a') and (
                            link.startswith('#') or link == '' or link.lower().replace(
                                ' ', '').startswith('javascript::void(0)')):
                            null_link_count += 1
                            null_link_detected = True

                        # Construct full URL from relative URL (if webpage sample
                        # is processed offline)
                        if not link.startswith('http') and not link.startswith(
                                "javascript"):
                            # link = base_url + '/' + link

                            # link = link.replace(base_url_to_be_replaced, url)

                            link = link.replace(
                                base_url_to_be_replaced, url_scheme)
                            link = link.replace('///', '//')
                            link = link.replace('file://C:/', url)

                            link = link.replace('file://', url_scheme)

                        link_count += 1
                        original_link_count += 1

                        # Check null links after constructing full URL from local
                        # URL (if webpage sample is processed offline)
                        if tag_count == 1 and elem.get_attribute('outerHTML').lower().startswith('<a') and not null_link_detected and (
                                link == self.get_complete_webpage_url(url) or link == self.get_complete_webpage_url(url) + '#'):
                            null_link_count += 1
                            null_link_detected = True

                        if link != '' and link.startswith('http'):

                            captured_domains.append(link)

                            if tag_count == 0:
                                resource_URLs.append(link)
                            elif tag_count == 1:
                                if not elem.get_attribute('outerHTML').lower(
                                ).startswith('<link'):
                                    hyperlink_URLs.append(link)
                                else:
                                    if elem.get_attribute('rel') in [
                                    'stylesheet', 'shortcut icon', 'icon']:
                                        resource_URLs.append(link)

                            if elem.get_attribute('outerHTML').lower().startswith('<meta') or \
                                    elem.get_attribute('outerHTML').lower().startswith('<script') or \
                                    elem.get_attribute('outerHTML').lower().startswith('<link'):

                                meta_script_link_URLs.append(link)

                            elif elem.get_attribute('outerHTML').lower().startswith('<a'):
                                pass
                            else:
                                request_URLs.append(link)

                    except BaseException:
                        pass

                tag_count += 1

            # Calculate null or self redirecct hyperlinks

            # feature['PctNullSelfRedirectHyperlinks'] =
            # float('{:.6f}'.format(float(null_link_count)/float(original_link_count)))
            # fixed to 10 decimal places
            if len(hyperlink_URLs) > 0:
                features.update({'PctNullSelfRedirectHyperlinks':'{:.10f}'.format(float(
                    null_link_count) / float(len(hyperlink_URLs)))})
            else:
                features.update({'PctNullSelfRedirectHyperlinks':'{:.10f}'.format(
                    0)})

        # Check whether brand name appears in subdomains and paths

        # domain_tokens = tldextract.TLDExtract(suffix_list_urls=None, fallback_to_snapshot=False)
        domain_tokens = tldextract.TLDExtract(suffix_list_urls=None)
        domains = []
        domains_freq = {}

        # create dictionary of domain frequencies
        # (I think iterating over captured_domains is fine;
        # I had to refactor the code slightly)
        for url in captured_domains:
            domain_str = domain_tokens(url).domain + '.' + domain_tokens(url).suffix

            if url.startswith('http') and domain_str not in domains:

                domains.append(domain_str)

            if url.startswith('http'):
                if domain_str not in domains_freq:
                    domains_freq[domain_str] = 1
                else:
                    domains_freq[domain_str] += 1

            if len(url) > 0:
                max_freq_domain = max(
                    domains_freq.items(),
                    key=operator.itemgetter(1))[0]
            else:
                max_freq_domain = ''

            try:
                # is IP
                IP(max_freq_domain)
                brand_name = max_freq_domain

            # not IP, extract first dot separated token
            except BaseException:
                pass
                brand_name = max_freq_domain.split('.')[0]

        parsed = urlparse(url)
        # ext = tldextract.TLDExtract(suffix_list_urls=None, fallback_to_snapshot=False)
        ext = tldextract.TLDExtract(suffix_list_urls=None)
        ext1 = ext(url)
        if brand_name.lower() in ext1.subdomain.lower(
        ) or brand_name.lower() in parsed.path.lower():
            if brand_name != '':
                features.update({'EmbeddedBrandName':1})
            else:
                features.update({'EmbeddedBrandName':0})
        else:
            features.update({'EmbeddedBrandName':0})

        # Check frequent domain name in HTML matches with webpage domain name
        if max_freq_domain != domain_query:
            features.update({'FrequentDomainNameMismatch':1})
        else:
            features.update({'FrequentDomainNameMismatch':0})

        # Count percentage of external hyperlinks
        external_hyperlink_count = 0

        for link in hyperlink_URLs:

            ext2 = ext(link)

            domain_str_ext2 = ext2.domain + '.' + ext2.suffix
            if ext2.suffix == '':
                try:
                    IP(ext2.domain)
                    domain_str_ext2 = ext2.domain

                except BaseException:
                    pass

            if domain_str_ext2 != domain_query:
                external_hyperlink_count += 1

        # print 'len(hyperlink_URLs) = ' + str(len(hyperlink_URLs))
        # feature['PctExtHyperlinks'] =
        # float('{:.6f}'.format(float(external_hyperlink_count)/float(len(hyperlink_URLs))))
        # fixed to 10 decimal places
        if len(hyperlink_URLs) > 0:
            features.update({'PctExtHyperlinks':'{:.10f}'.format(
                float(external_hyperlink_count) /
                float(
                    len(hyperlink_URLs)))})
        else:
            features.update({'PctExtHyperlinks':'{:.10f}'.format(0)})

        # Calculate URL of anchor (RT)
        percent_external_or_null_hyperlinks = float(
            features['PctExtHyperlinks']) + float(features['PctNullSelfRedirectHyperlinks'])

        if percent_external_or_null_hyperlinks < 0.31:
            features.update({'PctExtNullSelfRedirectHyperlinksRT':1})
        elif percent_external_or_null_hyperlinks >= 0.31 and percent_external_or_null_hyperlinks <= 0.67:
            features.update({'PctExtNullSelfRedirectHyperlinksRT':0})
        else:
            features.update({'PctExtNullSelfRedirectHyperlinksRT':-1})

        # Count percentage of external resources
        external_resource_count = 0

        for url in resource_URLs:

            ext2 = ext(url)

            domain_str_ext2 = ext2.domain + '.' + ext2.suffix
            if ext2.suffix == '':
                try:
                    IP(ext2.domain)
                    domain_str_ext2 = ext2.domain

                except BaseException:
                    pass

            if domain_str_ext2 != domain_query:
                external_resource_count += 1

        if len(resource_URLs) > 0:
            # fix to 10 decimal places
            features.update({'PctExtResourceUrls':'{:.10f}'.format(
                float(external_resource_count) /
                float(
                    len(resource_URLs)))})
        else:
            # fix to 10 decimal places
            features.update({'PctExtResourceUrls':'{:.10f}'.format(
                0)})

        # Count percentage of external request URLs (RT)
        external_request_URLs = 0
        for url in request_URLs:

            ext2 = ext(url)

            domain_str_ext2 = ext2.domain + '.' + ext2.suffix
            if ext2.suffix == '':
                try:
                    IP(ext2.domain)
                    domain_str_ext2 = ext2.domain

                except BaseException:
                    pass

            if domain_str_ext2 != domain_query:
                external_request_URLs += 1

        # print 'len(request_URLs) = ' + str(len(request_URLs))

        if len(request_URLs) > 0:
            if float(external_request_URLs) / float(len(request_URLs)) < 0.22:
                features.update({'PctExtResourceUrlsRT':1})
            elif float(external_request_URLs) / float(len(request_URLs)) >= 0.22 and float(external_request_URLs) / float(len(request_URLs)) <= 0.61:
                features.update({'PctExtResourceUrlsRT':0})
            else:
                features.update({'PctExtResourceUrlsRT':-1})
        else:
            features.update({'PctExtResourceUrlsRT':1})

        # Count percentage external meta script link (RT)
        external_meta_script_link_count = 0
        for meta_script_link_URL in meta_script_link_URLs:

            ext_meta_script_link = ext(meta_script_link_URL)

            domain_str_ext_meta_script_link = ext_meta_script_link.domain + \
                '.' + ext_meta_script_link.suffix
            if ext_meta_script_link.suffix == '':
                try:
                    IP(ext_meta_script_link.domain)
                    domain_str_ext_meta_script_link = ext_meta_script_link.domain

                except BaseException:
                    pass

            if domain_str_ext_meta_script_link != domain_query:
                external_meta_script_link_count += 1

        # print 'len(meta_script_link_URLs) = ' + str(len(meta_script_link_URLs))
        if len(meta_script_link_URLs) > 0:
            if float(external_meta_script_link_count) / \
                    float(len(meta_script_link_URLs)) < 0.17:
                features.update({'ExtMetaScriptLinkRT':1})
            elif float(external_meta_script_link_count) / float(len(meta_script_link_URLs)) >= 0.17 and float(external_meta_script_link_count) / float(len(meta_script_link_URLs)) <= 0.81:
                features.update({'ExtMetaScriptLinkRT':0})
            else:
                features.update({'ExtMetaScriptLinkRT':-1})
        else:
            features.update({'ExtMetaScriptLinkRT':1})

        # Check whether favicon is external
        # <link rel="shortcut icon" type="image/ico" href="favicon.ico" />

        link_elems = resources["driver"].find_elements(By.XPATH, 'link')
        favicon_URL = ''

        for link_elem in link_elems:
            if link_elem.get_attribute(
                    'rel') == 'shortcut icon' or link_elem.get_attribute('rel') == 'icon':
                favicon_URL = link_elem.get_attribute('href')
                break

        if favicon_URL != '':
            # if favicon_URL.startswith('http'):
            ext_fav = ext(favicon_URL)

            domain_str_ext_fav = ext_fav.domain + '.' + ext_fav.suffix
            if ext_fav.suffix == '':
                try:
                    IP(ext_fav.domain)
                    domain_str_ext_fav = ext_fav.domain

                except BaseException:
                    pass

            if domain_str_ext_fav != domain_query:
                features.update({'ExtFavicon':1})
            else:
                features.update({'ExtFavicon':0})

        else:
            features.update({'ExtFavicon':0})

        form_elems = resources["driver"].find_elements(By.TAG_NAME, 'form')

        # Check for external form action
        for form_elem in form_elems:

            if form_elem.get_attribute('action') is not None:
                if form_elem.get_attribute('action').startswith('http'):

                    # check internal or external form
                    ext_form = ext(form_elem.get_attribute('action'))

                    domain_str_ext_form = ext_form.domain + '.' + ext_form.suffix
                    if ext_form.suffix == '':
                        try:
                            IP(ext_form.domain)
                            domain_str_ext_form = ext_form.domain

                        except BaseException:
                            pass

                    if domain_str_ext_form != domain_query:
                        features.update({'ExtFormAction':1})
                        break

        # Check for insecure form action
        for form_elem in form_elems:

            if form_elem.get_attribute('action') is not None:

                if form_elem.get_attribute('action').startswith('http'):

                    if form_elem.get_attribute('action').startswith('https'):
                        pass
                    else:
                        features.update({'InsecureForms':1})
                        break

                else:
                    # look at page URL
                    if parsed.scheme == 'https':
                        pass
                    else:
                        features.update({'InsecureForms':1})
                        break

        # Check for relative form action
        for form_elem in form_elems:

            if form_elem.get_attribute('action') is not None:

                if form_elem.get_attribute('action').startswith('http'):
                    pass

                else:
                    features.update({'RelativeFormAction':1})
                    break

        # Check for abnormal form action
        for form_elem in form_elems:

            if form_elem.get_attribute('action') is not None:
                # if normal form
                if form_elem.get_attribute('action').startswith('http'):
                    pass
                else:

                    if form_elem.get_attribute('action').lower().replace(' ', '') in [
                            '', '#', 'about:blank', 'javascript:true']:
                        features.update({'AbnormalFormAction':1})
                        break

        # Check server form handler (R)
        # otherwise legitimate state
        features.update({'AbnormalExtFormActionR':1})
        for form_elem in form_elems:

            if form_elem.get_attribute('action') is not None:
                # check link to external domain
                if form_elem.get_attribute('action').startswith(
                        'http'):
                    # pass

                    ext_form = ext(form_elem.get_attribute('action'))

                    domain_str_form = ext_form.domain + '.' + ext_form.suffix
                    if ext_form.suffix == '':
                        try:
                            IP(ext_form.domain)
                            domain_str_form = ext_form.domain

                        except BaseException:
                            pass

                    if domain_str_form != domain_query:
                        features.update({'AbnormalExtFormActionR':0})
                        break

                else:

                    if form_elem.get_attribute('action').lower().replace(
                            ' ', '') in ['', 'about:blank']:
                        features.update({'AbnormalExtFormActionR':-1})
                        break

        # Check for right click disabled
        page_src_str = resources["driver"].page_source
        page_src_no_space_lower_str = page_src_str.replace(' ', '').lower()

        # document.addEventListener('contextmenu', event =>
        # event.preventDefault());

        if 'addEventListener'.lower() in page_src_no_space_lower_str and 'contextmenu' in page_src_no_space_lower_str and 'preventDefault' in page_src_no_space_lower_str:
            features.update({"RightClickDisabled":1})

        elif 'event.button==2' in page_src_no_space_lower_str:
            features.update({'RightClickDisabled':1})

        else:
            disable_right_click_list = resources["driver"].find_elements(
                By.XPATH, '//*[@oncontextmenu="return false"]')
            disable_right_click_list.extend(resources["driver"].find_elements(
                By.XPATH, '//*[@oncontextmenu="return false;"]'))

            if len(disable_right_click_list) > 0:
                features.update({'RightClickDisabled':1})

        # Check for pop-up

            # if 'window.open(' in page_src_no_space_lower_str and
            # ('onLoad="'.lower() in page_src_no_space_lower_str or
            # 'onClick="'.lower() in page_src_no_space_lower_str):

        onload_count = len(resources["driver"].find_elements(By.XPATH, '//*[@onLoad]'))
        onclick_count = len(resources["driver"].find_elements(By.XPATH, '//*[@onClick]'))

        if 'window.open(' in page_src_no_space_lower_str and (
                onload_count > 0 or onclick_count > 0):
            features.update({'PopUpWindow':1})
        else:
            features.update({'PopUpWindow':0})

        # Check mailto function exist
        if 'mailto:' in page_src_no_space_lower_str:
            features.update({'SubmitInfoToEmail':1})
        else:
            features.update({'SubmitInfoToEmail':0})

        # Check for empty webpage title
        if resources["driver"].title.strip() == '':
            features.update({'MissingTitle':1})
        else:
            features.update({'MissingTitle':0})

        # Check whether form contain only images without text
        form_elems = resources["driver"].find_elements(By.TAG_NAME, 'form')
        visible_text_in_form = ''
        image_elems_in_form = []
        for form_elem in form_elems:

            # visible_text_in_form += form_elem.text.strip() + ' '
            try:
                visible_text_in_form += form_elem.text.strip() + ' '
            except BaseException:
                pass

            image_elems_in_form.extend(form_elem.find_elements(By.XPATH, './/img'))

        if visible_text_in_form.strip() == '' and len(image_elems_in_form) > 0:
            features.update({'ImagesOnlyInForm':1})
        else:
            features.update({'ImagesOnlyInForm':0})

        # Check for fake links in status bar

        # case 1 - mentioned alot in literature
        hyperlinks_case_1 = resources["driver"].find_elements(
            By.XPATH, '//a[@onmouseover and @onmouseout]')
        if 'window.status=' in page_src_no_space_lower_str and len(
                hyperlinks_case_1) > 0:
            features.update({'FakeLinkInStatusBar':1})

        # #case2  - Google search result ads using this           # Disable this temporarily
        # hyperlinks_case_2 = resources["driver"].find_elements_by_xpath('//a[@onclick]')
        # if len(hyperlinks_case_2) > 0 and ('location.href=' in page_src_no_space_lower_str or 'document.location=' in page_src_no_space_lower_str or 'window.location=' in page_src_no_space_lower_str or 'this.href=' in page_src_no_space_lower_str):
            # feature['FakeLinkInStatusBar'] = 1

        # case 3
        if 'onclick=' in page_src_no_space_lower_str and 'stopEvent'.lower() in page_src_no_space_lower_str and (
                'location.href=' in page_src_no_space_lower_str or 'document.location=' in page_src_no_space_lower_str or 'window.location=' in page_src_no_space_lower_str or 'this.href=' in page_src_no_space_lower_str):
            features.update({'FakeLinkInStatusBar':1})

        features.update({"classVal":self.classVal})
        self.features.append(features)
        resources.update({"features":features})
        resources.update({"featureNames":self.featureNames})
        return resources


if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings(
        category=InsecureRequestWarning)
    cssutils.log.setLevel(logging.CRITICAL)
    run = startFishing()
    run.installResources()
    run.initializeSelenium()

    fisher = scrape(
        urlFile="data/urls.txt",
        dataDir="data",
        driver=run.driver,
        classVal=0
    )

    pageData = pageAnalyzer()
    fisher.addAnalyzer(pageData)

    fisher.goFish()
    print(pageData.features)

    DC = saveFish(
        urlFile="data/urls.txt",
        dataDir="data",
        driver=run.driver,
        classVal=0,
        analyzers=fisher.analyzers,
        allFeatures=fisher.allFeatures,
        allFeatureNames=fisher.allFeatureNames
    )
    DC.createDatasets()
    DC.classify()
    print(DC.score)
    print(DC.classifications)

    DC.closePWW3()
    DC.closeSelenium()
