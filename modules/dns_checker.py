"""
DNS Checker Module
==================
Queries DNS records (A, AAAA, MX, NS, CNAME, TXT, SOA) for a hostname.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import dns.resolver
    import dns.exception
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    logger.warning("dnspython not installed. DNS checks will be limited.")


def check_dns(hostname: str) -> dict:
    """
    Query DNS records for a hostname.

    Args:
        hostname: The hostname to query DNS records for.

    Returns:
        dict with DNS record types as keys and lists of records as values.
    """
    result = {
        "A": [],
        "AAAA": [],
        "MX": [],
        "NS": [],
        "CNAME": [],
        "TXT": [],
        "SOA": None,
        "error": None,
    }

    if not DNS_AVAILABLE:
        result["error"] = "DNS lookup library (dnspython) not available."
        return result

    record_types = ["A", "AAAA", "MX", "NS", "CNAME", "TXT"]

    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(hostname, rtype)
            for rdata in answers:
                if rtype == "MX":
                    result["MX"].append({
                        "priority": rdata.preference,
                        "exchange": str(rdata.exchange).rstrip("."),
                    })
                elif rtype == "NS":
                    result["NS"].append(str(rdata.target).rstrip("."))
                elif rtype == "CNAME":
                    result["CNAME"].append(str(rdata.target).rstrip("."))
                elif rtype == "TXT":
                    result["TXT"].append(str(rdata).strip('"'))
                else:
                    result[rtype].append(str(rdata))

        except dns.resolver.NoAnswer:
            # No records of this type — that's normal
            pass
        except dns.resolver.NXDOMAIN:
            result["error"] = f"Domain '{hostname}' does not exist (NXDOMAIN)."
            logger.warning("DNS NXDOMAIN for %s", hostname)
            return result
        except dns.exception.Timeout:
            logger.warning("DNS timeout for %s record type %s", hostname, rtype)
        except Exception as e:
            logger.warning("DNS query error for %s/%s: %s", hostname, rtype, e)

    # SOA record
    try:
        answers = dns.resolver.resolve(hostname, "SOA")
        for rdata in answers:
            result["SOA"] = {
                "mname": str(rdata.mname).rstrip("."),
                "rname": str(rdata.rname).rstrip("."),
                "serial": rdata.serial,
                "refresh": rdata.refresh,
                "retry": rdata.retry,
                "expire": rdata.expire,
                "minimum": rdata.minimum,
            }
            break
    except Exception:
        pass

    logger.info("DNS check completed for %s", hostname)
    return result
