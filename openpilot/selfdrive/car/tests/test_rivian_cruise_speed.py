import time
from unittest.mock import patch

from opendbc.car import Bus, gen_empty_fingerprint
from opendbc.car.rivian.interface import CarInterface
from opendbc.car.rivian.rivian_bridge import RivianBridge
from opendbc.car.rivian.values import CAR
from openpilot.cereal import messaging
from openpilot.common.constants import CV
from openpilot.common.test import OpenpilotTestCase
from openpilot.selfdrive.car.cruise import VCruiseHelper
from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner


class TestRivianCruiseSpeed(OpenpilotTestCase):
  def test_dash_set_speed_reaches_planner_in_true_frame(self):
    fingerprint = gen_empty_fingerprint()
    fingerprint[0][0x321] = 8
    fingerprint[1].update({0x1310: 8, 0x131a: 8})
    cp = CarInterface.get_params(CAR.RIVIAN_R1, fingerprint, [], True, False, False)
    cp_sp = CarInterface.get_params_sp(cp, CAR.RIVIAN_R1, fingerprint, [], True, False, False)
    self.assertTrue(cp.pcmCruise)
    self.assertTrue(cp_sp.pcmCruiseSpeed)

    dash_target = 70. * CV.MPH_TO_MS
    ratio = 0.96
    true_target = dash_target * ratio
    bridge = RivianBridge(start=False)
    bridge.state = {"stale": False, "set_speed_ms": dash_target}
    bridge._received_at = time.monotonic()
    with patch("opendbc.car.rivian.carstate.RivianBridge", return_value=bridge):
      ci = CarInterface(cp, cp_sp)
    ci.can_parsers[Bus.pt].vl["ESP_Status"]["ESP_Vehicle_Speed"] = true_target * CV.MS_TO_KPH
    ci.can_parsers[Bus.adas].vl["Cluster"].update({"Cluster_Unit": 1, "Cluster_VehicleSpeed": 70.})
    ci.can_parsers[Bus.cam].vl["ACM_Status"]["ACM_FeatureStatus"] = 1
    ci.can_parsers[Bus.alt].vl["WheelButtons_Fwd"]["RightButton_Scroll"] = 255
    cs, _ = ci.update([])

    # Follow card's existing publication path; the HUD reads vCruiseCluster.
    helper = VCruiseHelper(cp, cp_sp)
    helper.update_v_cruise(cs, enabled=True, is_metric=False)
    cs.vCruise = float(helper.v_cruise_kph)
    cs.vCruiseCluster = float(helper.v_cruise_cluster_kph)
    self.assertAlmostEqual(cs.vCruiseCluster * CV.KPH_TO_MPH, 70., places=5)
    self.assertAlmostEqual(cs.vEgoRaw, true_target, places=5)
    self.assertAlmostEqual(cs.vEgo, true_target, places=5)

    services = ("radarState", "controlsState", "selfdriveState", "carControl", "vehicleParameters",
                "modelV2", "carStateSP", "liveMapDataSP", "gpsLocation")
    sm = {service: getattr(messaging.new_message(service), service) for service in services}
    sm["carState"] = cs.as_reader()
    sm["controlsState"].longControlState = "pid"
    sm["selfdriveState"].enabled = True
    sm["carControl"].enabled = True
    sm["modelV2"].velocity.x = [true_target] * 33
    sm["modelV2"].orientationRate.z = [0.01] * 33
    sm["modelV2"].position.x = [float(i) for i in range(33)]
    planner = LongitudinalPlanner(cp, cp_sp, init_v=true_target)
    planner.update(sm)
    self.assertAlmostEqual(planner.output_v_target, true_target, places=5)
    self.assertAlmostEqual(planner.a_cruise, 0., places=5)
