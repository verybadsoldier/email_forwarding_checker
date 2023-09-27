import json
import logging
from typing import List, Optional
import schedule
import time

from email_forwarding_checker.forwarding_checker import ForwardingChecker
from email_forwarding_checker.mqtt import Mqtt

_logger = logging.getLogger(__name__)


class Daemon:
    def __init__(
        self,
        fc: ForwardingChecker,
        mqtt_host: str,
        mqtt_port: int,
        mqtt_topic_base: str,
    ) -> None:
        self._fc = fc
        self._mqtt = Mqtt(mqtt_host, mqtt_port)

        self._emails: Optional[List[str]] = None
        self._email_timeout: Optional[int] = None
        self._mqtt_topic_base = mqtt_topic_base

    def _job(self):
        try:
            _logger.info("Starting mail check")
            report = self._fc.check_multiple_emails(self._emails, self._email_timeout)

            self._mqtt.connect()

            json_object = json.dumps(report)

            _logger.info("Publishing check report to MQTT")
            self._mqtt.publish(self._mqtt_topic_base, json_object)
        except Exception as ex:
            _logger.exception("Error in job execution", ex)

    def run(self, interval: int, run_now: bool, emails: List[str], email_timeout: int):
        self._emails = emails
        self._email_timeout = email_timeout

        _logger.info(f"Scheduling job for every {interval} seconds...")
        schedule.every(interval).seconds.do(self._job)

        if run_now:
            _logger.info("Running job one time now")
            schedule.run_all()

        while True:
            schedule.run_pending()
            time.sleep(1)
