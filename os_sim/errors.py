class OSSimError(Exception): pass
class CorruptPage(OSSimError): pass
class InvalidPage(OSSimError): pass
class WriteBarrierError(OSSimError): pass
