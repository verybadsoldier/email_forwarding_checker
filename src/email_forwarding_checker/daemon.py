import logging
from typing import List, Optional
import schedule
import time

from email_forwarding_checker.forwarding_checker import ForwardingChecker
from email_forwarding_checker.mqtt import Mqtt

_logger = logging.getLogger(__name__)

class Daemon:
    def __init__(self, fc: ForwardingChecker, mqtt_host: str, mqtt_port: int=1883) -> None:
        self._fc = fc
        self._mqtt = Mqtt(mqtt_host, mqtt_port)
        self._topic_root = 'email'
        self._emails = Optional[List[str]]

    def _job(self):
        _logger.info(f'Starting mail check')
        report = self._fc.check_multiple_emails(self._emails)
        _logger.info(f'Mail check finished: {str(report)}')

        for k, v in report.items():
            topic = f"{self._topic_root}/{k}"
            _logger.info(f'Publishing test result for email address "{k}": {v}')
            self._mqtt.publish(topic, '1' if v else '0')

    def run(self, interval: int, emails: List[str]):
        _logger.info(f'Scheduling job for every {interval} seconds...')
        schedule.every(interval).seconds.do(self._job)

        while True:
            schedule.run_pending()
            time.sleep(1)
