
import os
import re
import requests


DATA_GOV_API_URL = "https://api.data.gov.in/resource/"


def verify_mca(cin, company_name=None):
    result = {
        "cin": cin.strip().upper() if cin else None,
        "company_name": company_name,
        "status": "manual_check_required",
        "source": "data.gov.in",
        "company_data": None,
        "warnings": [],
        "message": ""
    }

    if not cin or not cin.strip():
        result["warnings"].append("CIN was not provided.")
        result["message"] = "A CIN is required for MCA lookup."
        return result

    cin = cin.strip().upper()

    # Basic CIN format validation
    if not re.fullmatch(r"[A-Z0-9]{21}", cin):
        result["status"] = "invalid_input"
        result["warnings"].append("CIN format is invalid.")
        result["message"] = "Please provide a valid 21-character CIN."
        return result

    api_key = os.getenv("DATA_GOV_API_KEY")
    resource_id = os.getenv("DATA_GOV_RESOURCE_ID")

    if not api_key or not resource_id:
        result["warnings"].append(
            "Government Open Data API key or resource ID is not configured."
        )
        result["message"] = (
            "Please verify this CIN through the official MCA portal."
        )
        result["official_mca_url"] = (
            "https://www.mca.gov.in/content/mca/global/en/"
            "mca/fo-llp-services/company-llp-name-search.html"
        )
        return result

    try:
        url = f"{DATA_GOV_API_URL}{resource_id}"

        params = {
            "api-key": api_key,
            "format": "json",
            "filters[CIN]": cin,
            "limit": 1
        }

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()
        payload = response.json()

        records = payload.get("records", [])

        if not records:
            result["status"] = "record_not_found"
            result["message"] = (
                "No matching record was returned by the configured dataset. "
                "This does not prove that the company does not exist."
            )
            return result

        record = records[0]

        # Normalize returned field names
        normalized_record = {
            str(key).lower(): value
            for key, value in record.items()
        }

        returned_cin = (
            normalized_record.get("cin")
            or normalized_record.get("corporateidentificationnumber")
        )

        returned_name = (
            normalized_record.get("companyname")
            or normalized_record.get("company_name")
        )

        returned_status = (
            normalized_record.get("companystatus")
            or normalized_record.get("company_status")
        )

        returned_address = (
            normalized_record.get("registered_office_address")
            or normalized_record.get("registeredofficeaddress")
        )

        if returned_cin and returned_cin.upper() != cin:
            result["status"] = "record_mismatch"
            result["warnings"].append(
                "Returned CIN does not match the requested CIN."
            )
            result["message"] = "The returned record could not be matched."
            return result

        result["company_data"] = {
            "cin": returned_cin,
            "company_name": returned_name,
            "company_status": returned_status,
            "registered_office_address": returned_address,
            "registration_date": (
                normalized_record.get("companyregistrationdate_date")
                or normalized_record.get("companyregistrationdate")
            ),
            "company_class": normalized_record.get("companyclass"),
            "company_category": normalized_record.get("companycategory"),
            "registered_state": normalized_record.get("companystatecode")
        }

        if company_name and returned_name:
            if company_name.strip().casefold() != returned_name.strip().casefold():
                result["warnings"].append(
                    "Provided company name does not exactly match the dataset name."
                )
                result["status"] = "name_mismatch"
            else:
                result["status"] = "record_found"
        else:
            result["status"] = "record_found"

        result["message"] = (
            "A matching record was returned by the configured "
            "Government Open Data dataset. Confirm current details "
            "on the official MCA portal."
        )

        result["dataset_updated_date"] = payload.get("updated_date")

    except requests.Timeout:
        result["status"] = "service_unavailable"
        result["warnings"].append("Government data request timed out.")

    except requests.RequestException as exc:
        result["status"] = "service_unavailable"
        result["warnings"].append(f"Government data request failed: {str(exc)}")

    except (ValueError, TypeError) as exc:
        result["status"] = "service_error"
        result["warnings"].append(f"Invalid API response: {str(exc)}")

    return result
