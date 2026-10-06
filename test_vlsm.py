import pytest
import sys
import ipaddress
from vlsm import parse_args, assign_subnets

## helpers
def run(monkeypatch, *argv):
	monkeypatch.setattr(sys, "argv", ["vlsm.py", *argv])
	return parse_args()

def run_error(monkeypatch, capsys, *argv):
	monkeypatch.setattr(sys, "argv", ["vlsm.py", *argv])
	with pytest.raises(SystemExit) as exc:
		parse_args()
	assert exc.value.code == 2
	return capsys.readouterr().err

PARENT = ipaddress.IPv4Network("192.0.2.0/24")

##########  subnet assignment logic ##########

## testing against known subnet plan

def test_known_subnets_single():
	subnets = [{"name": "a", "hosts_required": 7, "network": None}]
	assign_subnets(PARENT, subnets)
	assert subnets[0]["network"] == ipaddress.IPv4Network("192.0.2.0/28")

def test_known_subnets_largest_first_input_order_unsorted():
	subnets = [{"name": "small", "hosts_required": 17, "network": None}, 
	           {"name": "big", "hosts_required": 67, "network": None}]
	assign_subnets(PARENT, subnets)
	assert subnets[0]["network"] == ipaddress.IPv4Network("192.0.2.0/25")

def test_known_subnets_multiple():
	subnets = [{"name": "a", "hosts_required": 7, "network": None}, 
	           {"name": "b", "hosts_required": 67, "network": None}, 
			   {"name": "c", "hosts_required": 3, "network": None}]
	assign_subnets(PARENT, subnets)
	assert subnets[0]["network"] == ipaddress.IPv4Network("192.0.2.0/25")
	assert subnets[1]["network"] == ipaddress.IPv4Network("192.0.2.128/28")
	assert subnets[2]["network"] == ipaddress.IPv4Network("192.0.2.144/29")

## testing subnet size boundaries and overlap 

def test_fills_parent_exactly():
	subnets = [{"name": "a", "hosts_required": 126, "network": None}, 
	           {"name": "b", "hosts_required": 126, "network": None}]
	assign_subnets(PARENT, subnets)
	assert subnets[0]["network"] == ipaddress.IPv4Network("192.0.2.0/25")
	assert subnets[1]["network"] == ipaddress.IPv4Network("192.0.2.128/25")

def test_overflows_parent_by_one_error():
	subnets = [{"name": "a", "hosts_required": 126, "network": None}, 
	           {"name": "b", "hosts_required": 126, "network": None},
			   {"name": "c", "hosts_required": 1, "network": None}]
	with pytest.raises(ValueError):
		assign_subnets(PARENT, subnets)

def test_ran_out_of_address_space_error():
	subnets = [{"name": "a", "hosts_required": 128, "network": None}, 
	           {"name": "b", "hosts_required": 999, "network": None}]
	with pytest.raises(ValueError):
		assign_subnets(PARENT, subnets)

def test_no_overlaps_and_all_subnet_of_parent(): 
	subnets = [{"name": "a", "hosts_required": 7, "network": None}, 
	           {"name": "b", "hosts_required": 67, "network": None}, 
			   {"name": "c", "hosts_required": 3, "network": None},
			   {"name": "d", "hosts_required": 30, "network": None}]
	assign_subnets(PARENT, subnets)

	for subnet in subnets:
			assert subnet["network"].subnet_of(PARENT)

	for i in range(len(subnets)-1):
		assert subnets[i]["network"].broadcast_address < subnets[i+1]["network"].network_address

########## input validation ##########

## testing valid inputs

def test_valid_ipv4_network(monkeypatch):
	args = run(monkeypatch, "192.0.2.0/24", "a", "28", "b", "57")
	assert args.network == ipaddress.IPv4Network("192.0.2.0/24")

def test_valid_one_subnet_pair(monkeypatch):
	args = run(monkeypatch, "192.0.2.0/24", "a", "28")
	assert args.subnets == ["a", "28"]

def test_valid_two_subnet_pairs(monkeypatch):
	args = run(monkeypatch, "192.0.2.0/24", "a", "28", "b", "57")
	assert args.subnets == ["a", "28", "b", "57"]

## testing invalid network input

def test_network_missing_prefix(monkeypatch, capsys):
	err = run_error(monkeypatch, capsys, "192.0.2.0", "a", "28")
	assert "prefix" in err

@pytest.mark.parametrize("invalid", [
	"192.0.2", # missing octet
	"192.0.2.0/33", # prefix too long
	"192.0.2.3", # host bits set
	"192.0.2.256", # octet out of range
	"string/16", # not an IP address
	"192.0.2.0/", # missing number in prefix
	"subnet", # network omitted
])

def test_invalid_networks_raise_error(monkeypatch, capsys, invalid):
	err = run_error(monkeypatch, capsys, invalid, "a", "28")
	assert "network" in err

## testing invalid subnet pairs (name and host requirements)

def test_missing_value_in_subnet_pair_error(monkeypatch, capsys):
	err = run_error(monkeypatch, capsys, "192.0.2.0/24", "a", "28", "b")
	assert "name/host" in err

@pytest.mark.parametrize("invalid_hosts", [
	"string",
	"28.5",
	"-1",
	"0",
])

def test_host_requirement_non_integer_error(monkeypatch, capsys, invalid_hosts):
	err = run_error(monkeypatch, capsys, "192.0.2.0/24", "a", invalid_hosts)
	assert "integer" in err

## testing missing arguments 

def test_no_argument_error(monkeypatch, capsys):
	err = run_error(monkeypatch, capsys)
	assert "arguments" in err

def test_no_subnet_pairs_error(monkeypatch, capsys):
	err = run_error(monkeypatch, capsys)
	assert "arguments" in err