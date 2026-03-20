# Design: Tiered Help System for APRSD REPEAT Plugins

**Date:** 2026-03-19
**Status:** Approved

## Overview

Implement a tiered help system for APRSD REPEAT plugins that balances informativeness with APRS message length constraints (~67 chars max). Users can request basic help (`help nearest`) or detailed help (`help nearest full`).

## Problem

Current help responses are either:
- Too verbose (4 messages per plugin = radio traffic congestion)
- Not informative enough (users don't know all available bands/filters)

## Solution

A two-tier help system:
- **Basic help**: 1-2 messages with syntax + preview of options
- **Full help**: 4-8 messages with complete bands, filters, response format, and examples

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RepeatHelpPlugin                          │
│  - Replaces APRSD's built-in HelpPlugin                     │
│  - Parses: "help", "help <plugin>", "help <plugin> full"    │
│  - Dispatches to help_basic() or help_full()                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    TieredHelpMixin                           │
│  - help_basic() → 1-2 short messages                        │
│  - help_full() → complete reference                         │
│  - help() → backward compat, returns help_basic()           │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
     NearestPlugin    NearestObjectPlugin   VersionPlugin
```

## File Changes

### New file: `aprsd_repeat_plugins/help.py`

- `TieredHelpMixin` class with abstract `help_basic()` and `help_full()` methods
- `RepeatHelpPlugin` that handles help command dispatch
- `MAX_APRS_MSG_LEN = 67` constant for validation

### Modify: `aprsd_repeat_plugins/nearest.py`

- `NearestPlugin` inherits from `TieredHelpMixin`
- Implements `help_basic()` and `help_full()`
- `NearestObjectPlugin` inherits from `NearestPlugin` (already does), gets mixin via inheritance

### Modify: `aprsd_repeat_plugins/version.py`

- `VersionPlugin` inherits from `TieredHelpMixin`
- Implements `help_basic()` and `help_full()`

## Message Content

### NearestPlugin basic (2 messages)

```
n [#] [band] [+filter] ex: n 3 70cm +echo
bands:2m,70cm,6m,1.25m filters:echo,dmr,dstar
```

### NearestPlugin full (7 messages)

```
n [#] [band] [+filter] - find nearest repeaters
bands: 2m,70cm,6m,1.25m,33cm,23cm,13cm,9cm,5cm,3cm
filters: echo,irlp,dmr,dstar,ares,races,skywarn
filters: allstar,wires,fm
response: CALL FREQ OFFSET TONE DIST DIR
ex: n 3 70cm +echo (3 70cm echolink repeaters)
ex: n 5 2m +dmr (5 2m DMR repeaters)
```

### NearestObjectPlugin basic (2 messages)

```
o [#] [band] [+filter] ex: o 2 2m +irlp
bands:2m,70cm,6m,1.25m filters:echo,dmr,dstar
```

### NearestObjectPlugin full (5 messages)

```
o [#] [band] [+filter] - repeaters as APRS objects
bands: 2m,70cm,6m,1.25m,33cm,23cm,13cm,9cm,5cm,3cm
filters: echo,irlp,dmr,dstar,ares,races,skywarn
filters: allstar,wires,fm
ex: o 2 70cm (2 nearest 70cm as objects)
```

### VersionPlugin basic (1 message)

```
v - shows REPEAT plugin version
```

### VersionPlugin full (1 message)

```
v or version - shows REPEAT plugin version
```

## Configuration

Users disable APRSD's built-in HelpPlugin and enable RepeatHelpPlugin:

```yaml
aprsd:
  enabled_plugins:
    - aprsd_repeat_plugins.help.RepeatHelpPlugin
    - aprsd_repeat_plugins.nearest.NearestPlugin
    - aprsd_repeat_plugins.nearest.NearestObjectPlugin
    - aprsd_repeat_plugins.version.VersionPlugin
```

## Error Handling

1. `help` alone → List available plugins: "plugins: nearest object version"
2. `help <unknown>` → "Unknown plugin. Available: nearest, object, version"
3. Message length validation → Log warning if any help message exceeds 67 chars

## Testing

- Unit tests for `TieredHelpMixin` interface
- Unit tests for `RepeatHelpPlugin` parsing (`help`, `help nearest`, `help nearest full`)
- Verify all help messages are ≤67 characters
- Integration test with mock packet
