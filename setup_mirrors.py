#!/usr/bin/env python

import argparse
import requests

REPOS_URL = "https://api.github.com/user/repos"


def next_link(response):
    if "Link" not in response.headers:
        return None

    links = requests.utils.parse_header_links(response.headers["Link"])

    next = [link for link in links if link["rel"] == "next"]

    if len(next) > 0:
        return next[0]["url"]
    else:
        return None


def fetch_repos(user, token):
    repos = []
    next_url = REPOS_URL
    while True:
        response = requests.get(next_url, auth=(user, token))
        repos = repos + response.json()

        next_url = next_link(response)

        if not next_url:
            return repos


class Gogs:
    def __init__(self, base_url, user, token):
        self.base_url = base_url
        self.user = user
        self.token = token

    def user_id(self):
        url = "{}/api/v1/user".format(self.base_url)
        params = {"token": self.token}
        response = requests.get(url, params=params)
        return response.json()["id"]

    def org_id(self, org_name):
        url = "{}/api/v1/orgs/{}".format(self.base_url, org_name)
        params = {"token": self.token}
        response = requests.get(url, params=params)
        return response.json()["id"]

    def mirror(self, owner_id, repo):
        url = f"{self.base_url}/api/v1/repos/migrate"
        body = {
            "clone_addr": repo["clone_url"],
            "uid": owner_id,
            "repo_name": repo["name"],
            "mirror": True,
            "private": repo["private"],
            "description": repo["description"]
        }

        params = {"token": self.token}
        return requests.post(url, json=body, params=params)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gh-user", required=True, help="github user")
    parser.add_argument("--gh-token", help="github token")
    parser.add_argument("--gogs-url", required=True, help="gogs server URL")
    parser.add_argument("--gogs-user", required=True, help="gogs user")
    parser.add_argument("--gogs-token", help="gogs token")
    parser.add_argument("--gogs-org", help="Gogs organization to mirror to")
    parser.add_argument("--with-forks", type=bool, help="Mirror forks")
    args = parser.parse_args()

    gh_user = args.gh_user
    gh_token = args.gh_token
    gogs_url = args.gogs_url
    gogs_user = args.gogs_user
    gogs_token = args.gogs_token
    gogs_org = args.gogs_org
    with_forks = args.with_forks

    if not gh_token:
        gh_token = input("Github token: ")
    if not gogs_token:
        gogs_token = input("Gogs token: ")

    # Load repositories
    repos = fetch_repos(gh_user, gh_token)

    # Filter out repos from orgs that the user belongs to
    repos = [r for r in repos if r["owner"]["login"] == gh_user]

    # Filter out forks
    if not with_forks:
        repos = [r for r in repos if not r["fork"]]

    gogs = Gogs(gogs_url, gogs_user, gogs_token)

    if gogs_org:
        print("Mirror to organization {}".format(gogs_org))
        gogs_id = gogs.org_id(gogs_org)
    else:
        print("Mirror to user {}".format(gogs_user))
        gogs_id = gogs.user_id()

    # Set up the mirrors
    for repo in repos:
        response = gogs.mirror(gogs_id, repo)
        if response.status_code == 201:
            print("Mirror for {} set up".format(repo["name"]))
        elif response.status_code == 500:
            print("Repository {} already exists".format(repo["name"]))
        else:
            print("Unknown error {} for repo {}".format(
                response.status_code, repo["name"]))


if __name__ == "__main__":
    main()
