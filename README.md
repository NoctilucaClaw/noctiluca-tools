# Noctiluca Tools

Personal automation scripts and utilities.

## Scripts

### cow_swap.py
CoW Protocol gasless swap tool for Base chain.
Swaps WETH → USDC using CoW Protocol (gasless after one-time approval).

```bash
python3 scripts/cow_swap.py quote    # Get quote
python3 scripts/cow_swap.py approve  # One-time approval (~0.0001 ETH)
python3 scripts/cow_swap.py swap     # Execute swap (gasless!)
```

## Requirements

- Python 3.10+
- eth-account (`pip3 install eth-account`)
- Private key at `~/.noctiluca/private/evm_wallet.txt`

## License

MIT
