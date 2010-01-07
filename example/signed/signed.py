"""
Functions for creating and restoring url-safe signed JSON objects.

The format used looks like this:

>>> signed.dumps("hello")
'ImhlbGxvIg.RjVSUCt6S64WBilMYxG89-l0OA8'

There are two components here, separatad by a '.'. The first component is a 
URLsafe base64 encoded JSON of the object passed to dumps(). The second 
component is a base64 encoded hmac/SHA1 hash of "$first_component.$secret"

signed.loads(s) checks the signature and returns the deserialised object. 
If the signature fails, a BadSignature exception is raised.

>>> signed.loads("ImhlbGxvIg.RjVSUCt6S64WBilMYxG89-l0OA8")
u'hello'
>>> signed.loads("ImhlbGxvIg.RjVSUCt6S64WBilMYxG89-l0OA8-modified")
...
BadSignature: Signature failed: RjVSUCt6S64WBilMYxG89-l0OA8-modified

You can optionally compress the JSON prior to base64 encoding it to save 
space, using the compress=True argument. This checks if compression actually
helps and only applies compression if the result is a shorter string:

>>> signed.dumps(range(1, 20), compress=True)
'.eJwFwcERACAIwLCF-rCiILN47r-GyZVJsNgkxaFxoDgxcOHGxMKD_T7vhAml.oFq6lAAEbkHXBHfGnVX7Qx6NlZ8'

The fact that the string is compressed is signalled by the prefixed '.' at the
start of the base64 JSON.

There are 65 url-safe characters: the 64 used by url-safe base64 and the '.'. 
These functions make use of all of them.
"""

from django.conf import settings
from django.utils.hashcompat import sha_constructor
from django.utils import simplejson
import hmac, base64

def signature(value, key = None, extra_key = ''):
    "Generate a secure signature for a value"
    return base64_hmac(value, (key or settings.SECRET_KEY) + extra_key)

def dumps(obj, key = None, compress = False, extra_key = ''):
    """
    Returns URL-safe, sha1 signed base64 compressed JSON string. If key is 
    None, settings.SECRET_KEY is used instead.
    
    If compress is True (not the default) checks if compressing using zlib can
    save some space. Prepends a '.' to signify compression. This is included 
    in the signature, to protect against zip bombs.
    
    extra_key can be used to further salt the hash, in case you're worried 
    that the NSA might try to brute-force your SHA-1 protected secret.
    """
    json = simplejson.dumps(obj, separators=(',', ':'))
    is_compressed = False # Flag for if it's been compressed or not
    if compress:
        import zlib # Avoid zlib dependency unless compress is being used
        compressed = zlib.compress(json)
        if len(compressed) < (len(json) - 1):
            json = compressed
            is_compressed = True
    base64d = encode(json).strip('=')
    if is_compressed:
        base64d = '.' + base64d
    return sign(base64d, (key or settings.SECRET_KEY) + extra_key)

def loads(s, key = None, extra_key = ''):
    "Reverse of dumps(), raises ValueError if signature fails"
    if isinstance(s, unicode):
        s = s.encode('utf8') # base64 works on bytestrings, not on unicodes
    try:
        base64d = unsign(s, (key or settings.SECRET_KEY) + extra_key)
    except ValueError:
        raise
    decompress = False
    if base64d[0] == '.':
        # It's compressed; uncompress it first
        base64d = base64d[1:]
        decompress = True
    json = decode(base64d)
    if decompress:
        import zlib
        jsond = zlib.decompress(json)
    return simplejson.loads(json)

def encode(s):
    return base64.urlsafe_b64encode(s).strip('=')

def decode(s):
    return base64.urlsafe_b64decode(s + '=' * (len(s) % 4))

class BadSignature(ValueError):
    # Extends ValueError, which makes it more convenient to catch and has 
    # basically the correct semantics.
    pass

def sign(value, key = None, extra_key = ''):
    if isinstance(value, unicode):
        raise TypeError, \
            'sign() needs bytestring, not unicode: %s' % repr(value)
    return value + '.' + signature(value, key=key, extra_key=extra_key)

def unsign(signed_value, key = None, extra_key = ''):
    if isinstance(signed_value, unicode):
        raise TypeError, 'unsign() needs bytestring, not unicode'
    if not '.' in signed_value:
        raise BadSignature, 'Missing sig (no . found in value)'
    value, sig = signed_value.rsplit('.', 1)
    if signature(value, key=key, extra_key=extra_key) == sig:
        return value
    else:
        raise BadSignature, 'Signature failed: %s' % sig

def base64_hmac(value, key):
    return encode(hmac.new(key, value, sha_constructor).digest())


# BELOW: First attempt at turning this lot in to a class

class Signer(object):
    def __init__(self, key = None, previous_key = None):
        self.key = key or settings.SECRET_KEY
        self.previous_key = previous_key or getattr(
            settings, 'PREVIOUS_SECRET_KEY', None
        )

    def signature(self, value, key = None, extra_key = ''):
        key = key or self.key
        return base64_hmac(value, (key or settings.SECRET_KEY) + extra_key)

    def serialize(self, obj):
        return simplejson.dumps(obj, separators=(',', ':'))

    def unserialize(self, bytes):
        return simplejson.loads(bytes)

    def asciiencode(self, s):
        return base64.urlsafe_b64encode(s).strip('=')

    def asciidecode(self, s):
        return base64.urlsafe_b64decode(s + '=' * (len(s) % 4))

    def dumps(self,obj, key = None, compress = False, extra_key = ''):
        """
        Returns URL-safe, sha1 signed base64 compressed JSON string. If key is 
        None, settings.SECRET_KEY is used instead.

        If compress is True (not the default) checks if compressing using zlib can
        save some space. Prepends a '.' to signify compression. This is included 
        in the signature, to protect against zip bombs.

        extra_key can be used to further salt the hash, in case you're worried 
        that the NSA might try to brute-force your SHA-1 protected secret.
        """
        key = key or self.key
        serialized = self.serialize(obj)

        is_compressed = False # Flag for if it's been compressed or not
        if compress:
            import zlib # Avoid zlib dependency unless compress is being used
            compressed = zlib.compress(serialized)
            if len(compressed) < (len(serialized) - 1):
                serialized = compressed
                is_compressed = True
        base64d = self.asciiencode(serialized).strip('=')
        if is_compressed:
            base64d = '.' + base64d
        return self.sign(base64d, key + extra_key)

    def loads(self, s, key = None, extra_key = ''):
        "Reverse of dumps(), raises ValueError if signature fails"
        key = key or self.key
        if isinstance(s, unicode):
            s = s.encode('utf8') # base64 works on bytestrings, not on unicodes
        try:
            asciid = self.unsign(s, key + extra_key)
        except ValueError:
            raise
        decompress = False
        if asciid[0] == '.':
            # It's compressed; uncompress it first
            asciid = asciid[1:]
            decompress = True
        bytes = self.asciidecode(asciid)
        if decompress:
            import zlib
            bytes = zlib.decompress(bytes)
        return self.unserialize(bytes)

    def sign(self, value, key = None, extra_key = ''):
        key = key or self.key
        if isinstance(value, unicode):
            raise TypeError, \
                'sign() needs bytestring, not unicode: %s' % repr(value)
        return value + '.' + self.signature(value, key=key, extra_key=extra_key)

    def unsign(self, signed_value, key = None, extra_key = ''):
        key = key or self.key
        if isinstance(signed_value, unicode):
            raise TypeError, 'unsign() needs bytestring, not unicode'
        if not '.' in signed_value:
            raise BadSignature, 'Missing sig (no . found in value)'
        value, sig = signed_value.rsplit('.', 1)
        if self.signature(value, key=key, extra_key=extra_key) == sig:
            return value
        else:
            raise BadSignature, 'Signature failed: %s' % sig


