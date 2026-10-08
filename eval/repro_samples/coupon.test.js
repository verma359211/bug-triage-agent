const { calculateTotals } = require("../src/services/pricing");

test("combined discounts stop at fifty percent", () => {
  const totals = calculateTotals(
    [{ productId: "mug", quantity: 1 }],
    ["SAVE30", "VIP30"],
  );

  expect(totals.discountPercent).toBe(50);
});
