terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

# this assumes that these keys would be filled in with real values
variable "do_token" {}
variable "pvt_key" {}
variable "pub_key" {}

provider "digitalocean" {
  token = var.do_token
}

data "digitalocean_ssh_key" "terraform" {
  name = "terraform"
}
