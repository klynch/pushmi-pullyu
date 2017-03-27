Pushmi-Pullyu
=============

This is a quick script to pull repositories from a remote Docker registry and push them to a different registry. This
works by reading the Docker authentication configuration file and making an API call to the source registry to gather
the list of tags. Once this occurs, it connects to the local Docker daemon and pulls, retags, and pushes each image it
encounters.

If authentication is required, you will need to login to the source and destination registries using the `docker login`
command.

Supported Registries include:
* gcr.io
* quay.io
* hub.docker.com
