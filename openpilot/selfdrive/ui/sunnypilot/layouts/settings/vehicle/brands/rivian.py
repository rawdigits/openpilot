"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.selfdrive.ui.sunnypilot.layouts.settings.vehicle.brands.base import BrandSettings
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.sunnypilot.widgets.list_view import multiple_button_item_sp, toggle_item_sp


class RivianSettings(BrandSettings):
  def __init__(self):
    super().__init__()
    # yeet-angle-standalone: who owns set speed and follow gap, see RivianButtonSource in params_keys.h
    self.button_source_item = multiple_button_item_sp(
      title=lambda: tr("Wheel Buttons"),
      description="",
      buttons=[lambda: tr("Auto"), lambda: tr("Comma"), lambda: tr("Bridge")],
      button_width=300,
      callback=self._on_button_source_selected,
      param="RivianButtonSource",
      inline=False,
    )
    self.scroll_invert_toggle = toggle_item_sp(
      tr("Invert Follow Scroll"),
      tr("Comma only: swap which way the right scroll wheel moves the follow distance closer or farther."),
      param="RivianScrollInvert",
    )
    self.items = [self.button_source_item, self.scroll_invert_toggle]

  @staticmethod
  def _on_button_source_selected(index):
    ui_state.params.put("RivianButtonSource", index)

  def update_settings(self):
    source = ui_state.params.get("RivianButtonSource", return_default=True)
    source = source if source in (0, 1, 2) else 0
    descs = [
      tr("Auto: Comma when the longitudinal kit forwards the steering wheel buttons, Bridge otherwise."),
      tr("Comma: set speed and follow distance come only from the steering wheel buttons. " +
         "The bridge's set speed and follow level are ignored. Falls back to Bridge without forwarded buttons."),
      tr("Bridge: the TCM bridge sets speed and follow distance. " +
         "The wheel buttons only change the set speed while the bridge is offline or has no target."),
    ]
    self.button_source_item.set_description(descs[source])
    self.button_source_item.show_description(True)
    self.button_source_item.action_item.set_selected_button(source)
    has_long = ui_state.has_longitudinal_control
    self.button_source_item.set_visible(has_long)
    self.scroll_invert_toggle.set_visible(has_long and source != 2)
