"""shop: a small Orders service used as the "system under test" for every module.

It is deliberately layered (domain / db / gateways / services / api) so each layer
has a different testing story:

- ``domain``   -- pure Python, no I/O. Unit tests + property-based tests live here.
- ``db``       -- SQLAlchemy models and repositories. Needs a real (or real-ish) database.
- ``gateways`` -- outbound calls to systems we don't own (a payment processor, Redis).
                  These are the natural home for test doubles.
- ``services`` -- orchestrates the above. This is what "integration" usually means.
- ``api``      -- the FastAPI app: HTTP in, HTTP out.

See docs/05-backend-testing-playbook.md for the reasoning behind this shape.
"""
