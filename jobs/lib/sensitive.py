"""Financial and credential protection.

Two layers:
- `sensitive_sender` / `sensitive_subject`: skip mail before the model reads it.
- `find_secrets`: used by the guardrail hook on every write, so card numbers, SSNs,
  bank details, one-time codes, and passwords can never land in a draft, sheet, doc,
  or calendar event, even if something was read by mistake.
"""
import re

# Owner's rule (2026-10-08): receipts and invoices are fine. Banking, investments, loans,
# and anything carrying an SSN or account number (tax, payroll) are never read.
FINANCIAL_SENDER_DOMAINS = (
    # banks and credit cards
    "chase.com", "bankofamerica.com", "bofa.com", "wellsfargo.com", "citi.com", "capitalone.com",
    "americanexpress.com", "aexp.com", "discover.com", "usbank.com", "ally.com", "marcus.com",
    "schoolsfirstfcu.org", "patelco.org", "mechanicsbank.com",
    # investments and retirement
    "schwab.com", "fidelity.com", "vanguard.com", "robinhood.com", "coinbase.com", "etrade.com",
    "wealthfront.com", "betterment.com", "tiaa.org", "empower.com",
    # loans
    "sofi.com", "studentaid.gov", "nelnet.com", "mohela.com", "aidvantage.com", "navient.com",
    "earnest.com", "laurelroad.com", "rocketmortgage.com",
    # money movement
    "paypal.com", "venmo.com", "zellepay.com", "cash.app", "wise.com",
    # tax and payroll (SSNs, account numbers)
    "irs.gov", "ftb.ca.gov", "intuit.com", "turbotax.com", "adp.com", "gusto.com", "paychex.com", "workday.com",
)
FINANCIAL_SENDER_LOCALPARTS = ("faoemail", "financialaid", "payroll", "statements")

_SUBJECT = re.compile(
    r"verification code|security code|one[- ]time (pass)?code|passcode|2fa|two[- ]factor|"
    r"password reset|reset your password|sign[- ]in attempt|new sign[- ]in|login attempt|"
    r"statement is (ready|available)|direct deposit|\bW-?2\b|\b1099\b|tax (form|return|document)|"
    r"financial aid|bank account|account number|routing number|"
    r"\bloan\b|loan (payment|balance|servicer)|student loan|mortgage|"
    r"brokerage|portfolio|401\(?k\)?|\bIRA\b|investment account|credit card statement|minimum payment",
    re.I,
)

# Gmail query clause the skills append to every inbox and sent-mail search.
GMAIL_EXCLUDE = "-has:attachment " + " ".join(
    f"-from:{d}" for d in ("chase.com", "bankofamerica.com", "wellsfargo.com", "capitalone.com",
                           "americanexpress.com", "schwab.com", "fidelity.com", "vanguard.com",
                           "robinhood.com", "sofi.com", "studentaid.gov", "nelnet.com", "mohela.com",
                           "aidvantage.com", "paypal.com", "venmo.com", "irs.gov", "intuit.com")
)


def sensitive_sender(addr: str) -> bool:
    addr = (addr or "").lower().strip()
    local, _, domain = addr.partition("@")
    if any(domain == d or domain.endswith("." + d) for d in FINANCIAL_SENDER_DOMAINS):
        return True
    return any(p in local for p in FINANCIAL_SENDER_LOCALPARTS)


def sensitive_subject(subject: str) -> bool:
    return bool(_SUBJECT.search(subject or ""))


def _luhn(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        n = int(ch)
        if alt:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        alt = not alt
    return total % 10 == 0


# 15-16 digits (Amex, Visa/MC), not glued to URLs or ids (Gmail thread ids are 19 digits after "thread-f:")
_CARD = re.compile(r"(?<![\w:/=#.-])(?:\d[ -]?){14,15}\d(?![\w-])")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_BANK = re.compile(r"\b(routing|account|acct|iban|swift)\s*(number|no\.?|#)?\s*[:#]?\s*(?=[A-Z0-9]*\d)[A-Z0-9]{6,}", re.I)
_OTP = re.compile(r"\b(code|passcode|otp|pin)\b[^0-9\n]{0,20}\b\d{6,8}\b", re.I)
_PASSWORD = re.compile(r"\bpass(word|wd|phrase)?\s*[:=]\s*\S+", re.I)


def find_secrets(text: str) -> list[str]:
    """Return the kinds of secrets found (never the values themselves)."""
    text = text or ""
    found = []
    for m in _CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if len(digits) in (15, 16) and _luhn(digits):
            found.append("card number")
            break
    if _SSN.search(text):
        found.append("SSN")
    if _BANK.search(text):
        found.append("bank account detail")
    if _OTP.search(text):
        found.append("one-time code")
    if _PASSWORD.search(text):
        found.append("password")
    return found
