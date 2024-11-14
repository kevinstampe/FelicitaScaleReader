import os

def is_raspberry_pi():
    if "rpi" in str(os.uname()).lower():
        return True
    
    try:
        # Check if processor is BCM (common for Raspberry Pi models)
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "raspberry pi" in line.lower():
                    return True
                if "rpi" in line.lower():
                    return True
                
    except FileNotFoundError:
        pass

    return False