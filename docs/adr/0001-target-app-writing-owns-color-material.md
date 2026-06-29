# Target App Writing Owns Color Material

WalBridge will treat Target App adapters as Color Material renderers and keep filesystem writes, resolved path/name/flag policy, user-file protection, and failure reporting in a deeper Target App writing module. This keeps the Target App catalogue declarative while giving the Sync Run one interface for writing generated material; the rejected alternative was to keep side-effecting per-writer adapters, which made path safety and fallback behavior local to each adapter instead of local to the writing module.
