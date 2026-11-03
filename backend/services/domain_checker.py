
import socket
import ssl
import whois
import requests

from datetime import datetime
from urllib.parse import urlparse


def extract_domain(url):
    """Extract domain name from URL."""

    if not url:
        return None

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed_url = urlparse(url)

    return parsed_url.hostname


def check_dns(domain):
    """Check whether domain has DNS records."""

    try:
        ip_address = socket.gethostbyname(domain)

        return {
            "status": "Active",
            "ip_address": ip_address
        }

    except socket.gaierror:
        return {
            "status": "Not Found",
            "ip_address": None
        }


def check_ssl(domain):
    """Check SSL certificate."""

    try:
        context = ssl.create_default_context()

        with socket.create_connection(
            (domain, 443), timeout=5
        ) as connection:

            with context.wrap_socket(
                connection,
                server_hostname=domain
            ) as secure_socket:

                certificate = secure_socket.getpeercert()

                expiry_date = datetime.strptime(
                    certificate["notAfter"],
                    "%b %d %H:%M:%S %Y %Z"
                )

                return {
                    "status": "Valid",
                    "expiry_date": expiry_date.strftime("%Y-%m-%d")
                }

    except Exception:
        return {
            "status": "Invalid or Unavailable",
            "expiry_date": None
        }


def check_domain_age(domain):
    """Check domain registration age using WHOIS."""

    try:
        domain_info = whois.whois(domain)

        creation_date = domain_info.creation_date

        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if not creation_date:
            return {
                "status": "Unknown",
                "age_days": None
            }

        if creation_date.tzinfo:
            creation_date = creation_date.replace(tzinfo=None)

        age_days = (datetime.utcnow() - creation_date).days

        return {
            "status": "Available",
            "age_days": age_days
        }

    except Exception:
        return {
            "status": "Unknown",
            "age_days": None
        }


def verify_domain(url):
    """Perform complete domain verification."""

    domain = extract_domain(url)

    if not domain:
        return {
            "domain": None,
            "status": "Invalid",
            "message": "Invalid domain name"
        }

    dns_result = check_dns(domain)
    ssl_result = check_ssl(domain)
    age_result = check_domain_age(domain)

    warnings = []

    if dns_result["status"] != "Active":
        warnings.append("Domain DNS records not found")

    if ssl_result["status"] != "Valid":
        warnings.append("SSL certificate is invalid or unavailable")

    if age_result["age_days"] is not None:
        if age_result["age_days"] < 180:
            warnings.append("Domain is less than 180 days old")

    return {
        "domain": domain,
        "dns": dns_result,
        "ssl": ssl_result,
        "domain_age": age_result,
        "warnings": warnings
    }
