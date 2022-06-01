# pylint: disable=no-member
"""Gamepad interface to controlller."""
from __future__ import annotations
import threading
import logging
import warnings
from typing import Any, Union, Callable
import atexit
import weakref
import json

from pyremoteplay.controller import Controller
from .mapping import AxisType, HatType, default_maps, dualshock4_map

try:
    import pygame
except ModuleNotFoundError:
    warnings.warn("pygame not installed")

_LOGGER = logging.getLogger(__name__)

DEFAULT_DEADZONE = 0.1


def _format_json_keys(data: dict):
    """Format number JSON keys to int."""
    return {
        int(key)
        if key.isdigit()
        else key.lower(): val.upper()
        if isinstance(val, str)
        else val
        for key, val in data.items()
    }


def __init_pygame():
    pygame.init()
    pygame.joystick.init()
    pygame.event.set_allowed(
        [
            pygame.JOYBUTTONDOWN,
            pygame.JOYBUTTONUP,
            pygame.JOYAXISMOTION,
            pygame.JOYHATMOTION,
            pygame.JOYDEVICEADDED,
            pygame.JOYDEVICEREMOVED,
        ]
    )


__init_pygame()


class Gamepad:
    """Gamepad. Wraps a PyGame Joystick to interface with RP Controller.
    Instances are not re-entrant after calling `close`.
    Creating an instance automatically starts the event loop.
    Joystick instances are closed automatically when deallocated.
    If creating a new instance with the same joystick as an existing gamepad,
    the existing gamepad will be returned. This ensures that only one gamepad instance
    will exist per joystick.

    :param joystick: Either the id from `pygame.joystick.Joystick.get_instance_id()` or an instance of `pygame.joystick.Joystick`.
    """

    __thread: threading.Thread = None
    __stop_event = threading.Event()
    __refs = set()
    __cb_refs = set()

    @staticmethod
    def joysticks() -> list[pygame.joystick.Joystick]:
        """Return All Joysticks."""
        joysticks = [
            pygame.joystick.Joystick(index)
            for index in range(pygame.joystick.get_count())
        ]
        return joysticks

    @staticmethod
    def get_all() -> list[Gamepad]:
        """Return All Gamepads."""
        return [Gamepad(joystick) for joystick in Gamepad.joysticks()]

    @staticmethod
    def check_map(mapping: dict) -> bool:
        """Check map. Return True if valid."""
        is_valid = True
        valid_buttons = Controller.buttons()
        buttons = mapping["button"]
        for button in buttons.values():
            if button is None or button == "":
                continue
            button = button.upper()
            if button not in valid_buttons:
                _LOGGER.error("Invalid button: %s", button)
                is_valid = False

        valid_axes = [item.name for item in AxisType]
        axes = list(mapping["axis"].values())
        hats = list(mapping["hat"].values())
        valid_hats = [item.name for item in HatType]
        for group in hats:
            for hat_type in group:
                if hat_type not in valid_hats:
                    _LOGGER.error("Invalid Hat Type: %s", hat_type)
                    is_valid = False
            axes.extend(list(group.values()))

        for axis in axes:
            if axis is None or axis == "":
                continue
            axis = axis.upper()
            if axis in valid_buttons:
                continue
            if axis not in valid_axes:
                _LOGGER.error("Invalid axis: %s", axis)
                is_valid = False
        return is_valid

    @classmethod
    def register(cls, callback: Callable[[pygame.event.Event], None]):
        """Register a callback for device added/removed events."""
        if not isinstance(callback, Callable):
            raise TypeError(f"Expected a callable. Got: {type(callback)}")
        ref = weakref.ref(callback)
        cls.__cb_refs.add(ref)

    @classmethod
    def unregister(cls, callback: Callable[[pygame.event.Event], None]):
        """Unregister a callback from receiving device added/removed events."""
        for ref in cls.__cb_refs:
            if ref() == callback:
                try:
                    cls.__cb_refs.remove(ref)
                except KeyError:
                    pass

    @classmethod
    def start(cls):
        """Start Gamepad loop. Called automatically when an instance is created."""
        if cls.running():
            return
        _LOGGER.debug("Starting Gamepad loop")
        cls.__stop_event.clear()
        cls.__thread = threading.Thread(target=cls.__worker, daemon=True)
        cls.__thread.start()
        atexit.register(cls.stop)

    @classmethod
    def stop(cls):
        """Stop Gamepad loop.
        Called automatically when all instances have called `quit` or when all instances are deleted.
        Any running instances will have quit called.
        """
        for ref in list(cls.__refs):
            instance = ref()
            instance.close()
        cls.__stop_event.set()
        cls.__thread = None
        _LOGGER.info("Stopped Gamepad loop")

    @classmethod
    def running(cls) -> bool:
        """Return True if running."""
        return cls.__thread is not None and cls.__thread.is_alive()

    @staticmethod
    def __check_joystick(
        joystick: Union[int, pygame.joystick.Joystick]
    ) -> pygame.joystick.Joystick:
        if isinstance(joystick, int):
            joystick = pygame.joystick.Joystick(joystick)
        else:
            # Hack to check we do have a Joystick object
            try:
                old_id = joystick.get_instance_id()
                joystick = pygame.joystick.Joystick(old_id)
                new_id = joystick.get_instance_id()
                if old_id != new_id:
                    raise RuntimeError(f"Joystick ID changed from {old_id} to {new_id}")
            except AttributeError as error:
                raise TypeError(
                    f"Expected an int or an instance of 'pygame.joystick.Joystick'. Got: {type(joystick)}"
                ) from error
        return joystick

    @classmethod
    def __worker(cls):
        while not cls.__stop_event.is_set():
            try:
                cls.__handle_events()
            except Exception as error:  # pylint: disable=broad-except
                _LOGGER.info("Error Handling Events: %s", error)

    @classmethod
    def __handle_events(cls):
        event = pygame.event.wait(timeout=1)
        if event.type == pygame.NOEVENT or not hasattr(event, "instance_id"):
            return
        if event.type in (pygame.JOYDEVICEREMOVED, pygame.JOYDEVICEADDED):
            if event.type == pygame.JOYDEVICEREMOVED:
                for ref in list(cls.__refs):
                    instance = ref()
                    if instance:
                        if event.instance_id == instance.instance_id:
                            _LOGGER.debug("Gamepad closed: Joystick removed")
                            instance.close()

            for ref in list(cls.__cb_refs):
                callback = ref()
                if callback:
                    callback(event)
            return

        for ref in cls.__refs:
            instance = ref()
            if instance.instance_id == event.instance_id:
                instance._handle_event(event)  # pylint: disable=protected-access

    @classmethod
    def __add_ref(cls, instance: Gamepad):
        ref = weakref.ref(instance)
        cls.__refs.add(ref)
        cls.start()

    @classmethod
    def __del_ref(cls, instance: Gamepad):
        for ref in list(cls.__refs):
            if ref() == instance:
                try:
                    cls.__refs.remove(ref)
                except KeyError:
                    pass

    def __new__(cls, joystick: Union[int, pygame.joystick.Joystick]):
        """Only allow one instance."""
        joystick = cls.__check_joystick(joystick)
        instance_id = joystick.get_instance_id()
        for ref in cls.__refs:
            instance = ref()
            if instance.instance_id == instance_id:
                return instance

        instance = super().__new__(cls)
        cls.__add_ref(instance)
        return instance

    def __del__(self):
        self.close()

    def __init__(self, joystick: Union[int, pygame.joystick.Joystick]):
        self._joystick = self.__check_joystick(joystick)
        self._controller = None
        self._deadzone = None
        self._mapping = {}
        self._last_button = ()
        self._last_hat = {}

        self.mapping = self.default_map()
        self.deadzone = DEFAULT_DEADZONE

    def default_map(self) -> dict:
        """Return Default Map."""
        mapping = dualshock4_map()
        if self._joystick:
            mapping = default_maps().get(self._joystick.get_name())
        return mapping

    def close(self):
        """Close. Quit handling events."""
        self.controller = None
        if self._joystick is not None and self._joystick.get_init():
            _LOGGER.info("Gamepad with joystick closed: %s", self._joystick.get_guid())
            self._joystick.quit()
        self._joystick = None
        Gamepad.__del_ref(self)

    def get_hat(self, hat: int) -> HatType:
        """Get Hat."""
        if not self.available:
            raise RuntimeError("Joystick Not Available")
        values = self._joystick.get_hat(hat)
        return self._parse_hat(values)

    def get_button(self, button: int) -> int:
        """Return button value."""
        if not self.available:
            raise RuntimeError("Joystick Not Available")
        return self._joystick.get_button(button)

    def get_axis(self, axis: int) -> float:
        """Return axis value."""
        if not self.available:
            raise RuntimeError("Joystick Not Available")
        return self._joystick.get_axis(axis)

    def _parse_hat(self, values: tuple[float, float]) -> HatType:
        """Parse hat value. Return enum."""
        # Only one hat direction can be active at a time
        if not values:
            return None
        values = (int(values[0]), int(values[1]))
        if values == (-1, 0):
            hat_type = HatType.left
        elif values == (1, 0):
            hat_type = HatType.right
        elif values == (0, -1):
            hat_type = HatType.down
        elif values == (0, 1):
            hat_type = HatType.up
        else:
            hat_type = None
        return hat_type

    def _send_button(self, button: str, action: Controller.ButtonAction):
        current = (button, action)
        if self._last_button == current:
            return
        self._last_button = current
        _LOGGER.debug("Button: %s, Action: %s", button, action)
        if self.controller:
            self.controller.button(button, action)

    def _send_stick(self, stick: str, axis: str, value: float):
        if self.controller:
            self.controller.stick(stick, axis=axis, value=value)

    def _handle_event(self, event: pygame.event.Event):
        """Handle event."""
        if not self.controller:
            return
        if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
            self._handle_button_event(event)
        elif event.type in (
            pygame.JOYAXISMOTION,
            pygame.JOYHATMOTION,
        ):
            self._handle_motion_event(event)

    def _handle_button_event(self, event: pygame.event.Event):
        """Handle Button Event."""
        action = None
        if event.type == pygame.JOYBUTTONDOWN:
            action = Controller.ButtonAction.PRESS
        elif event.type == pygame.JOYBUTTONUP:
            action = Controller.ButtonAction.RELEASE
        else:
            raise RuntimeError("Could not determine Button Action")

        button = self._mapping["button"].get(event.button)
        if action is None or not button:
            return
        self._send_button(button, action)

    def _handle_motion_event(self, event: pygame.event.Event):
        """Handle Motion Event."""
        name = None
        if event.type == pygame.JOYAXISMOTION:
            name = self._mapping["axis"].get(event.axis)
        elif event.type == pygame.JOYHATMOTION:
            self._handle_hat(event)
            return

        if not name:
            return

        name = name.upper()
        value = min(max(event.value, -1.0), 1.0)

        if name in Controller.buttons():
            # Handle Analog Trigger
            # TODO: This will be weird if analog stick is mapped to this
            action = (
                Controller.ButtonAction.PRESS
                if value > -1.0 + self.deadzone
                else Controller.ButtonAction.RELEASE
            )
            self._send_button(name, action)
            return

        try:
            stick, axis = name.split("_")
        except ValueError:
            _LOGGER.warning("Could not determine stick and axis from: %s", name)
            return

        if abs(event.value) < self.deadzone:
            value = 0.0
        self._send_stick(stick, axis, value)

    def _handle_hat(self, event: pygame.event.Event):
        assert event.type == pygame.JOYHATMOTION
        hat_map = self._mapping["hat"].get(event.hat)
        if not hat_map:
            return
        values = tuple(event.value)
        action = Controller.ButtonAction.PRESS
        name = None

        hat_type = self._parse_hat(values)
        if hat_type is None:
            hat_type = self._last_hat.get(event.hat)
            action = Controller.ButtonAction.RELEASE

        if hat_type is None:
            return
        name = hat_map.get(hat_type.name)
        if name is None:
            return
        self._last_hat[event.hat] = hat_type
        self._send_button(name, action)

    def get_config(self) -> dict[str, int]:
        """Return Joystick config."""
        if not self.available:
            raise RuntimeError("Joystick Not Available")
        return {
            "button": self._joystick.get_numbuttons(),
            "axis": self._joystick.get_numaxes(),
            "hat": self._joystick.get_numhats(),
        }

    @property
    def controller(self) -> Controller:
        """Return Controller."""
        return self._controller

    @controller.setter
    def controller(self, controller: Controller):
        """Set Controller."""
        if controller is not None and not isinstance(controller, Controller):
            raise TypeError(
                f"Expected instance of {Controller}; Got type {type(controller)}"
            )
        self._controller = controller

    @property
    def deadzone(self) -> float:
        """Return stick deadzone. Will be positive."""
        return self._deadzone

    @deadzone.setter
    def deadzone(self, deadzone: float):
        """Set Deadzone."""
        deadzone = abs(float(deadzone))
        if deadzone >= 1.0:
            raise ValueError("Deadzone must be less than 1.0")
        self._deadzone = deadzone

    @property
    def mapping(self) -> dict:
        """Return mapping."""
        return self._mapping

    @mapping.setter
    def mapping(self, mapping: dict):
        """Set Mapping."""
        mapping = json.dumps(mapping)
        mapping = json.loads(mapping, object_hook=_format_json_keys)
        if not Gamepad.check_map(mapping):
            raise ValueError("Invalid Mapping")
        self._mapping = mapping

    @property
    def instance_id(self) -> int:
        """Return instance id."""
        if not self._joystick:
            return None
        return self._joystick.get_instance_id()

    @property
    def guid(self) -> str:
        """Return GUID."""
        if not self._joystick:
            return None
        return self._joystick.get_guid()

    @property
    def name(self) -> str:
        """Return Name."""
        if not self._joystick:
            return None
        return self._joystick.get_name()

    @property
    def available(self) -> bool:
        """Return True if available."""
        if not self._joystick:
            return False
        return self._joystick.get_init()
