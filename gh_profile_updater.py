import os
import json
from github import Github, GithubException

CONFIG_FILE = 'profile_config.json'

def load_config(path=CONFIG_FILE):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)

def ensure_profile_repo(gh, username):
    repo_name = f"{username}"
    full_name = f"{username}/{repo_name}"
    try:
        return gh.get_repo(full_name)
    except GithubException:
        user = gh.get_user()
        return user.create_repo(repo_name, auto_init=True, private=False)

def update_readme(repo, config):
    bio = config.get('bio', '')
    lines = [bio, '']
    projects = config.get('projects', [])
    if projects:
        lines.append('## \ud83d\ude80 Featured Projects')
        for p in projects:
            line = f"- [{p['name']}]({p['url']}) - {p.get('description','')}"
            lines.append(line)
        lines.append('')
    icons = config.get('tech_icons', {})
    if icons:
        lines.append('## \ud83d\udee0 Tech Stack')
        icon_strs = [f"![{k}]({v})" for k, v in icons.items()]
        lines.append(' '.join(icon_strs))
        lines.append('')
    content = '\n'.join(lines)
    try:
        existing = repo.get_contents('README.md')
        repo.update_file(existing.path, 'Update README', content, existing.sha)
    except GithubException:
        repo.create_file('README.md', 'Add README', content)

def set_project_metadata(gh, projects):
    for p in projects:
        repo_full = p['url'].split('github.com/')[-1]
        try:
            r = gh.get_repo(repo_full)
            r.edit(description=p.get('description'))
            topics = p.get('topics', [])
            if topics:
                r.replace_topics(topics)
        except GithubException:
            pass

def pin_repositories(gh, username, repo_names):
    user_query = """
    query($login: String!) {
      user(login: $login) { id pinnedItems(first: 6, types: REPOSITORY) { nodes { ... on Repository { id } } } }
    }
    """
    data = gh.graphql(user_query, login=username)
    user_id = data['user']['id']
    pinned = data['user']['pinnedItems']['nodes']
    unpin = """mutation($repoId:ID!){ unpinRepository(input:{repositoryId:$repoId}) { clientMutationId } }"""
    for node in pinned:
        gh.graphql(unpin, repoId=node['id'])
    pin = """mutation($repoId:ID!){ pinRepository(input:{repositoryId:$repoId}) { clientMutationId } }"""
    for name in repo_names:
        try:
            repo = gh.get_repo(name if '/' in name else f"{username}/{name}")
            gh.graphql(pin, repoId=repo.node_id)
        except GithubException:
            pass

def main():
    token = os.environ['GITHUB_TOKEN']
    username = os.environ['GITHUB_USERNAME']
    config = load_config()
    gh = Github(token)
    repo = ensure_profile_repo(gh, username)
    update_readme(repo, config)
    set_project_metadata(gh, config.get('projects', []))
    pin_repositories(gh, username, config.get('pinned', []))

if __name__ == '__main__':
    main()
