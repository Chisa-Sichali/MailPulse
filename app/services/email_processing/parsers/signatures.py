import re


def remove_digital_signatures(body: str) -> str:
    body = re.sub(
        r"-----BEGIN PGP SIGNATURE-----.*?-----END PGP SIGNATURE-----",
        "",
        body,
        flags=re.DOTALL | re.IGNORECASE,
    )
    body = re.sub(
        r"-----BEGIN S/MIME SIGNATURE-----.*?-----END S/MIME SIGNATURE-----",
        "",
        body,
        flags=re.DOTALL | re.IGNORECASE,
    )
    body = re.sub(r"\n--+\s*\n.*", "", body, flags=re.DOTALL)
    return body.strip()
