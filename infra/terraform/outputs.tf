output "vm_ips" {
  value = vsphere_virtual_machine.k8s_node[*].default_ip_address
}

