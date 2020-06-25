import requests
import json
import os
import itertools

api_endpoint = 'https://api.github.com/graphql'
api_token = os.environ['GH_TOKEN']
header_auth = {'Authorization': 'token %s' % api_token}

def gem_repositories():
    json_request = {"query" : "{ search(type: REPOSITORY, query: \"\"\"topic:standard-GEM\"\"\", first: 50) { repos: edges { repo: node { ... on Repository { nameWithOwner } } } } }" }
    r = requests.post(url=api_endpoint, json=json_request, headers=header_auth)
    json_data = json.loads(r.text)['data']['search']['repos']
    gem_repositories = list(map(lambda x: x['repo']['nameWithOwner'], json_data))
    return gem_repositories

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
    print(matrix_json)