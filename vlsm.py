import math
import ipaddress 
import argparse
import sys

## Returns the smallest prefix length that has enough usable addresses for the number of hosts required
def prefix(required_hosts):
	if (required_hosts <= 0):
		raise ValueError(f"Host requirement {required_hosts} is too small")
	# Need space for a network and broadcast 
	total_num_addr = required_hosts + 2  

	# Calculate how many host bits to use
	host_bit = math.ceil(math.log2(total_num_addr))

	return 32 - host_bit

## Assigns a network to each subnet
def assign_subnets(network, subnets):
	# Points to next available address
	next_addr = network.network_address
        
	# Assign a network to each subnet
	for subnet in subnets:
		subnet_prefix = prefix(subnet["hosts_required"])	

		# Raise exception if the subnet requires more hosts than the parent network has 		
		if(subnet_prefix < network.prefixlen): 
			raise ValueError(f"Not enough address space for {subnet['name']} with {subnet['hosts_required']} hosts")              

		subnet["network"] = ipaddress.ip_network(f"{next_addr}/{subnet_prefix}")
		
		# Raise exception if the remaining space in the parent network isn't enough for subnet host requirements
		if not subnet["network"].subnet_of(network):
			raise ValueError(f"Not enough address space remaining for {subnet['name']} with {subnet['hosts_required']} hosts")
				
		next_addr = subnet["network"].broadcast_address + 1

## Subnet info prints as a table
def print_subnet_table(subnets):
	print()
	print(
		f"{'Name':<16}"
		f"{'Network':<18}"
		f"{'Prefix':<8}"
		f"{'Mask':<18}"
		f"{'Broadcast':<18}"
		f"{'Usable Hosts':<15}"
		f"{'Host Range':<38}"
	) 

	print("-" * 126)

	for subnet in subnets:
		network = subnet["network"]
		first_host = network.network_address + 1
		last_host = network.broadcast_address - 1
		usable_hosts = int(last_host) - int(first_host) + 1
		usable_range = f"{first_host} - {last_host}"	

		print(
			f"{subnet['name']:<16}"
			f"{str(network.network_address):<18}"
			f"/{str(network.prefixlen):<7}"
			f"{str(network.netmask):<18}"
			f"{str(network.broadcast_address):<18}"
			f"{usable_hosts:>12}   "
			f"{usable_range:<38}"
		)

	print("")

## Parse argument and validate input
def parse_args():
	parser = argparse.ArgumentParser(description="VLSM subnet calculator")
	parser.add_argument("network", help="Parent network (e.g. 203.0.113.0/24)")
	parser.add_argument("subnets", nargs="+", help="Subnet name and host requirements, given in pairs (e.g. HR 14 Sales 61)")
	args = parser.parse_args()

	if "/" not in args.network:
		parser.error(f"First argument must be a network with a prefix, got {args.network}")
	try: 
		args.network = ipaddress.IPv4Network(args.network, strict=True)
	except:
		parser.error(f"Invalid IPv4 network, got {args.network}")
	if len(args.subnets) < 2:
		parser.error("At least 1 subnet name/host requirement pair is required")
	if len(args.subnets) % 2 != 0:
		parser.error("Subnet name/host requirements must be given in pairs")
	try: 
		for i in range(1,len(args.subnets),2):
			int(args.subnets[i])
	except ValueError:
			parser.error(f"Host requirement must be a positive integer, got {args.subnets[i]}") 
	return args

def main():
	args = parse_args()
	# Create a list of subnets sorted from largest host requirement to smallest
	subnets = []
	for i in range(0, len(args.subnets), 2):
		subnet = {
			"name":args.subnets[i],
			"hosts_required":int(args.subnets[i+1]),
			"network":None,
		}
		subnets.append(subnet)
        	
	subnets.sort(key=lambda x: x["hosts_required"], reverse=True)

	# Create parent network
	network = ipaddress.ip_network(args.network)	

	# Create subnets
	try:
		assign_subnets(network, subnets)
	except ValueError as e:
		print(f"Error: {e}")
		sys.exit(1)
		
	# Print all subnet info 
	print_subnet_table(subnets)

if __name__ == "__main__":
	main()
