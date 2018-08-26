""" 
  Author: Surendra Kane

  Script to control individual Raspberry Pi GPIO's.
  Applicable ONLY for Raspberry PI 3, based on schematics.
  Please modify for other board versions to control correct GPIO's.
"""

import fauxmo
import logging
import time
import RPi.GPIO as GPIO

from debounce_handler import debounce_handler

logging.basicConfig(level=logging.DEBUG)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Key = trigger name used by Alexa
# Value = GPIO pin number / offset from 50000
gpio_pins = {'Outlet 1':20,
             'Outlet 2':21}

# Key = trigger name used by Alexa
# Value = offset from 50030
ir_devices = {'Bedroom TV Power':1,
              'Bedroom TV Volume Up':2,
              'Bedroom TV Volume Down':3}

class device_handler(debounce_handler):
    """Triggers on/off based on GPIO 'device' selected.
       Publishes the IP address of the Echo making the request.
    """
    TRIGGERS = {}

    for gpio_pin in gpio_pins:
        TRIGGERS.update({gpio_pin : gpio_pins[gpio_pin] + 50000})
        
    for ir_device in ir_devices:
        TRIGGERS.update({ir_device : ir_devices[ir_device] + 50030})
        
    def do_gpio(self,pin,state):
      print('pin: %d , state: %s' % (pin, state))
      if state == True:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin,GPIO.LOW)  # Reverse polarity
      else:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin,GPIO.HIGH) # Reverse polarity

    def do_ir(self,device):
      print('device: %s' % (device))
        
    def act(self, client_address, state, name):
        device = str(name)
        print "State", state, "on ", name, "from client @", client_address, "gpio pin: ",gpio_pins[device]

        if device in gpio_pins:
            self.do_gpio(gpio_pins[device],state)
            return True

        elif device in ir_devices:
            self.do_ir(device)
            return True

if __name__ == "__main__":
    # Startup the fauxmo server
    fauxmo.DEBUG = True
    p = fauxmo.poller()
    u = fauxmo.upnp_broadcast_responder()
    for i in range(10):
        if u.init_socket():
            break
        logging.info("Failed init_socket %d"%(i))
        time.sleep(i)
    p.add(u)

    # Register the device callback as a fauxmo handler
    d = device_handler()
    for trig, port in d.TRIGGERS.items():
        fauxmo.fauxmo(trig, u, p, None, port, d)

    # Loop and poll for incoming Echo requests
    logging.debug("Entering fauxmo polling loop")
    while True:
        try:
            # Allow time for a ctrl-c to stop the process
            p.poll(100)
            time.sleep(0.1)
        except Exception, e:
            logging.critical("Critical exception: " + str(e))
            break
