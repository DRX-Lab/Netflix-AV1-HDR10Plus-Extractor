import os
import shutil
import subprocess
import re
import argparse
import time
from colorama import Fore, Style, init

init(autoreset=True)

parser = argparse.ArgumentParser(description="Extract HDR10+ from Netflix AV1 MKV.")
parser.add_argument( "-i", "--input", help="Input Netflix AV1 MKV file.", required=True)
args = parser.parse_args()

input_file = args.input

print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Input file: {input_file}")

if not os.path.isfile(input_file):
    print(f"{Fore.RED}✖ File not found: {input_file}")
    exit(1)

print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Checking required binaries...")

TOOLS_PATH = "tools"
BINARIES = {
    "HandBrakeCLI_exe":  os.path.join(TOOLS_PATH, "HandBrakeCLI.exe"),
    "ffmpeg_exe": os.path.join(TOOLS_PATH, "ffmpeg.exe"),
    "hdr10plus_tool_exe": os.path.join(TOOLS_PATH, "hdr10plus_tool.exe"),
}

if not os.path.isdir(TOOLS_PATH):
    print(f"{Fore.RED}✖ Missing required folder: {TOOLS_PATH}")
    print(f"{Fore.RED}✖ Process cannot continue. Please create the missing folder and add the required binaries.")
    exit(1)

missing_binaries = [name for name, binary in BINARIES.items() if not shutil.which(binary)]
if missing_binaries:
    print(f"{Fore.RED}✖ Missing required binaries: {', '.join(missing_binaries)}")
    print(f"{Fore.RED}✖ Process cannot continue. Please install the missing dependencies.")
    exit(1)

print(f"{Fore.GREEN}✔ All required binaries found.")

base_name = os.path.splitext(os.path.basename(input_file))[0]
temp_hevc_file = f"{base_name}__encoded.hevc.mkv"
json_output = f"{base_name}.hdr10plus.json"
plot_output = f"{base_name}.hdr10plus_plot.png"

print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Output HEVC: {temp_hevc_file}")
print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Output JSON: {json_output}")
print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Output Plot: {plot_output}")

print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Starting conversion from AV1 HDR10+ to HEVC HDR10+...")

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

command = [
    BINARIES["HandBrakeCLI_exe"],
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

print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Launching HandBrakeCLI...")
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
    print(f"{Fore.RED}✖ HandBrakeCLI failed with exit code {process.returncode}")
    exit(1)
print(f"{Fore.GREEN}✔ Encoding completed.")

print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Extracting HDR10+ metadata from HEVC...")

ffmpeg_command = (
    f'"{BINARIES["ffmpeg_exe"]}" '
    f'-y '
    f'-nostdin '
    f'-loglevel error '
    f'-stats '
    f'-i "{temp_hevc_file}" '
    f'-c:v copy '
    f'-bsf:v hevc_mp4toannexb '
    f'-f hevc - | '
    f'"{BINARIES["hdr10plus_tool_exe"]}" '
    f'extract - '
    f'-o "{json_output}"'
)

print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Running ffmpeg and hdr10plus_tool...")

try:
    subprocess.run(ffmpeg_command, check=True, shell=True)
    print(f"{Fore.GREEN}✔ HDR10+ metadata extracted successfully to: {json_output}")
except subprocess.CalledProcessError as e:
    print(f"{Fore.RED}✖ Metadata extraction failed: {e}")
    if os.path.exists(temp_hevc_file):
        os.remove(temp_hevc_file)
        print(f"{Fore.YELLOW}⚠ Deleted temporary file: {temp_hevc_file}")
    exit(1)

print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Generating HDR10+ plot image...")

hdr10plus_plot_command = [
    BINARIES["hdr10plus_tool_exe"], "plot",
    json_output, "-t", "HDR10+ Plot",
    "-o", plot_output
]

try:
    subprocess.run(hdr10plus_plot_command, check=True)
    print(f"{Fore.GREEN}✔ Plot saved to: {plot_output}")
except subprocess.CalledProcessError as e:
    print(f"{Fore.RED}✖ Plot generation failed: {e}")
    if os.path.exists(temp_hevc_file):
        os.remove(temp_hevc_file)
        print(f"{Fore.YELLOW}⚠ Deleted temporary file: {temp_hevc_file}")
    exit(1)

if os.path.exists(temp_hevc_file):
    os.remove(temp_hevc_file)
    print(f"{Fore.YELLOW}⚠ Deleted temporary file: {temp_hevc_file}")

print(f"{Fore.GREEN}✔ All processing steps completed successfully.")