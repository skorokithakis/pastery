from brake.backends import cachebe
from ipware.ip import get_ip


class MyBrake(cachebe.CacheBackend):
    def get_ip(self, request):
        return get_ip(request)
