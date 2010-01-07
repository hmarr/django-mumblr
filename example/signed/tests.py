from django.conf import settings
import signed

from unittest import TestCase

class TestSignature(TestCase):
    
    def test_signature(self):
        "signature() function should generate a signature"
        for s in (
            'hello',
            '3098247:529:087:',
            u'\u2019'.encode('utf8'),
        ):
            self.assertEqual(
                signed.signature(s),
                signed.base64_hmac(s, settings.SECRET_KEY)
            )
    
    def test_signature_optional_arguments(self):
        "signature(value, key=..., extra_key=...) should work"
        self.assertEqual(
            signed.signature('hello', key='this-is-the-key'),
            signed.base64_hmac('hello', 'this-is-the-key')
        )
        self.assertEqual(
            signed.signature('hello', key='this-is-the-key', extra_key='X'),
            signed.base64_hmac('hello', 'this-is-the-keyX')
        )
        self.assertEqual(
            signed.signature('hello', extra_key='X'),
            signed.base64_hmac('hello', settings.SECRET_KEY + 'X')
        )

class TestSignUnsign(TestCase):

    def test_sign_unsign_no_unicode(self):
        "sign/unsign functions should not accept unicode strings"
        self.assertRaises(TypeError, signed.sign, u'\u2019')
        self.assertRaises(TypeError, signed.unsign, u'\u2019')
    
    def test_sign_uses_correct_key(self):
        "If a key is provided, sign should use it; otherwise, use SECRET_KEY"
        s = 'This is a string'
        self.assertEqual(
            signed.sign(s),
            s + '.' + signed.base64_hmac(s, settings.SECRET_KEY)
        )
        self.assertEqual(
            signed.sign(s, 'sekrit'),
            s + '.' + signed.base64_hmac(s, 'sekrit')
        )
    
    def sign_is_reversible(self):
        "sign/unsign should be reversible against any bytestring"
        examples = (
            'q;wjmbk;wkmb',
            '3098247529087',
            '3098247:529:087:',
            'jkw osanteuh ,rcuh nthu aou oauh ,ud du',
            u'\u2019'.encode('utf8'),
        )
        for example in examples:
            self.assert_(example != signed.sign(example))
            self.assertEqual(example, signed.unsign(utils.sign(example)))
    
    def unsign_detects_tampering(self):
        "unsign should raise an exception if the value has been tampered with"
        value = 'Another string'
        signed_value = signed.sign(value)
        transforms = (
            lambda s: s.upper(),
            lambda s: s + 'a',
            lambda s: 'a' + s[1:],
            lambda s: s.replace(':', ''),
        )
        self.assertEqual(value, signed.unsign(signed_value))
        for transform in transforms:
            self.assertRaises(
                signed.BadSignature, signed.unsign, transform(signed_value)
            )

class TestDumpsLoad(TestCase):
    
    def test_dumps_loads(self):
        "dumps and loads should work reversibly for any picklable object"
        objects = (
            ['a', 'list'],
            'a string',
            u'a unicode string \u2019',
            {'a': 'dictionary'},
        )
        for o in objects:
            self.assert_(o != signed.dumps(o))
            self.assertEqual(o, signed.loads(signed.dumps(o)))
    
    def test_decode_detects_tampering(self):
        "loads should raise exception for tampered objects"
        transforms = (
            lambda s: s.upper(),
            lambda s: s + 'a',
            lambda s: 'a' + s[1:],
            lambda s: s.replace('.', ''),
        )
        value = {'foo': 'bar', 'baz': 1}
        encoded = signed.dumps(value)
        self.assertEqual(value, signed.loads(encoded))
        for transform in transforms:
            self.assertRaises(
                signed.BadSignature, signed.loads, transform(encoded)
            )

class TestBaseConv(TestCase):
    
    def test_baseconv(self):
        from baseconv import base2, base16, base36, base62
        nums = [-10 ** 10, 10 ** 10] + range(-100, 100)
        for convertor in [base2, base16, base36, base62]:
            for i in nums:
                self.assertEqual(
                    i, convertor.to_int(convertor.from_int(i))
                )
