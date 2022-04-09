dev-app pipeline
================

This is a skeletal test/build/deploy pipeline for a containerized version of the Node demo app.

Aside from the default app itself, the following files were added to the skeleton:

* `ansiform/`: a directory containing basic provisioning logic for staging/production environments using Ansible and
  Terraform
* `ansiform/docker-install.yml`: ansible logic ensuring Docker Engine is installed on provisioned nodes
* `ansiform/droplets.tf`: Terraform-based node provisioning using DigitalOcean droplets
* `ansiform/provider.tf`: Terraform DigitalOcean provider setup
* `integration_tests.sh`: a stub representing whole-system tests that can be run before production deployment
* `dev-app/deploy`: Deployment logic for the dev app, using Ansible running locally
* `dev-app/docker-compose.yml`: Docker-compose configuration simplifying local development
* `dev-app/Dockerfile`: Docker image configuration for staging and production app deployments
* `dev-app/Jenkinsfile`: Pipeline definition, including build, test, and deploy
* `dev-app/Makefile`: Convenient wrappers for the various stage logics
