# Anonymization Measures for LLM Calls

This document summarizes the privacy protections currently implemented to reduce personal data exposure when calling external LLM providers.

## Implemented Measures

1. **Pre-LLM anonymization guard (enabled by configuration)**
   - User message, conversation history, user context, and RAG context are anonymized before prompt construction and before outbound LLM calls.
   - Deterministic placeholders are used so data can be safely restored after response parsing.

2. **Structured recursive anonymization/de-anonymization**
   - The guard processes nested payload structures (objects/lists) so masking is applied consistently, not only to top-level fields.
   - Server-side mapping is maintained for rehydration of placeholders in final responses returned to the client.

3. **Residual direct-PII fail-closed check**
   - Before sending to the LLM, outbound payloads are checked for unmasked direct PII patterns.
   - If residual direct PII is detected, the request is blocked (HTTP 422) instead of being sent.

4. **Response rehydration only inside backend**
   - LLM responses are parsed and placeholders are rehydrated server-side before returning output to the frontend.
   - Rehydration mapping is not exposed to the LLM provider.

5. **Test coverage for anonymization behavior**
   - Dedicated tests validate masking, deterministic placeholders, de-anonymization, and residual detection behavior.

## Scope Statement

- Current implementation provides **strong risk reduction** for direct personal data leakage to LLM providers.
- It does **not** constitute an absolute/legal guarantee of zero leakage in all possible edge cases.

## Practical Operating Notes

- Keep the PII guard enabled in all production environments.
- Treat any route that can call an LLM as in-scope for the same guard and fail-closed policy.
- Re-run test suite after changes to prompt-building, routing, or context-assembly logic.
