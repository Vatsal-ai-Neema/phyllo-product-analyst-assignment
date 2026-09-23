orders = [
    {"id":"ord_1001","status":"shipped","subtotal":4500,"tax":371,"shipping":599,"total":5470},
    {"id":"ord_1002","status":"delivered","subtotal":2200,"tax":181,"shipping":0,"total":2381},
    {"id":"ord_1003","status":"refunded","subtotal":8900,"tax":734,"shipping":599,"total":10233},
    {"id":"ord_1004","status":"shipped","subtotal":6200,"tax":511,"shipping":599,"total":6810},
    {"id":"ord_1005","status":"delivered","subtotal":1800,"tax":148,"shipping":599,"total":2547},
    {"id":"ord_1006","status":"shipped","subtotal":44.0,"tax":3.63,"shipping":5.99,"total":53.62},
]

print("Sum-check (subtotal+tax+shipping vs total), cents:")
for o in orders:
    computed = o["subtotal"]+o["tax"]+o["shipping"]
    print(f"  {o['id']}: computed={computed}, documented total={o['total']}, match={abs(computed-o['total'])<0.001}")

# normalize ord_1006 to cents (docs say integer smallest-unit; this order is in decimal dollars)
def norm_total(o):
    if o["id"] == "ord_1006":
        return round(o["total"]*100)
    return o["total"]

all_totals = {o["id"]: norm_total(o) for o in orders}
print("\nNormalized totals (cents):", all_totals)

excl_refund = sum(v for k,v in all_totals.items() if k != "ord_1003")
incl_refund = sum(all_totals.values())
print(f"\nSum excluding refunded ord_1003: {excl_refund} cents = ${excl_refund/100:.2f}")
print(f"Sum including refunded ord_1003: {incl_refund} cents = ${incl_refund/100:.2f}")

# variant using recomputed total for ord_1004 (7310 instead of 6810)
alt = dict(all_totals); alt["ord_1004"] = 7310
excl_refund_alt = sum(v for k,v in alt.items() if k != "ord_1003")
print(f"\nIf using subtotal+tax+shipping for ord_1004 instead of its 'total' field:")
print(f"  Sum excluding refund: {excl_refund_alt} cents = ${excl_refund_alt/100:.2f}")
