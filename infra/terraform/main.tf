
provider "libvirt" {
  uri = "qemu:///system"
}
resource "libvirt_volume" "os_image" {
  name = "ubuntu-22.04.qcow2"
  pool = "default"
  source = "https://cloud-images.ubuntu.com/releases/22.04/release/ubuntu-22.04-server-cloudimg-amd64.img"
}
resource "libvirt_domain" "k8s_master" {
  name   = "k8s-master-01"
  memory = "8192"
  vcpu   = 4
  disk { volume_id = libvirt_volume.os_image.id }
  network_interface {
    network_name = "default"
    addresses    = ["192.168.122.10"]
  }
}
