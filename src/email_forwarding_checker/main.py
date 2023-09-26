"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         fibonacci = email_forwarding_checker.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``fibonacci`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This file can be renamed depending on your needs or safely removed if not needed.

References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

from email_forwarding_checker.forwarding_checker import ForwardingChecker
import argparse
import logging
import sys
import yaml

from email_forwarding_checker import __version__
from email_forwarding_checker.daemon import Daemon

__author__ = "verybadsoldier"
__copyright__ = "verybadsoldier"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version=f"email_forwarding_checker {__version__}",
    )
    parser.add_argument(dest="n", help="n-th Fibonacci number", type=int, metavar="INT")
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
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(args):
    parser = argparse.ArgumentParser(description="Email Forwarding Checker")
    parser.add_argument(
        "--config_file", help="Config filename", type=str, default="config.yml"
    )

    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as a daemon permanently reporting via MQTT",
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

    config = dict(timeout=120, smtp_port=587, delete_emails=False, mqtt_host="localhost", mqtt_port=1883)

    args = parser.parse_args(args)

    with open(args.config_file, "r", encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)
        config.update(yaml_config)

    forwarding_checker = ForwardingChecker(
        smtp_sender=config["smtp_sender"],
        smtp_host=config["smtp_host"],
        smtp_port=config["smtp_port"],
        smtp_username=config["smtp_username"],
        smtp_password=config["smtp_password"],
        imap_host=config["imap_host"],
        imap_username=config["imap_username"],
        imap_password=config["imap_password"],
        delete_emails=config["delete_emails"],
    )

    if args.daemon:
        _logger.info('Starting in daemon...')
        d = Daemon(forwarding_checker, args['mqtt_host'], args['mqtt_port'])
        d.run(config["emails"])
    else:
        report = forwarding_checker.check_multiple_emails(config["emails"])
        print(report)


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m email_forwarding_checker.skeleton 42
    #
    run()
