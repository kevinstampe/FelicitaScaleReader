import json
import time
from RpiGPIO import GPIO

#For a 2L HX boiler with a 1300W heater element on 230V, 50Hz, a good starting point for PID tuning values would be:
#     P (Proportional): 60
#     I (Integral): 0.5
#     D (Derivative): 10

# These are initial values to stabilize temperature without causing too much overshoot. Since HX machines typically have some thermal lag due to their design, the integral and derivative terms are lower to avoid overcorrection.
# Tuning Tips:

#     Adjust the P term if you find the temperature swings are too wide (increase P) or too narrow (decrease P).
#     Tweak the I term to address any steady-state error or slight temperature drift.
#     Adjust the D term if there’s overshoot or if the system responds too slowly.

# Fine-tuning may be necessary to achieve stable performance based on your specific machine's thermal properties and the environmental conditions.


class BoilerHeater:

    def __init__(self):
        with open('/path/to/boilersettings.json', 'r') as f:
            settings = json.load(f)

        self.json_settings = settings[0]
        self.pid = PID(
            self.json_settings['Kp'], 
            self.json_settings['Ki'], 
            self.json_settings['Kd'],
            self.json_settings['Kaw'],
            self.json_settings['T_C'],
            self.json_settings['T'],
            self.json_settings['max'],
            self.json_settings['min'],
            self.json_settings['max_rate']
        )
        
        

class PIDController:
    def __init__(self, setpoint, antiwindup, Kp, Kd, Ki):
        self.setpoint = setpoint
        self.previous_delta = 0
        self.delta = 0
        self.antiwindup = antiwindup
        self.integral = 0
        self.derivative = 0
        self.Kp = Kp
        self.Kd = Kd
        self.Ki = Ki
        self.dt = 1
        self.output = 0
        self.boiler = 0
        self.sensor_reading = 0

    def calc(self, x):

        # Basic PID forumla with an antiwindup feature
        self.sensor_reading = x
        self.previous_delta = self.delta
        self.delta = self.setpoint - self.sensor_reading
        if self.sensor_reading > self.setpoint-self.antiwindup:
            if self.sensor_reading < self.setpoint+self.antiwindup:
                self.integral = self.integral + (self.delta * self.dt)
        self.derivative = (self.delta - self.previous_delta) / self.dt
        self.output = int((self.delta * self.Kp) + (self.Kd * self.derivative) + (self.integral * self.Ki))

        # heat the boiler elements if the PID output is positive
        if self.output>0:
            if self.sensor_reading>0: #safety catch incase PID is in error state
                if self.output>100:
                    self.output=100
                boilerPWM.start(self.output)
                self.boiler=self.output
            else:
                boilerPWM.stop()
        else:
            boilerPWM.stop()
            self.boiler=0


def read_temp_raw():
    # NTC 3950 100k thermistor
    temp = GPIO.input(4)
    return temp
    
    
    

def read_temp():
    # NTC 3950 100k thermistor
    temp = read_temp_raw()
    return temp
        

boilerPWM=GPIO.PWM(23, 50)

GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)