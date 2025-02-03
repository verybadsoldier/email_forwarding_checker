import argparse
import logging
import sys
from datetime import timedelta

import yaml

from email_forwarding_checker import __version__
from email_forwarding_checker.daemon import Daemon
from email_forwarding_checker.forwarding_checker import ForwardingChecker

__author__ = "verybadsoldier"
__copyright__ = "verybadsoldier"
__license__ = "GPLv3"

_logger = logging.getLogger(__name__)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def setdefault_recursively(tgt, defaults):
    for k in defaults:
        if isinstance(defaults[k], dict):  # if the current item is a dict,
            # expand it recursively
            setdefault_recursively(tgt.setdefault(k, {}), defaults[k])
        else:
            # ... otherwise simply set a default value if it's not set before
            tgt.setdefault(k, defaults[k])


def main(args):
    parser = argparse.ArgumentParser(description="Email Forwarding Checker")
    parser.add_argument(
        "--config_file", help="Config filename", type=str, default="config.yml"
    )

    parser.add_argument(
        "--daemon",
        "-d",
        action="store_true",
        help="Run as a daemon permanently reporting via MQTT",
    )

    parser.add_argument(
        "--emails",
        help="Overrides the emaiRun as a daemon permanently reporting via MQTT",
        type=str,
        nargs="*",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"email_forwarding_checker {__version__}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )

    config_defaults = dict(
        smtp=dict(port=587),
        mqtt=dict(host="localhost", port=1883, topic_base="email_forwarding_checker"),
        imap=dict(mailbox="inbox"),
        timeout=120,
        delete_emails=False,
        daemon=dict(check_interval_hours=24, run_now=False),
        email_timeout=120,
    )

    args = parser.parse_args(args)

    with open(args.config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        setdefault_recursively(config, config_defaults)

    if args.emails is not None and len(args.emails) > 0:
        config["emails"] = args.emails

    forwarding_checker = ForwardingChecker(
        smtp_sender=config["smtp"]["sender"],
        smtp_host=config["smtp"]["host"],
        smtp_port=config["smtp"]["port"],
        smtp_username=config["smtp"]["username"],
        smtp_password=config["smtp"]["password"],
        imap_host=config["imap"]["host"],
        imap_username=config["imap"]["username"],
        imap_password=config["imap"]["password"],
        imap_mailbox=config["imap"]["mailbox"],
        delete_emails=config["delete_emails"],
        email_timeout=config["email_timeout"],
        repeat_interval=config["repeat_interval"],
    )

    email_timeout = timedelta(seconds=config["email_timeout"])

    if args.daemon:
        setup_logging(logging.INFO)
        _logger.info("Starting in daemon with config: %s", str(config))
        d = Daemon(
            forwarding_checker,
            config["mqtt"]["host"],
            config["mqtt"]["port"],
            config["mqtt"]["topic_base"],
        )
        d.run(
            timedelta(hours=config["daemon"]["check_interval_hours"]),
            config["daemon"]["run_now"],
            config["emails"],
            email_timeout,
        )
    else:
        logging.getLogger().disabled = True
        report = forwarding_checker.check_multiple_emails(
            config["emails"], email_timeout
        )
        print(report)


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
