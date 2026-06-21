🕵️ Dark Web Tor Crawler

A production‑ready Python scraper for .onion sites, routing all traffic through the Tor anonymity network.
Built for authorised security research, threat intelligence gathering, and OSINT investigations.

---

⚠️ LEGAL & ETHICAL DISCLAIMER

READ THIS BEFORE USING THE TOOL

· This software is intended SOLELY for legitimate security research, penetration testing with explicit written authorisation, and threat intelligence analysis.
· Crawling .onion sites without permission may violate local, national, and international laws, including but not limited to computer misuse and data protection legislation.
· You are fully responsible for how you use this tool. The author assumes zero liability for any illegal or unethical activities conducted with it.
· Some .onion services host illegal material. Do not interact with or access such content.
· Always consult with your legal counsel before deploying this tool in any environment.

---

✨ Features

· 🔒 Full Tor integration – All HTTP/HTTPS traffic is routed through the Tor SOCKS5 proxy.
· 🔄 Automatic IP renewal – Requests a new exit node at a configurable interval (stem).
· 🧠 Intelligent retries – Exponential backoff with retry logic for transient network failures.
· 🔗 Recursive crawling – Follows .onion links up to a user‑defined depth.
· 📄 Structured output – Extracts titles, text previews, and all hyperlinks.
· 🖥️ Command‑line friendly – Full parameter control (depth, max pages, output file).
· 🛡️ Polite scraping – Configurable delays to avoid overwhelming target servers.

---

📋 Prerequisites

Requirement Notes
Python 3.7+ Tested on 3.8–3.12
Tor daemon Running locally with ControlPort and SOCKS enabled
Network access Must be able to reach the Tor network (no outbound firewall blocks on port 9050)

---

🔧 Installation

1. Install and configure Tor

```bash
# Debian/Ubuntu
sudo apt update && sudo apt install tor -y

# Edit the configuration
sudo nano /etc/tor/torrc
```

Ensure the following lines are uncommented or added:

```
SocksPort 9050
ControlPort 9051
CookieAuthentication 1
```

Then start the service:

```bash
sudo systemctl start tor
sudo systemctl enable tor   # optional, to start on boot
```

For macOS/Windows, download the Tor Expert Bundle from the Tor Project and run tor.exe or tor from the command line.

---

2. Clone or download the script

Save the script as dark_crawler.py in your project directory.

---

3. Install Python dependencies

Create a requirements.txt with:

```
requests>=2.28.0
beautifulsoup4>=4.11.0
stem>=1.8.0
urllib3>=1.26.0
```

Then install:

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install requests beautifulsoup4 stem urllib3
```

---

🚀 Usage

Basic command

```bash
python dark_crawler.py http://your-target.onion
```

Full example with options

```bash
python dark_crawler.py http://protonmailrmez3lotccipshtkleegetolb73fuirgp7rfuxlyz3qs.onion/ \
    --depth 2 \
    --pages 15 \
    --renew 3 \
    --output results.txt
```

Command‑line arguments

Arg Short Default Description
url (positional) Required Starting .onion URL to crawl
--depth -d 1 Maximum link depth to follow (0 = no recursion)
--pages -p 20 Maximum total pages to fetch (prevents infinite loops)
--renew -r 5 Renew Tor exit node every N pages fetched
--output -o None Save structured results to a text file

---

📦 Output Example

When you run the crawler, you'll see real‑time logs in the terminal:

```
2026-06-21 10:15:23 - INFO - Tor is active – IP: 185.220.101.23
2026-06-21 10:15:25 - INFO - Starting crawl: http://example.onion/ (depth=2, max_pages=10)
2026-06-21 10:15:27 - INFO - Fetching: http://example.onion/
2026-06-21 10:15:30 - INFO - Page 1: Welcome to Example – http://example.onion/
2026-06-21 10:15:35 - INFO - Fetching: http://example.onion/about
...
============================================================
Crawled 8 pages:
  http://example.onion/ – Welcome
    Links: 12 found
  http://example.onion/about – About Us
    Links: 3 found
============================================================
```

If --output results.txt is used, the file will contain structured data:

```
URL: http://example.onion/
Title: Welcome
Links: http://example.onion/about, http://example.onion/contact
Preview: This is the homepage text truncated to 500 characters...
------------------------------------------------------------
URL: http://example.onion/about
Title: About Us
Links: http://example.onion/team
Preview: We are a team of security researchers...
------------------------------------------------------------
```

---

⚙️ Configuration (Inside the Script)

You can tweak the following constants at the top of dark_crawler.py without touching the core logic:

Variable Default Description
TOR_SOCKS 'socks5h://127.0.0.1:9050' SOCKS proxy address (change if Tor runs elsewhere)
TOR_CONTROL_PORT 9051 Control port for stem to send NEWNYM signals
USER_AGENT 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...' Spoofed browser identity
MAX_RETRIES 3 Number of retry attempts on failed requests
BACKOFF_FACTOR 2 Exponential backoff multiplier (1s, 2s, 4s…)
TIMEOUT 30 Request timeout in seconds
LOG_LEVEL logging.INFO Change to DEBUG for verbose troubleshooting

---

🧠 How It Works

1. Session initialisation – Creates a requests.Session with SOCKS5 proxying to Tor.
2. IP rotation – Uses stem to connect to Tor's control port and send a NEWNYM signal, requesting a fresh exit circuit.
3. Fetch & parse – Retrieves the HTML, parses it with BeautifulSoup, and extracts:
   · Page title
   · All .onion anchor links (normalised to absolute URLs)
   · A plain‑text preview (first 500 characters)
4. Recursive queue – New links are added to a FIFO queue, respecting the --depth limit.
5. Polite delay – Sleeps for 1 second between requests to reduce load on hidden services.
6. Output – Prints a summary to stdout and optionally writes detailed results to a file.

---

🛠️ Troubleshooting

Issue Likely Cause Solution
Tor is not available Tor daemon isn't running Run sudo systemctl start tor or check your OS services
Authentication failed CookieAuthentication not set in torrc Uncomment CookieAuthentication 1 in /etc/tor/torrc and restart Tor
Connection timed out .onion site is down or extremely slow Increase TIMEOUT; some hidden services take >60s to respond
403 Forbidden Target site blocks your user agent or requests pattern Change USER_AGENT or increase renew_interval to rotate IPs more often
ControlPort 9051 is not available Port conflict or Tor not compiled with control support Verify your torrc configuration and restart Tor
Only static HTML is parsed Site uses JavaScript to render content This scraper does not execute JS. For dynamic sites, consider adding selenium or playwright (but this requires extra libraries beyond the Python‑only scope)

---

📁 Project Structure

```
.
├── dark_crawler.py    # Main executable script
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

---

🤝 Contributing

Contributions that improve reliability, add new parsers, or enhance the output format are welcome.

Guidelines:

· Keep the tool pure Python (no external browsers, minimal system dependencies).
· Maintain strict adherence to the ethical use principle.
· Document any new features thoroughly.

---

📄 License

MIT License – you are free to use, modify, and distribute this software for any purpose, provided the original copyright notice and this permission notice are included. However, the license does not grant immunity from legal prosecution – you remain fully responsible for your actions when using this tool.

---

🙏 Acknowledgements

· Tor Project – for the anonymity network.
· stem library – for seamless Tor controller integration.
· requests & BeautifulSoup – for making HTTP and HTML parsing a breeze.

---

If you find this tool useful for your security research, please ⭐ star the repository and use it responsibly.
