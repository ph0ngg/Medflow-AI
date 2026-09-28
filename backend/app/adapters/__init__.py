"""
Adapter registry — chọn adapter theo config INTEGRATION_MODE.

Prototype: mock. Tích hợp thật: thêm adapter + cấu hình mode.
"""
from app.config import INTEGRATION_MODE

from app.adapters.base import (
    HISAdapter, InsuranceAdapter, QueueAdapter, PaymentAdapter, IdentityAdapter,
)
from app.adapters.his import MockHISAdapter
from app.adapters.insurance import MockInsuranceAdapter
from app.adapters.queue import MockQueueAdapter
from app.adapters.payment import MockPaymentAdapter
from app.adapters.identity import MockIdentityAdapter


def get_his_adapter() -> HISAdapter:
    if INTEGRATION_MODE == "mock":
        return MockHISAdapter()
    raise NotImplementedError(f"Integration mode '{INTEGRATION_MODE}' chưa hỗ trợ cho HIS")


def get_insurance_adapter() -> InsuranceAdapter:
    if INTEGRATION_MODE == "mock":
        return MockInsuranceAdapter()
    raise NotImplementedError(f"Integration mode '{INTEGRATION_MODE}' chưa hỗ trợ cho Insurance")


def get_queue_adapter() -> QueueAdapter:
    if INTEGRATION_MODE == "mock":
        return MockQueueAdapter()
    raise NotImplementedError(f"Integration mode '{INTEGRATION_MODE}' chưa hỗ trợ cho Queue")


def get_payment_adapter() -> PaymentAdapter:
    if INTEGRATION_MODE == "mock":
        return MockPaymentAdapter()
    raise NotImplementedError(f"Integration mode '{INTEGRATION_MODE}' chưa hỗ trợ cho Payment")


def get_identity_adapter() -> IdentityAdapter:
    if INTEGRATION_MODE == "mock":
        return MockIdentityAdapter()
    raise NotImplementedError(f"Integration mode '{INTEGRATION_MODE}' chưa hỗ trợ cho Identity")
