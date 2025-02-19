#
# This file is part of the batocera distribution (https://batocera.org).
# Copyright (c) 2025+.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# YOU MUST KEEP THIS HEADER AS IT IS
#

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from ... import Command
from ...controller import generate_sdl_game_controller_config
from ..Generator import Generator

_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ...types import HotkeysContext

class TR2XGenerator(Generator):

    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "tr2x",
            "keys": { "exit": ["KEY_LEFTALT", "KEY_F4"], "save_state": "KEY_F5", "restore_state": "KEY_F6" }
        }

    def generate(self, system, rom, playersControllers, metadata, guns, wheels, gameResolution):
        tr2xRomPath = Path(rom).parent
        tr2xConfigPath = tr2xRomPath / "cfg" / "TR2X.json5"
        tr2xSourcePath = Path("/usr/bin/tr2x")

        # Copy files & folders if they don’t exist
        for item in tr2xSourcePath.iterdir():
            dest = tr2xRomPath / item.name
            try:
                if item.is_dir():
                    if not dest.exists():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            except PermissionError as e:
                _logger.debug("Permission error while copying %s -> %s: %s", item, dest, e)
            except Exception as e:
                _logger.debug("Error copying %s -> %s: %s", item, dest, e)

        # Configuration
        tr2xConfigPath.parent.mkdir(parents=True, exist_ok=True)
        config_data = {}

        if tr2xConfigPath.exists():
            try:
                with open(tr2xConfigPath, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except json.JSONDecodeError:
                _logger.debug("Invalid JSON format in %s, overwriting with default settings.", tr2xConfigPath)

        # Update settings
        config_data.update(
            {
                "is_fullscreen": True,
                "width": gameResolution["width"],
                "height": gameResolution["height"]
            }
        )

        with open(tr2xConfigPath, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        commandArray = [tr2xRomPath / "TR2X"]

        return Command.Command(
            array=commandArray,
            env={
                "SDL_GAMECONTROLLERCONFIG": generate_sdl_game_controller_config(playersControllers),
                "SDL_JOYSTICK_HIDAPI": "0"
            }
        )

    def getInGameRatio(self, config, gameResolution, rom):
        if gameResolution["width"] / float(gameResolution["height"]) > ((16.0 / 9.0) - 0.1):
            return 16/9
        return 4/3
