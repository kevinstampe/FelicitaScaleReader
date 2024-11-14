def is_raspberry_pi():
    try:
        # Check /etc/os-release for "Raspberry Pi" mention
        with open("/etc/os-release", "r") as f:
            if "Raspbian" in f.read() or "Raspberry Pi" in f.read():
                return True
    except FileNotFoundError:
        pass

    try:
        # Check if processor is BCM (common for Raspberry Pi models)
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "BCM" in line:
                    return True
    except FileNotFoundError:
        pass

    return False