# Home Assistant bot

 It's yet another telegram bot implementation, this time as an integration with Home Assistant.
 At the moment only allows to expose and hide HA instance to the internet
 using the [ngrok](https://ngrok.com/) service.

Supposed to be running on the system in the same local network with HA instance.
Can be used as a generic exposing/hiding tool for any locally hosted service.
 
### Available commands
`/start` - command to start the bot

`/help` - show available commands

`/exposeha {0.5 <= float <= 1440}` - expose HA to the internet via ngrok.
Optionally takes float number of minutes to keep HA exposed. Uses the default 10 minutes timer if no argument passed.

`/hideha` - immediately hides the exposed HA instance

### Prerequisites
- python3
- Ngrok account
- Telegram account
- Home Assistant instance running on local/same machine (or any other service to be exposed)
- _sudo_ (for using as service on Linux-based system)

### Getting Started

#### Linux-based system (tested with RPi4)

0. Meet prerequisites
1. Clone this repository
2. Download and prepare ngrok executable ([getting started with ngrok](https://ngrok.com/download))
3. Create ngrok API-key ([what is ngrok API key]())
4. Create and activate virtual environment in the repository root folder `python3 -m venv venv && source venv/bin/activate`
5. Install dependencies `pip install -r requirements.txt`
6. Get Telegram bot token ([how do I create telegram bot]())
7. Copy the default config file: `cp secrets.default.ini secrets.ini`
8. Adjust the config file with your own values ([configuration file manual]())
9. Test if your setup works: `python3 main.py` (check [troubleshooting]() if not)
10. (Optional) Install script as a system service: `sudo python3 install_service.py` and follow script hints

### Configuration File

Coming soon... (probably)

### Troubleshooting

Coming soon... (probably)

### Known bugs and TODOs:

#### Bugs
- Initialization command returns error even if succeeded

#### TODOs
- More robust error handling
