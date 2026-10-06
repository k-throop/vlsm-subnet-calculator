# VLSM Subnet Calculator

A Python command line tool that takes a parent IPv4 network and a list of subnet names with host requirement counts, validates the input, and prints an addressing plan.

## Features

- Takes a parent network in CIDR notation and any number of name / host requirement count pairs
- Rounds each request up to the smallest subnet that fits (hosts + network and broadcast addresses)
- Reports an error if a requested subnet size does not fit inside the parent network 
- Allocates subnets largest-first and reports network, mask, and usable range
- Rejects invalid input with clear error messages
- Tested with pytest

## Requirements

- Python 3.9+
- pytest (for running tests only)

## Installation

```bash
git clone https://github.com/k-throop/vlsm-subnet-calculator.git
cd vlsm-subnet-calculator
python -m pip install -r requirements.txt
```

## Usage

```bash
python vlsm.py <network/prefix> <name> <hosts> [<name> <hosts> ...]
```

Example:

```bash
python vlsm.py 192.0.2.0/24 HR 7 Sales 67 IT 3
```

Output:

```
Name            Network           Prefix  Mask              Broadcast         Usable Hosts   Host Range                            
------------------------------------------------------------------------------------------------------------------------------
Sales           192.0.2.0         /25     255.255.255.128   192.0.2.127                126   192.0.2.1 - 192.0.2.126               
HR              192.0.2.128       /28     255.255.255.240   192.0.2.143                 14   192.0.2.129 - 192.0.2.142             
IT              192.0.2.144       /29     255.255.255.248   192.0.2.151                  6   192.0.2.145 - 192.0.2.150

```

## How It Works
1. Each subnet needs the requested number of addresses, plus 2 for network and broadcast, rounded up to a power of 2. For example, 7 hosts need 9 addresses, which is rounded up to 16 addresses to get /28. 
2. Subnets are allocated one after another from largest to smallest, beginning at the start of the parent network.  
3. If a subnet request will not fit inside the parent network, the tool stops with an error instead of printing a partial plan.

## Input Rules

| Argument | Rule |
|---|---|
| `network` | IPv4 address with CIDR prefix, e.g. `192.0.2.0/24`. Host bits must be zero. |
| `name` | Any string |
| `host requirements` | Integer |

`name` and `host requirements` must be given together as pairs, so after the network there is always an even number of values.

Invalid input prints a descriptive error message and exits with code 2.

## Running Tests

```bash
python -m pytest -v
```

The tests cover:

- Input validation: missing prefix, host bits set, out-of-range prefix, odd number of values, non-integer host requirements, missing arguments, and non-IPv4 network
- Allocation logic: a hand-calculated known subnet plan, largest-first ordering, subnet size boundaries, no overlapping subnets, exact fit, and requests that do not fit

## Known Limitations

- IPv4 only
- A request for 2 hosts gets a /30, not a /31. /32 also not supported.
