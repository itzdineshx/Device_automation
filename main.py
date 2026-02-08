from transformers import AutoProcessor, AutoModelForCausalLM
import re
import subprocess
import os
import json
import urllib.parse
import io
import sys

MODEL_ID = "google/functiongemma-270m-it"

# Global model references
processor = None
model = None

# Log buffer for UI
_log_buffer = []

def log(msg):
    """Log a message. Used by both CLI and UI."""
    _log_buffer.append(msg)
    print(msg)

def get_and_clear_log():
    """Get all logged messages and clear the buffer."""
    msgs = list(_log_buffer)
    _log_buffer.clear()
    return msgs

def load_model():
    global processor, model
    if processor is not None:
        return
    log("Loading AI model...")
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        device_map="auto",
        torch_dtype="auto"
    )
    log("Model loaded!")

# ═══════════════════════════════════════════════════════
#  SETTINGS MAP
# ═══════════════════════════════════════════════════════
SETTINGS_MAP = {
    "bluetooth":        "ms-settings:bluetooth",
    "wifi":             "ms-settings:network-wifi",
    "network":          "ms-settings:network",
    "airplane":         "ms-settings:network-airplanemode",
    "vpn":              "ms-settings:network-vpn",
    "hotspot":          "ms-settings:network-mobilehotspot",
    "proxy":            "ms-settings:network-proxy",
    "display":          "ms-settings:display",
    "night light":      "ms-settings:nightlight",
    "sound":            "ms-settings:sound",
    "notifications":    "ms-settings:notifications",
    "focus":            "ms-settings:quiethours",
    "power":            "ms-settings:powersleep",
    "battery":          "ms-settings:batterysaver",
    "storage":          "ms-settings:storagesense",
    "personalization":  "ms-settings:personalization",
    "background":       "ms-settings:personalization-background",
    "colors":           "ms-settings:personalization-colors",
    "lock screen":      "ms-settings:lockscreen",
    "themes":           "ms-settings:themes",
    "taskbar":          "ms-settings:taskbar",
    "start menu":       "ms-settings:personalization-start",
    "accounts":         "ms-settings:yourinfo",
    "date":             "ms-settings:dateandtime",
    "time":             "ms-settings:dateandtime",
    "language":         "ms-settings:regionlanguage",
    "keyboard":         "ms-settings:keyboard",
    "mouse":            "ms-settings:mousetouchpad",
    "touchpad":         "ms-settings:devices-touchpad",
    "printer":          "ms-settings:printers",
    "camera":           "ms-settings:privacy-webcam",
    "microphone":       "ms-settings:privacy-microphone",
    "location":         "ms-settings:privacy-location",
    "apps":             "ms-settings:appsfeatures",
    "default apps":     "ms-settings:defaultapps",
    "startup":          "ms-settings:startupapps",
    "update":           "ms-settings:windowsupdate",
    "windows update":   "ms-settings:windowsupdate",
    "recovery":         "ms-settings:recovery",
    "about":            "ms-settings:about",
    "clipboard":        "ms-settings:clipboard",
    "remote desktop":   "ms-settings:remotedesktop",
    "accessibility":    "ms-settings:easeofaccess",
    "privacy":          "ms-settings:privacy",
    "developer":        "ms-settings:developers",
    "security":         "windowsdefender:",
    "gaming":           "ms-settings:gaming-gamebar",
    "fonts":            "ms-settings:fonts",
}

# ═══════════════════════════════════════════════════════
#  APP MAP
# ═══════════════════════════════════════════════════════
APP_MAP = {
    "notepad":          "notepad.exe",
    "calculator":       "calc.exe",
    "calc":             "calc.exe",
    "paint":            "mspaint.exe",
    "chrome":           "start chrome",
    "google chrome":    "start chrome",
    "edge":             "start msedge",
    "firefox":          "start firefox",
    "browser":          "start msedge",
    "file explorer":    "explorer.exe",
    "explorer":         "explorer.exe",
    "files":            "explorer.exe",
    "task manager":     "taskmgr.exe",
    "command prompt":   "cmd.exe",
    "cmd":              "cmd.exe",
    "terminal":         "wt.exe",
    "powershell":       "powershell.exe",
    "control panel":    "control",
    "snipping tool":    "snippingtool.exe",
    "snip":             "snippingtool.exe",
    "word":             "start winword",
    "excel":            "start excel",
    "powerpoint":       "start powerpnt",
    "outlook":          "start outlook",
    "spotify":          "start spotify:",
    "vscode":           "code",
    "vs code":          "code",
    "code":             "code",
    "teams":            "start msteams:",
    "discord":          "start discord:",
    "whatsapp":         "start whatsapp:",
    "telegram":         "start telegram:",
    "photos":           "start ms-photos:",
    "maps":             "start bingmaps:",
    "weather":          "start bingweather:",
    "clock":            "start ms-clock:",
    "calendar":         "start outlookcal:",
    "settings":         "start ms-settings:",
    "store":            "start ms-windows-store:",
    "xbox":             "start xbox:",
    "movies":           "start mswindowsvideo:",
    "music":            "start mswindowsmusic:",
}

# ═══════════════════════════════════════════════════════
#  FUNCTION IMPLEMENTATIONS (all use subprocess/PowerShell)
# ═══════════════════════════════════════════════════════

# ─── PowerShell script to toggle a Windows radio (Bluetooth/WiFi) ───
RADIO_TOGGLE_PS = r'''
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]
function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}
[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$radio = $radios | Where-Object { $_.Kind -eq '%KIND%' }
if ($radio) {
    $result = Await ($radio.SetStateAsync('%STATE%')) ([Windows.Devices.Radios.RadioAccessStatus])
    Write-Host "%KIND% turned %STATE%"
} else {
    Write-Host "No %KIND% radio found"
}
'''

def toggle_radio(kind, state):
    """Toggle a Windows radio. kind='Bluetooth'|'WiFi', state='On'|'Off'"""
    ps = RADIO_TOGGLE_PS.replace('%KIND%', kind).replace('%STATE%', state)
    result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps],
                           capture_output=True, text=True, timeout=15)
    output = (result.stdout + result.stderr).strip()
    if output:
        log(f"  -> {output}")
    else:
        log(f"  -> {kind} {state.lower()} command sent")

def toggle_bluetooth(on=True):
    toggle_radio('Bluetooth', 'On' if on else 'Off')

def toggle_wifi(on=True):
    toggle_radio('WiFi', 'On' if on else 'Off')

def toggle_airplane_mode(on=True):
    subprocess.Popen("start ms-settings:network-airplanemode", shell=True)
    log(f"  -> Opened airplane mode settings (toggle manually)")

def toggle_night_light(on=True):
    state = '1' if on else '0'
    ps = f'''$path = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\CloudStore\Store\DefaultAccount\Current\default$windows.data.bluelightreduction.bluelightreductionstate\windows.data.bluelightreduction.bluelightreductionstate'
if (Test-Path $path) {{ Remove-Item $path -Force }}
Start-Process ms-settings:nightlight'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log(f"  -> Night light {'on' if on else 'off'} (settings opened)")

def toggle_hotspot(on=True):
    subprocess.Popen("start ms-settings:network-mobilehotspot", shell=True)
    log(f"  -> Opened hotspot settings (toggle manually)")

def toggle_location(on=True):
    subprocess.Popen("start ms-settings:privacy-location", shell=True)
    log(f"  -> Opened location settings (toggle manually)")

def open_settings(key):
    uri = SETTINGS_MAP.get(key)
    if uri:
        subprocess.Popen(f"start {uri}", shell=True)
        log(f"  -> Opened {key} settings")
        return True
    return False

def open_app(name):
    cmd = APP_MAP.get(name.lower().strip())
    if cmd:
        subprocess.Popen(cmd, shell=True)
        log(f"  -> Opened {name}")
        return True
    subprocess.Popen(f"start {name}", shell=True)
    log(f"  -> Trying to open {name}...")
    return True

def set_volume(level):
    level = max(0, min(100, int(level)))
    ps = f'''$wsh = New-Object -ComObject WScript.Shell
$vol = {level}
1..50 | ForEach-Object {{ $wsh.SendKeys([char]174) }}
Start-Sleep -Milliseconds 100
$steps = [Math]::Round($vol / 2)
1..$steps | ForEach-Object {{ $wsh.SendKeys([char]175) }}'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log(f"  -> Volume set to ~{level}%")

def mute_audio():
    ps = '(New-Object -ComObject WScript.Shell).SendKeys([char]173)'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Toggled mute")

def set_brightness(level):
    level = max(0, min(100, int(level)))
    ps = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log(f"  -> Brightness set to {level}%")

def take_screenshot():
    ps = '(New-Object -ComObject WScript.Shell).SendKeys("^{PRTSC}")'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    subprocess.Popen("snippingtool.exe", shell=True)
    log("  -> Screenshot tool opened")

def lock_screen():
    subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
    log("  -> Screen locked")

def shutdown_pc():
    log("  -> Shutting down in 10 seconds... (run 'shutdown /a' to cancel)")
    subprocess.run("shutdown /s /t 10", shell=True)

def restart_pc():
    log("  -> Restarting in 10 seconds... (run 'shutdown /a' to cancel)")
    subprocess.run("shutdown /r /t 10", shell=True)

def sleep_pc():
    subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
    log("  -> Putting to sleep...")

def logoff_pc():
    subprocess.run("shutdown /l", shell=True)
    log("  -> Logging off...")

def web_search(query):
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    subprocess.Popen(f'start "" "{url}"', shell=True)
    log(f"  -> Searching: {query}")

def open_website(url):
    if not url.startswith("http"):
        url = "https://" + url
    subprocess.Popen(f'start "" "{url}"', shell=True)
    log(f"  -> Opening {url}")


# ═══════════════════════════════════════════════════════
#  SMART KEYWORD ROUTER (primary — always works)
# ═══════════════════════════════════════════════════════

# Map of toggleable features -> (on_func, off_func)
TOGGLEABLE = {
    "bluetooth":    (lambda: toggle_bluetooth(True),  lambda: toggle_bluetooth(False)),
    "wifi":         (lambda: toggle_wifi(True),       lambda: toggle_wifi(False)),
    "wi-fi":        (lambda: toggle_wifi(True),       lambda: toggle_wifi(False)),
    "wireless":     (lambda: toggle_wifi(True),       lambda: toggle_wifi(False)),
    "airplane":     (lambda: toggle_airplane_mode(True), lambda: toggle_airplane_mode(False)),
    "airplane mode":(lambda: toggle_airplane_mode(True), lambda: toggle_airplane_mode(False)),
    "night light":  (lambda: toggle_night_light(True),  lambda: toggle_night_light(False)),
    "nightlight":   (lambda: toggle_night_light(True),  lambda: toggle_night_light(False)),
    "hotspot":      (lambda: toggle_hotspot(True),     lambda: toggle_hotspot(False)),
    "mobile hotspot":(lambda: toggle_hotspot(True),    lambda: toggle_hotspot(False)),
    "location":     (lambda: toggle_location(True),    lambda: toggle_location(False)),
}

def smart_execute(text):
    """Parse user input with keywords and execute the right action.
    Returns True if handled, False if needs AI fallback."""
    text_lower = text.lower().strip()

    # --- Detect ON/OFF intent ---
    wants_on = any(w in text_lower for w in ["turn on", "enable", "activate", "switch on", "start "])
    wants_off = any(w in text_lower for w in ["turn off", "disable", "deactivate", "switch off", "stop "])

    # --- Toggle hardware features (bluetooth, wifi, etc.) ---
    if wants_on or wants_off:
        for feature, (on_fn, off_fn) in sorted(TOGGLEABLE.items(), key=lambda x: len(x[0]), reverse=True):
            if feature in text_lower:
                if wants_on:
                    on_fn()
                else:
                    off_fn()
                return True

    # --- Volume ---
    vol_match = re.search(r'(?:set\s+)?volume\s+(?:to\s+)?(\d+)', text_lower)
    if vol_match:
        set_volume(int(vol_match.group(1)))
        return True
    if any(w in text_lower for w in ["mute", "unmute", "silence"]):
        mute_audio()
        return True
    if "volume up" in text_lower or "increase volume" in text_lower or "louder" in text_lower:
        set_volume(80)
        return True
    if "volume down" in text_lower or "decrease volume" in text_lower or "quieter" in text_lower or "lower volume" in text_lower:
        set_volume(30)
        return True

    # --- Brightness ---
    br_match = re.search(r'(?:set\s+)?brightness\s+(?:to\s+)?(\d+)', text_lower)
    if br_match:
        set_brightness(int(br_match.group(1)))
        return True
    if any(w in text_lower for w in ["brighter", "increase brightness", "brightness up"]):
        set_brightness(80)
        return True
    if any(w in text_lower for w in ["dimmer", "dim", "decrease brightness", "brightness down"]):
        set_brightness(30)
        return True

    # --- System actions ---
    if "screenshot" in text_lower or "screen shot" in text_lower or "snip" in text_lower:
        take_screenshot()
        return True
    if "lock" in text_lower and any(w in text_lower for w in ["screen", "computer", "pc", "laptop", "my"]):
        lock_screen()
        return True
    if "shut down" in text_lower or "shutdown" in text_lower:
        shutdown_pc()
        return True
    if "restart" in text_lower or "reboot" in text_lower:
        restart_pc()
        return True
    if "sleep" in text_lower:
        sleep_pc()
        return True
    if "log off" in text_lower or "logoff" in text_lower or "sign out" in text_lower:
        logoff_pc()
        return True

    # --- Web search ---
    search_match = re.search(r'(?:search|google|look up|find)\s+(?:for\s+)?(.+)', text_lower)
    if search_match:
        web_search(search_match.group(1).strip())
        return True

    # --- Open website ---
    url_match = re.search(r'(?:open|go to|visit|browse)\s+((?:https?://)?(?:www\.)?[\w.-]+\.\w{2,}(?:/\S*)?)', text_lower)
    if url_match:
        open_website(url_match.group(1).strip())
        return True

    # --- Open settings page (only if user says 'settings' or 'open') ---
    if any(w in text_lower for w in ["settings", "open", "show", "go to"]):
        for key in sorted(SETTINGS_MAP.keys(), key=len, reverse=True):
            if key in text_lower:
                open_settings(key)
                return True

    # --- Open apps ---
    for app_name in sorted(APP_MAP.keys(), key=len, reverse=True):
        if app_name in text_lower:
            open_app(app_name)
            return True

    # --- Play something ---
    if "play" in text_lower:
        play_match = re.search(r'play\s+(.+?)(?:\s+on\s+|\s*$)', text_lower)
        if play_match:
            query = play_match.group(1).strip()
            if "spotify" in text_lower:
                open_app("spotify")
            else:
                web_search(f"{query} play online")
            return True

    return False


# ═══════════════════════════════════════════════════════
#  AI MODEL FALLBACK (for ambiguous prompts)
# ═══════════════════════════════════════════════════════

# Keep function list small for the 270M model
ai_functions = [
    {
        "type": "function",
        "function": {
            "name": "open_settings",
            "description": "Open a Windows settings page",
            "parameters": {
                "type": "object",
                "properties": {
                    "setting": {"type": "string", "description": "Which setting to open: bluetooth, wifi, display, sound, network, power, battery, privacy, camera, microphone, apps, update"}
                },
                "required": ["setting"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open an application",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Application name like chrome, notepad, calculator, spotify, edge, explorer, terminal"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Set system volume to a level between 0 and 100",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Volume level 0-100"}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_brightness",
            "description": "Set screen brightness to a level between 0 and 100",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Brightness level 0-100"}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "system_action",
            "description": "Perform a system action",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action: shutdown, restart, sleep, lock, screenshot, mute"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
]

def ai_fallback(user_input):
    """Use the AI model when keyword matching fails."""
    if processor is None:
        load_model()
    messages = [
        {"role": "developer", "content": "You are a laptop assistant. Call the best function for the user's request."},
        {"role": "user", "content": user_input}
    ]

    inputs = processor.apply_chat_template(
        messages, tools=ai_functions, add_generation_prompt=True, return_tensors="pt"
    )
    outputs = model.generate(
        **inputs.to(model.device), max_new_tokens=128, pad_token_id=processor.eos_token_id
    )
    response = processor.decode(outputs[0][len(inputs["input_ids"][0]):], skip_special_tokens=True)

    match = re.search(r'call:(\w+)(\{.*?\})', response)
    if match:
        func_name = match.group(1)
        params_str = match.group(2)
        params = extract_params(params_str)
        log(f"  [AI chose: {func_name}({params})]")
        return execute_ai_function(func_name, params)
    else:
        log(f"  [AI] Sorry, I couldn't understand that. Try being more specific.")
        return False

def extract_params(params_str):
    params = {}
    try:
        cleaned = params_str.replace("<escape>", '"')
        params = json.loads(cleaned)
        return params
    except:
        pass
    for m in re.finditer(r'(\w+):\s*<escape>(.+?)<escape>', params_str):
        params[m.group(1)] = m.group(2)
    for m in re.finditer(r'"(\w+)":\s*(\d+)', params_str):
        params[m.group(1)] = int(m.group(2))
    for m in re.finditer(r'"(\w+)":\s*(true|false)', params_str, re.IGNORECASE):
        params[m.group(1)] = m.group(2).lower() == "true"
    for m in re.finditer(r'(\w+):\s*(\d+)', params_str):
        if m.group(1) not in params:
            params[m.group(1)] = int(m.group(2))
    return params

def execute_ai_function(func_name, params):
    if func_name == "open_settings":
        setting = params.get("setting", "").lower()
        return open_settings(setting)
    elif func_name == "open_app":
        return open_app(params.get("app_name", ""))
    elif func_name == "set_volume":
        set_volume(params.get("level", 50))
        return True
    elif func_name == "set_brightness":
        set_brightness(params.get("level", 50))
        return True
    elif func_name == "system_action":
        action = params.get("action", "").lower()
        actions = {
            "shutdown": shutdown_pc, "restart": restart_pc, "sleep": sleep_pc,
            "lock": lock_screen, "screenshot": take_screenshot, "mute": mute_audio,
        }
        fn = actions.get(action)
        if fn:
            fn()
            return True
        log(f"  -> Unknown action: {action}")
        return False
    elif func_name == "web_search":
        web_search(params.get("query", ""))
        return True
    return False


# ═══════════════════════════════════════════════════════
#  PUBLIC API for UI
# ═══════════════════════════════════════════════════════

def process_command(user_input):
    """Process a user command. Returns a list of response strings."""
    _log_buffer.clear()
    handled = smart_execute(user_input)
    if not handled:
        log("  [Thinking...]")
        ai_fallback(user_input)
    return get_and_clear_log()


# ═══════════════════════════════════════════════════════
#  CLI MODE
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    load_model()
    print("=" * 55)
    print("    LAPTOP CONTROL ASSISTANT (AI-Powered)")
    print("=" * 55)
    print()
    print('Type "exit" to quit.')
    print("-" * 55)

    while True:
        user_input = input("\n You > ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            print("\n Goodbye!")
            break
        process_command(user_input)
