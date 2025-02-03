import logging

import paho.mqtt.client as mqtt

_logger = logging.getLogger(__name__)


class Mqtt:
    def __init__(self, hostname, port=1883):
        self._mqtthost = hostname
        self._mqttport = port

        self._client = mqtt.Client()

    def connect(self):
        _logger.info("Connecting to MQTT host '%s:%d'", self._mqtthost, self._mqttport)

        self._client.connect(self._mqtthost, self._mqttport, 60)
        self._client.loop_start()
        
    def disconnect(self):
        self._client.disconnect()

    def publish(self, topic, value):
        _logger.info("Publishing MQTT message to topic '%s' with value '%d'", topic, value)
        self._client.publish(topic, value)
