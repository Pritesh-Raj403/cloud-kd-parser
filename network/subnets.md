# Subnet allocation for 10.20.0.0/16

Rule: allocate largest to smallest, start at 10.20.0.0, each subnet right after the previous one, smallest prefix that fits. Usable hosts = 2^(32-prefix) - 2.

## Working

| Subnet | Hosts needed | Prefix chosen | Why |
|---|---|---|---|
| app | 1000 | /22 | /23 gives 510 (too small), /22 gives 2^10 - 2 = 1022 |
| public | 250 | /24 | /25 gives 126 (too small), /24 gives 2^8 - 2 = 254 |
| data | 100 | /25 | /26 gives 62 (too small), /25 gives 2^7 - 2 = 126 |
| management | 20 | /27 | /28 gives 14 (too small), /27 gives 2^5 - 2 = 30 |

## Result

| Subnet | Network address | Prefix | Usable host range | Broadcast | Usable hosts |
|---|---|---|---|---|---|
| app | 10.20.0.0 | /22 | 10.20.0.1 - 10.20.3.254 | 10.20.3.255 | 1022 |
| public | 10.20.4.0 | /24 | 10.20.4.1 - 10.20.4.254 | 10.20.4.255 | 254 |
| data | 10.20.5.0 | /25 | 10.20.5.1 - 10.20.5.126 | 10.20.5.127 | 126 |
| management | 10.20.5.128 | /27 | 10.20.5.129 - 10.20.5.158 | 10.20.5.159 | 30 |

Each subnet starts where the previous one ended: app ends at 10.20.3.255, so public starts at 10.20.4.0; public ends at 10.20.4.255, so data starts at 10.20.5.0; data ends at 10.20.5.127, so management starts at 10.20.5.128.

## NACL explanation

A NACL is stateless: it does not remember that an inbound request was allowed, so the reply packet is judged on its own as a new packet. That is why replies need their own rules (ephemeral ports 1024-65535 going back to clients, and replies coming back from the app subnet).

Rules are checked from the lowest number upwards and the first match wins. The deny for 198.51.100.0/24 must have a lower number than the allow rules for TCP 80/443 from anywhere. If the allow came first, traffic from the abusive range would match the allow and never reach the deny.
