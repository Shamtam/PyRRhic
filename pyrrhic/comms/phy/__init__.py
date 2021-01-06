from .j2534 import _interfaces as j2534_interfaces

from .j2534 import J2534PassThru_ISO9141

def get_all_interfaces():
    return {
        'J2534': list(j2534_interfaces.keys()),
        'Serial': []
    }
