from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safer_getattr, guarded_setattr, guarded_iter_unpack_sequence, guarded_unpack_sequence

class PrintCollector:
    def __init__(self, _getattr=None):
        self.txt = []
        self._getattr = _getattr

    def write(self, s):
        self.txt.append(s)

    def _call_print(self, *args, **kwargs):
        for arg in args:
            self.write(str(arg))
        self.write("\n")

    def __str__(self):
        return "".join(self.txt)

code_str = 'print("hello", "world")'
byte_code = compile_restricted(code_str, '<string>', 'exec')

glob = {
    '_print_': lambda _getattr=None: PrintCollector(_getattr),
    '_getattr_': safer_getattr,
    '_getitem_': lambda obj, key: obj[key],
    '_setattr_': guarded_setattr,
    '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
    '_unpack_sequence_': guarded_unpack_sequence,
    '_getiter_': iter,
    '_write_': lambda x: x,
    '__builtins__': {}
}

loc = {}
try:
    exec(byte_code, glob, loc)
    print("SUCCESS")
    print("LOCALS:", loc)
except Exception as e:
    print("FAILED:", type(e).__name__, e)
