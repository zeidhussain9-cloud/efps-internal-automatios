"""Slack routing constants.

These are destinations, not business decisions. Owning modules decide when to
use each destination.
"""

WORKSPACE_ID = "T0BNK5NCZL1"
INVENTORY_CHANNEL = "C0BTQGG8VT3"
LEADS_CHANNEL = "C0BTM6PH55L"
PROPERTY_VERIFICATION_CHANNEL = "C0BUHUHRK0Q"
BUGS_CHANNEL = "C0BUHV01L8Y"

CHANNEL_NAMES = {
    INVENTORY_CHANNEL: "#eps-wapi-pannel",
    LEADS_CHANNEL: "#efps-leads",
    PROPERTY_VERIFICATION_CHANNEL: "#epf-prop-aprovals",
    BUGS_CHANNEL: "#eps-runtime-error-bugs-reporting",
}

TOP_LEVEL_COMMAND = "/efps"

# Legacy society-approval routing is intentionally absent. The property
# verification channel is for property verification only.
