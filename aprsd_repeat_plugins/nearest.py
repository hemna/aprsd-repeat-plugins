import logging

import requests
from aprsd import plugin, plugin_utils, trace


LOG = logging.getLogger("APRSD")

API_KEY_HEADER = "X-Api-Key"

# Copied over from haminfo.utils
# create from
# http://www.arrl.org/band-plan
FREQ_BAND_PLAN = {
    "160m": {"desc": "160 Meters (1.8-2.0 MHz)", "low": 1.8, "high": 2.0},
    "80m": {"desc": "80 Meters (3.5-4.0 MHz)", "low": 3.5, "high": 4.0},
    "60m": {"desc": "60 Meters (5 MHz channels)", "low": 5.0, "high": 5.9},
    "40m": {"desc": "40 Meters (7.0 - 7.3 MHz)", "low": 7.0, "high": 7.3},
    "30m": {"desc": "30 Meters(10.1 - 10.15 MHz)", "low": 10.1, "high": 10.15},
    "20m": {"desc": "20 Meters(14.0 - 14.35 MHz)", "low": 14.0, "high": 14.35},
    "17m": {
        "desc": "17 Meters(18.068 - 18.168 MHz)",
        "low": 18.068,
        "high": 18.168,
    },
    "15m": {"desc": "15 Meters(21.0 - 21.45 MHz)", "low": 21.0, "high": 21.45},
    "12m": {
        "desc": "12 Meters(24.89 - 24.99 MHz)",
        "low": 24.89,
        "high": 24.99,
    },
    "10m": {"desc": "10 Meters(28 - 29.7 MHz)", "low": 28.0, "high": 29.7},
    "6m": {"desc": "6 Meters(50 - 54 MHz)", "low": 50.0, "high": 54.0},
    "2m": {"desc": "2 Meters(144 - 148 MHz)", "low": 144.0, "high": 148.0},
    "1.25m": {
        "desc": "1.25 Meters(222 - 225 MHz)",
        "low": 222.0,
        "high": 225.0,
    },
    "70cm": {
        "desc": "70 Centimeters(420 - 450 MHz)",
        "low": 420.0,
        "high": 450,
    },
    "33cm": {
        "desc": "33 Centimeters(902 - 928 MHz)",
        "low": 902.0,
        "high": 928,
    },
    "23cm": {
        "desc": "23 Centimeters(1240 - 1300 MHz)",
        "low": 1240.0,
        "high": 1300.0,
    },
    "13cm": {
        "desc": "13 Centimeters(2300 - 2310 and 2390 - 2450 MHz)",
        "low": 2300.0,
        "high": 2450.0,
    },
    "9cm": {
        "desc": "9 centimeters(3300-3500 MHz)",
        "low": 3300.0,
        "high": 3500.0,
    },
    "5cm": {
        "desc": "5 Centimeters(5650.0 - 5925.0 MHz)",
        "low": 5650.0,
        "high": 5290.0,
    },
    "3cm": {
        "desc": "3 Centimeters(10000.000 - 10500.000 MHz )",
        "low": 10000.0,
        "high": 10500.0,
    },
}

# Mapping of human filter string to db column name
# These are the allowable filters.
STATION_FEATURES = {
    "ares": "ares",
    "races": "races",
    "skywarn": "skywarn",
    "allstar": "allstar_node",
    "echolink": "echolink_node",
    "echo": "echolink_node",
    "irlp": "irlp_node",
    "wires": "wires_node",
    "fm": "fm_analog",
    "dmr": "dmr",
    "dstar": "dstar",
}


class NearestPlugin(plugin.APRSDRegexCommandPluginBase):
    """Nearest!

    Syntax of request

    n[earest] [count] [band]

    count - the number of stations to return
    band  - the frequency band to look for
            Defaults to 2m


    """

    version = "1.0"
    command_regex = "^[nN]"
    command_name = "nearest"

    def help(self):
        _help = [
            "nearest: Return nearest repeaters to your last beacon.",
            "nearest: Send 'n [count] [band] [+filter]'",
            "nearest: band: example: 2m, 70cm",
            "nearest: filter: ex: +echo or +irlp",
        ]
        return _help

    @staticmethod
    def isfloat(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_int(value):
        try:
            int(value)
            return True
        except ValueError:
            return False

    @trace.trace
    def fetch_data(self, packet):
        fromcall = packet.get("from")
        message = packet.get("message_text", None)
        # ack = packet.get("msgNo", "0")

        # get last location of a callsign, get descriptive name from weather service
        try:
            self.config.exists(["services", "aprs.fi", "apiKey"])
        except Exception as ex:
            LOG.error(f"Failed to find config aprs.fi:apikey {ex}")
            return "No aprs.fi apikey found"

        api_key = self.config["services"]["aprs.fi"]["apiKey"]

        try:
            aprs_data = plugin_utils.get_aprs_fi(api_key, fromcall)
        except Exception as ex:
            LOG.error(f"Failed to fetch aprs.fi '{ex}'")
            return "Failed to fetch aprs.fi location"

        LOG.debug(f"NearestPlugin: aprs_data = {aprs_data}")
        if not len(aprs_data["entries"]):
            LOG.error("Didn't get any entries from aprs.fi")
            return "Failed to fetch aprs.fi location"

        lat = aprs_data["entries"][0]["lat"]
        lon = aprs_data["entries"][0]["lng"]

        command_parts = message.split(" ")
        # try and decipher the request parameters
        # n[earest] should be part[0]
        # part[1] could be

        # The command reference is:
        # N[earest] [<fields>]
        # IF it's a number, it's the number stations to return
        # if it has an '<int>m' in it, that's the frequency band
        # if it starts with a +<key> it's a filter.
        count = None
        band = None
        filters = []
        for part in command_parts[1:]:
            LOG.debug(part)
            if self.is_int(part):
                # this is the number of stations
                count = int(part)
            elif part.endswith("m"):
                # this is the frequency band
                if part in FREQ_BAND_PLAN:
                    band = part
                else:
                    LOG.error(
                        f"User tried to use an invalid frequency band {part}",
                    )
            elif part.startswith("+"):
                # this is the filtering
                filter = part[1:].lower()
                if filter in STATION_FEATURES:
                    filters.append(STATION_FEATURES[filter])
            else:
                # We don't know what this is.
                return "Usage: n [num] [band] [+filter]"

        if not count:
            # They didn't specify a count
            # so we default to 1
            count = 1

        if not band:
            # They didn't specify a frequency band
            # so we use 2meters
            band = "2m"

        LOG.info(
            "Looking for {} nearest stations in band {} "
            "with filters: {}".format(count, band, filters),
        )

        try:
            url = "{}/nearest".format(
                self.config["services"]["haminfo"]["base_url"],
            )
            api_key = self.config["services"]["haminfo"]["apiKey"]
            params = {"lat": lat, "lon": lon, "count": count, "band": band}
            if filters:
                params["filters"] = ",".join(filters)

            headers = {API_KEY_HEADER: api_key}
            result = requests.post(url=url, json=params, headers=headers)
            data = result.json()

        except Exception as ex:
            LOG.error(f"Couldn't fetch nearest stations '{ex}'")
            data = None

        return data

    @trace.trace
    def process(self, packet):
        LOG.info("Nearest Plugin")

        data = self.fetch_data(packet)

        if data:
            # just do the first one for now
            replies = []
            for entry in data:
                LOG.info(f"Using {entry}")

                if self.isfloat(entry["offset"]) and float(entry["offset"]) > 0:
                    offset_direction = "+"
                else:
                    offset_direction = "-"

                # US and UK are in miles, everywhere else is metric?
                # by default units are meters
                distance = entry["distance"]
                units = ""
                if self.isfloat(distance):
                    distance = float(distance)

                    if (
                        entry["country"].lower() == "united states"
                        or entry["country"].lower() == "united kingdom"
                    ):
                        distance = f"{distance / 1609:.1f}"
                        units = "mi"
                    else:
                        distance = f"{distance / 1000:.1f}"
                        units = "km"

                uplink_offset = entry["uplink_offset"]
                if self.isfloat(uplink_offset):
                    uplink_offset = f"{float(uplink_offset):.1f}"

                reply = "{} {}{} T{} {}{} {}".format(
                    entry["callsign"],
                    entry["frequency"],
                    offset_direction,
                    uplink_offset,
                    distance,
                    units,
                    entry["direction"],
                )
                replies.append(reply)
            return replies
        else:
            return "None Found"


class NearestObjectPlugin(NearestPlugin):
    """Return an inmessage object notation for the repeater.

    http://www.aprs.org/aprs12/item-in-msg.txt

    https://github.com/hemna/aprsd-nearest-plugin/issues/2

    """

    version = "1.0"
    command_regex = "^[oO]"
    command_name = "nearest"

    @trace.trace
    def process(self, packet):
        LOG.info("Nearest Object Plugin")
        data = self.fetch_data(packet)[0]

        if data:
            callsign = data["callsign"]
            latlon = "{:.2f}N/{:.2f}W".format(data["lat"], data["long"])

            uplink_tone = data["uplink_offset"]
            if self.isfloat(uplink_tone):
                uplink_tone = f"{float(uplink_tone):.1f}"

            offset = data["offset"]
            offset = f"{float(offset):.2f}"
            offset = "{}".format(offset.replace(".", ""))

            reply = "){:9s}!{}r{}Mhz T{} {}".format(
                callsign, latlon, data["frequency"], uplink_tone, offset,
            )

            return reply
        else:
            return "None Found"
