import logging
import dateparser
import xmltodict
import logging
import requests
from mcp.server.fastmcp import FastMCP

def standardize_date(date_str):
    """
    Convert a date string into the standard YYYY-MM-DD format.

    :param date_str: A date string (e.g., '2022-1-1', '2022-Jan-1').
    :return: A standardized date string in the format YYYY-MM-DD.
    """
    try:
        # Parse the date string to a datetime object
        parsed_date = dateparser.parse(date_str)
        standardized_date = parsed_date.strftime('%Y-%m-%d')
        return standardized_date
    except Exception as e:
        return None 
    
###########################################################
# Extractors
###########################################################

def parse_title(_title):
    '''
    Recursively extract the title from a complex nested dictionary.
    
    :param _title: A nested dictionary containing title data.
    :return: Extracted title as a string or None if not found.
    '''
    if _title is None:
        # If _title is None, return None
        return ''
    
    if isinstance(_title, str):
        # If _title is a string, return it
        return _title
    
    if isinstance(_title, list):
        # If _title is a list, extract the title from each item
        extracted_text = []
        for item in _title:
            extracted_part = parse_title(item)
            if extracted_part:
                extracted_text.append(extracted_part)
        return " ".join(extracted_text) if extracted_text else None
    
    if not isinstance(_title, dict):
        # If _title is not a dictionary, return None
        return None
    
    extracted_text = []
    for key, value in _title.items():
        extracted_part = parse_title(value)
        if extracted_part:
            extracted_text.append(extracted_part)

    return " ".join(extracted_text) if extracted_text else None


def extract_title(data):
    '''
    Recursively extract the title from a complex nested dictionary.
    
    :param _title: A nested dictionary containing title data.
    :return: Extracted title as a string or None if not found.
    '''
    _title = data['MedlineCitation']['Article']['ArticleTitle']
    title = parse_title(_title)

    return title



def extract_date(data):
    '''
    Extract the date from a complex nested dictionary.
    '''
    # all potential dates
    date_dict = {}

    def make_raw_date(date_obj):
        year = date_obj['Year']
        month = date_obj['Month'] if 'Month' in date_obj else None
        day = date_obj['Day'] if 'Day' in date_obj else None
        return f"{year}-{month}-{day}"

    # Extract the publication date
    # the date can be {'Year': '2023', 'Month': 'Dec', 'Day': '11'}
    # but sometimes it can be {'Year': '2023', 'Month': 'Dec'}
    # even {'Year': '2023'}
    # so we need to handle this case, and return a string in the format of 'YYYY-MM-DD'
    try: date_dict['date_pub'] = make_raw_date(data['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate'])
    except: date_dict['date_pub'] = None

    try: date_dict['date_completed'] = make_raw_date(data['MedlineCitation']['DateCompleted'])
    except: date_dict['date_completed'] = None

    try: date_dict['date_revised'] = make_raw_date(data['MedlineCitation']['DateRevised'])
    except: date_dict['date_revised'] = None
    
    _publication_date = data['PubmedData']['History']['PubMedPubDate']
    for _pd in _publication_date:
        pub_status = _pd['@PubStatus']
        try: date_dict['date_history_%s' % pub_status] = make_raw_date(_pd)
        except: date_dict['date_revised'] = None
    
    for date_key in [
        'date_history_pubmed',
        'date_history_medline',
        'date_completed',
        'date_revised',
        'date_pub'
    ]:
        if date_key not in date_dict: continue 
        date = standardize_date(date_dict[date_key])

        # just find the first date that is not None
        if date is not None:
            return date
        
    return '1701-10-09'


def extract_pmid(data):
    '''
    Extract the PMID from a complex nested dictionary.
    '''
    pmid = data['MedlineCitation']['PMID']['#text']
    return pmid


def extract_doi(data):
    '''
    Extract the DOI from a complex nested dictionary.
    '''
    doi = ''
    pmcid = ''
    if 'ArticleIdList' in data['PubmedData']:
        _article_id = data['PubmedData']['ArticleIdList']['ArticleId']

        # sometimes ArticleId is a list of objects, sometimes a single object  
        # need to handle both cases
        if isinstance(_article_id, list):
            for article_id in _article_id:
                if article_id['@IdType'] == 'doi':
                    doi = article_id['#text'] if '#text' in article_id else ''
                elif article_id['@IdType'] == 'pmc':
                    pmcid = article_id['#text'] if '#text' in article_id else ''
                else:
                    pass
        else:
            # if it's a single object, usually it's a pmid, just skip
            pass

    # convert doi to lower case
    doi = doi.lower()

    return doi


def extract_pmcid(data):
    '''
    Extract the PMCID from a complex nested dictionary.
    '''
    pmcid = ''
    if 'ArticleIdList' in data['PubmedData']:
        _article_id = data['PubmedData']['ArticleIdList']['ArticleId']

        # sometimes ArticleId is a list of objects, sometimes a single object  
        # need to handle both cases
        if isinstance(_article_id, list):
            for article_id in _article_id:
                if article_id['@IdType'] == 'pmc':
                    pmcid = article_id['#text'] if '#text' in article_id else ''
                else:
                    pass
        else:
            # if it's a single object, usually it's a pmid, just skip
            pass

    return pmcid


def extract_paper_type(data):
    '''
    Extract the paper type from a complex nested dictionary.

    # e.g., 'Journal Article', 'Review', 'Editorial'
    # sometimes 'PublicationType' can be a list, sometimes a single object
    # need to handle both cases
    '''
    paper_type = ''
    try:
        if isinstance(data['MedlineCitation']['Article']['PublicationTypeList']['PublicationType'], list):
            _publication_types = data['MedlineCitation']['Article']['PublicationTypeList']['PublicationType']
            # join all types with '|'
            paper_type = '|'.join([pt['#text'] for pt in _publication_types])
        else:
            paper_type = data['MedlineCitation']['Article']['PublicationTypeList']['PublicationType']['#text']

    except Exception as e:
        # when parsing a paper in pubmed24n0648.xml.gz, it throws an error
        paper_type = 'Unknown'

    return paper_type


def extract_abstract(data):
    '''
    Extract the abstract from a complex nested dictionary.
    '''
    abstract = ''

    if 'Abstract' in data['MedlineCitation']['Article']:
        # somethimes abstract is a list of object, sometimes a single object, sometimes a string
        # need to handle both cases
        _abstract = data['MedlineCitation']['Article']['Abstract']['AbstractText']
        if isinstance(_abstract, list):
            # item in the list can be a string or an object, need to handle both cases
            tmp = []
            for at in _abstract:
                if at is None: continue
                
                if '@Label' in at:
                    tmp.append(at['@Label'])
                if '#text' in at:
                    tmp.append(at['#text'])
            abstract = ' '.join(tmp)

        elif isinstance(_abstract, dict):
            if '@Label' in _abstract:
                abstract = _abstract['@Label']
            if '#text' in _abstract:
                abstract = _abstract['#text']

        elif _abstract is None:
            abstract = ''

        else:
            abstract = str(data['MedlineCitation']['Article']['Abstract']['AbstractText'])

    return abstract


def extract_authors(data):
    '''
    Extract the authors from a complex nested dictionary.
    '''
    authors = []

    def get_name(author):
        if 'LastName' in author and 'Initials' in author:
            return f"{author['LastName']} {author['Initials']}"
        elif 'LastName' in author and 'ForeName' in author:
            return f"{author['LastName']} {author['ForeName'][0]}"
        else:
            return None
        
    try:
        if 'AuthorList' in data['MedlineCitation']['Article']:
            _authors = data['MedlineCitation']['Article']['AuthorList']['Author']
            if isinstance(_authors, list):
                for author in _authors:
                    _author = get_name(author)
                    if _author:
                        authors.append(_author)
            elif isinstance(_authors, dict):
                _author = get_name(_authors)
                if _author:
                    authors.append(_author)
            else:
                pass

    except Exception as e:
        logging.error(f"* error extracting authors: {e}")
        
    return authors


def extract_references(data):
    '''
    Extract the references from a complex nested dictionary.
    '''
    references = []
    try:
        if 'ReferenceList' in data['PubmedData'] and \
            data['PubmedData']['ReferenceList'] is not None and \
            'Reference' in data['PubmedData']['ReferenceList']:

            _references = data['PubmedData']['ReferenceList']['Reference']

            if isinstance(_references, list):
                for _reference in _references:
                    if 'ArticleIdList' in _reference:
                        _article_ids = _reference['ArticleIdList']['ArticleId']
                        if isinstance(_article_ids, dict):
                            references.append(_article_ids['#text'])
                        elif isinstance(_article_ids, list):
                            references.append(_article_ids[0]['#text'])

            elif isinstance(_references, dict):
                reference = _references
                if 'ArticleIdList' in reference:
                    _article_ids = reference['ArticleIdList']['ArticleId']
                    if isinstance(_article_ids, dict):
                        references.append(_article_ids['#text'])
                    elif isinstance(_article_ids, list):
                        references.append(_article_ids[0]['#text'])
            else:
                # what type of data is this? 
                # I don't know, just skip it
                pass
        else:
            # what??? no references?
            pass
        
    except Exception as e:
        pmid = extract_pmid(data)
        logging.error(f"* error extracting references from {pmid}, return []: {e}")

    return references


def extract_mesh_terms(data):
    '''
    Extract the MeSH terms from a complex nested dictionary.
    '''
    mesh_terms = []

    if 'MeshHeadingList' not in data['MedlineCitation']:
        return mesh_terms
    
    # print('*' * 50)
    # print(data['MedlineCitation']['MeshHeadingList'])
    
    _mesh_terms = data['MedlineCitation']['MeshHeadingList']['MeshHeading']
    if isinstance(_mesh_terms, list):
        for mesh_term in _mesh_terms:
            if 'DescriptorName' in mesh_term:
                mesh_terms.append(mesh_term['DescriptorName']['#text'])

    elif isinstance(_mesh_terms, dict):
        if 'DescriptorName' in _mesh_terms:
            mesh_terms.append(_mesh_terms['DescriptorName']['#text'])
    else:
        pass

    return mesh_terms


def create_paper(xml_text):
    '''
    Extract basic information from the converted XML data
    '''
    xml_dict = xmltodict.parse(xml_text)
        
    # Get both article and book article data
    articles = xml_dict.get("PubmedArticleSet", {}).get("PubmedArticle", [])
    
    # Convert to list if not already
    if articles and not isinstance(articles, list):
        articles = [articles]
    else:
        articles = articles or []
    
    if len(articles) == 0:
        return None

    data = articles[0]
    
    pmid = extract_pmid(data)

    # Extract the DOI (if available)
    doi = extract_doi(data)

    # Extract the PMCID (if available)
    pmcid = extract_pmcid(data)

    # Extract the title
    title = extract_title(data)

    # Extract the paper type
    paper_type = extract_paper_type(data)

    # Extract the source (e.g., journal name)
    source = data['MedlineCitation']['Article']['Journal']['Title']

    # extracct the publication date
    publication_date = extract_date(data)
    
    # extract the abstract
    abstract = extract_abstract(data)

    # extract the authors
    authors = extract_authors(data)

    full_text = ''
    full_text_type = ''
    references = extract_references(data)

    # extract the mesh terms
    mesh_terms = extract_mesh_terms(data)
    
    
    return dict(
        pmid=pmid,
        pmcid=pmcid,
        doi=doi,
        title=title,
        type=paper_type,
        source=source,
        publication_date=publication_date,
        authors=authors,
        abstract=abstract,
        full_text=full_text,
        full_text_type=full_text_type,
        references=references,
        mesh_terms=mesh_terms,

    )




###########################################################
# MCP Server
###########################################################

# Create server
mcp = FastMCP("PubMed")


@mcp.tool()
def get_paper_abstract(pmid: str) -> str:
    """Get the abstract of a paper from PubMed
    
    Args:
        pmid: The PubMed ID of the paper

    Returns:
        The abstract of the paper
    """
    endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}"
    url = endpoint.format(pmid=pmid)
    logging.info(f"get_paper_abstract by url: {url}")
    try:
        response = requests.get(url)
        paper = create_paper(response.text)
        return paper['abstract']
    
    except Exception as e:
        # print the full stack trace
        import traceback
        traceback.print_exc()
        
        logging.error(f"Error getting paper abstract: {e}")
        return f"Error getting paper abstract: {e}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("action", type=str, choices=["run", "test"])
    parser.add_argument("--port", type=int, default=50002)
    args = parser.parse_args()

    if args.action == "run":
        mcp.settings.port = args.port
        mcp.run(
            transport="sse",
        )
    elif args.action == "test":
        print(get_paper_abstract("36990608"))

