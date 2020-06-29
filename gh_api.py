import requests
import json
from os import environ
from difflib import context_diff

api_endpoint = 'https://api.github.com/graphql'
api_token = environ['GH_TOKEN']
header_auth = {'Authorization': 'token %s' % api_token}

def gem_repositories():
    json_request = {"query" : "{ search(type: REPOSITORY, query: \"\"\"topic:standard-GEM\"\"\", first: 50) { repos: edges { repo: node { ... on Repository { nameWithOwner } } } } }" }
    r = requests.post(url=api_endpoint, json=json_request, headers=header_auth)
    json_data = json.loads(r.text)['data']['search']['repos']
    gem_repositories = map(lambda x: x['repo']['nameWithOwner'], json_data)
    filtered_repositories = filter(lambda x: 'standard-GEM' not in x, gem_repositories)
    return filtered_repositories

def releases(nameWithOwner):
    owner, repo =  nameWithOwner.split('/')
    json_request = { "query": "{ repository(owner: \"%s\", name: \"%s\") { releases(last: 10) { edges { node { tagName } } } } }" % (owner, repo) }
    r = requests.post(url=api_endpoint, json=json_request, headers=header_auth)
    json_data = json.loads(r.text)['data']['repository']['releases']['edges']
    release_tags = list(map(lambda x: x['node']['tagName'], json_data))
    if not release_tags:
        return []
    return release_tags

def standard_versions():
    return releases('MetabolicAtlas/standard-GEM') + ['develop']

def matrix():
    m = []
    for g in gem_repositories():
        for v in standard_versions():
            m.append({ 'gem': g, 'version': v })
    matrix_json = {"include": m }
    print(json.dumps(matrix_json))

def valid():
    repo_standard = requests.get('https://raw.githubusercontent.com/{}/standardizeRepo/.standard-GEM.md'.format('SysBioChalmers/Human-GEM'))
    if repo_standard.status_code ==  404:
        print('gem is missing standard file')
    repo_standard = repo_standard.text
    raw_standard = requests.get('https://raw.githubusercontent.com/MetabolicAtlas/standard-GEM/{}/.standard-GEM.md'.format('develop')).text
    print(raw_standard)
    for line in context_diff(repo_standard, raw_standard):
        print(line)