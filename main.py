from transformers import AutoProcessor, AutoModelForCausalLM
import re
import subprocess
import os
import json
import urllib.parse
import io
import sys
import datetime
import shutil
import ctypes

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
    "multitasking":     "ms-settings:multitasking",
    "projecting":       "ms-settings:project",
    "typing":           "ms-settings:typing",
    "pen":              "ms-settings:pen",
    "usb":              "ms-settings:usb",
    "autoplay":         "ms-settings:autoplay",
    "default browser":  "ms-settings:defaultapps",
    "optional features": "ms-settings:optionalfeatures",
    "maps":             "ms-settings:maps",
    "offline maps":     "ms-settings:maps",
    "speech":           "ms-settings:speech",
    "signin":           "ms-settings:signinoptions",
    "sign in":          "ms-settings:signinoptions",
    "email":            "ms-settings:emailandaccounts",
    "sync":             "ms-settings:sync",
    "family":           "ms-settings:family-group",
    "color management": "ms-settings:display-advancedgraphics",
    "graphics":         "ms-settings:display-advancedgraphics",
    "scaling":          "ms-settings:display",
    "night mode":       "ms-settings:nightlight",
    "screen timeout":   "ms-settings:powersleep",
    "sleep timeout":    "ms-settings:powersleep",
    "ethernet":         "ms-settings:network-ethernet",
    "dial-up":          "ms-settings:network-dialup",
    "data usage":       "ms-settings:datausage",
    "background apps":  "ms-settings:privacy-backgroundapps",
    "firewall":         "ms-settings:windowsdefender",
    "device encryption": "ms-settings:deviceencryption",
    "troubleshoot":     "ms-settings:troubleshoot",
    "activation":       "ms-settings:activation",
    "device manager":   "devmgmt.msc",
    "disk management":  "diskmgmt.msc",
    "event viewer":     "eventvwr.msc",
    "services":         "services.msc",
    "group policy":     "gpedit.msc",
    "system info":      "msinfo32",
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
    "zoom":             "start zoommtg:",
    "slack":            "start slack:",
    "notion":           "start notion:",
    "onenote":          "start onenote:",
    "sticky notes":     "start ms-stickynotes:",
    "feedback":         "start feedback-hub:",
    "tips":             "start ms-get-started:",
    "magnifier":        "magnify.exe",
    "narrator":         "narrator.exe",
    "on-screen keyboard": "osk.exe",
    "osk":              "osk.exe",
    "character map":    "charmap.exe",
    "registry editor":  "regedit.exe",
    "regedit":          "regedit.exe",
    "remote desktop":   "mstsc.exe",
    "rdp":              "mstsc.exe",
    "disk cleanup":     "cleanmgr.exe",
    "defragment":       "dfrgui.exe",
    "system config":    "msconfig.exe",
    "resource monitor":  "resmon.exe",
    "performance monitor": "perfmon.exe",
    "reliability":      "start perfmon /rel",
    "wordpad":          "write.exe",
    "sound recorder":   "start ms-callrecording:",
    "screen recorder":  "start ms-screenclip:",
    "camera app":       "start microsoft.windows.camera:",
    "alarm":            "start ms-clock:",
    "timer":            "start ms-clock:",
    "stopwatch":        "start ms-clock:",
    "mail":             "start outlookmail:",
    "people":           "start ms-people:",
    "video editor":     "start ms-photos:videospage",
    "3d viewer":        "start com.microsoft.3dviewer:",
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
#  PROCESS / TASK MANAGEMENT
# ═══════════════════════════════════════════════════════

def kill_process(name):
    """Kill a running process by name."""
    name = name.strip().lower()
    if not name.endswith(".exe"):
        name += ".exe"
    result = subprocess.run(f'taskkill /IM "{name}" /F', shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        log(f"  -> Closed {name}")
    else:
        log(f"  -> Could not close {name}: {result.stderr.strip()}")

def list_running_apps():
    """List currently running visible apps."""
    ps = 'Get-Process | Where-Object {$_.MainWindowTitle -ne ""} | Select-Object -Property Name,MainWindowTitle | Format-Table -AutoSize | Out-String -Width 200'
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    log(f"  -> Running apps:\n{result.stdout.strip()[:1500]}")


# ═══════════════════════════════════════════════════════
#  FILE / FOLDER MANAGEMENT
# ═══════════════════════════════════════════════════════

def open_folder(folder_name):
    """Open a common folder."""
    folders = {
        "downloads":  os.path.expanduser("~/Downloads"),
        "documents":  os.path.expanduser("~/Documents"),
        "desktop":    os.path.expanduser("~/Desktop"),
        "pictures":   os.path.expanduser("~/Pictures"),
        "videos":     os.path.expanduser("~/Videos"),
        "music":      os.path.expanduser("~/Music"),
        "appdata":    os.environ.get("APPDATA", ""),
        "temp":       os.environ.get("TEMP", ""),
        "home":       os.path.expanduser("~"),
        "user":       os.path.expanduser("~"),
        "c drive":    "C:\\",
        "c:":         "C:\\",
        "d drive":    "D:\\",
        "d:":         "D:\\",
        "root":       "C:\\",
    }
    path = folders.get(folder_name.lower().strip())
    if path and os.path.exists(path):
        subprocess.Popen(f'explorer "{path}"', shell=True)
        log(f"  -> Opened {folder_name}: {path}")
        return True
    # Try opening as a literal path
    if os.path.exists(folder_name):
        subprocess.Popen(f'explorer "{folder_name}"', shell=True)
        log(f"  -> Opened {folder_name}")
        return True
    log(f"  -> Folder not found: {folder_name}")
    return False

def empty_recycle_bin():
    """Empty the Windows Recycle Bin."""
    ps = 'Clear-RecycleBin -Force -ErrorAction SilentlyContinue'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Recycle bin emptied")

def create_folder(path):
    """Create a new folder on the Desktop."""
    full = os.path.join(os.path.expanduser("~/Desktop"), path)
    os.makedirs(full, exist_ok=True)
    log(f"  -> Created folder: {full}")


# ═══════════════════════════════════════════════════════
#  DISPLAY & APPEARANCE
# ═══════════════════════════════════════════════════════

def toggle_dark_mode(on=True):
    """Toggle Windows dark/light mode."""
    val = 0 if on else 1  # 0 = dark, 1 = light
    ps = f'''Set-ItemProperty -Path HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name AppsUseLightTheme -Value {val}
Set-ItemProperty -Path HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name SystemUsesLightTheme -Value {val}'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log(f"  -> {'Dark' if on else 'Light'} mode enabled")

def set_screen_resolution(width, height):
    """Attempt to change screen resolution."""
    ps = f'''Add-Type @"
using System; using System.Runtime.InteropServices;
public class Disp {{
  [DllImport("user32.dll")] public static extern int ChangeDisplaySettings(ref DEVMODE dm, int flags);
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
  public struct DEVMODE {{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmDeviceName;
    public short dmSpecVersion; public short dmDriverVersion; public short dmSize; public short dmDriverExtra;
    public int dmFields; public int dmPositionX; public int dmPositionY; public int dmDisplayOrientation;
    public int dmDisplayFixedOutput; public short dmColor; public short dmDuplex; public short dmYResolution;
    public short dmTTOption; public short dmCollate;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmFormName;
    public short dmLogPixels; public int dmBitsPerPel; public int dmPelsWidth; public int dmPelsHeight;
    public int dmDisplayFlags; public int dmDisplayFrequency;
  }}
}}
"@
$dm = New-Object Disp+DEVMODE
$dm.dmSize = [Runtime.InteropServices.Marshal]::SizeOf($dm)
$dm.dmPelsWidth = {width}; $dm.dmPelsHeight = {height}
$dm.dmFields = 0x180000
[Disp]::ChangeDisplaySettings([ref]$dm, 0)'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log(f"  -> Resolution set to {width}x{height}")

def rotate_screen(angle=0):
    """Open display settings for rotation (0, 90, 180, 270)."""
    subprocess.Popen("start ms-settings:display", shell=True)
    log(f"  -> Opened display settings for rotation")

def toggle_color_filter(on=True):
    """Toggle Windows color filters (grayscale, etc.)."""
    val = 1 if on else 0
    ps = f'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\ColorFiltering" -Name Active -Value {val} -Type DWord -Force'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log(f"  -> Color filter {'enabled' if on else 'disabled'}")

def toggle_high_contrast(on=True):
    """Toggle high contrast mode."""
    if on:
        subprocess.Popen("start ms-settings:easeofaccess-highcontrast", shell=True)
    else:
        subprocess.Popen("start ms-settings:easeofaccess-highcontrast", shell=True)
    log(f"  -> Opened high contrast settings")

def set_wallpaper(path):
    """Set desktop wallpaper from a file path."""
    if os.path.exists(path):
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
        log(f"  -> Wallpaper set to {path}")
    else:
        log(f"  -> File not found: {path}")

def toggle_taskbar_autohide(on=True):
    """Toggle taskbar auto-hide."""
    val = 3 if on else 2  # 3 = auto-hide, 2 = always show
    ps = f'''$p = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StuckRects3'
$v = (Get-ItemProperty -Path $p).Settings
$v[8] = {val}
Set-ItemProperty -Path $p -Name Settings -Value $v
Stop-Process -Name explorer -Force'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log(f"  -> Taskbar auto-hide {'enabled' if on else 'disabled'}")


# ═══════════════════════════════════════════════════════
#  NETWORK & CONNECTIVITY
# ═══════════════════════════════════════════════════════

def show_ip_address():
    """Show the current IP addresses."""
    ps = '(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"}).IPAddress'
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    ips = result.stdout.strip()
    log(f"  -> IP Addresses: {ips if ips else 'Not connected'}")

def show_public_ip():
    """Show public IP address."""
    ps = '(Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing).Content'
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True, timeout=10)
    ip = result.stdout.strip()
    log(f"  -> Public IP: {ip if ip else 'Could not determine'}")

def ping_host(host):
    """Ping a host and show result."""
    result = subprocess.run(f'ping -n 3 {host}', shell=True, capture_output=True, text=True, timeout=15)
    log(f"  -> Ping {host}:\n{result.stdout.strip()[-500:]}")

def flush_dns():
    """Flush the DNS resolver cache."""
    result = subprocess.run('ipconfig /flushdns', shell=True, capture_output=True, text=True)
    log(f"  -> {result.stdout.strip()}")

def show_wifi_password():
    """Show saved WiFi password for the current network."""
    ps = '''$prof = (netsh wlan show interfaces | Select-String "Profile" | ForEach-Object { ($_ -split ":")[1].Trim() })
if ($prof) { netsh wlan show profile name="$prof" key=clear | Select-String "Key Content" } else { Write-Host "Not connected to WiFi" }'''
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    log(f"  -> {result.stdout.strip() if result.stdout.strip() else 'Could not retrieve WiFi password'}")

def show_network_info():
    """Show network adapter info."""
    ps = 'Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object Name,InterfaceDescription,LinkSpeed,MacAddress | Format-Table -AutoSize | Out-String'
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    log(f"  -> Network Adapters:\n{result.stdout.strip()[:1000]}")

def speed_test():
    """Open a speed test in browser."""
    subprocess.Popen('start "" "https://fast.com"', shell=True)
    log("  -> Opened speed test (fast.com)")


# ═══════════════════════════════════════════════════════
#  POWER & BATTERY
# ═══════════════════════════════════════════════════════

def hibernate_pc():
    """Hibernate the PC."""
    subprocess.run("shutdown /h", shell=True)
    log("  -> Hibernating...")

def cancel_shutdown():
    """Cancel a pending shutdown/restart."""
    subprocess.run("shutdown /a", shell=True)
    log("  -> Shutdown cancelled")

def set_power_plan(plan):
    """Set Windows power plan: balanced, high, saver."""
    plans = {
        "balanced":         "381b4222-f694-41f0-9685-ff5bb260df2e",
        "high performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "high":             "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "power saver":      "a1841308-3541-4fab-bc81-f71556f20b4a",
        "saver":            "a1841308-3541-4fab-bc81-f71556f20b4a",
    }
    guid = plans.get(plan.lower().strip())
    if guid:
        subprocess.run(f'powercfg /setactive {guid}', shell=True, capture_output=True)
        log(f"  -> Power plan set to {plan}")
    else:
        log(f"  -> Unknown plan: {plan}. Try: balanced, high performance, power saver")

def show_battery_level():
    """Show battery percentage."""
    ps = '(Get-WmiObject Win32_Battery).EstimatedChargeRemaining'
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    level = result.stdout.strip()
    if level:
        log(f"  -> Battery: {level}%")
    else:
        log("  -> No battery detected (desktop PC?)")

def generate_battery_report():
    """Generate a detailed battery report."""
    report_path = os.path.join(os.path.expanduser("~/Desktop"), "battery-report.html")
    subprocess.run(f'powercfg /batteryreport /output "{report_path}"', shell=True, capture_output=True)
    subprocess.Popen(f'start "" "{report_path}"', shell=True)
    log(f"  -> Battery report saved to Desktop and opened")

def set_screen_timeout(minutes):
    """Set screen timeout in minutes."""
    seconds = int(minutes) * 60
    subprocess.run(f'powercfg /change monitor-timeout-ac {minutes}', shell=True, capture_output=True)
    subprocess.run(f'powercfg /change monitor-timeout-dc {minutes}', shell=True, capture_output=True)
    log(f"  -> Screen timeout set to {minutes} minutes")

def set_sleep_timeout(minutes):
    """Set sleep timeout in minutes."""
    subprocess.run(f'powercfg /change standby-timeout-ac {minutes}', shell=True, capture_output=True)
    subprocess.run(f'powercfg /change standby-timeout-dc {minutes}', shell=True, capture_output=True)
    log(f"  -> Sleep timeout set to {minutes} minutes")


# ═══════════════════════════════════════════════════════
#  CLIPBOARD
# ═══════════════════════════════════════════════════════

def clear_clipboard():
    """Clear the clipboard."""
    subprocess.run('echo off | clip', shell=True, capture_output=True)
    log("  -> Clipboard cleared")

def open_clipboard_history():
    """Open Windows clipboard history (Win+V)."""
    ps = '(New-Object -ComObject WScript.Shell).SendKeys("^v")'
    # Actually Win+V
    ps = 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait("^v")'
    subprocess.Popen("start ms-settings:clipboard", shell=True)
    log("  -> Opened clipboard settings")


# ═══════════════════════════════════════════════════════
#  MEDIA CONTROLS
# ═══════════════════════════════════════════════════════

def media_play_pause():
    """Send media play/pause key."""
    ps = '(New-Object -ComObject WScript.Shell).SendKeys([char]179)'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Media: Play/Pause")

def media_next():
    """Send media next track key."""
    ps = '(New-Object -ComObject WScript.Shell).SendKeys([char]176)'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Media: Next track")

def media_previous():
    """Send media previous track key."""
    ps = '(New-Object -ComObject WScript.Shell).SendKeys([char]177)'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Media: Previous track")

def media_stop():
    """Send media stop key."""
    ps = '(New-Object -ComObject WScript.Shell).SendKeys([char]178)'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Media: Stopped")


# ═══════════════════════════════════════════════════════
#  WINDOW MANAGEMENT
# ═══════════════════════════════════════════════════════

def minimize_all_windows():
    """Minimize all windows (show desktop)."""
    ps = '(New-Object -ComObject Shell.Application).MinimizeAll()'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> All windows minimized")

def show_desktop():
    """Toggle show desktop."""
    ps = '(New-Object -ComObject Shell.Application).ToggleDesktop()'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Toggled desktop view")

def restore_all_windows():
    """Restore all minimized windows."""
    ps = '(New-Object -ComObject Shell.Application).UndoMinimizeAll()'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> All windows restored")

def close_current_window():
    """Close the current foreground window."""
    ps = '(New-Object -ComObject WScript.Shell).SendKeys("%{F4}")'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Sent Alt+F4 to close window")

def switch_window():
    """Send Alt+Tab."""
    ps = '(New-Object -ComObject WScript.Shell).SendKeys("%{TAB}")'
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Alt+Tab sent")

def snap_window_left():
    """Snap current window to left half."""
    ps = 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait("^({LEFT})")'
    # Actually Win+Left
    ps = '''$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys("^{ESC}"); Start-Sleep -Milliseconds 50; $wsh.SendKeys("{LEFT}")'''
    # Use keyboard shortcut properly
    ps = '''Add-Type @"
using System; using System.Runtime.InteropServices;
public class KBD {
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
}
"@
[KBD]::keybd_event(0x5B,0,0,0); [KBD]::keybd_event(0x25,0,0,0)
Start-Sleep -Milliseconds 50
[KBD]::keybd_event(0x25,0,2,0); [KBD]::keybd_event(0x5B,0,2,0)'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Window snapped left")

def snap_window_right():
    """Snap current window to right half."""
    ps = '''Add-Type @"
using System; using System.Runtime.InteropServices;
public class KBD {
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
}
"@
[KBD]::keybd_event(0x5B,0,0,0); [KBD]::keybd_event(0x27,0,0,0)
Start-Sleep -Milliseconds 50
[KBD]::keybd_event(0x27,0,2,0); [KBD]::keybd_event(0x5B,0,2,0)'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Window snapped right")

def maximize_window():
    """Maximize current window."""
    ps = '''Add-Type @"
using System; using System.Runtime.InteropServices;
public class KBD {
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
}
"@
[KBD]::keybd_event(0x5B,0,0,0); [KBD]::keybd_event(0x26,0,0,0)
Start-Sleep -Milliseconds 50
[KBD]::keybd_event(0x26,0,2,0); [KBD]::keybd_event(0x5B,0,2,0)'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Window maximized")

def minimize_window():
    """Minimize current window."""
    ps = '''Add-Type @"
using System; using System.Runtime.InteropServices;
public class KBD {
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
}
"@
[KBD]::keybd_event(0x5B,0,0,0); [KBD]::keybd_event(0x28,0,0,0)
Start-Sleep -Milliseconds 50
[KBD]::keybd_event(0x28,0,2,0); [KBD]::keybd_event(0x5B,0,2,0)'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Window minimized")


# ═══════════════════════════════════════════════════════
#  SYSTEM INFORMATION
# ═══════════════════════════════════════════════════════

def show_system_info():
    """Show basic system information."""
    ps = '''$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor
$ram = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$freeRam = [math]::Round($os.FreePhysicalMemory/1MB, 1)
Write-Host "OS: $($os.Caption) $($os.OSArchitecture)"
Write-Host "CPU: $($cpu.Name)"
Write-Host "RAM: $freeRam GB free / $ram GB total"
Write-Host "Computer: $($os.CSName)"
Write-Host "User: $env:USERNAME"'''
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    log(f"  -> System Info:\n{result.stdout.strip()}")

def show_disk_usage():
    """Show disk space usage."""
    ps = 'Get-PSDrive -PSProvider FileSystem | Select-Object Name,@{N="Used(GB)";E={[math]::Round($_.Used/1GB,1)}},@{N="Free(GB)";E={[math]::Round($_.Free/1GB,1)}},@{N="Total(GB)";E={[math]::Round(($_.Used+$_.Free)/1GB,1)}} | Format-Table -AutoSize | Out-String'
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    log(f"  -> Disk Usage:\n{result.stdout.strip()}")

def show_cpu_usage():
    """Show current CPU usage."""
    ps = "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty LoadPercentage"
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    log(f"  -> CPU Usage: {result.stdout.strip()}%")

def show_ram_usage():
    """Show current RAM usage."""
    ps = '''$os = Get-CimInstance Win32_OperatingSystem
$total = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$free = [math]::Round($os.FreePhysicalMemory/1MB, 1)
$used = [math]::Round($total - $free, 1)
$pct = [math]::Round(($used/$total)*100, 0)
Write-Host "RAM: $used GB / $total GB ($pct% used)"'''
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    log(f"  -> {result.stdout.strip()}")

def show_uptime():
    """Show system uptime."""
    ps = '(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime | ForEach-Object { "Uptime: $($_.Days)d $($_.Hours)h $($_.Minutes)m" }'
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    log(f"  -> {result.stdout.strip()}")

def show_windows_version():
    """Show Windows version details."""
    ps = '[System.Environment]::OSVersion.VersionString + "`n" + (Get-CimInstance Win32_OperatingSystem).Caption'
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    log(f"  -> {result.stdout.strip()}")

def show_startup_apps():
    """List apps that run at startup."""
    ps = 'Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location | Format-Table -AutoSize -Wrap | Out-String -Width 200'
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    log(f"  -> Startup apps:\n{result.stdout.strip()[:1500]}")

def show_installed_apps():
    """List installed programs."""
    ps = 'Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Where-Object {$_.DisplayName} | Select-Object DisplayName,DisplayVersion | Sort-Object DisplayName | Format-Table -AutoSize | Out-String -Width 200'
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
    log(f"  -> Installed Apps:\n{result.stdout.strip()[:2000]}")


# ═══════════════════════════════════════════════════════
#  SECURITY & MAINTENANCE
# ═══════════════════════════════════════════════════════

def run_virus_scan():
    """Start a quick Windows Defender scan."""
    ps = 'Start-MpScan -ScanType QuickScan'
    subprocess.Popen(["powershell", "-Command", ps])
    log("  -> Windows Defender quick scan started (runs in background)")

def run_full_virus_scan():
    """Start a full Windows Defender scan."""
    ps = 'Start-MpScan -ScanType FullScan'
    subprocess.Popen(["powershell", "-Command", ps])
    log("  -> Windows Defender full scan started (may take a while)")

def update_defender():
    """Update Windows Defender definitions."""
    ps = 'Update-MpSignature'
    subprocess.Popen(["powershell", "-Command", ps])
    log("  -> Updating Windows Defender definitions...")

def check_windows_update():
    """Open Windows Update settings."""
    subprocess.Popen("start ms-settings:windowsupdate", shell=True)
    log("  -> Opened Windows Update")

def open_firewall():
    """Open Windows Firewall settings."""
    subprocess.Popen("start ms-settings:windowsdefender", shell=True)
    log("  -> Opened Windows Security")

def clear_temp_files():
    """Clear temporary files."""
    temp = os.environ.get("TEMP", "")
    if temp:
        ps = f'Remove-Item "{temp}\\*" -Recurse -Force -ErrorAction SilentlyContinue'
        subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Temp files cleared")

def disk_cleanup():
    """Open disk cleanup utility."""
    subprocess.Popen("cleanmgr.exe", shell=True)
    log("  -> Disk Cleanup opened")


# ═══════════════════════════════════════════════════════
#  INPUT & ACCESSIBILITY
# ═══════════════════════════════════════════════════════

def open_onscreen_keyboard():
    """Open the on-screen keyboard."""
    subprocess.Popen("osk.exe", shell=True)
    log("  -> On-screen keyboard opened")

def open_emoji_panel():
    """Open the emoji picker (Win+.)."""
    ps = '''Add-Type @"
using System; using System.Runtime.InteropServices;
public class KBD2 {
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
}
"@
[KBD2]::keybd_event(0x5B,0,0,0); [KBD2]::keybd_event(0xBE,0,0,0)
Start-Sleep -Milliseconds 50
[KBD2]::keybd_event(0xBE,0,2,0); [KBD2]::keybd_event(0x5B,0,2,0)'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Emoji panel opened")

def open_magnifier():
    """Open Windows Magnifier."""
    subprocess.Popen("magnify.exe", shell=True)
    log("  -> Magnifier opened")

def open_narrator():
    """Open Windows Narrator."""
    subprocess.Popen("narrator.exe", shell=True)
    log("  -> Narrator started")

def toggle_focus_assist(on=True):
    """Open Focus Assist settings."""
    subprocess.Popen("start ms-settings:quiethours", shell=True)
    log(f"  -> Opened Focus Assist settings")


# ═══════════════════════════════════════════════════════
#  TIME, DATE & PRODUCTIVITY
# ═══════════════════════════════════════════════════════

def show_datetime():
    """Show current date and time."""
    now = datetime.datetime.now()
    log(f"  -> {now.strftime('%A, %B %d, %Y  %I:%M:%S %p')}")

def set_timer(minutes):
    """Open the Clock app for a timer."""
    subprocess.Popen("start ms-clock:timer", shell=True)
    log(f"  -> Clock app opened (set a {minutes}-minute timer)")

def set_alarm():
    """Open the Clock app alarms."""
    subprocess.Popen("start ms-clock:alarm", shell=True)
    log("  -> Clock app opened (alarms)")

def open_run_dialog():
    """Open the Run dialog (Win+R)."""
    ps = '''Add-Type @"
using System; using System.Runtime.InteropServices;
public class KBD3 {
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
}
"@
[KBD3]::keybd_event(0x5B,0,0,0); [KBD3]::keybd_event(0x52,0,0,0)
Start-Sleep -Milliseconds 50
[KBD3]::keybd_event(0x52,0,2,0); [KBD3]::keybd_event(0x5B,0,2,0)'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Run dialog opened")

def open_task_view():
    """Open Task View (Win+Tab)."""
    ps = '''Add-Type @"
using System; using System.Runtime.InteropServices;
public class KBD4 {
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
}
"@
[KBD4]::keybd_event(0x5B,0,0,0); [KBD4]::keybd_event(0x09,0,0,0)
Start-Sleep -Milliseconds 50
[KBD4]::keybd_event(0x09,0,2,0); [KBD4]::keybd_event(0x5B,0,2,0)'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Task View opened")

def open_action_center():
    """Open Action Center / Notification Center."""
    ps = '''Add-Type @"
using System; using System.Runtime.InteropServices;
public class KBD5 {
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
}
"@
[KBD5]::keybd_event(0x5B,0,0,0); [KBD5]::keybd_event(0x41,0,0,0)
Start-Sleep -Milliseconds 50
[KBD5]::keybd_event(0x41,0,2,0); [KBD5]::keybd_event(0x5B,0,2,0)'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Action Center opened")

def new_virtual_desktop():
    """Create a new virtual desktop."""
    ps = '''Add-Type @"
using System; using System.Runtime.InteropServices;
public class KBD6 {
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
}
"@
[KBD6]::keybd_event(0x5B,0,0,0); [KBD6]::keybd_event(0x11,0,0,0); [KBD6]::keybd_event(0x44,0,0,0)
Start-Sleep -Milliseconds 50
[KBD6]::keybd_event(0x44,0,2,0); [KBD6]::keybd_event(0x11,0,2,0); [KBD6]::keybd_event(0x5B,0,2,0)'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> New virtual desktop created")

def close_virtual_desktop():
    """Close current virtual desktop."""
    ps = '''Add-Type @"
using System; using System.Runtime.InteropServices;
public class KBD7 {
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
}
"@
[KBD7]::keybd_event(0x5B,0,0,0); [KBD7]::keybd_event(0x11,0,0,0); [KBD7]::keybd_event(0x73,0,0,0)
Start-Sleep -Milliseconds 50
[KBD7]::keybd_event(0x73,0,2,0); [KBD7]::keybd_event(0x11,0,2,0); [KBD7]::keybd_event(0x5B,0,2,0)'''
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    log("  -> Virtual desktop closed")


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
    "dark mode":    (lambda: toggle_dark_mode(True),   lambda: toggle_dark_mode(False)),
    "light mode":   (lambda: toggle_dark_mode(False),  lambda: toggle_dark_mode(True)),
    "dark theme":   (lambda: toggle_dark_mode(True),   lambda: toggle_dark_mode(False)),
    "color filter":  (lambda: toggle_color_filter(True), lambda: toggle_color_filter(False)),
    "high contrast": (lambda: toggle_high_contrast(True), lambda: toggle_high_contrast(False)),
    "focus assist":  (lambda: toggle_focus_assist(True), lambda: toggle_focus_assist(False)),
    "do not disturb":(lambda: toggle_focus_assist(True), lambda: toggle_focus_assist(False)),
    "dnd":           (lambda: toggle_focus_assist(True), lambda: toggle_focus_assist(False)),
    "taskbar auto hide": (lambda: toggle_taskbar_autohide(True), lambda: toggle_taskbar_autohide(False)),
    "narrator":      (lambda: open_narrator(),  lambda: subprocess.run('taskkill /IM narrator.exe /F', shell=True, capture_output=True)),
    "magnifier":     (lambda: open_magnifier(), lambda: subprocess.run('taskkill /IM magnify.exe /F', shell=True, capture_output=True)),
}

def smart_execute(text):
    """Parse user input with keywords and execute the right action.
    Returns True if handled, False if needs AI fallback."""
    text_lower = text.lower().strip()

    # --- Detect ON/OFF intent ---
    wants_on = any(w in text_lower for w in ["turn on", "enable", "activate", "switch on", "start "])
    wants_off = any(w in text_lower for w in ["turn off", "disable", "deactivate", "switch off", "stop "])

    # --- Toggle hardware features (bluetooth, wifi, dark mode, etc.) ---
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
    if "max volume" in text_lower or "full volume" in text_lower:
        set_volume(100)
        return True

    # --- Brightness ---
    br_match = re.search(r'(?:set\s+)?brightness\s+(?:to\s+)?(\d+)', text_lower)
    if br_match:
        set_brightness(int(br_match.group(1)))
        return True
    if any(w in text_lower for w in ["brighter", "increase brightness", "brightness up", "max brightness"]):
        set_brightness(80 if "max" not in text_lower else 100)
        return True
    if any(w in text_lower for w in ["dimmer", "dim", "decrease brightness", "brightness down", "min brightness"]):
        set_brightness(30 if "min" not in text_lower else 5)
        return True

    # --- Media controls ---
    if any(w in text_lower for w in ["play pause", "play/pause", "pause music", "resume music", "pause media", "play media"]):
        media_play_pause()
        return True
    if any(w in text_lower for w in ["next track", "next song", "skip song", "skip track"]):
        media_next()
        return True
    if any(w in text_lower for w in ["previous track", "previous song", "last song", "go back song"]):
        media_previous()
        return True
    if any(w in text_lower for w in ["stop music", "stop media", "stop playing"]):
        media_stop()
        return True

    # --- Process/Task management ---
    kill_match = re.search(r'(?:kill|close|end|terminate|force close|quit)\s+(?:the\s+)?(?:app\s+)?(?:process\s+)?(.+?)(?:\s+app|\s+process|\s*$)', text_lower)
    if kill_match and not any(w in text_lower for w in ["window", "desktop", "virtual"]):
        target = kill_match.group(1).strip()
        if target and target not in ("my", "the", "a", "all"):
            kill_process(target)
            return True
    if any(w in text_lower for w in ["list running", "running apps", "running processes", "what's running", "show processes", "task list"]):
        list_running_apps()
        return True

    # --- Window management ---
    if any(w in text_lower for w in ["minimize all", "show desktop", "hide all"]):
        minimize_all_windows()
        return True
    if any(w in text_lower for w in ["restore all", "show all windows", "unhide all"]):
        restore_all_windows()
        return True
    if "close window" in text_lower or "close this window" in text_lower:
        close_current_window()
        return True
    if "alt tab" in text_lower or "switch window" in text_lower:
        switch_window()
        return True
    if "snap left" in text_lower or "snap window left" in text_lower:
        snap_window_left()
        return True
    if "snap right" in text_lower or "snap window right" in text_lower:
        snap_window_right()
        return True
    if "maximize window" in text_lower or "maximize this" in text_lower or "full screen" in text_lower:
        maximize_window()
        return True
    if "minimize window" in text_lower or "minimize this" in text_lower:
        minimize_window()
        return True
    if "new desktop" in text_lower or "new virtual desktop" in text_lower or "create desktop" in text_lower:
        new_virtual_desktop()
        return True
    if "close desktop" in text_lower or "close virtual desktop" in text_lower or "remove desktop" in text_lower:
        close_virtual_desktop()
        return True
    if "task view" in text_lower:
        open_task_view()
        return True

    # --- System actions ---
    if "screenshot" in text_lower or "screen shot" in text_lower or "snip" in text_lower or "screen capture" in text_lower:
        take_screenshot()
        return True
    if "lock" in text_lower and any(w in text_lower for w in ["screen", "computer", "pc", "laptop", "my"]):
        lock_screen()
        return True
    if "shut down" in text_lower or "shutdown" in text_lower:
        shutdown_pc()
        return True
    if "cancel shutdown" in text_lower or "abort shutdown" in text_lower or "stop shutdown" in text_lower:
        cancel_shutdown()
        return True
    if "restart" in text_lower or "reboot" in text_lower:
        restart_pc()
        return True
    if "hibernate" in text_lower:
        hibernate_pc()
        return True
    if "sleep" in text_lower and not "sleep timeout" in text_lower:
        sleep_pc()
        return True
    if "log off" in text_lower or "logoff" in text_lower or "sign out" in text_lower:
        logoff_pc()
        return True

    # --- Power plan ---
    power_match = re.search(r'(?:power plan|power mode|set power)\s+(?:to\s+)?(.+)', text_lower)
    if power_match:
        set_power_plan(power_match.group(1).strip())
        return True
    if "high performance" in text_lower and "power" in text_lower:
        set_power_plan("high performance")
        return True
    if "power saver" in text_lower or "battery saver" in text_lower:
        set_power_plan("power saver")
        return True
    if "balanced" in text_lower and "power" in text_lower:
        set_power_plan("balanced")
        return True

    # --- Screen/sleep timeout ---
    screen_timeout_match = re.search(r'screen\s+timeout\s+(?:to\s+)?(\d+)', text_lower)
    if screen_timeout_match:
        set_screen_timeout(int(screen_timeout_match.group(1)))
        return True
    sleep_timeout_match = re.search(r'sleep\s+timeout\s+(?:to\s+)?(\d+)', text_lower)
    if sleep_timeout_match:
        set_sleep_timeout(int(sleep_timeout_match.group(1)))
        return True

    # --- Resolution ---
    res_match = re.search(r'resolution\s+(?:to\s+)?(\d{3,4})\s*[x×]\s*(\d{3,4})', text_lower)
    if res_match:
        set_screen_resolution(int(res_match.group(1)), int(res_match.group(2)))
        return True

    # --- Battery & System info ---
    if any(w in text_lower for w in ["battery level", "battery status", "battery percentage", "how much battery", "charge level"]):
        show_battery_level()
        return True
    if "battery report" in text_lower:
        generate_battery_report()
        return True
    if any(w in text_lower for w in ["system info", "system information", "my specs", "pc specs", "computer specs", "about my pc", "about my computer"]):
        show_system_info()
        return True
    if any(w in text_lower for w in ["disk space", "disk usage", "storage space", "free space", "drive space"]):
        show_disk_usage()
        return True
    if any(w in text_lower for w in ["cpu usage", "processor usage", "cpu load"]):
        show_cpu_usage()
        return True
    if any(w in text_lower for w in ["ram usage", "memory usage", "free ram", "used ram"]):
        show_ram_usage()
        return True
    if any(w in text_lower for w in ["uptime", "how long running", "boot time"]):
        show_uptime()
        return True
    if any(w in text_lower for w in ["windows version", "os version", "which windows"]):
        show_windows_version()
        return True
    if any(w in text_lower for w in ["startup apps", "startup programs", "startup list"]):
        show_startup_apps()
        return True
    if any(w in text_lower for w in ["installed apps", "installed programs", "installed software", "list apps"]):
        show_installed_apps()
        return True

    # --- Network info ---
    if any(w in text_lower for w in ["my ip", "ip address", "show ip", "what is my ip"]):
        if "public" in text_lower:
            show_public_ip()
        else:
            show_ip_address()
        return True
    if "public ip" in text_lower:
        show_public_ip()
        return True
    ping_match = re.search(r'ping\s+(.+)', text_lower)
    if ping_match:
        ping_host(ping_match.group(1).strip())
        return True
    if "flush dns" in text_lower or "clear dns" in text_lower:
        flush_dns()
        return True
    if any(w in text_lower for w in ["wifi password", "show password", "network password"]):
        show_wifi_password()
        return True
    if any(w in text_lower for w in ["network info", "network status", "network adapters", "connection info"]):
        show_network_info()
        return True
    if any(w in text_lower for w in ["speed test", "internet speed", "test speed", "bandwidth"]):
        speed_test()
        return True

    # --- File/Folder management ---
    folder_match = re.search(r'(?:open|go to|show)\s+(?:my\s+)?(?:the\s+)?(downloads|documents|desktop|pictures|videos|music|home|appdata|temp|c drive|d drive|c:|d:)', text_lower)
    if folder_match:
        open_folder(folder_match.group(1))
        return True
    if "empty recycle" in text_lower or "empty trash" in text_lower or "clear recycle" in text_lower:
        empty_recycle_bin()
        return True
    create_match = re.search(r'create\s+(?:a\s+)?(?:new\s+)?folder\s+(?:called\s+|named\s+)?(.+)', text_lower)
    if create_match:
        create_folder(create_match.group(1).strip())
        return True

    # --- Clipboard ---
    if "clear clipboard" in text_lower or "empty clipboard" in text_lower:
        clear_clipboard()
        return True
    if "clipboard history" in text_lower or "clipboard settings" in text_lower:
        open_clipboard_history()
        return True

    # --- Security & Maintenance ---
    if any(w in text_lower for w in ["virus scan", "scan for virus", "quick scan", "malware scan", "defender scan"]):
        if "full" in text_lower:
            run_full_virus_scan()
        else:
            run_virus_scan()
        return True
    if "update defender" in text_lower or "defender update" in text_lower or "update virus" in text_lower:
        update_defender()
        return True
    if "windows update" in text_lower or "check for updates" in text_lower or "update windows" in text_lower:
        check_windows_update()
        return True
    if "firewall" in text_lower:
        open_firewall()
        return True
    if any(w in text_lower for w in ["clear temp", "delete temp", "clean temp"]):
        clear_temp_files()
        return True
    if any(w in text_lower for w in ["disk cleanup", "clean disk", "free up space"]):
        disk_cleanup()
        return True

    # --- Input & Accessibility ---
    if any(w in text_lower for w in ["on-screen keyboard", "onscreen keyboard", "virtual keyboard", "screen keyboard"]):
        open_onscreen_keyboard()
        return True
    if any(w in text_lower for w in ["emoji", "emoji panel", "emoji picker"]):
        open_emoji_panel()
        return True

    # --- Productivity ---
    if any(w in text_lower for w in ["what time", "current time", "what date", "current date", "what day"]):
        show_datetime()
        return True
    timer_match = re.search(r'(?:set\s+)?(?:a\s+)?timer\s+(?:for\s+)?(\d+)', text_lower)
    if timer_match:
        set_timer(int(timer_match.group(1)))
        return True
    if "alarm" in text_lower:
        set_alarm()
        return True
    if "run dialog" in text_lower or "run box" in text_lower:
        open_run_dialog()
        return True
    if "action center" in text_lower or "notification center" in text_lower or "notifications panel" in text_lower:
        open_action_center()
        return True

    # --- Web search ---
    search_match = re.search(r'(?:search|google|look up|find|bing)\s+(?:for\s+)?(.+)', text_lower)
    if search_match:
        web_search(search_match.group(1).strip())
        return True

    # --- Open website ---
    url_match = re.search(r'(?:open|go to|visit|browse)\s+((?:https?://)?(?:www\.)?[\w.-]+\.\w{2,}(?:/\S*)?)', text_lower)
    if url_match:
        open_website(url_match.group(1).strip())
        return True

    # --- Open settings page (only if user says 'settings' or 'open') ---
    if any(w in text_lower for w in ["settings", "open", "show", "go to", "launch"]):
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
