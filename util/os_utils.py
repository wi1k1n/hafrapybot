import platform

def Windows():
    return platform.system() == "Windows"
def Linux():
    return platform.system() == "Linux"