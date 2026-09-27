"""
Multi-Alarm Clock Application
==============================

MULTI_alarm_ system

author : AKRATI SHARMA

    python alarm_clock.py
"""

import time
import datetime
import json
import logging
import os
import re
import sys


try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False



# Constants


DATA_DIR = "."
ALARMS_FILE = os.path.join(DATA_DIR, "alarms.json")
LOG_FILE = os.path.join(DATA_DIR, "alarm_clock.log")
DEFAULT_SOUND_FILE = os.path.join(DATA_DIR, "song.mp3")

DEFAULT_MAX_SNOOZES = 3
DEFAULT_SNOOZE_MINUTES = 5
ALARM_RING_SECONDS = 10

VALID_DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

TIME_INPUT_FORMATS = ("%H:%M:%S", "%H:%M")



# Logging setup


def setup_logging():
    """
    Configure a logger that writes to both the console and a log file.

    Returns the configured logger instance so callers can use it directly
    instead of relying on the root logger.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    logger = logging.getLogger("alarm_clock")
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if this is called more than once.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()



# Validation helpers


def normalize_time_format(time_str):
    """
    Parse a user-supplied time string in a forgiving way and return it
    normalized to zero-padded 24-hour "HH:MM:SS" format, or None if it
    can't be parsed as a valid time at all.

    Accepts single or double digit hours, with or without seconds:
    "7:30", "07:30", "7:30:00", and "07:30:00" are all valid and all
    normalize to "07:30:00".
    """
    if not isinstance(time_str, str):
        return None

    cleaned = time_str.strip()
    for fmt in TIME_INPUT_FORMATS:
        try:
            parsed = datetime.datetime.strptime(cleaned, fmt)
            return parsed.strftime("%H:%M:%S")
        except ValueError:
            continue
    return None


def validate_time_format(time_str):
    """
    Return True if time_str can be parsed as a 24-hour time (see
    normalize_time_format for the accepted formats).
    """
    return normalize_time_format(time_str) is not None


def validate_days(days_str):
    """
    Parse a comma-separated list of day abbreviations (e.g. "mon,wed,fri")
    and return a list of valid, lower-cased day strings.

    An empty string means "every day" is not implied here; callers should
    treat an empty list as "no repeat / one-time alarm".
    Invalid day names are silently skipped and logged as a warning.
    """
    if not days_str:
        return []

    days = []
    for part in days_str.split(","):
        cleaned = part.strip().lower()
        if not cleaned:
            continue
        if cleaned in VALID_DAYS:
            days.append(cleaned)
        else:
            logger.warning(f"Ignoring unrecognized day: '{cleaned}'")
    return days


def prompt_for_valid_time(prompt_text="Enter the alarm time (HH:MM or HH:MM:SS): "):
    """
    Repeatedly prompt the user until a valid time is entered, returning
    it normalized to "HH:MM:SS".
    """
    while True:
        candidate = input(prompt_text).strip()
        normalized = normalize_time_format(candidate)
        if normalized is not None:
            return normalized
        print(
            "Invalid time format. Use 24-hour HH:MM or HH:MM:SS, "
            "e.g. 7:30 or 07:30:00."
        )


def prompt_for_days(prompt_text=None):
    """
    Prompt the user for an optional list of repeat days.
    """
    if prompt_text is None:
        prompt_text = (
            "Enter repeat days as comma-separated values "
            "(mon,tue,wed,thu,fri,sat,sun), or leave blank for one-time: "
        )
    raw = input(prompt_text).strip()
    return validate_days(raw)


def prompt_for_sound_file(prompt_text=None, current=None):
    """
    Prompt the user for a path to a custom sound file. Returns the
    stripped path (or the current value if left blank when editing),
    warning if the file cannot be found so the user isn't surprised
    later when the alarm falls back to a beep.
    """
    if prompt_text is None:
        default_desc = current if current else DEFAULT_SOUND_FILE
        prompt_text = (
            f"Enter path to a sound file (blank to keep '{default_desc}'): "
        )
    raw = input(prompt_text).strip()
    if not raw:
        return current

    # Allow a quoted path (e.g. dragged-and-dropped into some terminals)
    # and a leading/trailing whitespace to be forgiven.
    cleaned = raw.strip('"').strip("'").strip()

    if not os.path.exists(cleaned):
        print(
            f"Warning: '{cleaned}' was not found. The alarm will fall "
            "back to a generated beep at ring time unless the file "
            "exists by then."
        )
    return cleaned



# Alarm model


class Alarm:
    """
    Represents a single alarm: a time to trigger at, an optional label,
    optional repeat days, and its own snooze configuration.
    """

    _next_id = 1

    def __init__(
        self,
        alarm_time,
        label="Alarm",
        days=None,
        sound_file=DEFAULT_SOUND_FILE,
        max_snoozes=DEFAULT_MAX_SNOOZES,
        snooze_minutes=DEFAULT_SNOOZE_MINUTES,
        enabled=True,
        alarm_id=None,
    ):
        self.id = alarm_id if alarm_id is not None else Alarm._next_id
        if alarm_id is None:
            Alarm._next_id += 1
        else:
            Alarm._next_id = max(Alarm._next_id, alarm_id + 1)

        self.alarm_time = alarm_time
        self.label = label
        self.days = days or []
        self.sound_file = sound_file
        self.max_snoozes = max_snoozes
        self.snooze_minutes = snooze_minutes
        self.enabled = enabled
        self.snooze_count = 0
        self.last_triggered_date = None

    def is_due(self, now):
        """
        Determine whether this alarm should trigger at the given
        datetime `now`. Handles one-time alarms and repeating alarms.
        """
        if not self.enabled:
            return False

        current_time_str = now.strftime("%H:%M:%S")
        if current_time_str != self.alarm_time:
            return False

        today_str = now.strftime("%Y-%m-%d")
        if self.last_triggered_date == today_str:
            # Already triggered once today; avoid re-triggering within
            # the same second repeatedly.
            return False

        if self.days:
            weekday_str = now.strftime("%a").lower()[:3]
            if weekday_str not in self.days:
                return False

        return True

    def mark_triggered(self, now):
        self.last_triggered_date = now.strftime("%Y-%m-%d")
        self.snooze_count = 0

    def describe(self):
        repeat_desc = ", ".join(self.days) if self.days else "one-time"
        status = "enabled" if self.enabled else "disabled"
        return (
            f"[{self.id}] {self.label} - {self.alarm_time} "
            f"({repeat_desc}) - {status}"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "alarm_time": self.alarm_time,
            "label": self.label,
            "days": self.days,
            "sound_file": self.sound_file,
            "max_snoozes": self.max_snoozes,
            "snooze_minutes": self.snooze_minutes,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            alarm_time=data["alarm_time"],
            label=data.get("label", "Alarm"),
            days=data.get("days", []),
            sound_file=data.get("sound_file", DEFAULT_SOUND_FILE),
            max_snoozes=data.get("max_snoozes", DEFAULT_MAX_SNOOZES),
            snooze_minutes=data.get("snooze_minutes", DEFAULT_SNOOZE_MINUTES),
            enabled=data.get("enabled", True),
            alarm_id=data.get("id"),
        )



# Persistence

class AlarmStorage:
    """
    Handles reading and writing the list of alarms to a JSON file on disk.
    """

    def __init__(self, filepath=ALARMS_FILE):
        self.filepath = filepath

    def load(self):
        if not os.path.exists(self.filepath):
            logger.info("No existing alarms file found; starting fresh.")
            return []

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(f"Failed to read alarms file: {exc}")
            return []

        alarms = []
        for entry in raw:
            try:
                alarms.append(Alarm.from_dict(entry))
            except (KeyError, TypeError) as exc:
                logger.warning(f"Skipping malformed alarm entry: {exc}")

        logger.info(f"Loaded {len(alarms)} alarm(s) from {self.filepath}")
        return alarms

    def save(self, alarms):
        os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump([a.to_dict() for a in alarms], f, indent=2)
        except OSError as exc:
            logger.error(f"Failed to save alarms file: {exc}")



# Sound playback

class AlarmSound:
    """
    Thin wrapper around pygame's mixer so the rest of the program does not
    need to worry about pygame being unavailable or misconfigured.

    The alarm actually rings now: whatever is played is looped
    continuously (via loops=-1) until stop() is called, instead of playing
    once for a fixed number of seconds. If no usable sound file is found,
    a generated beep tone is used instead so the alarm still makes noise
    out of the box. If even that is unavailable (no numpy, no audio
    device at all), it falls back to the terminal bell as a last resort.
    """

    BEEP_FREQUENCY_HZ = 880
    BEEP_DURATION_SECONDS = 0.5

    def __init__(self):
        self._initialized = False
        self._beep_sound = None    # cached pygame.mixer.Sound (generated tone)
        self._using_music = False  # True while a file is playing via mixer.music

    def _ensure_initialized(self):
        if not PYGAME_AVAILABLE:
            return False
        if not self._initialized:
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2)
                self._initialized = True
            except Exception as exc:
                logger.error(f"Could not initialize audio mixer: {exc}")
                return False
        return True

    def play(self, sound_file):
        """
        Start ringing. Prefers the given sound_file if it exists and can
        be loaded; otherwise falls back to a generated beep tone; and as
        a last resort, the terminal bell. Rings on a loop until stop()
        is called.
        """
        if not self._ensure_initialized():
            self._ring_terminal_bell()
            return

        if sound_file and os.path.exists(sound_file):
            try:
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play(loops=-1)
                self._using_music = True
                return
            except Exception as exc:
                logger.error(
                    f"Failed to play sound file '{sound_file}': {exc}. "
                    "Falling back to a generated beep."
                )
        else:
            logger.warning(
                f"Sound file '{sound_file}' not found; using a generated beep."
            )

        self._using_music = False
        beep = self._get_beep_sound()
        if beep is not None:
            try:
                beep.play(loops=-1)
                return
            except Exception as exc:
                logger.error(f"Failed to play generated beep: {exc}")

        self._ring_terminal_bell()

    def stop(self):
        if self._using_music:
            try:
                pygame.mixer.music.stop()
            except Exception as exc:
                logger.error(f"Failed to stop music playback: {exc}")
        if self._beep_sound is not None:
            try:
                self._beep_sound.stop()
            except Exception as exc:
                logger.error(f"Failed to stop beep playback: {exc}")

    def _get_beep_sound(self):
        """
        Lazily build and cache a short sine-wave beep as a pygame Sound
        object, so it can be looped like a real alarm tone. Requires
        numpy; returns None if numpy or pygame's sndarray support is
        unavailable.
        """
        if self._beep_sound is not None:
            return self._beep_sound

        try:
            import numpy as np

            sample_rate = 44100
            num_samples = int(sample_rate * self.BEEP_DURATION_SECONDS)
            t = np.linspace(0, self.BEEP_DURATION_SECONDS, num_samples, False)
            waveform = np.sin(self.BEEP_FREQUENCY_HZ * t * 2 * np.pi)
            # Leave a short silent gap at the end of each loop so repeated
            # beeps sound like distinct pulses rather than one flat tone.
            gap_samples = int(sample_rate * 0.15)
            waveform[-gap_samples:] = 0
            audio = (waveform * 32767).astype(np.int16)
            stereo = np.column_stack((audio, audio))
            self._beep_sound = pygame.sndarray.make_sound(stereo)
            return self._beep_sound
        except ImportError:
            logger.warning(
                "numpy is not installed, so a synthetic beep can't be "
                "generated. Install it with 'pip install numpy' for audio "
                "without needing your own sound file."
            )
            return None
        except Exception as exc:
            logger.error(f"Failed to generate beep tone: {exc}")
            return None

    def _ring_terminal_bell(self):
        """
        Last-resort fallback when no audio backend is usable at all:
        trigger the terminal bell character, which most terminals will
        play as an audible beep.
        """
        print("\a" * 3, end="", flush=True)
        print("(No audio backend available - install pygame and numpy "
              "for a real alarm sound.)")



# Alarm manager


class AlarmManager:
    """
    Owns the collection of alarms, coordinates persistence, and runs the
    main checking loop that triggers alarms when they come due.
    """

    def __init__(self, storage=None, sound=None):
        self.storage = storage or AlarmStorage()
        self.sound = sound or AlarmSound()
        self.alarms = self.storage.load()

    # -- Alarm management -------------------------------------------------

    def add_alarm(self, alarm_time, label="Alarm", days=None, **kwargs):
        alarm = Alarm(alarm_time=alarm_time, label=label, days=days, **kwargs)
        self.alarms.append(alarm)
        self.storage.save(self.alarms)
        logger.info(f"Added alarm: {alarm.describe()}")
        return alarm

    def remove_alarm(self, alarm_id):
        before = len(self.alarms)
        self.alarms = [a for a in self.alarms if a.id != alarm_id]
        removed = len(self.alarms) != before
        if removed:
            self.storage.save(self.alarms)
            logger.info(f"Removed alarm with id {alarm_id}")
        return removed

    def get_alarm(self, alarm_id):
        for alarm in self.alarms:
            if alarm.id == alarm_id:
                return alarm
        return None

    def toggle_alarm(self, alarm_id):
        alarm = self.get_alarm(alarm_id)
        if alarm is None:
            return False
        alarm.enabled = not alarm.enabled
        self.storage.save(self.alarms)
        state = "enabled" if alarm.enabled else "disabled"
        logger.info(f"Alarm {alarm_id} is now {state}")
        return True

    def edit_alarm(self, alarm_id, alarm_time=None, label=None, days=None, sound_file=None):
        alarm = self.get_alarm(alarm_id)
        if alarm is None:
            return False
        if alarm_time is not None:
            alarm.alarm_time = alarm_time
        if label is not None:
            alarm.label = label
        if days is not None:
            alarm.days = days
        if sound_file is not None:
            alarm.sound_file = sound_file
        self.storage.save(self.alarms)
        logger.info(f"Updated alarm: {alarm.describe()}")
        return True

    def list_alarms(self):
        return list(self.alarms)

    # -- Runtime loop -------------------------------------------------------

    def get_due_alarms(self, now=None):
        now = now or datetime.datetime.now()
        return [alarm for alarm in self.alarms if alarm.is_due(now)]

    def run(self, poll_interval=1):
        """
        Continuously poll the clock and trigger any alarm whose time has
        arrived. This call blocks until interrupted with Ctrl+C.
        """
        if not self.alarms:
            print("No alarms are set. Add one from the menu first.")
            return

        print("Alarm clock running. Press Ctrl+C to return to the menu.\n")
        logger.info("Alarm loop started.")

        try:
            while True:
                now = datetime.datetime.now()
                print(now.strftime("%H:%M:%S"), end="\r")

                for alarm in self.get_due_alarms(now):
                    alarm.mark_triggered(now)
                    self.storage.save(self.alarms)
                    self._trigger_alarm(alarm)

                time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\nReturning to menu.")
            logger.info("Alarm loop stopped by user.")

    def _trigger_alarm(self, alarm):
        """
        Handle the full ring / snooze / stop cycle for a single alarm,
        generalizing the original script's snooze logic.
        """
        logger.info(f"Triggering alarm: {alarm.describe()}")

        while True:
            print(f"\nWAKE UP!!! ({alarm.label})")
            self.sound.play(alarm.sound_file)  # rings continuously, on a loop

            if alarm.snooze_count >= alarm.max_snoozes:
                # Let it ring for a bit so a maxed-out alarm still wakes
                # you up, rather than silently giving up.
                time.sleep(ALARM_RING_SECONDS)
                self.sound.stop()
                print("\nMaximum snoozes reached!")
                print("Alarm stopped.")
                logger.info(f"Alarm {alarm.id} auto-stopped (max snoozes).")
                return

            choice = input(
                "\ns = Snooze\n"
                "q = Stop alarm\n"
                "Enter choice: "
            ).strip().lower()

            self.sound.stop()

            if choice == "s":
                alarm.snooze_count += 1
                remaining = alarm.max_snoozes - alarm.snooze_count
                print(
                    f"Alarm snoozed for {alarm.snooze_minutes} minute(s). "
                    f"({remaining} snooze(s) left)"
                )
                logger.info(f"Alarm {alarm.id} snoozed.")
                time.sleep(alarm.snooze_minutes * 60)
                continue

            elif choice == "q":
                print("Alarm stopped.")
                logger.info(f"Alarm {alarm.id} stopped by user.")
                return

            else:
                print("Invalid choice. Alarm stopped.")
                logger.info(f"Alarm {alarm.id} stopped (invalid input).")
                return



# Command line menu


def print_menu():
    print("\n===== Alarm Clock Menu =====")
    print("1. Add alarm")
    print("2. List alarms")
    print("3. Edit alarm")
    print("4. Delete alarm")
    print("5. Enable/disable alarm")
    print("6. Start alarm clock")
    print("7. Exit")


def handle_add(manager):
    alarm_time = prompt_for_valid_time()
    label = input("Enter a label for this alarm (blank for default): ").strip()
    if not label:
        label = "Alarm"
    days = prompt_for_days()
    sound_file = prompt_for_sound_file()

    kwargs = {}
    if sound_file:
        kwargs["sound_file"] = sound_file

    manager.add_alarm(alarm_time, label=label, days=days, **kwargs)
    print("Alarm added.")


def handle_list(manager):
    alarms = manager.list_alarms()
    if not alarms:
        print("No alarms set.")
        return
    print("\nCurrent alarms:")
    for alarm in alarms:
        print("  " + alarm.describe())


def handle_edit(manager):
    handle_list(manager)
    alarms = manager.list_alarms()
    if not alarms:
        return

    try:
        alarm_id = int(input("Enter the id of the alarm to edit: ").strip())
    except ValueError:
        print("Invalid id.")
        return

    existing = manager.get_alarm(alarm_id)
    if existing is None:
        print("No alarm found with that id.")
        return

    print("Leave a field blank to keep its current value.")
    new_time = input("New time (HH:MM or HH:MM:SS): ").strip()
    new_label = input("New label: ").strip()
    new_days_raw = input("New repeat days (comma-separated): ").strip()
    new_sound = prompt_for_sound_file(
        prompt_text=f"New sound file path (blank to keep '{existing.sound_file}'): ",
        current=existing.sound_file,
    )

    kwargs = {}
    if new_time:
        normalized = normalize_time_format(new_time)
        if normalized is not None:
            kwargs["alarm_time"] = normalized
        else:
            print("Invalid time format; time not updated.")
    if new_label:
        kwargs["label"] = new_label
    if new_days_raw:
        kwargs["days"] = validate_days(new_days_raw)
    if new_sound != existing.sound_file:
        kwargs["sound_file"] = new_sound

    if kwargs:
        manager.edit_alarm(alarm_id, **kwargs)
        print("Alarm updated.")
    else:
        print("No changes made.")


def handle_delete(manager):
    handle_list(manager)
    alarms = manager.list_alarms()
    if not alarms:
        return

    try:
        alarm_id = int(input("Enter the id of the alarm to delete: ").strip())
    except ValueError:
        print("Invalid id.")
        return

    if manager.remove_alarm(alarm_id):
        print("Alarm deleted.")
    else:
        print("No alarm found with that id.")


def handle_toggle(manager):
    handle_list(manager)
    alarms = manager.list_alarms()
    if not alarms:
        return

    try:
        alarm_id = int(input("Enter the id of the alarm to toggle: ").strip())
    except ValueError:
        print("Invalid id.")
        return

    if manager.toggle_alarm(alarm_id):
        print("Alarm toggled.")
    else:
        print("No alarm found with that id.")


def run_menu_loop():
    manager = AlarmManager()

    actions = {
        "1": handle_add,
        "2": handle_list,
        "3": handle_edit,
        "4": handle_delete,
        "5": handle_toggle,
    }

    while True:
        print_menu()
        choice = input("Enter choice: ").strip()

        if choice in actions:
            actions[choice](manager)
        elif choice == "6":
            manager.run()
        elif choice == "7":
            print("Goodbye!")
            logger.info("Application exited by user.")
            break
        else:
            print("Invalid choice, please try again.")



# Entry point

def main():
    logger.info("Alarm clock application starting.")
    try:
        run_menu_loop()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        logger.info("Application interrupted by user.")


if __name__ == "__main__":
    main()




