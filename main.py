import os
import sys
import subprocess
import re
import argparse
import time
import platform
from colorama import Fore, Style, init

init(autoreset=True)

def get_executable_name(name):
    """Return executable name with .exe on Windows."""
    return f"{name}.exe" if platform.system().lower() == "windows" else name

def check_tool(executable, display_name):
    """Check if a tool exists in current directory."""
    location = os.path.join(os.getcwd(), executable)
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Checking for {display_name}...")
    if not os.path.isfile(location):
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Missing tool: {os.path.basename(location)}")
        sys.exit(1)
    print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} Found {display_name}: {os.path.basename(location)}")
    return location

def get_display_name(path):
    """Return basename if file, folder name if directory."""
    if os.path.isdir(path):
        return os.path.basename(os.path.abspath(path))
    return os.path.basename(path)

def remove_temp_file(path):
    """Delete a temporary file if it exists."""
    if os.path.exists(path):
        os.remove(path)
        print(f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} Deleted temporary file: {get_display_name(path)}")

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Running: {description}")
    try:
        subprocess.run(command, check=True, shell=True)
        print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} Completed: {description}")
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed: {description} ({e})")
        sys.exit(1)

def format_hhmmss(seconds):
    seconds = int(seconds)
    return time.strftime("%H:%M:%S", time.gmtime(seconds))

def parse_eta_to_seconds(eta_str):
    match = re.match(r"(\d{2})h(\d{2})m(\d{2})s", eta_str)
    if match:
        h, m, s = map(int, match.groups())
        return h * 3600 + m * 60 + s
    return 0

def display_progress_bar(progress, eta_str, elapsed_seconds):
    bar_length = 60
    filled = int(bar_length * progress)
    eta_seconds = parse_eta_to_seconds(eta_str)
    print(
        f"[{'■' * filled}{' ' * (bar_length - filled)}] "
        f"{int(progress * 100)}% "
        f"Elapsed: {format_hhmmss(elapsed_seconds)} | "
        f"Remaining: {format_hhmmss(eta_seconds)}",
        end='\r'
    )

# === Argument Parsing ===
parser = argparse.ArgumentParser(description="Extract HDR10+ from Netflix AV1 MKV.")
parser.add_argument("-i", "--input", help="Input Netflix AV1 MKV file.", required=True)
args = parser.parse_args()

input_file = args.input
print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Input file: {get_display_name(input_file)}")

if not os.path.isfile(input_file):
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} File not found: {get_display_name(input_file)}")
    sys.exit(1)

# === Tools ===
TOOLS_PATH = "tools"
handbrake = check_tool(os.path.join(TOOLS_PATH, get_executable_name("HandBrakeCLI")), "HandBrakeCLI")
ffmpeg = check_tool(os.path.join(TOOLS_PATH, get_executable_name("ffmpeg")), "FFmpeg")
hdr10plus_tool = check_tool(os.path.join(TOOLS_PATH, get_executable_name("hdr10plus_tool")), "HDR10+ Tool")

# === Output Files ===
base_name = os.path.splitext(os.path.basename(input_file))[0]
temp_hevc_file = f"{base_name}__encoded.hevc.mkv"
json_output = f"{base_name}.hdr10plus.json"
plot_output = f"{base_name}.hdr10plus_plot.png"

print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Output HEVC: {get_display_name(temp_hevc_file)}")
print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Output JSON: {get_display_name(json_output)}")
print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Output Plot: {get_display_name(plot_output)}")
print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Starting conversion from AV1 HDR10+ to HEVC HDR10+...")

# === HandBrake Encoding ===
command = [
    handbrake,
    "-i", input_file,
    "-o", temp_hevc_file,
    "--encoder", "x265_10bit",
    "--encoder-preset", "ultrafast",
    "--quality", "0",
    "--vb", "100",
    "--width", "608",
    "--height", "342",
    "--crop", "0:0:0:0",
    "--format", "av_mkv",
    "--audio", "none",
    "--subtitle", "none"
]

progress_pattern = r'(\d+\.\d+)\s%\s.*ETA\s(\d{2}h\d{2}m\d{2}s)'
previous_progress = -1
start_time = time.time()

process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    bufsize=1,
    universal_newlines=True
)

print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Monitoring encoding progress...\n")
for line in process.stdout:
    match = re.search(progress_pattern, line.strip())
    if match:
        progress = float(match.group(1)) / 100
        eta = match.group(2)
        if progress != previous_progress:
            elapsed = time.time() - start_time
            display_progress_bar(progress, eta, elapsed)
            previous_progress = progress

process.stdout.close()
process.wait()
print()

if process.returncode != 0:
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} HandBrakeCLI failed with exit code {process.returncode}")
    sys.exit(1)
print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} Encoding completed.")

# === HDR10+ Metadata Extraction ===
ffmpeg_command = (
    f'"{ffmpeg}" '
    f'-y '
    f'-nostdin '
    f'-loglevel error '
    f'-stats '
    f'-i "{temp_hevc_file}" '
    f'-c:v copy '
    f'-bsf:v hevc_mp4toannexb '
    f'-f hevc - | '
    f'"{hdr10plus_tool}" '
    f'extract - '
    f'-o "{json_output}"'
)
run_command(ffmpeg_command, f"Extract HDR10+ metadata from {get_display_name(temp_hevc_file)}")

# === HDR10+ Plot Generation ===
hdr10plus_plot_command = [
    hdr10plus_tool, "plot",
    json_output, "-t", "HDR10+ Plot",
    "-o", plot_output
]
run_command(hdr10plus_plot_command, f"Generate HDR10+ plot: {get_display_name(plot_output)}")

# === Cleanup ===
remove_temp_file(temp_hevc_file)
print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} All processing steps completed successfully.")