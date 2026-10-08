const { calculateTotals } = require("../src/services/pricing");

test("one coupon applies its percentage", () => {
  const totals = calculateTotals(
    [{ productId: "mug", quantity: 1 }],
    ["SAVE30"],
  );

  expect(totals.discountPercent).toBe(30);
});
