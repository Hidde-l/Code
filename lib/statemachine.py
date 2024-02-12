import time
from time import sleep
import buzzer
import external
from external import set_external_led, set_external_GPIO
from measure import is_pyro_inserted, is_bw_inserted, is_armed, get_vbat_voltage, is_buzzer_switch_on, is_light_switch_on

class States():
        SYSTEMS_CHECK = 0
        ERROR_MODE = 1
        DATA_MODE = 2

class Statemachine:

        def __init__(self, PYRO_FIRE_DELAY_MS=60000):
                self.state = States.SYSTEMS_CHECK
                self.last_in_state_action = round(time.monotonic()*1000)
                self.last_state_transition = round(time.monotonic()*1000)
                self.launched_time =0
                self.do_state_action()
                self.STATE_ACTION_DELAY_MS = 5000
                self.MIN_STATE_DELAY_MS = 500
                self.PYRO_FIRE_DELAY_MS = PYRO_FIRE_DELAY_MS
                self.LAUNCHED = False


        def tick(self):
            if self.last_in_state_action + self.STATE_ACTION_DELAY_MS < round(time.monotonic()*1000):
                self.do_state_action()
                self.last_in_state_action = round(time.monotonic()*1000)
            if self.last_state_transition + self.MIN_STATE_DELAY_MS < round(time.monotonic()*1000):
                self.check_state_transition()

        def check_state_transition(self):
            if self.state == States.SYSTEMS_CHECK:
                if not self._battery_voltage_valid():
                    self.do_state_transition(States.ERROR_MODE)
                else:
                    self.do_state_transition(States.DATA_MODE)

            elif self.state == States.ERROR_MODE:
                if self._battery_voltage_valid():
                    self.do_state_transition(States.DATA_MODE)

            elif self.state == States.DATA_MODE:
                if not self._battery_voltage_valid():
                    self.do_state_transition(States.ERROR_MODE)


        def do_state_action(self):
            if self.state == States.SYSTEMS_CHECK:
                external.neopixel_set_rgb(0, 255, 0) #GREEN
            elif self.state == States.ERROR_MODE:
                #self._queue_long_beep()
                external.neopixel_set_rgb(255,0,0) #RED
            elif self.state == States.DATA_MODE:
                external.neopixel_set_rgb(0,0,255) #BLUE

                if is_buzzer_switch_on():
                    set_external_GPIO(True)
                    # self._queue_long_beep()

                #if is_light_switch_on():
                external._ext_led.value = True
                sleep(1) # wait for 1 second
                set_external_GPIO(False)
                external._ext_led.value = False
                sleep(1) # wait for 1 second


        def do_state_transition(self, to_state):
            state_trans_has_happened = False

            if self.state == States.SYSTEMS_CHECK:
                if to_state == States.ERROR_MODE:
                    self.state = States.ERROR_MODE
                    state_trans_has_happened = True
                elif to_state == States.DATA_MODE:
                    self.state = States.DATA_MODE
                    self._queue_short_beep()
                    state_trans_has_happened = True

            elif self.state == States.ERROR_MODE:
                if to_state == States.DATA_MODE:
                    self.state = States.DATA_MODE
                    self._queue_short_beep()
                    state_trans_has_happened = True

            elif self.state == States.DATA_MODE:
                if to_state == States.PREPERATION_MODE:
                    self.state = States.PREPERATION_MODE
                    self._queue_short_beep()
                    state_trans_has_happened = True
                elif to_state == States.ERROR_MODE:
                    self.state = States.ERROR_MODE
                    state_trans_has_happened = True

            if state_trans_has_happened:
                self.do_state_action()
                self._reset_state_timer()

        def check_if_pyro_should_be_fired(self):
            if self.state != States.LAUNCHED_MODE: # Not in launching state of the statediagram
                return False
            if self.LAUNCHED == False: # Has not launched yet
                return False
            if self.launched_time == 0: # The launchtimer has not been set yet
                return False
            if self.launched_time + self.PYRO_FIRE_DELAY_MS < round(time.monotonic()*1000): # The amount of time has passed
                return True
            else:
                return False

        def set_launched_time(self):
            if self.LAUNCHED == True:
                self.launched_time = round(time.monotonic()*1000)

        def _reset_state_timer(self):
            self.last_state_transition = round(time.monotonic()*1000)

        def _queue_short_beep(self):
            buzzer.append_buzzer_note(2000, 100)
            buzzer.append_buzzer_wait(100)
            buzzer.append_buzzer_note(2000, 100)
            buzzer.append_buzzer_wait(100)

        def _queue_long_beep(self):
            buzzer.append_buzzer_note(2000, 1000)
            buzzer.append_buzzer_wait(1000)

        def _battery_voltage_valid(self): # Todo: Make it depend on the battery configuration
            if get_vbat_voltage() > 3.0:
                return True
            else:
                return True