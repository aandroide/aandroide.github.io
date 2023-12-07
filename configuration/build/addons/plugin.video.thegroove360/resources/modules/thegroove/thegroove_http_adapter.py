
from requests.adapters import HTTPAdapter
import dns.resolver  # NOTE: dnspython package
from resources.lib.tldextract import tldextract


class CustomAdapter(HTTPAdapter):
    def __init__(self, nameservers):
        self.nameservers = nameservers
        self.fqdn = ""
        super().__init__()

    def resolve(self, host, nameservers, record_type):
        dns_resolver = dns.resolver.Resolver()
        dns_resolver.nameservers = nameservers
        answers = dns_resolver.resolve(host, record_type)
        for rdata in answers:
            return str(rdata)

    def get_connection(self, url, proxies=None):
        ext = tldextract.extract(url)
        fqdn = ".".join([ext.subdomain, ext.domain, ext.suffix]).strip(".")

        self.fqdn = "https://" + fqdn
        print("FQDN: {}".format(fqdn))
        print(self.nameservers)
        a_record = self.resolve(fqdn, self.nameservers, 'A')
        print("A record: {}".format(a_record))

        resolved_url = url.replace(fqdn, a_record)  # NOTE: Replace first occurrence only
        print("Resolved URL: {}".format(resolved_url))

        return super().get_connection(resolved_url, proxies=proxies)

    def send(self, request, **kwargs):
        # HTTP headers are case-insensitive (RFC 7230)
        host_header = self.fqdn
        request.headers["host"] = self.fqdn

        print(self.fqdn)

        connection_pool_kwargs = self.poolmanager.connection_pool_kw

        if host_header:
            connection_pool_kwargs["assert_hostname"] = host_header
        elif "assert_hostname" in connection_pool_kwargs:
            # an assert_hostname from a previous request may have been left
            connection_pool_kwargs.pop("assert_hostname", None)

        return super(CustomAdapter, self).send(request, **kwargs)
