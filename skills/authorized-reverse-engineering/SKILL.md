---
name: authorized-reverse-engineering
description: Plan lawful, authorized software and binary reverse engineering for debugging, interoperability, incident response, and security research in isolated environments.
---

# Authorized Reverse Engineering

1. Confirm ownership or explicit authorization and define the permitted scope before interacting with a target.
2. Preserve the original artifact; record hashes, source, version, platform, and acquisition context.
3. Start with static inspection: file type, metadata, strings, imports, symbols, dependencies, and disassembly/decompilation as appropriate.
4. Use Ghidra or radare2 for static binary analysis; use Frida for dynamic instrumentation only on owned/authorized test targets; use mitmproxy only for traffic from systems you control or are authorized to test.
5. Use a disposable VM/container, snapshots, no production credentials, restricted networking, and benign test inputs. Treat unknown binaries as hostile.
6. Record hypotheses separately from confirmed observations. Validate conclusions with a second method when possible.
7. Do not attempt credential theft, unauthorized access, persistence, exfiltration, or bypass of third-party protections. Stop if authorization or scope is unclear.
8. Produce a reproducible report with hashes, steps, observations, limitations, and cleanup instructions.
