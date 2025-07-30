import dns.resolver

def resolve_srv_record(ip):
    answers = dns.resolver.resolve(f'_minecraft._tcp.{ip}', 'SRV')
    if answers:
        srv_record = answers[0]
        address = str(srv_record.target).rstrip('.')
        port = srv_record.port
        print(f"解析SRV记录成功: {address}:{port}")
        return address, port