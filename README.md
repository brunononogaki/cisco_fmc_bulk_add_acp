# Cisco FMC Bulk Add Access Policies (ACPs)

This is an automation to bulk add Access Policies in a FMC, reading from a CSV file.
Before running in a production environment, please test with few items, as you can face a case not covered by this automation.
If you have any doubt or find any bug, please contact me at bruno.nonogaki@global.ntt

<br><br>
#### Structure

```bash
.
├── Makefile
├── README.md
├── acp.csv
├── ext
│   ├── config
│   │   └── fmc_info.json
│   └── service
│       ├── FMC.py
│       ├── acps.py
│       ├── connection.py
│       ├── domains.py
│       ├── fqdns.py
│       ├── hosts.py
│       ├── networks.py
│       ├── objects.py
│       ├── ports.py
│       └── security_zones.py
├── main.py
└── requirements.txt
```

<br><br>
#### Preparing the environment

- Install Python3 (tested on Python 3.10)

- Create a Virtual Environment
```bash
python -m venv "venv"
source venv/bin/activate
```

- Install the dependencies

```bash
$ pip install -r requirements.txt
```

<br><br>
#### Configuration

Create a fmc_info.json file with FMC's IP and credential and place it insude /ext/config folder
```
{
  "fmc_ip" : "X.X.X.X",
  "fmc_user" : "xxxxx",
  "fmc_passwd" : "XXXXXXX"
}
```
If you don't create it, the application you ask for these information and will create the file for you.


<br><br>
#### Input File

Please create a CSV file called acp.csv and place it in the root directory (same directory as main.py). In this file you must add the following information:
- ACP Policy
- Policy Name
- Category
- Action (Allow/Block)
- Source Interface
- Destination Interface
- Source Network
- Destination Network
- Source Ports
- Destination Ports

The remaining fields in ACP are kept as default!

This file must have the following structure:
```
#ACP Policy,Name,Category,Action,Source Interface,Destination Interface,Source Network,Destination Network,Source Ports,Destination Ports
First_ACP,Rule Test 1,Teste,Allow,inside_zone,outside_zone,10.236.132.0/24;10.236.131.0/24,10.236.139.252;10.236.139.251,443/TCP;443/TCP;2002/TCP,443/TCP;443/TCP;2002/TCP
First_ACP,Rule Test 2,Teste,Block,inside_zone,outside_zone,,,,
```

Note that:
- The automation will ignore any line starting with #, such as the header
- The CSV must be splitted with , and not ;
- In case of multiple ports, split them with a ; - For example: 443/TCP;5060/TCP
- In case of multiple hosts or networks, split them with a ; - For example: 192.168.10.0/24;192.168.20.0/24
- Network address must be in the format X.X.X.X/XX
- In case of a source or destination network is a FQDN, type the FQDN without the leading . (dot). For example: global.ntt and NOT .global.ntt
- In case of a source or destination network is a group, type the name of the group. This name can not contain a . (dot).
- Add the Ports in the following format: <PORTNUMBER>/<PROTOCOL>, example: 5060/TCP
- In case of a network or port is ANY, leave the field blank in the CSV file
- In case the category does not exist, the application will create it
- In case the port is a Port Group, make sure you create this port group prior to add the ACPs. The application will not create the port group automatically.


<br><br>
#### Execution

```bash
$ python main.py
```

The application will start creating the ACPs one by one. Note that:
- If the IP Address/FQDN of the Source or Destination does not exist as an object in FMC, the automation will create that!
- If the Port of the Source or Destination does not exist as an object in FMC, the automation will create that!
- If the Source or Destination is a Group, you MUST create this group manually before running the automation. It will not create for you!
- You must add valid Source Interface and Destination Interface. The automation will not create for you!
- If the ACP Policy does not exist, the application will create it
- If the Category does not exist, the application will create it