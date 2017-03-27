#!/usr/bin/env python3

import argparse
import requests
import json
import os
import base64
from collections import namedtuple
import docker

Registry = namedtuple('Registry', ['name', 'tag_url', 'tag_func'])
REGISTRY_REGISTRY = {
    'hub.docker.com': Registry(
        name='hub.docker.com',
        tag_url='https://registry.hub.docker.com/v1/repositories/library/mongo/tags',
        tag_func=lambda x: [i['name'] for i in x],
    ),
    'quay.io': Registry(
        name='quay.io',
        tag_url='https://quay.io/v1/repositories/{organization}/{repository}/tags',
        tag_func=lambda x: list(x.keys()),
    ),
    'gcr.io': Registry(
        name='gcr.io',
        tag_url='https://gcr.io/v2/{organization}/{repository}/tags/list',
        tag_func=lambda x: x['tags'],
    ),
}


def get_config_auth(registry, config):
    with open(config) as config:
        config = json.load(config)
        if registry in config['auths']:
            auth = config['auths'][registry]['auth']
            username,password = base64.b64decode(auth).decode('utf-8').split(':')
            return requests.auth.HTTPBasicAuth(username, password)
    return None


def get_tags(image, config):
    parts = image.split('/')
    if len(parts) == 3:
        registry, organization, repository = parts
    elif len(parts) == 2:
        registry = 'hub.docker.com'
        organization, repository = parts
    elif len(parts) == 1:
        registry = 'hub.docker.com'
        organization = 'library'
        repository = parts
    else:
        raise Exception('image issues')

    registry = REGISTRY_REGISTRY[registry]
    url = registry.tag_url.format(organization=organization, repository=repository)
    response = requests.get(url, auth=get_config_auth(registry.name, config))
    if response.status_code == 200:
        return registry.tag_func(response.json())
    else:
        raise Exception('registry issues')


def list_tags(args, tags):
    for tag in tags:
        print(tag)

def pull_tags(args, tags):
    client = docker.from_env()
    for tag in tags:
        print("Pulling image {}:{}".format(args.source, tag))
        client.images.pull(args.source, tag=tag)

def sync_tags(args, tags):
    client = docker.from_env()
    for tag in tags:
        print("Pulling image {}:{}".format(args.source, tag))
        image = client.images.pull(args.source, tag=tag)
        image.tag(args.destination, tag=tag)
        print("Pushing image {}:{}".format(args.destination, tag))
        client.images.push(args.destination, tag=tag)

parser = argparse.ArgumentParser(description='Pull all tags of a docker image and push to another repository')
parser.add_argument('--config', default='~/.docker/config.json', help='the docker configuration file used for login')
subparsers = parser.add_subparsers()
list_parser = subparsers.add_parser('list', help='list tags in source repository')
list_parser.set_defaults(func=list_tags)
pull_parser = subparsers.add_parser('pull', help='pull all tags from source registry')
pull_parser.set_defaults(func=pull_tags)
sync_parser = subparsers.add_parser('sync', aliases=['push'], help='syncrhonize tags from source registry to destionation')
sync_parser.add_argument('destination', help='the destination repository')
sync_parser.set_defaults(func=sync_tags)
parser.add_argument('source', help='the source repository')

args = parser.parse_args()
tags = get_tags(args.source, os.path.expanduser(args.config))
args.func(args, tags)
