import datetime
import logging

import requests
from aprsd import messaging, plugin, plugin_utils

import aprsd_repeat_plugins


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


class InvalidRequest(Exception):
    message = "Couldn't decipher request"


class NoAPRSFIApiKeyException(Exception):
    message = "No aprs.fi ApiKey found in config"


class NoAPRSFILocationException(Exception):
    message = "Unable to find location from aprs.fi"


class NearestPlugin(plugin.APRSDRegexCommandPluginBase):
    """Nearest!

    Syntax of request

    n[earest] [count] [band]

    count - the number of stations to return
    band  - the frequency band to look for
            Defaults to 2m


    """

    version = aprsd_repeat_plugins.__version__
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

    def _tone(self, tone, human=False):
        LOG.debug(f"TONE {tone}")
        if tone == "0" or tone == "0.0000":
            uplink_tone = "off"
        elif self.isfloat(tone):
            if human:
                uplink_tone = f"{float(tone):.1f}"
            else:
                tone = int(float(tone))
                uplink_tone = f"{tone}"

        return f"T{uplink_tone}"

    def _offset(self, offset):
        offset = float(offset)
        if offset < 0:
            offset = f"{offset:.2f}"
        else:
            offset = f"+{offset:.2f}"
        return "{}".format(offset.replace(".", ""))

    def fetch_data(self, packet):
        fromcall = packet.get("from")
        message = packet.get("message_text", None)
        # ack = packet.get("msgNo", "0")

        # get last location of a callsign, get descriptive name from weather service
        try:
            self.config.exists(["services", "aprs.fi", "apiKey"])
        except Exception as ex:
            LOG.error(f"Failed to find config aprs.fi:apikey {ex}")
            raise NoAPRSFIApiKeyException()

        api_key = self.config["services"]["aprs.fi"]["apiKey"]

        try:
            aprs_data = plugin_utils.get_aprs_fi(api_key, fromcall)
        except Exception as ex:
            LOG.exception(ex)
            LOG.error(f"Failed to fetch aprs.fi '{ex}'")
            raise NoAPRSFILocationException()

        if not len(aprs_data["entries"]):
            LOG.error("Didn't get any entries from aprs.fi")
            raise NoAPRSFILocationException()

        lat = aprs_data["entries"][0]["lat"]
        lon = aprs_data["entries"][0]["lng"]

        command_parts = message.split(" ")
        LOG.info(command_parts)
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
            if self.is_int(part):
                # this is the number of stations
                count = int(part)
                # Lets max out at 10 replies
                if count > 10:
                    count = 10
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
            elif not part:
                continue
            else:
                # We don't know what this is.
                raise InvalidRequest()

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
            params = {
                "lat": lat, "lon": lon, "count": count, "band": band,
                "callsign": fromcall,
            }
            if filters:
                params["filters"] = ",".join(filters)

            headers = {API_KEY_HEADER: api_key}
            result = requests.post(url=url, json=params, headers=headers)
            data = result.json()

        except Exception as ex:
            LOG.error(f"Couldn't fetch nearest stations '{ex}'")
            data = None

        return data

    def process(self, packet):
        LOG.info("Nearest Plugin")

        try:
            data = self.fetch_data(packet)
        except NoAPRSFILocationException as ex:
            return ex.message
        except NoAPRSFILocationException as ex:
            return ex.message
        except InvalidRequest as ex:
            return ex.message
        except Exception:
            return "Failed to fetch data"

        if data:
            # just do the first one for now
            replies = []
            for entry in data:
                LOG.info(f"Using {entry}")

                if "offset" not in entry:
                    offset_direction = ""
                elif self.isfloat(entry["offset"]) and float(entry["offset"]) > 0:
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

                uplink_offset = self._tone(entry["uplink_offset"], human=True)

                reply = "{} {}{} {} {}{} {}".format(
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

    version = aprsd_repeat_plugins.__version__
    command_regex = "^[oO]"
    command_name = "object"

    def help(self):
        _help = [
            "object: Return nearest repeaters as APRS object to your last beacon.",
            "object: Send 'o [count] [band] [+filter]'",
            "object: band: example: 2m, 70cm",
            "object: filter: ex: +echo or +irlp",
        ]
        return _help

    def decdeg2dms(self, degrees_decimal):
        is_positive = degrees_decimal >= 0
        degrees_decimal = abs(degrees_decimal)
        minutes, seconds = divmod(degrees_decimal * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        degrees = degrees if is_positive else -degrees

        # degrees = str(int(degrees)).zfill(2).replace("-", "0")
        degrees = str(int(degrees)).replace("-", "0")
        # minutes = str(int(minutes)).zfill(2).replace("-", "0")
        minutes = str(int(minutes)).replace("-", "0")
        # seconds = str(int(round(seconds * 0.01, 2) * 100)).zfill(2)
        seconds = str(int(round(seconds * 0.01, 2) * 100))

        return {"degrees": degrees, "minutes": minutes, "seconds": seconds}

    def decdeg2dmm_m(self, degrees_decimal):
        is_positive = degrees_decimal >= 0
        degrees_decimal = abs(degrees_decimal)
        minutes, seconds = divmod(degrees_decimal * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        degrees = degrees if is_positive else -degrees

        # degrees = str(int(degrees)).zfill(2).replace("-", "0")
        degrees = abs(int(degrees))
        # minutes = str(round(minutes + (seconds / 60), 2)).zfill(5)
        minutes = int(round(minutes + (seconds / 60), 2))
        hundredths = round(seconds / 60, 2)

        return {
            "degrees": degrees, "minutes": minutes, "seconds": seconds,
            "hundredths": hundredths,
        }

    def convert_latitude(self, degrees_decimal):
        det = self.decdeg2dmm_m(degrees_decimal)
        if degrees_decimal > 0:
            direction = "N"
        else:
            direction = "S"

        degrees = str(det.get("degrees")).zfill(2)
        minutes = str(det.get("minutes")).zfill(2)
        seconds = det.get("seconds")
        hun = det.get("hundredths")
        hundredths = f"{hun:.2f}".split(".")[1]

        LOG.debug(
            f"LAT degress {degrees}  minutes {str(minutes)} "
            f"seconds {seconds} hundredths {hundredths} direction {direction}",
        )

        lat = f"{degrees}{str(minutes)}.{hundredths}{direction}"
        return lat

    def convert_longitude(self, degrees_decimal):
        det = self.decdeg2dmm_m(degrees_decimal)
        if degrees_decimal > 0:
            direction = "E"
        else:
            direction = "W"

        degrees = str(det.get("degrees")).zfill(3)
        minutes = str(det.get("minutes")).zfill(2)
        seconds = det.get("seconds")
        hun = det.get("hundredths")
        hundredths = f"{hun:.2f}".split(".")[1]

        LOG.debug(
            f"LON degress {degrees}  minutes {str(minutes)} "
            f"seconds {seconds} hundredths {hundredths} direction {direction}",
        )

        lon = f"{degrees}{str(minutes)}.{hundredths}{direction}"
        return lon

    def _get_latlon(self, latitude_str, longitude_str):
        return "{}/{}".format(
                self.convert_latitude(float(latitude_str)),
                self.convert_longitude(float(longitude_str)),
        )

    def process(self, packet):
        LOG.info("Nearest Object Plugin")
        stations = self.fetch_data(packet)

        if not stations:
            return "None Found"

        replies = []

        for data in stations:
            callsign = data["callsign"]

            latlon = self._get_latlon(data["lat"], data["long"])

            uplink_tone = self._tone(data["uplink_offset"])
            offset = self._offset(data["offset"])

            distance = float(data["distance"])
            distance = f"{distance / 1609:.1f}"
            freq = float(data["frequency"])

            # reply = ";{:.3f}-VA*111111z{}r{:.3f}MHz T{} {}".format(
            # reply=";{:.3f}VAA*111111z{}rT{} {}".format(
            #        freq, latlon, uplink_tone, offset,
            # )
            packet["from"]
            fromcall = self.config["aprs"]["login"]

            local_datetime = datetime.datetime.now()
            UTC_OFFSET_TIMEDELTA = datetime.datetime.utcnow() - local_datetime
            result_utc_datetime = local_datetime + UTC_OFFSET_TIMEDELTA
            time_zulu = result_utc_datetime.strftime("%d%H%M")

            reply = "{}>APZ100:;{:9s}*{}z{}r{:.3f}MHz {} {}".format(
                fromcall, callsign, time_zulu, latlon, freq, uplink_tone, offset,
            )
            msg = messaging.RawMessage(reply)
            msg.retry_count = 1
            replies.append(msg)

        return replies
