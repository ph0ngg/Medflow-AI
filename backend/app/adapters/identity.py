"""
Mock Identity Adapter — mô phỏng nguồn định danh/xác thực được phép kết nối.

Trong prototype: xác minh định dạng CCCD (12 chữ số) và tra cứu danh tính
mô phỏng. Khi có nguồn định danh thật, thay adapter này.
"""
import re

from app.adapters.base import IdentityInfo

# Danh tính mô phỏng theo mã CCCD (demo)
_MOCK_IDENTITIES = {
    "001085000001": IdentityInfo(full_name="Nguyễn Văn A", dob="15/03/1985", cccd="001085000001", valid=True),
    "001090000002": IdentityInfo(full_name="Trần Thị B", dob="22/07/1990", cccd="001090000002", valid=True),
    "001078000003": IdentityInfo(full_name="Lê Văn C", dob="10/11/1978", cccd="001078000003", valid=True),
}

_CCCD_RE = re.compile(r"^\d{12}$")


class MockIdentityAdapter:
    def verify_cccd(self, cccd: str) -> IdentityInfo:
        cccd = (cccd or "").strip()
        if not _CCCD_RE.match(cccd):
            return IdentityInfo(cccd=cccd, valid=False)
        if cccd in _MOCK_IDENTITIES:
            return _MOCK_IDENTITIES[cccd]
        # CCCD hợp lệ nhưng chưa có hồ sơ → bệnh nhân mới
        return IdentityInfo(cccd=cccd, valid=True)
