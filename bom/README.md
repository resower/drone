# bom

Rev C parts list with prices and the script that produces it.

| File | Contents |
|---|---|
| `CF2_RevC_BOM.csv` | System, part, quantity, unit and line price (USD), mass, price basis and a fit note for each line. |
| `bom_totals.json` | Subtotal, 25 % spares and crash reserve, total, estimated all-up mass. |
| `bom_revc.py` | Builds the CSV and totals from the part table. Run from this folder. |

Totals: subtotal US$1,354.59, spares reserve US$338.65, total about US$1,693. Estimated mass with the real parts is about 1.93 kg.

## Caveats

- Prices are from vendor pages at the time of writing; some items were sold out, and the `price_basis` column says which price is a listing, a fallback or an estimate. Re-check before ordering.
- The wheel-drive motors and the companion computer are estimates.
- The CAD in `../cad` still uses placeholder sizes. The fit notes record where a real part does not fit: the J1/J2 servos against the arm fairing, the 4-in-1 ESC board (45.6 x 44 mm) and the Pi Zero 2 W (65 mm) against their bays.
