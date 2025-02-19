from __future__ import annotations

import codecs
import logging
import re
from typing import TYPE_CHECKING

from ...utils.configparser import CaseSensitiveConfigParser
from .dolphinTriforcePaths import DOLPHIN_TRIFORCE_CONFIG

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from ...controller import Controller, ControllerMapping
    from ...Emulator import Emulator

_logger = logging.getLogger(__name__)

# Create the controller configuration file
def generateControllerConfig(system: Emulator, playersControllers: ControllerMapping, rom: Path) -> None:

    generateHotkeys(playersControllers)
    generateControllerConfig_arcade(system, playersControllers, rom) # Pass ROM name to allow for per ROM configuration

def generateControllerConfig_arcade(system: Emulator, playersControllers: ControllerMapping, rom: Path) -> None:
    # Exclude Buttons/Z from mapping as that is the test mode. Buttons/X is used to insert credit. Therefore it is set to Select.
    arcadeMapping = {
        'a':             'Buttons/B',
        'b':             'Buttons/A',
        'select':        'Buttons/X',
        'x':             'Buttons/Y',
        'start':         'Buttons/Start',
        'pageup':        'Triggers/L',
        'pagedown':      'Triggers/R',
        'l2':            'Triggers/L',
        'r2':            'Triggers/R',
        'up':            'D-Pad/Up',
        'down':          'D-Pad/Down',
        'left':          'D-Pad/Left',
        'right':         'D-Pad/Right',
        'joystick1up':   'Main Stick/Up',
        'joystick1left': 'Main Stick/Left',
        'joystick2up':   'C-Stick/Up',
        'joystick2left': 'C-Stick/Left',
        'hotkey':        'Buttons/Hotkey'
    }
    # Reversed directional mappings for Virtua Striker games
    virtuaMapping = {
        'a':             'Buttons/B',
        'b':             'Buttons/A',
        'select':        'Buttons/X',
        'x':             'Buttons/Y',
        'start':         'Buttons/Start',
        'pageup':        'Triggers/L',
        'pagedown':      'Triggers/R',
        'l2':            'Triggers/L',
        'r2':            'Triggers/R',
        'up':            'D-Pad/Up',
        'down':          'D-Pad/Down',
        'left':          'D-Pad/Left',
        'right':         'D-Pad/Right',
        'joystick1up':   'Main Stick/Left',
        'joystick1left': 'Main Stick/Down',
        'joystick2up':   'C-Stick/Up',
        'joystick2left': 'C-Stick/Left',
        'hotkey':        'Buttons/Hotkey'
    }

    # Applies the opposing directional value we don't have
    arcadeReverseAxes = {
        'Main Stick/Up':   'Main Stick/Down',
        'Main Stick/Left': 'Main Stick/Right',
        'C-Stick/Up':      'C-Stick/Down',
        'C-Stick/Left':    'C-Stick/Right'
    }
    # Handles Virtua Striker also
    virtuaReverseAxes = {
        'Main Stick/Down':   'Main Stick/Up',
        'Main Stick/Left': 'Main Stick/Right',
        'C-Stick/Up':      'C-Stick/Down',
        'C-Stick/Left':    'C-Stick/Right'
    }

    # If joystick1up is missing on the pad, use up instead, and if l2/r2 is missing, use l1/r1
    arcadeReplacements = {
        'joystick1up':    'up',
        'joystick1left':  'left',
        'joystick1down':  'down',
        'joystick1right': 'right',
        'l2':             'pageup',
        'r2':             'pagedown'
    }

    # This section allows a per ROM override of the default key options.
    configname = rom.with_name(rom.name + ".cfg")       # Define ROM configuration name
    if configname.is_file():  # File exists
        import ast
        with configname.open() as cconfig:
            line = cconfig.readline()
            while line:
                entry = "{" + line + "}"
                res = ast.literal_eval(entry)
                arcadeMapping.update(res)
                line = cconfig.readline()

    if "virtua" in rom.name.lower():
        generateControllerConfig_any(system, playersControllers, "Config/GCPadNew.ini", "GCPad", virtuaMapping, virtuaReverseAxes, arcadeReplacements)
    else:
        generateControllerConfig_any(system, playersControllers, "Config/GCPadNew.ini", "GCPad", arcadeMapping, arcadeReverseAxes, arcadeReplacements)

def generateHotkeys(playersControllers: ControllerMapping) -> None:
    configFileName = DOLPHIN_TRIFORCE_CONFIG / "Config" / "Hotkeys.ini"
    f = codecs.open(str(configFileName), "w", encoding="utf_8")

    hotkeysMapping = {
        'a':             'Keys/Reset',
        'b':             'Keys/Toggle Pause',
        'x':             'Keys/Load from selected slot',
        'y':             'Keys/Save to selected slot',
        'r2':            None,
        'start':         'Keys/Exit',
        'pageup':        'Keys/Take Screenshot',
        'pagedown':      'Keys/Toggle 3D Side-by-side',
        'up':            'Keys/Select State Slot 1',
        'down':          'Keys/Select State Slot 2',
        'left':          None,
        'right':         None,
        'joystick1up':   None,
        'joystick1left': None,
        'joystick2up':   None,
        'joystick2left': None
    }

    nplayer = 1
    for playercontroller, pad in sorted(playersControllers.items()):
        if nplayer == 1:
            f.write("[Hotkeys1]" + "\n")
            f.write("Device = SDL/0/" + pad.real_name.strip() + "\n")
            # Search the hotkey button
            hotkey = None
            if "hotkey" not in pad.inputs:
                return
            hotkey = pad.inputs["hotkey"]
            if hotkey.type != "button":
                return

            for x in pad.inputs:
                print
                input = pad.inputs[x]
                keyname = None
                if input.name in hotkeysMapping:
                    keyname = hotkeysMapping[input.name]
                # Write the configuration for this key
                if keyname is not None:
                    write_key(f, keyname, input.type, input.id, input.value, pad.axis_count, False, hotkey.id)

        nplayer += 1

    f.write
    f.close()

def generateControllerConfig_any(system: Emulator, playersControllers: ControllerMapping, filename: str, anyDefKey: str, anyMapping: dict[str, str], anyReverseAxes: Mapping[str, str], anyReplacements: Mapping[str, str] | None, extraOptions: Mapping[str, str] = {}) -> None:
    configFileName = DOLPHIN_TRIFORCE_CONFIG / filename
    f = codecs.open(str(configFileName), "w", encoding="utf_8")
    nplayer = 1
    nsamepad = 0
    # In case of two pads having the same name, dolphin wants a number to handle this
    double_pads = dict()

    for playercontroller, pad in sorted(playersControllers.items()):
        # Handle x pads having the same name
        if pad.real_name.strip() in double_pads:
            nsamepad = double_pads[pad.real_name.strip()]
        else:
            nsamepad = 0

        double_pads[pad.real_name.strip()] = nsamepad+1
        f.write("[" + anyDefKey + str(nplayer) + "]" + "\n")
        f.write("Device = SDL/" + str(nsamepad).strip() + "/" + pad.real_name.strip() + "\n")

        if system.isOptSet("triforce_pad_profiles") and system.getOptBoolean("triforce_pad_profiles") == True:
            if not generateControllerConfig_any_from_profiles(f, pad):
                generateControllerConfig_any_auto(f, pad, anyMapping, anyReverseAxes, anyReplacements, extraOptions, system)
        else:
            generateControllerConfig_any_auto(f, pad, anyMapping, anyReverseAxes, anyReplacements, extraOptions, system)
        # Rumble option
        if system.isOptSet("triforce_rumble"):
            f.write(f"Rumble/Motor = {system.config['triforce_rumble']}\n")
        else:
            f.write("Rumble/Motor = \n")
        nplayer += 1

    f.write
    f.close()

def generateControllerConfig_any_auto(f: codecs.StreamReaderWriter, pad: Controller, anyMapping: dict[str, str], anyReverseAxes: Mapping[str, str], anyReplacements: Mapping[str, str] | None, extraOptions: Mapping[str, str], system: Emulator) -> None:
    for opt in extraOptions:
        f.write(opt + " = " + extraOptions[opt] + "\n")
    # Recompute the mapping according to available buttons on the pads and the available replacements
    currentMapping = anyMapping
    # Apply replacements
    if anyReplacements is not None:
        for x in anyReplacements:
            if x not in pad.inputs and x in currentMapping:
                currentMapping[anyReplacements[x]] = currentMapping[x]
                if x == "joystick1up":
                    currentMapping[anyReplacements["joystick1down"]] = anyReverseAxes[currentMapping["joystick1up"]]
                if x == "joystick1left":
                    currentMapping[anyReplacements["joystick1right"]] = anyReverseAxes[currentMapping["joystick1left"]]
                if x == "joystick2up":
                    currentMapping[anyReplacements["joystick2down"]] = anyReverseAxes[currentMapping["joystick2up"]]
                if x == "joystick2left":
                    currentMapping[anyReplacements["joystick2right"]] = anyReverseAxes[currentMapping["joystick2left"]]

    for x in pad.inputs:
        input = pad.inputs[x]
        keyname = None
        if input.name in currentMapping:
            keyname = currentMapping[input.name]
        # Write the configuration for this key
        if keyname is not None:
            if 'Triggers' in keyname and input.type == 'axis':
                write_key(f, keyname + '-Analog', input.type, input.id, input.value, pad.axis_count, False, None)
            else:
                write_key(f, keyname, input.type, input.id, input.value, pad.axis_count, False, None)
        # Write the 2nd part
        if input.name in { "joystick1up", "joystick1left", "joystick2up", "joystick2left"} and keyname is not None:
            write_key(f, anyReverseAxes[keyname], input.type, input.id, input.value, pad.axis_count, True, None)

def generateControllerConfig_any_from_profiles(f: codecs.StreamReaderWriter, pad: Controller) -> bool:
    for profileFile in (DOLPHIN_TRIFORCE_CONFIG / "Config" / "Profiles" / "GCPad").glob("*.ini"):
        try:
            _logger.debug("Looking profile : %s", profileFile)
            profileConfig = CaseSensitiveConfigParser(interpolation=None)
            profileConfig.read(profileFile)
            profileDevice = profileConfig.get("Profile","Device")
            _logger.debug("Profile device : %s", profileDevice)
            deviceVals = re.match("^([^/]*)/[0-9]*/(.*)$", profileDevice)
            if deviceVals is not None:
                if deviceVals.group(1) == "SDL" and deviceVals.group(2).strip() == pad.real_name.strip():
                    _logger.debug("Eligible profile device found")
                    for key, val in profileConfig.items("Profile"):
                        if key != "Device":
                            f.write(f"{key} = {val}\n")
                    return True
        except:
            _logger.error("profile %s : FAILED", profileFile)

    return False

def write_key(f: codecs.StreamReaderWriter, keyname: str, input_type: str, input_id: str, input_value: str, input_global_id: int | None, reverse: bool, hotkey_id: str | None) -> None:
    f.write(keyname + " = ")
    if hotkey_id is not None:
        f.write("`Button " + str(hotkey_id) + "` & ")
    f.write("`")
    if input_type == "button":
        f.write("Button " + str(input_id))
    elif input_type == "hat":
        if input_value == "1":   # up
            f.write("Hat 0 N")
        elif input_value == "4": # down
            f.write("Hat 0 S")
        elif input_value == "8": # left
            f.write("Hat 0 W")
        elif input_value == "2": # right
            f.write("Hat 0 E")
    elif input_type == "axis":
        if (reverse and input_value == "-1") or (not reverse and input_value == "1") or (not reverse and input_value == "0"):
            if "-Analog" in keyname:
                f.write("Full Axis " + str(input_id) + "+")
            else:
                f.write("Axis " + str(input_id) + "+")
        else:
            f.write("Axis " + str(input_id) + "-")
    f.write("`\n")
