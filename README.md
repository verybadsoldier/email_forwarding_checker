# Email Forwarding Checker

A small programm that periodically checks if a configured email forwarding for different addresses is working by sending test emails. Purpose is that you will get a notification via MQTT if forwarding stops working and it does not go unnoticed.

## How it works

Configure a list of email addresses that should be checked. For those addresses there should be a forwarding configured. Then test emails will be sent periodically to those email adresses via a configurable SMTP server.

Lastly, it will be checked if the test emails arrived at the destination by looking into a configurable IMAP postbox. If the test emails do not arrive there within a specific amount of time, then the forwarding is considered to be not working.





## Hot to use it
Install the Python package via `pip`, install it from source or use the docker image:

`docker pull ghcr.io/verybadsoldier/email_forwarding_checker`

### Docker

Example docker-compose.yml:
```
version: '3'
services:
  email_forwarding_checker:
    image: ghcr.io/verybadsoldier/email_forwarding_checker:0.2.2
    container_name: email_forwarding_checker
    volumes:
      - ./config.yml:/config.yml
    restart: always
    environment:
      - TZ=Europe/Berlin
```

### Configuration

Example config:
```
smtp:
  host: smtp.zoho.com
  username: myuser
  password: mypasswd
  sender: checker@check.com

imap:
  host: imap.zoho.com
  username: myimapuser
  password: myimappw

mqtt:
  host: 192.168.2.33
  topic_base: home/email_forwarding_checker

daemon:
  check_interval_hours: 1
  run_now: true  # run once instantly upon startup, then every check_interval_hours hours

email_timeout: 2400  # if the test email does not arrive with this time in seconds, then the forwarding is considered to have failed
repeat_interval: 5  # within email_timeout, check every n seconds for the test email
delete_emails: false  # delete the test emails from the IMAP postbox after arrival
emails:
        - address1@gmail.com
        - address2@gmail.com
        - address3@gmail.com
```
