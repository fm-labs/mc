import logging
import os
import json

from fastapi import Request, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from paypalserversdk.configuration import Environment

from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
from paypalserversdk.logging.configuration.api_logging_configuration import (
    LoggingConfiguration,
    RequestLoggingConfiguration,
    ResponseLoggingConfiguration,
)
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient
from paypalserversdk.controllers.orders_controller import OrdersController
from paypalserversdk.controllers.payments_controller import PaymentsController
from paypalserversdk.models.amount_breakdown import AmountBreakdown
from paypalserversdk.models.amount_with_breakdown import AmountWithBreakdown
from paypalserversdk.models.checkout_payment_intent import CheckoutPaymentIntent
from paypalserversdk.models.order_request import OrderRequest
from paypalserversdk.models.item import Item
from paypalserversdk.models.item_category import ItemCategory
from paypalserversdk.models.money import Money
from paypalserversdk.models.purchase_unit_request import PurchaseUnitRequest
from paypalserversdk.exceptions.error_exception import ErrorException
from paypalserversdk.api_helper import ApiHelper

router = APIRouter(prefix="/paypal")

# ---- PayPal client (same config as your Flask app) ---------------------------------
paypal_client: PaypalServersdkClient = PaypalServersdkClient(
    environment=Environment.SANDBOX,
    client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
        o_auth_client_id=os.getenv("PAYPAL_CLIENT_ID", ""),
        o_auth_client_secret=os.getenv("PAYPAL_CLIENT_SECRET", ""),
    ),
    logging_configuration=LoggingConfiguration(
        log_level=logging.INFO,
        # Disable masking of sensitive headers for Sandbox testing.
        # Set to True in production.
        mask_sensitive_headers=False,
        request_logging_config=RequestLoggingConfiguration(
            log_headers=True, log_body=True
        ),
        response_logging_config=ResponseLoggingConfiguration(
            log_headers=True, log_body=True
        ),
    ),
)

orders_controller: OrdersController = paypal_client.orders
payments_controller: PaymentsController = paypal_client.payments  # kept for parity


# ---- Create order ------------------------------------------------------------------
@router.post("/orders")
async def create_order(request: Request):
    try:
        # Body parity with your Flask version (reads `cart`, though not used below)
        body = await request.json()
        #cart = body.get("cart")  # noqa: F841 (kept for parity / future use)

        currency_code = "EUR"
        total = "1"

        order = orders_controller.create_order(
            {
                "body": OrderRequest(
                    intent=CheckoutPaymentIntent.CAPTURE,
                    purchase_units=[
                        PurchaseUnitRequest(
                            amount=AmountWithBreakdown(
                                currency_code=currency_code,
                                value=total,
                                breakdown=AmountBreakdown(
                                    item_total=Money(currency_code=currency_code, value=total)
                                ),
                            ),
                            items=[
                                Item(
                                    name="Test Item",
                                    unit_amount=Money(currency_code=currency_code, value=total),
                                    quantity="1",
                                    description="Super Fresh Test Item",
                                    sku="sku01test",
                                    category=ItemCategory.DIGITAL_GOODS,
                                )
                            ],
                        )
                    ],
                )
            }
        )

        print(f"{order=}")
        print(ApiHelper.json_serialize(order.body))


        # ApiHelper.json_serialize returns a JSON string — parse to dict for JSONResponse
        payload = json.loads(ApiHelper.json_serialize(order.body))
        return JSONResponse(content=payload, status_code=200)

    except ErrorException as e:
        # Surface PayPal SDK errors cleanly
        detail = getattr(e, "message", None) or str(e)
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        # Generic safeguard
        raise HTTPException(status_code=500, detail=str(e))

# ---- Capture order -----------------------------------------------------------------
@router.post("/orders/{order_id}/capture")
def capture_order(order_id: str):
    try:
        order = orders_controller.capture_order(
            {"id": order_id, "prefer": "return=representation"}
        )
        payload = json.loads(ApiHelper.json_serialize(order.body))
        return JSONResponse(content=payload, status_code=200)

    except ErrorException as e:
        detail = getattr(e, "message", None) or str(e)
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

