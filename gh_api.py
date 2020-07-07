import requests
import json
from os import environ

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

def gem_follows_standard(nameWithOwner, release, version):
    repo_standard = requests.get('https://raw.githubusercontent.com/{}/standardizeRepo/.standard-GEM.md'.format(nameWithOwner, release))
    if repo_standard.status_code ==  404:
        return False
    repo_standard = repo_standard.text
    raw_standard = requests.get('https://raw.githubusercontent.com/MetabolicAtlas/standard-GEM/{}/.standard-GEM.md'.format(version)).text
    import difflib
    the_diff = difflib.ndiff(repo_standard, raw_standard)
    return True

def validate(nameWithOwner, version):
    model_filename = 'model.yml'
    data = {}
    data[nameWithOwner] = []
    for release in releases(nameWithOwner):
        release_data = {}
        is_standard = gem_follows_standard(nameWithOwner, version)
        release_data['standard-GEM'] = { version : is_standard }
        if is_standard:
            model = nameWithOwner.split('/')[1]
            response = requests.get('https://raw.githubusercontent.com/{}/{}/model/{}.yml'.format(nameWithOwner, release, model))
            with open(model_filename, 'w') as file:
                file.write(response.text)
            print('Validating YAML with yamllint')
            # yamllint
            is_valid_yaml = False
            try:
                import yamllint
                from yamllint.config import YamlLintConfig
                conf = YamlLintConfig('{extends: default, rules: {line-length: disable}}')
                with open(model_filename, 'r') as file:
                    gen = yamllint.linter.run(file, conf)
                    print(list(gen))
                is_valid_yaml = len(list(gen)) == 0
            except Exception as e:
                print(e)
            finally:
                release_data['yamllint'] = { yamllint.__version__ : is_valid_yaml }
            # cobrapy import
            print('Trying to load yml with cobrapy')
            is_valid_cobrapy = False
            try:
                import cobra
                cobra.io.load_yaml_model(model_filename)
                is_valid_cobrapy = True
            except Exception as e:
                print(e)
            finally:
                release_data['cobrapy-yaml-load'] = { cobra.__version__ : is_valid_cobrapy }

    data[nameWithOwner].append(release_data)
    print(json.dumps(data, indent=4, sort_keys=True))
