# cloudshell-L1-Polatis

## Installation

Obtain these files:

    PolatisPython.exe
    polatis_python_runtime_configuration.json
    polatis_datamodel.xml

Important: After downloading, right-click PolatisPython.exe, open Properties, 
and ***unblock*** the EXE. Otherwise it will fail without an error message.

On the CloudShell machine, copy these files:

    PolatisPython.exe
    polatis_python_runtime_configuration.json

to

    c:\Program Files (x86)\QualiSystems\CloudShell\Server\Drivers


In Resource Manager, Admin, Resource Families, right-click the root of the tree, 'Import'

    polatis_datamodel.xml


Log files will be written in c:\Program Files (x86)\QualiSystems\CloudShell\Server\Logs\Polatis\

Note: On some systems, the base directory is

    c:\Program Files (x86)\QualiSystems\TestShell\Server
    
instead of

    c:\Program Files (x86)\QualiSystems\CloudShell\Server


## Usage

The driver supports two modes, logical and physical. Logical mode is more common.

### Logical mode
In logical mode, an Rx/Tx pair (e.g. 1, 257) will be represented in CloudShell 
as a single logical port (e.g. 1). When you model the Polatis connection to some device,
you make a single connection in Resource Manager between the Polatis logical port and the 
device port. This will be a single connection in CloudShell that represents two physical fibers.

If no custom Rx/Tx port number pairings are specified, the pairs are calculated automatically from 
the size of the switch. For example, on a 256x256 switch, logical port 2 represents port 2 for Rx, port 258 for Tx. To use these default mappings, you would use this config file:

    {
      "common_variable": {
        "connection_port": 3082
      },
      "driver_variable": {
        "port_mode_logical_or_physical": "logical"
      }
    }

If you have a different Rx/Tx mapping, you can explicitly specify it:

    {
      "common_variable": {
        "connection_port": 3082
      },
      "driver_variable": {
        "port_mode_logical_or_physical": "logical",
        "logical_port_pair_mapping": {
          1: 512,
          2: 511,
          3: 510,
          // ...
          255: 258,
          256: 257
        }
      }
    }

This example is for a 256x256 device.

Note that the same mapping will be used for all Polatis devices in CloudShell, regardless of size differences. 


### Physical mode
In physical mode, each fiber Rx connector and Tx connector is modeled as a separate CloudShell port resource. To represent the Polatis connection to some device,
you must model the Tx and Rx ports on the device as separate port resources, and you make two connections in Resource Manager between the
Polatis Rx and Tx ports and the device Tx and Rx ports. In physical mode, you must manually keep track of the association between Rx and Tx ports. For example, on a 256x256 device,
port 1 is Rx and the corresponding Tx is typically 1+256=257, but you can use any arbitrary pairings.


Config file for physical mode:

    {
      "common_variable": {
        "connection_port": 3082
      },
      "driver_variable": {
        "port_mode_logical_or_physical": "physical"
      }
    }


- Import polatis_datamodel.xml into Resource Manager
- Create L1 switch resource and set IP address, username, password
- In Configuration view in Resource Manager, push Auto Load
- Create multiple DUTs each with a port subresource
- In Connections view of the L1 switch resource, connect the DUT ports
- Create an empty reservation and add DUTs
- Create a route between two DUTs
- Connect the route
- See log files in c:\Program Files (x86)\QualiSystems\CloudShell\Server\Logs\\Polatis_*\


## Development

### Prerequisites
- Python 2.7 must be in %PATH%
- Pip must be in %PATH%


Download and extract the source bundle:
    https://github.com/QualiSystems/cloudshell-L1-polatis/archive/master.zip

Or if you have git:
    git clone https://github.com/QualiSystems/cloudshell-L1-Polatis.git


Run compile_driver.bat


## Notes

The only .py you should need to edit is polatis_l1_handler.py.

The address, username, and password of the switch resource become known to the driver only when 'login' is called. 

The port number is not stored on the resource. If it can't just be hard coded in the driver, take the setting from c:\Program Files (x86)\QualiSystems\CloudShell\Server\Drivers\\polatis_python_runtime_configuration.json.

### JSON config
The sample code includes hard-coding of default values for the JSON settings.

CLI prompts on some switches can be completely arbitrary. A JSON setting is included for customizing the prompt regex. This is to avoid having to recompile the driver in the event that the customer switch has been given a bizarre prompt. If you don't have such prompt issues, you can delete all code related to this setting.

polatis_python_runtime_configuration.json is not mandatory. If your driver doesn't need any runtime settings, you can delete all the code in polatis_l1_handler.py that deals with the JSON.

### Driver implementation tips

Even if your driver makes REST calls and doesn't maintain a persistent connection, you still need to implement 'login' to store the address, username, and password for later use by the mapping functions. 'login' will always be called at least once before mapping functions are called.    

#### SSH

For an SSH device, it is convenient to use Paramiko.

    import paramiko
    # ...
        def receive(self):
            # read until the prompt regex is found
            prompt_regex = '>'
            rv = ''
            while True:
                self.channel.settimeout(30)
                r = self.channel.recv(2048)
                if r:
                    rv += r
                t = re.sub(r'\x1b\[\d+m', '', rv)
                if not r or len(re.findall(prompt_regex, t)) > 0:
                    return t

        def do_command(self, command):
            self.channel.send(command + '\n')
            return self.receive()
            
        def login(self, address, username, password)
            self.ssh = paramiko.SSHClient()
            # must store the SSHClient in a non-local variable to avoid garbage collection
            self.ssh.load_system_host_keys()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(address,
                        port=22,
                        username=username,
                        password=password,
                        look_for_keys=True)
            self.channel = self.ssh.invoke_shell()
            self.receive() # eat banner
         

Communication with your device may have unique timing requirements.

You might have to handle SSH connections being automatically closed by the remote host.

CloudShell may call login() automatically, but it may not be often enough to refresh the connection with some devices that disconnect frequently.    

To log in with an RSA key file (id_rsa), pass look_for_keys=True to the SSH connect() as shown above. Paramiko will search for ~/.ssh/id_rsa. The driver runs in the system account, so the key file should be at C:\Windows\System32\Config\systemprofile\\.ssh\id_rsa. Continue to specify the username and password on the resource. The password will be used to decrypt the id_rsa file, and along with the username this key will be used to log in. This feature has never been tested with a blank password, so create the id_rsa with a password to be safe.    

If you connect to a color terminal, the returned data may be polluted with control sequences in the form ESC[123m (regex: r'\x1b\\[\d+m'). This could interfere with your detection of the prompt regex. Buffer all the received data and look for the prompt regex in a separate copy of the data with the control sequences deleted.


