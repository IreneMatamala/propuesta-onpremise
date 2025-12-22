variable "vsphere_user" {}
variable "vsphere_password" {
  sensitive = true
}
variable "vsphere_server" {}

variable "datacenter" {}
variable "cluster" {}
variable "datastore" {}
variable "network_name" {}

variable "vm_template" {
  description = "Template Linux hardened"
}

variable "vm_count" {
  default = 2
}

variable "vm_cpu" {
  default = 4
}

variable "vm_memory" {
  default = 8192
}

