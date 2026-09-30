import RunwayML from "@runwayml/sdk";

// Free call: reads the organization's credit balance and tier limits.
const client = new RunwayML();

const org = await client.organization.retrieve();

console.log(`Credit balance: ${org.creditBalance}`);
console.log(`Max monthly credit spend: ${org.tier.maxMonthlyCreditSpend}`);
console.log(`Models available on this tier: ${Object.keys(org.tier.models).length}`);
