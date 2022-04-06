resource "digitalocean_droplet" "web-staging" {
  count  = 1
  image  = "ubuntu-20-04-x64"
  name   = "web-${count.index}"
  region = "fra1"
  size   = "s-1vcpu-1gb"

  ssh_keys = [
      data.digitalocean_ssh_key.terraform.id  # this assumes a digitalocean key having been set up
  ]
}

output "droplet_ip_addresses" {
  value = {
    for droplet in digitalocean_droplet.web-staging:
    droplet.name => droplet.ipv4_address
  }
}
