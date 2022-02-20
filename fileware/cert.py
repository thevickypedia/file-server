import binascii
import json
import os
import time
from getpass import getuser
from urllib.error import HTTPError
from urllib.request import urlopen

import OpenSSL


def ip_info() -> dict:
    """Gets public IP information.

    Returns:
        dict:
        JSON loaded information from public IP information.
    """
    try:
        return json.load(urlopen('https://ipinfo.io/json'))
    except HTTPError:
        pass
    try:
        return json.load(urlopen('http://ip.jsontest.com'))
    except HTTPError:
        pass
    return {}


def _get_serial() -> bytes:
    """Generates a serial number for the self-signed SSL.

    See Also:
        - This function is not called, but it is here only as a just in case measure to insert serial number manually.
        - Serial Number is a unique identifier assigned by the CA which issued the certificate.

    Returns:
        bytes:
        Encoded serial number for the certificate.
    """
    serial_hex = binascii.hexlify(os.urandom(18)).decode().upper()
    return " ".join(serial_hex[i:i + 2] for i in range(0, len(serial_hex), 2)).encode('UTF-8')


def _generate_serial_hash(byte_size: int = 18, int_size: int = 36) -> int:
    """Generates a hashed serial number.

    Args:
        byte_size: Size of the bytes object containing random bytes.
        int_size: Size of the base int.

    Returns:
        int:
        Returns the hashed serial.
    """
    return int(binascii.hexlify(os.urandom(byte_size)).decode().upper(), int_size)


def generate_cert(common_name: str,
                  email_address: str = None,
                  country_name: str = None,
                  locality_name: str = None,
                  state_or_province_name: str = None,
                  organization_name: str = None,
                  organization_unit_name: str = "Information Technology",
                  validity_start_in_seconds: int = 0,
                  validity_end_in_seconds: int = 10 * 365 * 24 * 60 * 60,
                  key_file: str = "key.pem",
                  cert_file: str = "cert.pem",
                  key_size: int = 4096) -> bool:
    """Creates a private/self-signed certificate.

    Args:
        common_name: DNS name of the origin.
        email_address: Contact email address for the cert. Defaults to ``USER@expose-localhost.com``
        country_name: Name of the country. Defaults to ``US``
        locality_name: Name of the city. Defaults to ``New York``
        state_or_province_name: Name of the state/province. Defaults to ``New York``
        organization_name: Name of the organization. Defaults to ``common_name``
        organization_unit_name: Name of the organization unit. Defaults to ``Information Technology``
        validity_start_in_seconds: From when the cert validity begins. Defaults to ``0``.
        validity_end_in_seconds: Expiration duration of the cert. Defaults to ``10 years``
        key_file: Name of the key file.
        cert_file: Name of the certificate.
        key_size: Size of the public key. Defaults to 4096.

    See Also:
        Use ``openssl x509 -inform pem -in cert.crt -noout -text`` to look at the generated cert using openssl.

    Returns:
        bool:
        Boolean flag to indicate whether ``cert.pem`` and ``key.pem`` files are empty.
    """
    ip_ = ip_info()
    country_name = country_name or ip_.get('country', 'US')
    locality_name = locality_name or ip_.get('city', 'New York')
    state_or_province_name = state_or_province_name or ip_.get('region', 'New York')

    if key_size not in [2048, 4096]:
        raise ValueError('Certificate key size should be either 2048 or 4096.')
    signature_bytes = 256 if key_size == 2048 else 512  # Refer: https://crypto.stackexchange.com/a/3508

    # Creates a key pair
    key = OpenSSL.crypto.PKey()
    key.generate_key(type=OpenSSL.crypto.TYPE_RSA, bits=key_size)

    # Creates a self-signed cert
    cert = OpenSSL.crypto.X509()
    cert.get_subject().C = country_name
    cert.get_subject().ST = state_or_province_name
    cert.get_subject().L = locality_name
    cert.get_subject().O = organization_name or common_name[0].upper() + common_name.partition('.')[0][1:]  # noqa: E741
    cert.get_subject().OU = organization_unit_name
    cert.get_subject().CN = common_name
    cert.get_subject().emailAddress = email_address or f"{getuser()}@expose-localhost.com"
    cert.set_serial_number(serial=cert.get_serial_number() or _generate_serial_hash())
    cert.gmtime_adj_notBefore(amount=validity_start_in_seconds)
    cert.gmtime_adj_notAfter(amount=validity_end_in_seconds)
    cert.set_issuer(issuer=cert.get_subject())
    cert.set_pubkey(pkey=key)
    # noinspection PyTypeChecker
    cert.sign(pkey=key, digest=f'sha{signature_bytes}')

    # Writes the cert file into specified names
    with open(cert_file, "w") as f:
        f.write(OpenSSL.crypto.dump_certificate(type=OpenSSL.crypto.FILETYPE_PEM, cert=cert).decode("utf-8"))
    with open(key_file, "w") as f:
        f.write(OpenSSL.crypto.dump_privatekey(type=OpenSSL.crypto.FILETYPE_PEM, pkey=key).decode("utf-8"))

    if os.stat(cert_file).st_size != 0 and os.stat(key_file).st_size != 0:
        time.sleep(1)
        return True
