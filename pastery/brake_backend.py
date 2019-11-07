from brake.backends import cachebe
from ipware import get_client_ip


class MyBrake(cachebe.CacheBackend):
    def get_ip(self, request):
        return get_client_ip(request)[0]
