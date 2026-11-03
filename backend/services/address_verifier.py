
import re


def normalize_address(address):
    if not address:
        return ""

    address = address.lower().strip()
    address = re.sub(r"[^a-z0-9\s]", " ", address)
    address = re.sub(r"\s+", " ", address)

    return address


def verify_address(provided_address, registered_address=None):
    result = {
        "provided_address": provided_address,
        "registered_address": registered_address,
        "status": "manual_check_required",
        "match_percentage": None,
        "warnings": [],
        "message": ""
    }

    if not provided_address:
        result["warnings"].append("Company address was not provided.")
        result["message"] = "Please provide a company address."
        return result

    if not registered_address:
        result["warnings"].append(
            "No registered address was available for comparison."
        )
        result["message"] = (
            "Address comparison requires an address from an authoritative record."
        )
        return result

    provided = normalize_address(provided_address)
    registered = normalize_address(registered_address)

    provided_words = set(provided.split())
    registered_words = set(registered.split())

    if not provided_words or not registered_words:
        result["warnings"].append("Address information is incomplete.")
        result["message"] = "Unable to compare the supplied addresses."
        return result

    common_words = provided_words.intersection(registered_words)

    # Similarity is based on shared address tokens.
    # It is not a geographic or legal verification.
    similarity = (
        len(common_words) /
        max(len(provided_words), len(registered_words))
    ) * 100

    result["match_percentage"] = round(similarity, 2)

    if similarity >= 80:
        result["status"] = "strong_text_match"
        result["message"] = (
            "The supplied address has a strong text match "
            "with the registered address."
        )

    elif similarity >= 50:
        result["status"] = "partial_text_match"
        result["warnings"].append(
            "Only part of the supplied address matches the registered address."
        )
        result["message"] = "Manual address verification is recommended."

    else:
        result["status"] = "address_mismatch"
        result["warnings"].append(
            "The supplied address differs significantly from the registered address."
        )
        result["message"] = "Please review the address details."

    result["warnings"].append(
        "Text similarity does not prove that a physical office exists "
        "at this address."
    )

    return result
