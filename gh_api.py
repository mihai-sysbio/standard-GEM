import requests
import json
import os

api_endpoint = 'https://api.github.com/graphql'
api_token = os.environ['GH_TOKEN']
header_auth = {'Authorization': 'token %s' % api_token}

def standard_repos():
    json_request = {"query" : "{ search(type: REPOSITORY, query: \"\"\"topic:standard-GEM\"\"\", first: 50) { repos: edges { repo: node { ... on Repository { nameWithOwner } } } } }" }
    r = requests.post(url=api_endpoint, json=json_request, headers=header_auth)
    json_data = json.loads(r.text)['data']['search']['repos']
    standard_repos = list(map(lambda x: x['repo']['nameWithOwner'], json_data))
    return standard_repos

def releases(nameWithOwner):
    owner, repo =  nameWithOwner.split('/')
    json_request = { "query": "{ repository(owner: \"%s\", name: \"%s\") { releases(last: 10) { edges { node { tagName } } } } }" % (owner, repo) }
    r = requests.post(url=api_endpoint, json=json_request, headers=header_auth)
    json_data = json.loads(r.text)['data']['repository']['releases']['edges']
    release_tags = map(lambda x: x['node']['tagName'], json_data)
    return list(release_tags)

def standard_versions():
    releases('MetabolicAtlas/standard-GEM')