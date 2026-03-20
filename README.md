# APRSD REPEAT Service Plugins

[![PyPI](https://img.shields.io/pypi/v/aprsd-repeat-plugins.svg)](https://pypi.org/project/aprsd-repeat-plugins/)
[![Status](https://img.shields.io/pypi/status/aprsd-repeat-plugins.svg)](https://pypi.org/project/aprsd-repeat-plugins/)
[![Python Version](https://img.shields.io/pypi/pyversions/aprsd-repeat-plugins)](https://pypi.org/project/aprsd-repeat-plugins)
[![License](https://img.shields.io/pypi/l/aprsd-repeat-plugins)](https://opensource.org/licenses/MIT)

APRSD plugins for finding the nearest repeaters to your last APRS beacon location using the REPEAT service.

## Features

- **NearestPlugin**: Find the nearest repeaters to your last APRS beacon location
- **NearestObjectPlugin**: Return nearest repeaters as APRS object notation
- **VersionPlugin**: Display plugin version information
- Support for multiple frequency bands (2m, 70cm, 6m, etc.)
- Filtering by repeater features (EchoLink, IRLP, DMR, D-STAR, etc.)
- Distance calculations in miles (US/UK) or kilometers (elsewhere)
- Integration with aprs.fi for location lookup
- Integration with haminfo REST API for repeater database

## Requirements

- Python 3.11+
- APRSD 3.0.0 or higher
- aprs.fi API key
- haminfo REST API access (API key and base URL)

## Installation

You can install APRSD REPEAT Service Plugins via pip from PyPI:

```bash
pip install aprsd-repeat-plugins
```

Or install from source:

```bash
git clone https://github.com/hemna/aprsd-repeat-plugins.git
cd aprsd-repeat-plugins
pip install -e .
```

## Configuration

### 1. Enable the Plugins

Add the plugins to your APRSD configuration file (typically `aprsd.yml` or `aprsd.yaml`):

```yaml
aprsd:
  enabled_plugins:
    - aprsd_repeat_plugins.nearest.NearestPlugin
    - aprsd_repeat_plugins.nearest.NearestObjectPlugin
    # Optional: Enable version plugin
    # - aprsd_repeat_plugins.version.VersionPlugin
```

### 2. Configure API Keys

Add the required API keys and service URLs to your configuration:

```yaml
services:
  aprs.fi:
    apiKey: YOUR_APRS_FI_API_KEY

aprsd_repeat_plugins:
  haminfo_apiKey: YOUR_HAMINFO_API_KEY
  haminfo_base_url: http://your-haminfo-server:8081
```

### 3. Export Configuration Options

To see all available configuration options, use the CLI tool:

```bash
aprsd-repeat-plugins-export-config --format json
```

This will output all configuration options with their types, defaults, and descriptions.

### Complete Configuration Example

Here's a complete example configuration section:

```yaml
aprsd:
  enabled_plugins:
    - aprsd.plugins.ping.PingPlugin
    - aprsd_repeat_plugins.nearest.NearestPlugin
    - aprsd_repeat_plugins.nearest.NearestObjectPlugin
  units: imperial

services:
  aprs.fi:
    apiKey: 152327.lds79D1bgvlbd

aprsd_repeat_plugins:
  haminfo_apiKey: dm0KBljSS90Pn7-Rux29wfeSLF9P30Pe0JkWcYS_5RM
  haminfo_base_url: http://192.168.1.22:8081
```

## Usage

### NearestPlugin

The `NearestPlugin` finds the nearest repeaters to your last APRS beacon location.

#### Command Syntax

```
n[earest] [count] [band] [+filter]
```

- `count`: Number of stations to return (default: 1, max: 10)
- `band`: Frequency band (e.g., `2m`, `70cm`, `6m`, `1.25m`, `33cm`, `23cm`, `13cm`, `9cm`, `5cm`, `3cm`)
- `filter`: Optional feature filter (e.g., `+echo`, `+irlp`, `+dmr`, `+dstar`)

#### Example Interactions

**Basic usage - find nearest repeater:**
```
You: n
APRSD: W6ABC 146.940 -.6 T88.5 2.3mi NE
```

**Find 3 nearest repeaters:**
```
You: n 3
APRSD: W6ABC 146.940 -.6 T88.5 2.3mi NE
      W6XYZ 147.330 +.6 T100.0 5.1mi SW
      W6DEF 145.230 -.6 T103.5 8.7mi N
```

**Find nearest 70cm repeater:**
```
You: n 70cm
APRSD: W6ABC 446.000 -5 T88.5 1.2mi SE
```

**Find nearest EchoLink-enabled repeater:**
```
You: n +echo
APRSD: W6ABC 146.940 -.6 T88.5 3.4mi NE
```

**Find 5 nearest 2m DMR repeaters:**
```
You: n 5 2m +dmr
APRSD: W6ABC 146.940 -.6 T88.5 2.3mi NE
      W6XYZ 147.330 +.6 T100.0 5.1mi SW
      W6DEF 145.230 -.6 T103.5 8.7mi N
      W6GHI 147.450 +.6 T103.5 12.4mi E
      W6JKL 146.640 -.6 T88.5 15.8mi W
```

#### Offset Examples

The offset field shows the actual frequency offset in MHz, which is especially useful for
non-standard repeater configurations:

| Band | Offset | Description |
|------|--------|-------------|
| 2m | `-.6` | Standard negative 600 kHz offset |
| 2m | `+.6` | Standard positive 600 kHz offset |
| 2m | `-2.5` | Non-standard 2.5 MHz offset (some regions) |
| 70cm | `-5` | Standard negative 5 MHz offset |
| 70cm | `+5` | Standard positive 5 MHz offset |
| 70cm | `-7.6` | Non-standard 7.6 MHz offset (common in some areas) |
| Any | `0` | Simplex (no offset) |

#### Supported Frequency Bands

- `160m` - 160 Meters (1.8-2.0 MHz)
- `80m` - 80 Meters (3.5-4.0 MHz)
- `60m` - 60 Meters (5 MHz channels)
- `40m` - 40 Meters (7.0-7.3 MHz)
- `30m` - 30 Meters (10.1-10.15 MHz)
- `20m` - 20 Meters (14.0-14.35 MHz)
- `17m` - 17 Meters (18.068-18.168 MHz)
- `15m` - 15 Meters (21.0-21.45 MHz)
- `12m` - 12 Meters (24.89-24.99 MHz)
- `10m` - 10 Meters (28-29.7 MHz)
- `6m` - 6 Meters (50-54 MHz)
- `2m` - 2 Meters (144-148 MHz) - **Default**
- `1.25m` - 1.25 Meters (222-225 MHz)
- `70cm` - 70 Centimeters (420-450 MHz)
- `33cm` - 33 Centimeters (902-928 MHz)
- `23cm` - 23 Centimeters (1240-1300 MHz)
- `13cm` - 13 Centimeters (2300-2450 MHz)
- `9cm` - 9 Centimeters (3300-3500 MHz)
- `5cm` - 5 Centimeters (5650-5925 MHz)
- `3cm` - 3 Centimeters (10000-10500 MHz)

#### Supported Filters

- `+ares` - ARES repeaters
- `+races` - RACES repeaters
- `+skywarn` - Skywarn repeaters
- `+allstar` - AllStar linked repeaters
- `+echolink` or `+echo` - EchoLink-enabled repeaters
- `+irlp` - IRLP-enabled repeaters
- `+wires` - WIRES-enabled repeaters
- `+fm` - FM analog repeaters
- `+dmr` - DMR repeaters
- `+dstar` - D-STAR repeaters

### NearestObjectPlugin

The `NearestObjectPlugin` returns the nearest repeaters in APRS object notation format, suitable for creating APRS objects.

#### Command Syntax

```
o[bject] [count] [band] [+filter]
```

Parameters are the same as `NearestPlugin`.

#### Example Interactions

**Get nearest repeater as APRS object:**
```
You: o
APRSD: ;W6ABC     *123456z3745.00N/12225.00Wr146.520+ T88.5 2.3mi NE
```

**Get 3 nearest 70cm repeaters as objects:**
```
You: o 3 70cm
APRSD: ;W6ABC     *123456z3745.00N/12225.00Wr446.000+ T88.5 1.2mi SE
      ;W6XYZ     *123456z3745.10N/12225.10Wr446.100+ T100.0 3.4mi SW
      ;W6DEF     *123456z3745.20N/12225.20Wr446.200+ T103.5 5.6mi N
```

### VersionPlugin

The `VersionPlugin` displays the plugin version information. It is disabled by default.

#### Command Syntax

```
v[ersion]
```

#### Example Interaction

```
You: v
APRSD: APRS REPEAT Version: 1.0.0
```

### Help System

The REPEAT plugins include a tiered help system to provide concise or detailed
help over APRS without flooding the network.

#### Basic Help

Send `help <plugin>` for a quick syntax reference (1-2 messages):

```
help nearest
help object
help version
```

#### Detailed Help

Send `help <plugin> full` for complete documentation (4-8 messages):

```
help nearest full
help object full
```

#### RepeatHelpPlugin Configuration

To use the REPEAT help system, enable `RepeatHelpPlugin` and disable APRSD's
built-in HelpPlugin:

```yaml
aprsd:
  enabled_plugins:
    - aprsd_repeat_plugins.help.RepeatHelpPlugin
    - aprsd_repeat_plugins.nearest.NearestPlugin
    - aprsd_repeat_plugins.nearest.NearestObjectPlugin
    - aprsd_repeat_plugins.version.VersionPlugin
```

## Response Format

The `NearestPlugin` returns responses in the following format:

```
<CALLSIGN> <FREQUENCY> <OFFSET> <TONE> <DISTANCE><UNITS> <DIRECTION>
```

Where:
- `CALLSIGN`: Repeater callsign
- `FREQUENCY`: Repeater output frequency in MHz (e.g., `146.940`)
- `OFFSET`: Offset in MHz with sign (e.g., `-.6`, `+5`, `-7.6`, `0` for simplex)
- `TONE`: CTCSS/PL tone required for access (e.g., `T88.5`, `Toff` if none)
- `DISTANCE`: Distance in miles (US/UK) or kilometers (elsewhere)
- `UNITS`: Distance units (`mi` or `km`)
- `DIRECTION`: Compass direction from your location (N, NE, E, SE, S, SW, W, NW)

Example:
```
W6ABC 146.940 -.6 T88.5 2.3mi NE
```

**Why show the actual offset?** While many repeaters use standard offsets (±600 kHz for 2m,
±5 MHz for 70cm), a significant number use non-standard offsets. For example, approximately
28% of 70cm repeaters in the database use offsets other than ±5 MHz (such as -7.6 MHz or
-9 MHz). Showing the actual offset ensures you can correctly program your radio regardless
of local frequency coordination practices.

## Troubleshooting

### Plugin Not Responding

1. **Check plugin is enabled**: Verify the plugin is listed in `aprsd.enabled_plugins` in your configuration
2. **Check API keys**: Ensure both `aprs.fi.apiKey` and `aprsd_repeat_plugins.haminfo_apiKey` are configured
3. **Check base URL**: Verify `aprsd_repeat_plugins.haminfo_base_url` is correct and accessible
4. **Check logs**: Review APRSD logs for error messages

### "Unable to find location from aprs.fi"

- Ensure your callsign has sent a recent APRS beacon with location data
- Verify your `aprs.fi` API key is valid
- Check that aprs.fi has recent location data for your callsign

### "Missing aprsd_repeat_plugins.haminfo_apiKey"

- Add the `haminfo_apiKey` to your configuration under the `aprsd_repeat_plugins` section
- Restart APRSD after adding the configuration

### Invalid Frequency Band Error

- Use the exact band names listed in the "Supported Frequency Bands" section
- Common bands: `2m`, `70cm`, `6m`, `1.25m`, `33cm`, `23cm`

## Development

### Setting Up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/hemna/aprsd-repeat-plugins.git
cd aprsd-repeat-plugins
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
tox
```

Or run specific test environments:
```bash
tox -e py311    # Run Python 3.11 tests
tox -e lint     # Run linting
tox -e fmt      # Format code
```

### Code Quality

The project uses:
- **ruff** for linting and code formatting
- **pytest** for testing
- **tox** for test automation

## Contributing

Contributions are very welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the terms of the [MIT License](https://opensource.org/licenses/MIT), APRSD REPEAT Service Plugins is free and open source software.

## Issues

If you encounter any problems, please [file an issue](https://github.com/hemna/aprsd-repeat-plugins/issues) along with a detailed description.

## Credits

This project was generated from [@hemna](https://github.com/hemna)'s [APRSD Plugin Python Cookiecutter](https://github.com/hemna/cookiecutter-aprsd-plugin) template.

## Links

- [PyPI Package](https://pypi.org/project/aprsd-repeat-plugins/)
- [GitHub Repository](https://github.com/hemna/aprsd-repeat-plugins)
- [APRSD Documentation](https://aprsd.readthedocs.io/)
