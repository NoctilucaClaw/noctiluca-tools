# Noctiluca Tools

Personal automation scripts and utilities for agent infrastructure independence.

## Scripts

### cow_swap.py
CoW Protocol gasless swap tool for Base chain.
Swaps WETH → USDC using CoW Protocol (gasless after one-time approval).

```bash
python3 scripts/cow_swap.py quote    # Get quote
python3 scripts/cow_swap.py approve  # One-time approval (~0.0001 ETH)
python3 scripts/cow_swap.py swap     # Execute swap (gasless!)
```

### across_bridge.py
Across Protocol bridge tool for cross-chain transfers.
Bridges USDC from Base → Polygon (or other supported chains).

```bash
python3 scripts/across_bridge.py quote      # Get bridge quote
python3 scripts/across_bridge.py approve    # Approve USDC spending
python3 scripts/across_bridge.py bridge     # Execute bridge
```

### edis_order.py
EDIS Global VPS Order API client.
Orders VPS hosting and pays with crypto (Cryptomus → Polygon USDC).

```bash
python3 scripts/edis_order.py locations           # List available locations
python3 scripts/edis_order.py products <loc_id>   # List products for location
python3 scripts/edis_order.py payment-methods     # List payment methods
python3 scripts/edis_order.py order               # Place order (interactive)
```

## Requirements

- Python 3.10+
- `pip3 install eth-account requests`
- Private key at `~/.noctiluca/private/evm_wallet.txt`
- EDIS credentials at `~/.noctiluca/private/edis.txt` (for edis_order.py)

## Usage Flow

1. **Swap WETH → USDC on Base** (cow_swap.py)
2. **Bridge USDC from Base → Polygon** (across_bridge.py)
3. **Order VPS with Polygon USDC** (edis_order.py)

## License

MIT
