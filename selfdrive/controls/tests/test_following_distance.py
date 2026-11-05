import pytest
import itertools
from parameterized import parameterized_class

from cereal import log

from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import desired_follow_distance, get_T_FOLLOW
from openpilot.selfdrive.test.longitudinal_maneuvers.maneuver import Maneuver


def run_following_distance_simulation(v_lead, t_end=100.0, e2e=False, personality=0):
  man = Maneuver(
    '',
    duration=t_end,
    initial_speed=float(v_lead),
    lead_relevancy=True,
    initial_distance_lead=100,
    speed_lead_values=[v_lead],
    breakpoints=[0.],
    e2e=e2e,
    personality=personality,
  )
  valid, output = man.evaluate()
  assert valid
  return output[-1,2] - output[-1,1]


# Known failures from the yeetfollow tuning (shorter stop distance), see automotive/openpilot#4.
# Keyed by (e2e, personality, speed); strict so a case that starts passing is noticed.
KNOWN_FAILURE_REASON = "known: yeetfollow tuning, see automotive/openpilot#4"
KNOWN_FAILURES = {
  (True, log.LongitudinalPersonality.standard, 0),
  (True, log.LongitudinalPersonality.aggressive, 0),
  (False, log.LongitudinalPersonality.standard, 0),
  (False, log.LongitudinalPersonality.aggressive, 0),
}


@parameterized_class(("e2e", "personality", "speed"), itertools.product(
                      [True, False], # e2e
                      [log.LongitudinalPersonality.relaxed, # personality
                       log.LongitudinalPersonality.standard,
                       log.LongitudinalPersonality.aggressive],
                      [0,10,35])) # speed
class TestFollowingDistance:
  def test_following_distance(self, request):
    if (self.e2e, self.personality, self.speed) in KNOWN_FAILURES:
      request.applymarker(pytest.mark.xfail(strict=True, reason=KNOWN_FAILURE_REASON))
    v_lead = float(self.speed)
    simulation_steady_state = run_following_distance_simulation(v_lead, e2e=self.e2e, personality=self.personality)
    correct_steady_state = desired_follow_distance(v_lead, v_lead, get_T_FOLLOW(self.personality))
    err_ratio = 0.2 if self.e2e else 0.1
    assert simulation_steady_state == pytest.approx(correct_steady_state, abs=err_ratio * correct_steady_state + .5)
