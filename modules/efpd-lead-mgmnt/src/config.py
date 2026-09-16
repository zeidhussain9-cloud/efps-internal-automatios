"""Lead runtime configuration."""
from __future__ import annotations
import os
AWS_REGION=os.getenv("AWS_REGION","us-east-1")
DDB_PREFIX=os.getenv("EFPS_DDB_PREFIX","efps")
DDB_LEADS=f"{DDB_PREFIX}-leads";DDB_INTERACTIONS=f"{DDB_PREFIX}-interactions";DDB_SESSIONS=f"{DDB_PREFIX}-sessions";DDB_AUDIT=f"{DDB_PREFIX}-lead-audit"
LEADS_CHANNEL=os.getenv("EFPS_LEADS_CHANNEL","C0BTM6PH55L");APPROVALS_CHANNEL=os.getenv("EFPS_APPROVALS_CHANNEL","C0BUHUHRK0Q");PANEL_CHANNEL=os.getenv("EFPS_PANEL_CHANNEL","C0BTQGG8VT3")
