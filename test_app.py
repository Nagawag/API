import pytest
from fastapi.testclient import TestClient
from app import (
    app,
    validate_amount,
    validate_currency,
    validate_email,
    generate_id,
    PaymentService,
    FakeRepository
)

client = TestClient(app)


def test_validate_amount():
    assert validate_amount(100)
    assert not validate_amount(0)


def test_validate_currency():
    assert validate_currency("usd")
    assert not validate_currency("us")


def test_validate_email():
    assert validate_email("alice@test.com")
    assert not validate_email("alicetest.com")


def test_generate_id():
    assert generate_id("pay").startswith("pay_")


def setup_service():
    repo = FakeRepository()
    return PaymentService(repo)


def test_create_customer():
    service = setup_service()
    customer = service.create_customer("Alice", "alice@test.com")
    assert customer["name"] == "Alice"


def test_create_payment():
    service = setup_service()
    customer = service.create_customer("Bob", "bob@test.com")
    payment = service.create_payment(customer["id"], 100, "usd")
    assert payment["status"] == "pending"


def test_capture_payment():
    service = setup_service()
    customer = service.create_customer("Bob", "bob@test.com")
    payment = service.create_payment(customer["id"], 100, "usd")
    result = service.capture(payment["id"])
    assert result["status"] == "succeeded"


def test_refund():
    service = setup_service()
    customer = service.create_customer("Tom", "tom@test.com")
    payment = service.create_payment(customer["id"], 200, "usd")
    service.capture(payment["id"])
    refund = service.refund(payment["id"], 100)
    assert refund["amount"] == 100


def test_create_customer_api():
    response = client.post(
        "/customers",
        json={
            "name": "Alice",
            "email": "alice@test.com"
        }
    )
    assert response.status_code == 200


def test_create_payment_api():
    customer = client.post(
        "/customers",
        json={"name": "Bob", "email": "bob@test.com"}
    ).json()

    response = client.post(
        "/payments",
        json={
            "customer_id": customer["id"],
            "amount": 100,
            "currency": "usd"
        }
    )

    assert response.status_code == 200