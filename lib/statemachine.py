import time
import buzzer
import external
from measure import get_vbat_voltage

class States():
        SYSTEMS_CHECK = 0
        ERROR_MODE = 1
        SEARCH_MODE = 2

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
                    self.do_state_transition(States.SEARCH_MODE)

            elif self.state == States.ERROR_MODE:
                if self._battery_voltage_valid():
                    self.do_state_transition(States.SEARCH_MODE)

            elif self.state == States.SEARCH_MODE:
                if not self._battery_voltage_valid():
                    self.do_state_transition(States.ERROR_MODE)

        def do_state_action(self):
            if self.state == States.SYSTEMS_CHECK:
                external.neopixel_disable()
            elif self.state == States.ERROR_MODE:
                # self._queue_long_beep()
                external.neopixel_set_rgb(255,0,0) #RED
            elif self.state == States.SEARCH_MODE:
                external.neopixel_set_rgb(0,0,255) #BLUE

        def do_state_transition(self, to_state):
            state_trans_has_happened = False

            if self.state == States.SYSTEMS_CHECK:
                if to_state == States.ERROR_MODE:
                    self.state = States.ERROR_MODE
                    state_trans_has_happened = True
                elif to_state == States.SEARCH_MODE:
                    self.state = States.SEARCH_MODE
                    self._queue_short_beep()
                    state_trans_has_happened = True

            elif self.state == States.ERROR_MODE:
                if to_state == States.SEARCH_MODE:
                    self.state = States.SEARCH_MODE
                    self._queue_short_beep()
                    state_trans_has_happened = True

            elif self.state == States.SEARCH_MODE:
                if to_state == States.ERROR_MODE:
                    self.state = States.ERROR_MODE
                    state_trans_has_happened = True

            if state_trans_has_happened:
                for _ in range(self.state):
                    self._queue_short_beep()
                self.do_state_action()
                self._reset_state_timer()

        # def check_if_pyro_should_be_fired(self):
            # return False

        # def set_launched_time(self):
        #     if self.LAUNCHED == True:
        #         self.launched_time = round(time.monotonic()*1000)

        # def _reset_state_timer(self):
        #     self.last_state_transition = round(time.monotonic()*1000)

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
                return False
