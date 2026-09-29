# ⏰ Multi-Alarm Clock Application

A command-line **Multi-Alarm Clock Application built with Python** that allows users to create and manage multiple alarms, configure repeat days, use custom alarm sounds, snooze alarms, and save alarm data between program runs.

---

## ✨ Features

- ⏰ Create multiple alarms
- 🕐 Supports `HH:MM` and `HH:MM:SS` time formats
- 🏷️ Give alarms custom labels
- 🔁 Repeat alarms on selected days
- 🎵 Use custom sound files
- 😴 Snooze alarms
- 🔢 Supports up to 3 snoozes by default
- ⏱️ Default snooze duration of 5 minutes
- 🔊 Loops the alarm sound until stopped
- 🔔 Falls back to a generated beep if the sound file cannot be played
- 💾 Automatically saves alarms to `alarms.json`
- ✏️ Edit alarms
- 🗑️ Delete alarms
- 🔘 Enable or disable alarms
- 📋 List saved alarms
- 📝 Records application events in a log file

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Pygame | Alarm sound playback |
| NumPy | Generated beep fallback |
| JSON | Persistent alarm storage |
| `datetime` | Time and alarm scheduling |
| `time` | Timing and snooze delays |
| `logging` | Application logging |

---

# 📋 Requirements

Before running the application, make sure you have:

- Python 3 installed
- `pip` installed
- A working audio output device
- Git installed if cloning the repository
- The dependencies listed in `requirements.txt`

---

# 🚀 Setup and Installation

Follow these steps to set up the project from scratch.

## 1. Clone the Repository

Open Command Prompt, PowerShell, or a terminal and run:

```bash
git clone https://github.com/akratiisharmaa/Digital-alarm-clock.git
```

Move into the project directory:

```bash
cd Digital-alarm-clock
```

---

## 2. Create a Virtual Environment

Create a Python virtual environment:

```bash
python -m venv .venv
```

### Windows PowerShell

Activate it using:

```powershell
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

Activate it using:

```cmd
.venv\Scripts\activate
```

After activation, the terminal should show:

```text
(.venv)
```

---

## 3. Install Dependencies

The project includes a `requirements.txt` file containing the required Python packages.

Install all dependencies with:

```bash
python -m pip install -r requirements.txt
```

This installs the packages required by the application without needing to install them individually.

---

## 4. Configure the Alarm Sound

The default alarm sound is:

```text
song.mp3
```

Place the sound file in the project directory:

```text
Digital-alarm-clock/
│
├── alarm_clock.py
├── requirements.txt
├── song.mp3
└── README.md
```

You can also specify a different sound-file path when creating an alarm.

---

# ▶️ Running the Application

After completing the setup, run:

```bash
python alarm_clock.py
```

The application will display the main menu:

```text
===== Alarm Clock Menu =====
1. Add alarm
2. List alarms
3. Edit alarm
4. Delete alarm
5. Enable/disable alarm
6. Start alarm clock
7. Exit
```

---

# 📖 How to Use

## 1. Add an Alarm

Select:

```text
1
```

Enter the alarm time.

Both formats are supported:

```text
07:30
```

or:

```text
07:30:00
```

The time is interpreted using the 24-hour format.

---

## 2. Add a Label

Enter a label such as:

```text
Morning Alarm
```

If you leave it blank, the default label is:

```text
Alarm
```

---

## 3. Set Repeat Days

Enter comma-separated day abbreviations:

```text
mon,wed,fri
```

Available values are:

```text
mon,tue,wed,thu,fri,sat,sun
```

Leave the field blank if the alarm should be a one-time alarm.

---

## 4. Choose a Sound

Enter the path to your sound file.

For example:

```text
song.mp3
```

or:

```text
sounds/morning_alarm.mp3
```

If the specified file cannot be found, the application attempts to use a generated beep as a fallback.

---

## 5. List Alarms

Select:

```text
2
```

This displays all currently saved alarms, including their:

- ID
- Label
- Time
- Repeat days
- Enabled/disabled status

---

## 6. Edit an Alarm

Select:

```text
3
```

Enter the ID of the alarm you want to edit.

You can modify:

- Time
- Label
- Repeat days
- Sound file

---

## 7. Delete an Alarm

Select:

```text
4
```

Enter the ID of the alarm you want to delete.

---

## 8. Enable or Disable an Alarm

Select:

```text
5
```

Enter the alarm ID.

This toggles the alarm between enabled and disabled.

---

## 9. Start the Alarm Clock

Select:

```text
6
```

The application begins monitoring the current time.

When an alarm becomes due, the configured sound starts playing.

To return to the menu while the clock is running, press:

```text
Ctrl+C
```

---

# 😴 Snooze

When an alarm rings, the application displays:

```text
s = Snooze
q = Stop alarm
Enter choice:
```

Enter:

```text
s
```

to snooze the alarm.

The default snooze duration is **5 minutes**.

The default maximum number of snoozes is **3**.

---

# 🛑 Stop the Alarm

When the alarm is ringing, enter:

```text
q
```

The alarm sound will stop.

---

# 💾 Data Storage

The application automatically creates:

```text
alarms.json
```

This file stores the saved alarm information.

Because alarms are stored in this file, they remain available when the application is started again.

---

# 📝 Logging

The application creates:

```text
alarm_clock.log
```

The log records application events and errors, which can be useful when troubleshooting the application.

---

# 📁 Project Structure

After setup and execution, the project may look like:

```text
Digital-alarm-clock/
│
├── alarm_clock.py
├── requirements.txt
├── song.mp3
├── alarms.json
├── alarm_clock.log
└── README.md
```

### `alarm_clock.py`

Contains the main alarm-clock application.

### `requirements.txt`

Contains the external Python dependencies required by the project.

### `song.mp3`

Default alarm sound.

### `alarms.json`

Automatically generated file containing saved alarms.

### `alarm_clock.log`

Automatically generated application log.

### `README.md`

Project documentation and setup instructions.

---

# 🐛 Troubleshooting

## Pygame is not installed

If you see:

```text
ModuleNotFoundError: No module named 'pygame'
```

make sure the virtual environment is activated and run:

```bash
python -m pip install -r requirements.txt
```

---

## Sound does not play

Check that:

1. Your computer volume is turned on.
2. Your speakers or headphones are connected.
3. `song.mp3` exists.
4. The sound-file path is correct.
5. The dependencies in `requirements.txt` have been installed.
6. The virtual environment is activated.

You can verify Pygame with:

```bash
python -m pip show pygame
```

---

## Sound file cannot be found

Make sure the file exists at the path provided to the application.

For the default configuration:

```text
Digital-alarm-clock/
├── alarm_clock.py
└── song.mp3
```

---

# ⚡ Quick Start

If Python and Git are already installed:

```bash
git clone https://github.com/akratiisharmaa/Digital-alarm-clock.git
cd Digital-alarm-clock
python -m venv .venv
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python alarm_clock.py
```

### Windows Command Prompt

```cmd
.venv\Scripts\activate
python -m pip install -r requirements.txt
python alarm_clock.py
```

Then:

1. Select **1. Add alarm**
2. Enter the alarm time
3. Enter an optional label
4. Enter repeat days or leave blank
5. Enter the sound-file path
6. Select **6. Start alarm clock**
7. Wait for the alarm to trigger

---

# 👩‍💻 Author

**Akrati Sharma**

GitHub:  
https://github.com/akratiisharmaa

Repository:  
https://github.com/akratiisharmaa/Digital-alarm-clock/
