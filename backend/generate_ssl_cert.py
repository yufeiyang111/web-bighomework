"""
生成自签名 SSL 证书
用于开发环境的 HTTPS
"""
from OpenSSL import crypto
import os

def generate_self_signed_cert(cert_file='cert.pem', key_file='key.pem'):
    """生成自签名证书"""
    
    # 创建密钥对
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    
    # 创建自签名证书
    cert = crypto.X509()
    cert.get_subject().C = "CN"
    cert.get_subject().ST = "Beijing"
    cert.get_subject().L = "Beijing"
    cert.get_subject().O = "Web Education System"
    cert.get_subject().OU = "Development"
    cert.get_subject().CN = "192.168.95.32"
    
    # 添加 SAN (Subject Alternative Name) 以支持 IP 地址
    cert.add_extensions([
        crypto.X509Extension(b"subjectAltName", False, 
            b"DNS:localhost,IP:127.0.0.1,IP:192.168.95.32")
    ])
    
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 1年有效期
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    
    # 保存证书和密钥
    with open(cert_file, 'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    with open(key_file, 'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
    
    print(f"证书已生成: {cert_file}")
    print(f"密钥已生成: {key_file}")
    return cert_file, key_file

if __name__ == '__main__':
    generate_self_signed_cert()
